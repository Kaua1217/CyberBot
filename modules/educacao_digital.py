"""Módulo 3: educação digital (RF06 e RF07).

As respostas vêm de uma base própria e revisada (data/base_educativa.json).
NÃO há geração livre de texto: o CyberBot só devolve conteúdos que foram
escritos e conferidos antes, então ele não inventa informação.

Como a busca funciona:
1. Cada conteúdo da base tem um título e algumas perguntas de exemplo.
2. Todos esses textos viram vetores de números com TF-IDF.
3. A pergunta do usuário também vira um vetor.
4. A similaridade de cosseno mede o quanto a pergunta "aponta na mesma
   direção" de cada texto (0 = nada a ver, 1 = igual).
5. Devolvemos o conteúdo mais parecido, se passar de um limite mínimo.
"""

import json
from functools import lru_cache
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from utils.processamento_texto import normalizar, preprocessar

BASE = Path(__file__).resolve().parent.parent / "data" / "base_educativa.json"
# Similaridade mínima para aceitar uma resposta. Abaixo disso o bot diz que não sabe.
LIMIAR = 0.2

# Palavras muito comuns que não ajudam a achar o assunto ("stop words").
# Estão sem acento porque é assim que o texto sai do pré-processamento.
PALAVRAS_VAZIAS = ("a o e de da do das dos um uma uns umas que como qual quais para pra por com no na nos nas "
                   "em se eu me meu minha voce isso esse essa ser foi tem ter faco faz fazer agora ao aos as os "
                   "sao ja mais muito _num_").split()


@lru_cache(maxsize=1)
def carregar_base(caminho: str = str(BASE)) -> dict:
    """Lê o arquivo JSON da base educativa (uma vez só, graças ao lru_cache)."""
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _indice():
    """Monta o "índice de busca": o vetorizador e a matriz com todos os textos da base."""
    base = carregar_base()
    documentos, donos = [], []
    # "donos" guarda de qual conteúdo veio cada texto. Ex.: documentos[5] pertence a conteudos[donos[5]].
    for i, c in enumerate(base["conteudos"]):
        for texto in [c["titulo"], *c["perguntas"]]:
            documentos.append(texto)
            donos.append(i)
    # Palavras inteiras (e não pedaços de palavras) para que perguntas fora do tema
    # tenham similaridade perto de zero e o bot possa dizer que não sabe, em vez de
    # inventar uma ligação com outro assunto.
    vec = TfidfVectorizer(preprocessor=preprocessar, stop_words=PALAVRAS_VAZIAS, sublinear_tf=True)
    matriz = vec.fit_transform(documentos)
    return vec, matriz, donos


def listar_conteudos() -> list:
    """Todos os conteúdos educativos (usado na página Educação Digital)."""
    return carregar_base()["conteudos"]


def listar_questionario() -> list:
    """Todas as perguntas do questionário (usado na página Questionário)."""
    return carregar_base()["questionarios"]


def responder(pergunta: str, n: int = 1) -> list:
    """Devolve até n conteúdos mais parecidos com a pergunta, com a similaridade.

    Devolve lista vazia quando nada passa do limiar. Nesse caso a interface
    deve dizer que não sabe responder.
    """
    if len(normalizar(pergunta)) < 3:
        return []
    vec, matriz, donos = _indice()
    # Similaridade da pergunta com cada texto da base (uma lista de números de 0 a 1).
    sims = cosine_similarity(vec.transform([pergunta]), matriz)[0]
    # Um conteúdo tem vários textos (título + perguntas). Ficamos com a maior nota de cada conteúdo.
    melhor_por_conteudo = {}
    for sim, dono in zip(sims, donos):
        if sim > melhor_por_conteudo.get(dono, 0):
            melhor_por_conteudo[dono] = sim
    # Ordena do mais parecido para o menos parecido.
    ordenados = sorted(melhor_por_conteudo.items(), key=lambda x: -x[1])
    conteudos = carregar_base()["conteudos"]
    # Devolve os n primeiros que passaram do limiar, acrescentando o campo "similaridade".
    return [{**conteudos[i], "similaridade": round(float(s), 3)} for i, s in ordenados[:n] if s >= LIMIAR]


def corrigir(indice_pergunta: int, escolha: int) -> dict:
    """Corrige uma resposta do questionário.

    indice_pergunta: posição da pergunta na lista
    escolha: posição da alternativa marcada pelo usuário
    """
    q = listar_questionario()[indice_pergunta]
    return {"correta": escolha == q["resposta_correta"],
            "resposta_correta": q["alternativas"][q["resposta_correta"]],
            "explicacao": q["explicacao"]}
