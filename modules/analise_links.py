"""Módulo 2: análise estática de links (RF04 e RF05).

"Estática" quer dizer que a URL NUNCA é acessada (RNF07). Só olhamos o texto
do endereço e procuramos características que golpistas costumam usar.

Cada característica encontrada vira um "indicador" com um peso. A soma dos
pesos define o nível: baixo, atenção ou alto risco.
"""

import ipaddress
import re
from dataclasses import dataclass, field  # dataclass cria classes simples só com dados

from utils.processamento_texto import remover_acentos
from utils.validacao_urls import URLInvalida, dominio_registrado, extrair_partes

# ---------------------------------------------------------------------------
# Listas de referência. Para atualizar o sistema basta editar estas listas.
# ---------------------------------------------------------------------------

# Serviços que encurtam links. Não são golpe por si só, mas escondem o destino real.
ENCURTADORES = {
    "bit.ly", "tinyurl.com", "cutt.ly", "t.co", "is.gd", "ow.ly", "rebrand.ly",
    "shorturl.at", "s.id", "rb.gy", "encurtador.com.br", "goo.gl", "t.ly", "tiny.cc", "v.gd",
}

# Marca -> domínios oficiais.
# Se o nome da marca aparece no endereço, mas o domínio NÃO é um dos oficiais,
# é um sinal forte de imitação (ex.: "itau-desbloqueio.com").
MARCAS = {
    "itau": {"itau.com.br"},
    "bradesco": {"bradesco.com.br"},
    "santander": {"santander.com.br"},
    "nubank": {"nubank.com.br"},
    "caixa": {"caixa.gov.br"},
    "bancodobrasil": {"bb.com.br"},
    "correios": {"correios.com.br"},
    "receitafederal": {"gov.br"},
    "inss": {"gov.br", "inss.gov.br"},
    "detran": {"gov.br"},
    "govbr": {"gov.br"},
    "serasa": {"serasa.com.br"},
    "mercadolivre": {"mercadolivre.com.br"},
    "mercadopago": {"mercadopago.com.br"},
    "netflix": {"netflix.com"},
    "whatsapp": {"whatsapp.com"},
    "instagram": {"instagram.com"},
    "magalu": {"magazineluiza.com.br", "magalu.com"},
    "shopee": {"shopee.com.br"},
    "google": {"google.com", "google.com.br", "googleusercontent.com"},
    "facebook": {"facebook.com"},
    "microsoft": {"microsoft.com"},
    "paypal": {"paypal.com"},
    "amazon": {"amazon.com", "amazon.com.br"},
    "apple": {"apple.com"},
}

# Troca de números por letras parecidas ("leetspeak"): g00gle -> google, 1tau -> itau.
_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "8": "b"})

# Termos que imitam banco, entrega ou atendimento quando aparecem num domínio que não é de banco.
TERMOS_BANCARIOS = {"banco", "bank", "pix", "cartao", "fatura", "conta", "sac", "central", "suporte", "atendimento", "credito", "emprestimo",
                    "rastreamento", "rastreio", "encomenda", "pacote", "entrega", "fgts", "beneficio", "multa", "taxa"}

# Terminações que indicam que o começo do endereço imita um domínio inteiro (ex.: "google.com.golpe.net").
_RE_PARECE_DOMINIO = re.compile(r"(^|\.)[a-z0-9-]+\.(com|net|org|gov|edu|br)$")

# Terminações de domínio (TLD) baratas e muito usadas em golpes.
TLDS_SUSPEITOS = {"xyz", "top", "click", "online", "site", "info", "live", "shop", "buzz", "icu", "cfd", "sbs", "rest", "monster", "zip", "mov"}

# Palavras que aparecem em links de golpe para chamar o clique ou pedir dados.
PALAVRAS_ISCA = {"dados", "cadastro", "login", "verificar", "verificacao", "atualizar", "atualizacao", "seguranca", "desbloqueio", "desbloquear",
                 "premio", "resgate", "resgatar", "senha", "token", "regularizar", "confirmar", "bonus"}

# Portas normais da web: nenhuma (padrão), 80 (http) e 443 (https).
PORTAS_PADRAO = {None, 80, 443}


@dataclass
class Indicador:
    """Um sinal de alerta encontrado no link."""
    descricao: str         # texto explicativo mostrado ao usuário
    peso: int              # quanto esse sinal pesa na pontuação final
    categoria: str = "link"


