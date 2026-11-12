"""Validação de URLs e separação das partes do endereço.

IMPORTANTE: nada aqui acessa a internet. Só lemos o texto do endereço
(requisito RNF07: não abrir automaticamente links suspeitos).
"""

import ipaddress                   # biblioteca padrão para reconhecer endereços IP
import re
from urllib.parse import urlsplit  # biblioteca padrão que separa uma URL em partes

# Endereços maiores que isso são recusados (proteção contra entradas absurdas).
TAMANHO_MAXIMO_URL = 2048
# Verifica se o endereço começa com um "esquema", como http:// ou https://
_RE_ESQUEMA = re.compile(r"^[a-z][a-z0-9+.-]*://", re.I)
# Um nome de site "normal" só tem letras sem acento, números, pontos e hífens.
_RE_HOST_VALIDO = re.compile(r"^[a-z0-9.-]+$", re.I)


class URLInvalida(ValueError):
    """Erro próprio do projeto: a entrada não pode ser lida como endereço web.

    Ter uma classe de erro própria permite que o restante do código trate esse
    caso com uma mensagem amigável, sem quebrar o aplicativo.
    """


def normalizar_url(url: str) -> str:
    """Limpa a entrada e recusa o que claramente não é um endereço."""
    if not isinstance(url, str):
        raise URLInvalida("Informe o endereço como texto.")
    # Remove espaços nas pontas e sinais que costumam vir quando se copia um link: < > " '
    url = url.strip().strip("<>\"'")
    if not url:
        raise URLInvalida("Informe um endereço para analisar.")
    if len(url) > TAMANHO_MAXIMO_URL:
        raise URLInvalida("O endereço é longo demais para ser analisado.")
    if any(c.isspace() for c in url):
        raise URLInvalida("O endereço não pode conter espaços.")
    if not _RE_ESQUEMA.match(url):
        # Sem "http://" o urlsplit não entende onde está o domínio. Colocamos um
        # provisório só para conseguir separar as partes. Isso NÃO significa que
        # o endereço original usava http (guardamos essa informação à parte).
        url = "http://" + url
    return url


def extrair_partes(url: str) -> dict:
    """Separa o endereço em partes (esquema, domínio, porta, caminho...).

    Exemplo: "https://www.itau.com.br:443/login?x=1"
        esquema = "https", host = "www.itau.com.br", porta = 443,
        caminho = "/login", consulta = "x=1"

    Levanta URLInvalida se o endereço não puder ser interpretado.
    """
    original = url.strip() if isinstance(url, str) else url
    url = normalizar_url(url)
    try:
        partes = urlsplit(url)
        porta = partes.port  # pode dar ValueError se a porta for inválida (ex.: 99999)
    except ValueError as erro:
        raise URLInvalida("O endereço está malformado.") from erro

    # hostname já vem sem a porta e sem o "usuario@". Tiramos o ponto final, se houver.
    host = (partes.hostname or "").lower().rstrip(".")
    # Um domínio de verdade tem pelo menos um ponto (ex.: "site.com"), a não ser que seja um IP.
    if not host or "." not in host and not _eh_ip(host):
        raise URLInvalida("Não encontrei um domínio válido nesse endereço.")

    return {
        "original": original,                                        # como o usuário digitou
        "esquema_informado": bool(_RE_ESQUEMA.match(original or "")),  # o usuário escreveu http(s)://?
        "esquema": partes.scheme.lower(),                            # "http" ou "https"
        "usuario": partes.username,                                  # o que vem antes de um "@" (truque de golpe)
        "host": host,                                                # ex.: "www.itau.com.br"
        "porta": porta,                                              # None quando não foi informada
        "caminho": partes.path or "",                                # ex.: "/login"
        "consulta": partes.query or "",                              # o que vem depois do "?"
        "eh_ip": _eh_ip(host),                                       # o "domínio" é um número IP?
        "host_ascii": bool(_RE_HOST_VALIDO.match(host)),             # só tem caracteres comuns?
    }


def _eh_ip(host: str) -> bool:
    """Diz se o texto é um endereço IP (ex.: 192.168.0.1). Os colchetes são do IPv6."""
    try:
        ipaddress.ip_address(host.strip("[]"))
        return True
    except ValueError:
        return False


def dominio_registrado(host: str) -> str:
    """Encontra o domínio "de verdade", que é a parte que alguém registrou e paga.

    Exemplos:
        "www.itau.com.br"             -> "itau.com.br"
        "itau.com.br.golpe.xyz"       -> "golpe.xyz"   (o golpista é dono de golpe.xyz!)
        "login.netflix.com"           -> "netflix.com"

    No Brasil muitos sites terminam com dois níveis (com.br, gov.br...), por
    isso tratamos esses casos à parte. Uma versão futura pode usar a Public
    Suffix List completa, que cobre todos os países.
    """
    rotulos = host.split(".")
    sufixos_duplos = {"com.br", "gov.br", "org.br", "net.br", "edu.br", "jus.br", "mil.br", "leg.br", "art.br", "co.uk", "com.ar"}
    if len(rotulos) >= 3 and ".".join(rotulos[-2:]) in sufixos_duplos:
        return ".".join(rotulos[-3:])   # pega 3 partes: itau + com + br
    return ".".join(rotulos[-2:])       # pega 2 partes: netflix + com
