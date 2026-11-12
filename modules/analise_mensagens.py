"""Módulo 1: análise de mensagens (RF01, RF02 e RF03).

Combina duas fontes de "inteligência":
1. o classificador treinado (TF-IDF + modelo escolhido em models/treinamento.py),
   que aprendeu com exemplos rotulados;
2. regras escritas à mão, que procuram sinais concretos de golpe e mostram ao
   usuário POR QUE a mensagem parece golpe (RF03: exibir os indicadores).

O nível final é o MAIS ALTO entre o que o modelo indica e o que as regras indicam.
Assim, um golpe com palavras que o modelo nunca viu ainda pode ser pego pelas
regras, e o usuário sempre recebe uma explicação concreta.
"""

import re
from dataclasses import dataclass, field
from functools import lru_cache   # guarda o resultado de uma função para não repetir trabalho
from pathlib import Path

import joblib  # carrega o modelo salvo em arquivo .pkl

from modules.analise_links import analisar_link
from utils.processamento_texto import limitar, normalizar

# Pasta onde ficam classificador.pkl e vectorizer.pkl
PASTA_MODELOS = Path(__file__).resolve().parent.parent / "models"
# Níveis em ordem crescente de risco. A posição na lista serve para comparar níveis.
NIVEIS = ["legitima", "suspeita", "alto_risco"]
# Como cada nível aparece na tela. Usamos "Baixo risco" em vez de "Legítima"
# para não passar a ideia de certeza (seção 12 do planejamento).
ROTULOS = {"legitima": "Baixo risco", "suspeita": "Atenção", "alto_risco": "Alto risco"}


@dataclass
class Regra:
    """Uma regra de detecção."""
    nome: str          # nome curto mostrado ao usuário
    explicacao: str    # por que isso é perigoso
    peso: int          # importância do sinal (1 = fraco, 4 = muito forte)
    padroes: list      # expressões regulares procuradas no texto (sem acento e em minúsculas)
    categoria: str     # usada nas estatísticas do histórico