@dataclass
class ResultadoLink:
    """Tudo que a análise descobriu sobre um link."""
    url: str
    host: str = ""                 # nome completo do site (ex.: www.itau.com.br)
    dominio: str = ""              # domínio registrado (ex.: itau.com.br)
    nivel: str = "baixo"           # baixo | atencao | alto (ou "indefinido" quando há erro)
    pontuacao: int = 0             # soma dos pesos dos indicadores
    indicadores: list = field(default_factory=list)   # lista de Indicador
    observacoes: list = field(default_factory=list)   # avisos que não mudam a pontuação
    erro: str = ""                 # preenchido quando a entrada não é um endereço válido

    @property
    def rotulo(self) -> str:
        """Nome do nível para mostrar na tela."""
        return {"baixo": "Baixo risco", "atencao": "Atenção", "alto": "Alto risco"}.get(self.nivel, "Indefinido")


def _decodificar(host: str) -> str:
    """Converte punycode para os caracteres que o usuário vê na tela.

    Domínios com acentos ou letras de outros alfabetos são guardados em um
    formato especial que começa com "xn--". Exemplo: "xn--ita-boa.com" é
    exibido como "itaú.com". Golpistas usam isso para imitar sites famosos.
    """
    try:
        return host.encode("ascii").decode("idna")
    except (UnicodeError, ValueError):
        return host  # se não der para converter, devolve como veio


def _nivel(pontos: int) -> str:
    """Transforma a pontuação em nível. Os limites foram escolhidos testando exemplos."""
    if pontos >= 5:
        return "alto"
    if pontos >= 2:
        return "atencao"
    return "baixo"


