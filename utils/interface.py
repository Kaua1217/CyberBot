"""Peças de interface reaproveitadas pelas páginas do Streamlit.

Regra do projeto: a lógica de análise fica em modules/. Este arquivo só
MOSTRA os resultados na tela, para que a interface não misture regras de
negócio com apresentação (seção 5 do planejamento).
"""

import html
import re
import uuid  # gera identificadores aleatórios (usado para a sessão anônima)
from pathlib import Path

import streamlit as st

from modules.historico import Historico

# Pasta com o logo, os avatares e o arquivo de estilo.
ASSETS = Path(__file__).resolve().parent.parent / "assets"
AVATAR_BOT = str(ASSETS / "avatar_bot.svg")
AVATAR_VOCE = str(ASSETS / "avatar_voce.svg")

# Mensagens usam legitima/suspeita/alto_risco e links usam baixo/atencao/alto.
# Aqui juntamos os dois num nome de estilo só (a classe CSS do cartão).
ESTILO = {"legitima": "baixo", "baixo": "baixo", "suspeita": "atencao", "atencao": "atencao", "alto_risco": "alto", "alto": "alto"}
SELO = {"alto": "Alto risco", "atencao": "Atenção", "baixo": "Baixo risco"}
# Quantos dos 3 tracinhos do medidor ficam acesos em cada nível.
TRACOS = {"baixo": 1, "atencao": 2, "alto": 3}

# Aviso mostrado em todo resultado (seção 12: não apresentar a análise como certeza).
AVISO = ("Sou um verificador automático e posso errar. \"Baixo risco\" quer dizer só que não encontrei sinais "
         "dentro dos meus critérios. Na dúvida, confirme pelo canal oficial.")


def e(texto) -> str:
    """Escapa o texto antes de colocá-lo no HTML.

    Tudo que pode ter vindo do usuário (um domínio, um trecho da mensagem) passa
    por aqui, para que "<script>" apareça como texto e nunca seja executado.
    """
    return html.escape(str(texto))