# Lista de regras. Para ensinar um sinal novo ao CyberBot, basta adicionar uma Regra aqui.
# Observação: \b nas expressões significa "início ou fim de palavra".
REGRAS = [
    Regra("Pede senha ou código", "Pede senha, token ou código recebido por SMS. Nenhuma empresa séria pede isso.", 4,
          [r"\bsenha", r"\btoken\b", r"codigo (de )?(verificacao|seguranca|de \d|que (chegou|recebeu|enviamos))", r"\b6 digitos", r"codigo recebido"], "credenciais"),
    Regra("Pede dados pessoais", "Pede CPF, dados do cartão, documento ou selfie.", 3,
          [r"\bcpf\b", r"dados (do|bancarios|do seu) ?cartao", r"numero do cartao", r"dados bancarios", r"\bselfie\b", r"foto do (seu )?documento", r"confirme seus dados", r"informe seus dados", r"atualize seus dados"], "dados_pessoais"),
    Regra("Pressa ou ameaça", "Cria pressa ou ameaça (bloqueio, prazo curto, multa) para você agir sem pensar.", 2,
          [r"\burgente", r"\bimediatamente", r"\bso hoje\b", r"ainda hoje", r"ate hoje", r"em ate \d+ ?(h|hora|horas|minutos)", r"\bultimo aviso", r"sera (bloquead|cancelad|encerrad|desativad|suspens|cortad)", r"\bexpira", r"\bprisao\b", r"\bprotestad"], "urgencia"),
    # Peso baixo de propósito: muita mensagem normal fala de Pix ("fiz o Pix do churrasco").
    Regra("Pede dinheiro ou Pix", "Pede que você faça um Pix, transferência ou depósito.", 1,
          [r"\bpix\b", r"\btransfir", r"\btransferencia", r"\bdeposit", r"\bchave\b"], "dinheiro"),
    Regra("Taxa antecipada", "Pede uma taxa para liberar prêmio, empréstimo, entrega ou emprego. Isso é típico de golpe.", 3,
          [r"taxa (de )?(liberacao|adesao|cadastro|verificacao|antecipada)", r"pague (a|o) (taxa|frete)", r"para (liberar|receber|sacar|ativar)", r"kit de treinamento", r"deposito inicial"], "taxa"),
    Regra("Prêmio ou ganho fácil", "Promete prêmio, sorteio ou lucro fácil.", 2,
          [r"\bparabens", r"\bganhou\b", r"\bsorteado", r"\bpremio", r"\bresgat", r"dobre seu dinheiro", r"retorno de \d+%", r"\bgratis\b", r"ganhe (r\$|dinheiro|um)"], "recompensa"),
    Regra("Número novo", "Diz que trocou de número. Ligue para o número antigo para confirmar quem é.", 2,
          [r"numero novo", r"novo numero", r"troquei de numero", r"mudei de numero", r"esse e meu numero", r"anota esse numero"], "engenharia_social"),
    # Peso 1: citar um banco não é golpe, mas soma com outros sinais.
    Regra("Imita empresa ou órgão", "Diz falar em nome de banco, governo ou empresa conhecida. Confirme pelo canal oficial.", 1,
          [r"\bbanco\b", r"central de seguranca", r"receita federal", r"\binss\b", r"\bdetran\b", r"\bcorreios\b", r"\bgov\.?br\b", r"\bserasa\b", r"\bgerente\b",
           r"\bitau\b", r"\bbradesco\b", r"\bnubank\b", r"\bsantander\b", r"\bcaixa\b", r"suporte do whatsapp"], "imitacao"),
    Regra("Acesso remoto", "Pede para instalar um aplicativo. Com ele o golpista controla o seu celular.", 4,
          [r"\banydesk\b", r"\bteamviewer\b", r"instale o (aplicativo|app)", r"instalar o aplicativo", r"aplicativo de seguranca"], "acesso_remoto"),
    Regra("Conta segura ou motoboy", "Fala em 'conta segura' ou em buscar seu cartão. Bancos nunca fazem isso.", 4,
          [r"conta segura", r"\bmotoboy\b", r"buscar (o )?(seu )?cartao"], "engenharia_social"),
]

# Compila as expressões uma única vez, quando o módulo é carregado (fica mais rápido).
_REGRAS_COMPILADAS = [(r, [re.compile(p) for p in r.padroes]) for r in REGRAS]

# Encontra links dentro de uma mensagem para mandá-los à análise de links.
_RE_LINKS = re.compile(r"(https?://\S+|www\.\S+|\b[\w-]+(?:\.[\w-]+)*\.(?:com|net|org|xyz|top|info|online|site|click|br|ly|io|me)(?:/\S*)?)", re.I)


@dataclass
class ResultadoMensagem:
    """Tudo que a análise descobriu sobre uma mensagem."""
    nivel: str                       # legitima | suspeita | alto_risco (ou "indefinido" quando há erro)
    rotulo: str                      # texto mostrado na tela (ex.: "Alto risco")
    pontuacao: float                 # 0 a 1: chance estimada de ser golpe (suspeita + alto risco)
    previsao_modelo: str = ""        # o que o classificador sozinho previu
    confianca_modelo: float = 0.0    # probabilidade da classe prevista
    probabilidades: dict = field(default_factory=dict)  # probabilidade de cada classe
    indicadores: list = field(default_factory=list)     # [{nome, explicacao, categoria, peso}]
    links: list = field(default_factory=list)           # resultados de analise_links
    erro: str = ""


@lru_cache(maxsize=1)
def carregar_modelo():
    """Carrega o modelo e o vetorizador do disco.

    Com @lru_cache os arquivos são lidos só na primeira chamada; nas próximas
    a função devolve o que já está na memória.
    """
    clf = joblib.load(PASTA_MODELOS / "classificador.pkl")
    vec = joblib.load(PASTA_MODELOS / "vectorizer.pkl")
    return clf, vec