def analisar_link(url: str) -> ResultadoLink:
    """Analisa um endereço e devolve um ResultadoLink. Nunca acessa a internet."""
    # 1) Separa as partes do endereço. Se não for um endereço válido, devolve o erro
    #    em vez de quebrar o programa.
    try:
        p = extrair_partes(url)
    except URLInvalida as erro:
        return ResultadoLink(url=str(url)[:200], erro=str(erro), nivel="indefinido")

    host = p["host"]
    dominio = dominio_registrado(host) if not p["eh_ip"] else host
    rotulos_host = host.split(".")       # ex.: ["www", "itau", "com", "br"]
    tld = rotulos_host[-1]               # última parte: "br", "com", "xyz"...
    ind: list[Indicador] = []
    obs: list[str] = []

    def add(desc, peso):
        """Atalho para registrar um indicador."""
        ind.append(Indicador(desc, peso))

    # 2) Sinais FORTES (peso 4): quase nunca aparecem em sites legítimos.
    if p["eh_ip"]:
        if ipaddress.ip_address(host.strip("[]")).is_private:
            # IP de rede local (ex.: o roteador de casa). Aparece em uso legítimo, então pesa menos.
            add("O endereço usa um número IP de rede local no lugar de um nome de site. Isso aparece em roteadores e "
                "sistemas internos; sozinho não prova golpe, mas desconfie se veio numa mensagem.", 2)
        else:
            add("O endereço usa um número IP no lugar de um nome de site. Sozinho isso não prova golpe, "
                "mas sites legítimos quase nunca mandam links assim.", 4)
    if p["usuario"]:
        # Ex.: https://google.com@golpe.xyz leva para golpe.xyz, não para o Google.
        add(f"Tem um '@' antes do domínio. O navegador ignora o que vem antes dele ('{p['usuario']}'): "
            f"o destino real é {host}. É um truque para disfarçar o endereço.", 5)
    if "xn--" in host or not p["host_ascii"]:
        visto = _decodificar(host)
        extra = f" Na tela ele aparece como '{visto}'." if visto != host else ""
        add("O domínio usa caracteres especiais ou de outros alfabetos, que podem imitar letras de sites conhecidos." + extra, 4)

    # 3) Link encurtado (peso 2).
    if dominio in ENCURTADORES:
        add("É um link encurtado: o destino final não pode ser confirmado sem abrir o link, e o CyberBot não abre links.", 2)

    # 4) Marca conhecida fora do domínio oficial (peso 4).
    #    Juntamos o host sem pontos, hífens e acentos para pegar variações como
    #    "itau-seguro", "itau.seguro" ou "itaú".
    #    Antes disso: o começo do endereço imita um domínio inteiro?
    #    Ex.: "google.com.login-seguro.net" parece Google, mas o dono é login-seguro.net.
    prefixo = host[: -len(dominio)].rstrip(".") if not p["eh_ip"] and host != dominio else ""
    if prefixo and _RE_PARECE_DOMINIO.search(prefixo):
        add(f"O endereço começa com '{prefixo}', mas o domínio que vale é o do final: {dominio}. "
            "O começo serve só para enganar quem lê rápido.", 4)
    host_sem_pontuacao = re.sub(r"[^a-z0-9]", "", remover_acentos(_decodificar(host)))
    oficial = None   # marca cujo domínio oficial é este
    for marca, oficiais in MARCAS.items():
        # É oficial se o host for exatamente o domínio oficial ou um subdomínio dele
        # (ex.: "www.itau.com.br" termina com ".itau.com.br").
        eh_oficial = any(host == o or host.endswith("." + o) for o in oficiais)
        if eh_oficial:
            oficial = marca
            continue
        if marca in host_sem_pontuacao:
            if not (prefixo and _RE_PARECE_DOMINIO.search(prefixo)):   # já avisado acima
                add(f"Cita a marca '{marca}', mas o domínio ({dominio}) não é o oficial.", 4)
            break  # basta uma marca para o alerta
        if marca in host_sem_pontuacao.translate(_LEET):
            # Ex.: "g00gle" com zeros no lugar dos "o".
            add(f"Troca letras por números para imitar a marca '{marca}' (ex.: 0 no lugar de o, 1 no lugar de i). "
                "O domínio não é o oficial; isso não quer dizer que o site exista ou esteja no ar.", 4)
            break

    # 5) Sinais MÉDIOS e FRACOS: sozinhos não provam nada, mas somam.
    subdominios = len(rotulos_host) - len(dominio.split("."))
    if not p["eh_ip"] and subdominios >= 3:
        # Ex.: itau.com.br.seguranca.login.golpe.xyz
        add(f"Tem muitos subdomínios ({subdominios}), um truque para esconder o domínio verdadeiro.", 2)
    if tld in TLDS_SUSPEITOS:
        add(f"Termina em '.{tld}', uma terminação barata e muito usada em golpes.", 1)
    nome = dominio.split(".")[0]           # ex.: "itau" em "itau.com.br"
    punycode = nome.startswith("xn--")     # já foi tratado acima; evita alertas repetidos
    if nome.count("-") >= 2 and not punycode:
        add("O nome do site tem vários hífens, comum em imitações (ex.: banco-seguro-acesso).", 1)
    termos = sorted(t for t in TERMOS_BANCARIOS if t in nome.replace("-", " ").split() or t in nome.split("-"))
    if termos and oficial is None and not p["eh_ip"]:
        # Ex.: "banco-seguranca-login.com" não pertence a nenhum banco conhecido.
        add(f"O nome do site usa termos de banco, entrega ou atendimento ({', '.join(termos)}), mas não é o domínio de "
            "nenhum banco, órgão ou empresa conhecida. Domínio não confirmado.", 2)
    if re.search(r"[a-z]\d|\d[a-z]", nome) and not p["eh_ip"] and not punycode:
        # Letra colada em número: "1tau", "g0v", "paypa1"...
        add("Mistura letras e números no nome do site, o que pode imitar uma marca (ex.: 1tau, g0v).", 1)
    if p["porta"] not in PORTAS_PADRAO:
        add(f"Usa uma porta incomum ({p['porta']}).", 2)
    if len(p["original"]) > 100:
        add("O endereço é muito longo, o que dificulta ver para onde ele leva.", 1)
    # Procura palavras-isca no host, no caminho e na consulta.
    texto_isca = re.sub(r"[^a-z]", " ", (host + " " + p["caminho"] + " " + p["consulta"]).lower())
    iscas = sorted(PALAVRAS_ISCA.intersection(texto_isca.split()))
    if iscas:
        add("Contém palavras que costumam aparecer em páginas que pedem dados: " + ", ".join(iscas) + ". Sozinho isso não prova golpe.", 1)

    # 6) HTTP x HTTPS.
    if p["esquema_informado"] and p["esquema"] == "http":
        add("Usa HTTP sem o S: a conexão não é criptografada.", 1)
    if p["esquema"] == "https":
        # Seção 12: HTTPS NÃO é prova de que o site é legítimo, por isso vira só observação (peso zero).
        obs.append("O endereço usa HTTPS. Isso só indica que a conexão é criptografada; golpistas também usam HTTPS.")
    if not p["esquema_informado"]:
        obs.append("O endereço foi informado sem http:// ou https://.")
    obs.append("O link não foi aberto. A análise olha só o texto do endereço e pode errar.")

    # 7) Soma os pesos e define o nível.
    pontos = sum(i.peso for i in ind)
    # Nunca dizer "é seguro": não achar sinais não é garantia.
    if oficial and not ind:
        obs.insert(0, f"{dominio} é um domínio oficial conhecido. Mesmo assim, confira o endereço completo "
                      "e se a página pede algo incomum: não encontrar sinais não garante que é seguro.")
    elif _nivel(pontos) == "baixo":
        obs.insert(0, "Não encontrar sinais de alerta não garante que o site é seguro. Confira se o endereço é exatamente o oficial.")
    return ResultadoLink(url=p["original"], host=host, dominio=dominio, nivel=_nivel(pontos),
                         pontuacao=pontos, indicadores=ind, observacoes=obs)