def preparar_app():
    """Configuração comum a todas as páginas.

    É chamada uma vez pelo app.py a cada execução. Como a barra lateral é
    desenhada aqui (e não em cada página), as opções do usuário continuam
    marcadas quando ele troca de página.
    """
    st.set_page_config(page_title="CyberBot", page_icon=str(ASSETS / "marca.svg"), layout="centered")
    # Carrega o estilo próprio do projeto (fontes, cartões, cores dos níveis).
    st.markdown(f"<style>{(ASSETS / 'estilo.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    st.logo(str(ASSETS / "logo.svg"), size="large", icon_image=str(ASSETS / "marca.svg"))

    # st.session_state guarda dados enquanto a aba do navegador estiver aberta.
    # Criamos um identificador anônimo para a sessão: assim o histórico funciona
    # sem cadastro e sem coletar nome ou e-mail (seção 8 do planejamento).
    # Quando o histórico está ligado, o identificador também vai para o endereço
    # da página (?s=...). Assim, se o app for reiniciado ou a página recarregada
    # nesse mesmo endereço, o usuário volta a ver as análises que salvou.
    if "sessao_id" not in st.session_state:
        da_url = st.query_params.get("s", "")
        st.session_state.sessao_id = da_url if re.fullmatch(r"[0-9a-f]{32}", da_url) else uuid.uuid4().hex

    with st.sidebar:
        st.markdown('<p class="cb-lema">Um segundo par de olhos antes de você clicar, pagar ou responder.</p>',
                    unsafe_allow_html=True)
        # O histórico começa DESLIGADO. O usuário escolhe se quer salvar (RF08).
        st.toggle("Guardar meu histórico", key="salvar_historico",
                  help="Desligado por padrão. Guarda só o resultado de cada análise, por até 30 dias.")
        # A opção de salvar o texto só aparece se o histórico estiver ligado.
        if st.session_state.get("salvar_historico"):
            if st.query_params.get("s") != st.session_state.sessao_id:
                st.query_params["s"] = st.session_state.sessao_id   # guarda a sessão no endereço da página
            st.checkbox("Guardar também o texto", key="salvar_conteudo",
                        help="Números longos (CPF, cartão, telefone) e e-mails são mascarados e o texto é cortado em 300 caracteres.")
            st.caption("Guardando. Para voltar a este histórico depois, use o mesmo endereço da página.")
        else:
            st.caption("Desligado: nada do que você mandar agora fica salvo. O que já estava salvo continua na "
                       "página Meu histórico até você apagar ou até completar 30 dias.")
        st.divider()
        st.markdown('<p class="cb-rodape">Eu nunca peço senha, código ou dados do cartão. '
                    'Se alguém pedir em meu nome, é golpe.<br><br>Projeto acadêmico</p>',
                    unsafe_allow_html=True)


def cabecalho(sobrelinha: str, titulo: str, lead: str = ""):
    """Título de cada página: uma linha pequena em cima, o título e uma frase de apoio."""
    st.markdown(f'<div class="cb-cabecalho"><div class="cb-sobrelinha">{e(sobrelinha)}</div>'
                f'<h1 class="cb-titulo">{e(titulo)}</h1>'
                + (f'<p class="cb-lead">{lead}</p>' if lead else "") + '</div>', unsafe_allow_html=True)


def _cartao(estilo: str, titulo: str, resumo: str, legenda: str, corpo: str = "") -> str:
    """Monta o HTML do cartão de resultado: selo, frase principal, medidor e detalhes."""
    tracos = "".join(f'<span class="{"on" if i < TRACOS[estilo] else ""}"></span>' for i in range(3))
    return (f'<div class="cb-veredito {estilo}"><span class="cb-selo">{SELO[estilo]}</span>'
            f'<h3>{e(titulo)}</h3><p>{e(resumo)}</p>'
            f'<div class="cb-medidor">{tracos}</div><div class="cb-medidor-legenda">{e(legenda)}</div>'
            f'{corpo}</div>')


def _lista_sinais(sinais: list) -> str:
    """Lista de sinais encontrados: cada um com nome em negrito e explicação."""
    itens = "".join(f'<li><span class="cb-ponto"></span><div><b>{e(nome)}</b><span class="cb-exp">{e(exp)}</span></div></li>'
                    for nome, exp in sinais)
    return f'<div class="cb-secao">O que me chamou a atenção</div><ul class="cb-sinais">{itens}</ul>'


def _conselhos(passos: list) -> str:
    """Caixa "O que eu faria agora" com passos práticos."""
    if not passos:
        return ""
    itens = "".join(f"<li>{e(p)}</li>" for p in passos)
    return f'<div class="cb-conselho"><b>O que eu faria agora</b><ol>{itens}</ol></div>'


# Passo prático para cada tipo de sinal. A ordem define a prioridade.
CONSELHOS = [
    ({"credenciais"}, "Não passe senha, token nem código que chegou por SMS. Nenhuma empresa séria pede isso."),
    ({"dinheiro", "taxa"}, "Não faça Pix nem pague taxa antes de confirmar por outro caminho."),
    ({"engenharia_social"}, "Ligue para a pessoa ou empresa num número que você já conhecia, não no que veio na mensagem."),
    ({"link", "clique"}, "Não clique no link. Abra o app oficial ou digite o endereço do site você mesmo."),
    ({"acesso_remoto"}, "Não instale nenhum aplicativo que pedirem."),
    ({"dados_pessoais"}, "Não envie CPF, foto de documento nem dados do cartão."),
    ({"urgencia", "imitacao", "recompensa"}, "Respire: a pressa é a principal arma do golpe. Confira pelo canal oficial com calma."),
]


def mostrar_resultado_mensagem(r):
    """Desenha na tela o resultado de modules.analise_mensagens.analisar_mensagem."""
    if r.erro:
        st.warning(r.erro)
        return
    estilo = ESTILO[r.nivel]
    n = len([i for i in r.indicadores if i["peso"] > 0])
    if estilo == "alto":
        titulo = "Isso tem cara de golpe."
        resumo = (f"Encontrei {n} sinal{'is' if n != 1 else ''} que aparece{'m' if n != 1 else ''} muito em golpes."
                  if n else "A mensagem é muito parecida com golpes que eu já conheço.")
    elif estilo == "atencao":
        titulo = "Desconfie e confira antes de agir."
        resumo = "Não dá para cravar que é golpe, mas tem coisas aqui que merecem cuidado."
    else:
        titulo = "Não achei sinais de golpe."
        resumo = "Isso não é garantia: se pedirem dinheiro, senha ou dados, confirme antes."

    corpo = ""
    if r.indicadores:
        corpo += _lista_sinais([(i["nome"], i["explicacao"]) for i in r.indicadores])
    elif estilo != "baixo":
        # Nenhuma regra disparou: o nível veio só do classificador.
        corpo += ('<p class="cb-nota">Nenhuma regra específica disparou; quem apontou o risco foi o modelo, '
                  'que achou a mensagem parecida com golpes da base de treino.</p>')
    if estilo != "baixo":
        categorias = {i["categoria"] for i in r.indicadores}
        passos = [texto for cats, texto in CONSELHOS if cats & categorias][:3]
        corpo += _conselhos(passos or ["Não responda ainda. Confirme pelo canal oficial da empresa ou com a pessoa."])

    st.markdown(_cartao(estilo, titulo, resumo, f"Chance estimada pelo modelo de ser golpe: {r.pontuacao:.0%}", corpo),
                unsafe_allow_html=True)
    # Limitações desta análise específica (texto cortado, outro idioma...).
    for aviso in r.avisos:
        st.info(aviso)
    # Links encontrados dentro da mensagem aparecem em caixas que abrem e fecham.
    for l in r.links:
        with st.expander(f"Link na mensagem: {l.dominio} · {l.rotulo}"):
            mostrar_resultado_link(l, titulo=False)
    # Detalhes técnicos para quem quiser entender o que o modelo calculou.
    with st.expander("Como cheguei nesse resultado"):
        nomes = {"legitima": "legítima", "suspeita": "suspeita", "alto_risco": "alto risco"}
        st.markdown(f"Juntei duas coisas: um **modelo** treinado com mensagens de exemplo e **regras** que procuram "
                    f"sinais conhecidos de golpe. Fico sempre com o resultado mais cauteloso dos dois.\n\n"
                    f"O modelo achou a mensagem mais parecida com **{nomes.get(r.previsao_modelo, r.previsao_modelo)}** "
                    f"({r.confianca_modelo:.0%} de confiança).")
        st.caption(" · ".join(f"{nomes.get(k, k).capitalize()}: {v:.0%}" for k, v in r.probabilidades.items()))
    st.caption(AVISO)


def mostrar_resultado_link(r, titulo: bool = True):
    """Desenha na tela o resultado de modules.analise_links.analisar_link.

    titulo=False é usado quando o link aparece dentro do resultado de uma
    mensagem, onde o nível já está no título da caixa.
    """
    if r.erro:
        st.warning(r.erro)
        return
    estilo = ESTILO[r.nivel]
    sinais = "".join(f'<li><span class="cb-ponto"></span><div><span class="cb-exp">{e(i.descricao)}</span></div></li>'
                     for i in r.indicadores)
    lista = (f'<div class="cb-secao">O que me chamou a atenção</div><ul class="cb-sinais">{sinais}</ul>' if sinais else "")
    dominio = f'<div class="cb-dominio">Quem é o dono do endereço: <code>{e(r.dominio)}</code></div>'
    notas = "".join(f'<p class="cb-nota">{e(o)}</p>' for o in r.observacoes)
    if not titulo:
        # Versão compacta, dentro do resultado de uma mensagem.
        st.markdown(dominio + lista + notas, unsafe_allow_html=True)
        return
    if estilo == "alto":
        t, resumo = "Eu não abriria esse link.", "O endereço tem truques que golpistas usam para se passar por outro site."
        passos = ["Não abra o link nem digite nada nele.", "Se precisa acessar o serviço, use o app oficial ou digite o endereço você mesmo."]
    elif estilo == "atencao":
        t, resumo = "Esse link merece cuidado.", "Achei sinais que, juntos, pedem atenção. Sozinhos não provam golpe."
        passos = ["Só abra se você souber quem mandou e estava esperando esse link.", "Nunca digite senha ou dados do cartão numa página aberta por link."]
    else:
        t, resumo = "Não vi nada estranho no endereço.", "Mas isso não garante que o site é seguro: confira se é exatamente o endereço oficial."
        passos = []
    st.markdown(_cartao(estilo, t, resumo, f"Pontos de alerta no endereço: {r.pontuacao}",
                        dominio + lista + _conselhos(passos) + notas), unsafe_allow_html=True)


# @st.cache_resource faz o Streamlit criar o objeto uma vez só e reaproveitar
# entre as execuções, em vez de abrir uma conexão nova com o banco a cada clique.
@st.cache_resource
def historico() -> Historico:
    return Historico()


def registrar(tipo: str, classificacao: str, pontuacao: float, indicadores: list, conteudo: str):
    """Grava a análise no histórico, mas SÓ se o usuário tiver ligado essa opção."""
    if not st.session_state.get("salvar_historico"):
        return
    historico().registrar(st.session_state.sessao_id, tipo, classificacao, pontuacao, indicadores,
                          conteudo=conteudo, salvar_conteudo=st.session_state.get("salvar_conteudo", False))