def encontrar_indicadores(texto: str) -> list:
    """Aplica todas as regras e devolve as que encontraram algo no texto."""
    t = normalizar(texto)  # minúsculas e sem acento, igual aos padrões das regras
    achados = []
    for regra, padroes in _REGRAS_COMPILADAS:
        # any(): basta UM padrão da regra aparecer para a regra valer.
        if any(p.search(t) for p in padroes):
            achados.append({"nome": regra.nome, "explicacao": regra.explicacao, "categoria": regra.categoria, "peso": regra.peso})
    return achados


def nivel_por_regras(indicadores: list, links: list) -> str:
    """Calcula o nível só com base nas regras (sem o modelo).

    Soma os pesos dos indicadores e acrescenta pontos para links suspeitos.
    Os limites (3 e 6) foram ajustados para quase não marcar mensagens normais
    como suspeitas: na base de treino só 1 de 64 mensagens legítimas foi marcada.
    """
    pontos = sum(i["peso"] for i in indicadores)
    pontos += sum(3 if l.nivel == "alto" else 1 if l.nivel == "atencao" else 0 for l in links)
    if pontos >= 6:
        return "alto_risco"
    if pontos >= 3:
        return "suspeita"
    return "legitima"


def analisar_mensagem(texto: str) -> ResultadoMensagem:
    """Função principal do módulo: recebe o texto e devolve o ResultadoMensagem."""
    # 1) Valida a entrada. Textos muito curtos não dão para analisar.
    texto = limitar(texto).strip()
    if len(texto) < 5:
        return ResultadoMensagem(nivel="indefinido", rotulo="Indefinido", pontuacao=0.0,
                                 erro="Cole uma mensagem com pelo menos algumas palavras.")

    # 2) Pergunta ao modelo. O vetorizador transforma o texto em números (TF-IDF)
    #    e o classificador devolve a probabilidade de cada classe.
    clf, vec = carregar_modelo()
    proba = clf.predict_proba(vec.transform([texto]))[0]
    probs = {c: float(p) for c, p in zip(clf.classes_, proba)}   # ex.: {"legitima": 0.1, ...}
    previsto = max(probs, key=probs.get)                         # classe com maior probabilidade

    # 3) Aplica as regras e analisa até 5 links encontrados na mensagem.
    indicadores = encontrar_indicadores(texto)
    links = [analisar_link(u.rstrip(".,;:!?)")) for u in _RE_LINKS.findall(texto)[:5]]  # tira pontuação do fim
    links = [l for l in links if not l.erro]                     # descarta o que não era link de verdade
    for l in links:
        if l.nivel != "baixo":
            indicadores.append({"nome": "Link suspeito", "categoria": "link", "peso": 3 if l.nivel == "alto" else 1,
                                "explicacao": f"O link {l.dominio} tem {len(l.indicadores)} sinal(is) de alerta."})

    # 4) Nível pelas regras. Os links já entram pelo parâmetro "links", por isso
    #    tiramos o indicador "Link suspeito" da lista para não contar duas vezes.
    por_regras = nivel_por_regras([i for i in indicadores if i["nome"] != "Link suspeito"], links)

    # 5) Fica com o nível MAIS ALTO entre modelo e regras (comparando a posição em NIVEIS).
    nivel = max(previsto, por_regras, key=NIVEIS.index)

    return ResultadoMensagem(
        nivel=nivel, rotulo=ROTULOS[nivel],
        pontuacao=round(probs.get("suspeita", 0) + probs.get("alto_risco", 0), 3),
        previsao_modelo=previsto, confianca_modelo=round(probs[previsto], 3), probabilidades=probs,
        indicadores=indicadores, links=links,
    )
