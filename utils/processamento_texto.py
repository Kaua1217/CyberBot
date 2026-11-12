"""Pré-processamento de texto.

Este arquivo prepara o texto antes de ele ser analisado. É usado:
- pelo classificador de mensagens (models/treinamento.py e modules/analise_mensagens.py);
- pela busca na base educativa (modules/educacao_digital.py);
- pelas regras de análise (que precisam do texto sem acentos e em minúsculas).
"""

import re            # expressões regulares: servem para encontrar padrões no texto
import unicodedata   # permite separar a letra do acento (ex.: "ã" vira "a" + "~")

# Tamanho máximo aceito. Textos maiores são cortados para o sistema não travar
# com entradas gigantes (requisito de proteção contra entradas malformadas).
TAMANHO_MAXIMO = 5000

# ---------------------------------------------------------------------------
# Padrões (expressões regulares) compilados uma única vez, para ficar mais rápido.
# ---------------------------------------------------------------------------

# Endereços de site: começam com http(s):// ou www., ou terminam com .com, .xyz, .br etc.
_RE_URL = re.compile(r"(https?://\S+|www\.\S+|\b[\w-]+\.(?:com|net|org|xyz|top|info|online|site|br|ly|io|me|co)(?:/\S*)?)", re.I)
# Endereços de e-mail: algo@algo.algo
_RE_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")
# Valores em reais: "R$ 2,99", "r$1.500"
_RE_DINHEIRO = re.compile(r"r\$\s*\d+[\d.,]*", re.I)
# Telefones brasileiros: (11) 98765-4321, 11987654321...
_RE_TELEFONE = re.compile(r"\(?\d{2}\)?\s?9?\d{4}-?\d{4}")
# Qualquer sequência de dígitos
_RE_NUMERO = re.compile(r"\d+")
# Tudo que NÃO é letra de a-z, sublinhado ou espaço (pontuação, emojis...)
_RE_NAO_PALAVRA = re.compile(r"[^a-z_ ]+")
# Um ou mais espaços, quebras de linha ou tabs seguidos
_RE_ESPACOS = re.compile(r"\s+")


def remover_acentos(texto: str) -> str:
    """Tira os acentos: "não é fácil" -> "nao e facil".

    A normalização NFD separa cada letra acentuada em duas partes (letra + acento).
    Depois descartamos as partes da categoria "Mn" (marcas/acentos).
    """
    nfkd = unicodedata.normalize("NFD", texto)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")


def limitar(texto: str) -> str:
    """Garante que a entrada é texto e corta o excesso de tamanho.

    Se vier None ou outro tipo (número, por exemplo), converte para texto
    em vez de dar erro. Isso deixa o sistema mais robusto.
    """
    if not isinstance(texto, str):
        texto = "" if texto is None else str(texto)
    return texto[:TAMANHO_MAXIMO]


def normalizar(texto: str) -> str:
    """Deixa o texto em minúsculas, sem acentos e com espaços simples.

    A pontuação é mantida. É a versão usada pelas regras de análise,
    que procuram expressões como "codigo de verificacao".
    """
    texto = remover_acentos(limitar(texto).lower())
    return _RE_ESPACOS.sub(" ", texto).strip()


def preprocessar(texto: str) -> str:
    """Prepara o texto para o TF-IDF (a representação numérica usada pelo modelo).

    Links, e-mails, valores em dinheiro, telefones e números viram marcadores
    (_url_, _email_, _dinheiro_, _telefone_, _num_). Assim o modelo aprende o
    padrão "a mensagem tem um link" ou "fala de dinheiro", sem decorar um
    endereço ou valor específico que nunca vai se repetir.

    Exemplo:
        "Pague R$ 2,99 em http://golpe.xyz HOJE!"
        -> "pague _dinheiro_ em _url_ hoje"
    """
    t = limitar(texto).lower()
    # A ordem importa: o e-mail vem antes do link, senão "ana@gmail.com"
    # teria o "gmail.com" confundido com um site.
    t = _RE_EMAIL.sub(" _email_ ", t)
    t = _RE_URL.sub(" _url_ ", t)
    t = _RE_DINHEIRO.sub(" _dinheiro_ ", t)
    t = _RE_TELEFONE.sub(" _telefone_ ", t)
    t = remover_acentos(t)
    t = _RE_NUMERO.sub(" _num_ ", t)        # números que sobraram (datas, códigos...)
    t = _RE_NAO_PALAVRA.sub(" ", t)          # tira pontuação e símbolos
    return _RE_ESPACOS.sub(" ", t).strip()   # junta espaços repetidos
