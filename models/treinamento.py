"""Treina e compara Naive Bayes e Regressão Logística com TF-IDF (seções 3 e 11 do planejamento).

Uso (na pasta CyberBot):
    python -m models.treinamento

Gera:
    models/classificador.pkl   modelo escolhido
    models/vectorizer.pkl      vetorizador TF-IDF
    docs/relatorio_modelo.md   métricas por classe e matriz de confusão

Passo a passo do que este script faz:
1. Lê as mensagens rotuladas do CSV.
2. Separa 75% para treino e 25% para teste, mantendo a proporção de cada classe.
3. Para cada modelo candidato: mede o F1 com validação cruzada (só no treino)
   e depois mede o desempenho no conjunto de teste.
4. Escolhe o modelo com melhor F1 na validação cruzada.
5. Retreina o escolhido com TODOS os dados e salva em arquivo.
6. Escreve um relatório com as métricas.
"""

from datetime import datetime
from pathlib import Path

import joblib                     # salva e carrega objetos Python em arquivo (.pkl)
import numpy as np
import pandas as pd               # leitura e manipulação de tabelas (o CSV)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import Pipeline

from utils.processamento_texto import preprocessar

# Caminhos dos arquivos, calculados a partir da pasta deste script.
RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "data" / "mensagens_treinamento.csv"
PASTA_MODELOS = RAIZ / "models"
RELATORIO = RAIZ / "docs" / "relatorio_modelo.md"
CLASSES = ["legitima", "suspeita", "alto_risco"]
# Semente fixa: garante que a divisão treino/teste seja sempre a mesma, para os
# resultados poderem ser reproduzidos por outra pessoa.
SEMENTE = 42


def carregar_dados(caminho=DADOS) -> pd.DataFrame:
    """Lê o CSV e limpa os dados."""
    df = pd.read_csv(caminho)
    df["texto"] = df["texto"].astype(str).str.strip()
    # Remove textos vazios e repetidos. Se a mesma mensagem caísse no treino e no
    # teste, o modelo pareceria melhor do que realmente é.
    df = df[df["texto"] != ""].drop_duplicates(subset="texto")
    df = df[df["categoria"].isin(CLASSES)]   # ignora linhas com rótulo desconhecido
    return df.reset_index(drop=True)


def novo_vetorizador() -> TfidfVectorizer:
    """Cria o vetorizador TF-IDF, que transforma texto em números.

    TF-IDF dá peso alto a pedaços de texto que aparecem muito numa mensagem,
    mas pouco no conjunto todo (ou seja, que são característicos dela).

    Usamos n-gramas de caracteres (pedaços de 3 a 5 letras dentro de cada palavra).
    Em testes com validação cruzada eles foram melhores que palavras inteiras
    (F1 ~0,80 contra ~0,73): lidam melhor com variações como "bloqueada/bloqueio"
    e com erros de digitação, comuns em mensagens de golpe.
    """
    return TfidfVectorizer(preprocessor=preprocessar, analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)


def candidatos() -> dict:
    """Os dois modelos recomendados no planejamento.

    - ComplementNB: variação do Naive Bayes que funciona bem com texto.
    - LogisticRegression: class_weight="balanced" compensa classes com tamanhos diferentes;
      C=5.0 controla o quanto o modelo pode se ajustar aos dados.
    """
    return {
        "Naive Bayes": ComplementNB(alpha=0.5),
        "Regressão Logística": LogisticRegression(max_iter=2000, C=5.0, class_weight="balanced"),
    }


def _matriz_md(matriz) -> str:
    """Converte a matriz de confusão em uma tabela Markdown para o relatório."""
    cab = "| real \\ previsto | " + " | ".join(CLASSES) + " |\n|---|" + "---|" * len(CLASSES) + "\n"
    linhas = "".join(f"| **{c}** | " + " | ".join(str(v) for v in matriz[i]) + " |\n" for i, c in enumerate(CLASSES))
    return cab + linhas


def treinar(salvar: bool = True, verbose: bool = True) -> dict:
    """Executa todo o processo de treino e avaliação."""
    df = carregar_dados()
    X, y = df["texto"], df["categoria"]   # X = textos, y = rótulos corretos

    # Divisão estratificada: treino e teste têm a mesma proporção de cada classe.
    X_treino, X_teste, y_treino, y_teste = train_test_split(X, y, test_size=0.25, stratify=y, random_state=SEMENTE)
    # Validação cruzada em 5 partes: treina 5 vezes, cada vez testando numa parte diferente do treino.
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMENTE)

    resultados = {}
    for nome, modelo in candidatos().items():
        # Pipeline junta o vetorizador e o modelo. Assim, na validação cruzada, o TF-IDF
        # é recalculado em cada parte e não "vê" os dados de teste antes da hora.
        pipe = Pipeline([("tfidf", novo_vetorizador()), ("clf", modelo)])
        prev_cv = cross_val_predict(pipe, X_treino, y_treino, cv=cv)
        pipe.fit(X_treino, y_treino)        # treina com todo o conjunto de treino
        prev_teste = pipe.predict(X_teste)  # prevê o conjunto de teste, nunca visto
        resultados[nome] = {
            "pipe": pipe,
            "f1_cv": f1_score(y_treino, prev_cv, average="macro"),          # média do F1 das 3 classes
            "acuracia_teste": accuracy_score(y_teste, prev_teste),
            "f1_teste": f1_score(y_teste, prev_teste, average="macro"),
            "relatorio": classification_report(y_teste, prev_teste, labels=CLASSES, digits=2, zero_division=0),
            "matriz": confusion_matrix(y_teste, prev_teste, labels=CLASSES),
        }
        if verbose:
            r = resultados[nome]
            print(f"{nome}: F1 macro (validação cruzada) = {r['f1_cv']:.3f} | teste: acurácia {r['acuracia_teste']:.3f}, F1 {r['f1_teste']:.3f}")

    # Escolhe pelo F1 da validação cruzada, para não "escolher olhando o teste"
    # (isso deixaria a nota do teste otimista demais).
    melhor = max(resultados, key=lambda n: resultados[n]["f1_cv"])

    # Modelo final: retreina com TODOS os dados, porque mais exemplos = modelo melhor.
    final_vec = novo_vetorizador()
    final_clf = candidatos()[melhor]
    final_clf.fit(final_vec.fit_transform(X), y)

    if salvar:
        # Salvamos vetorizador e modelo separados, como pede a estrutura de pastas do projeto.
        joblib.dump(final_clf, PASTA_MODELOS / "classificador.pkl")
        joblib.dump(final_vec, PASTA_MODELOS / "vectorizer.pkl")
        _escrever_relatorio(df, resultados, melhor, len(X_treino), len(X_teste))
        if verbose:
            print(f"Modelo escolhido: {melhor}. Arquivos salvos em models/ e relatório em docs/relatorio_modelo.md")
    return {"melhor": melhor, "resultados": resultados}


def _escrever_relatorio(df, resultados, melhor, n_treino, n_teste):
    """Gera docs/relatorio_modelo.md com dados, métricas, matriz de confusão e limitações."""
    contagem = df["categoria"].value_counts().reindex(CLASSES).fillna(0).astype(int)
    partes = [
        "# Relatório do modelo de classificação de mensagens\n",
        f"Gerado em {datetime.now():%d/%m/%Y %H:%M} por `models/treinamento.py`.\n",
        "## Dados\n",
        f"- Total: {len(df)} mensagens únicas, todas criadas para o projeto (coluna `origem`).",
        "- Por classe: " + ", ".join(f"{c}: {contagem[c]}" for c in CLASSES) + ".",
        f"- Divisão estratificada: {n_treino} para treino e {n_teste} para teste (25%), semente {SEMENTE}.",
        "- Duplicatas exatas removidas antes da divisão.\n",
        "## Comparação dos modelos\n",
        "| Modelo | F1 macro (validação cruzada 5 partes, treino) | Acurácia (teste) | F1 macro (teste) |",
        "|---|---|---|---|",
    ]
    for nome, r in resultados.items():
        marca = " (escolhido)" if nome == melhor else ""
        partes.append(f"| {nome}{marca} | {r['f1_cv']:.3f} | {r['acuracia_teste']:.3f} | {r['f1_teste']:.3f} |")
    partes.append("\nO modelo é escolhido pelo F1 da validação cruzada, sem olhar o conjunto de teste. "
                  "Depois ele é retreinado com todos os dados para uso no aplicativo.\n")
    # Métricas por classe e matriz de confusão de cada modelo (seção 11: não mostrar só a acurácia).
    for nome, r in resultados.items():
        partes += [f"## {nome}: métricas por classe (teste)\n", "```", r["relatorio"].rstrip(), "```\n",
                   "Matriz de confusão (linhas = classe real):\n", _matriz_md(r["matriz"])]
    partes += [
        "## Limitações\n",
        "- A base é pequena e foi escrita para o projeto. As métricas servem como ponto de partida e "
        "não representam o desempenho com mensagens reais.",
        "- Com poucos exemplos de teste, uma única mensagem errada muda bastante a porcentagem.",
        "- Golpes novos, com palavras que o modelo nunca viu, podem passar como legítimos. "
        "Por isso o aplicativo combina o modelo com regras explicáveis.",
        "- Próximo passo: chegar a 300 a 500 mensagens, incluindo mensagens reais anonimizadas e conjuntos públicos, respeitando as licenças.",
    ]
    RELATORIO.parent.mkdir(exist_ok=True)   # cria a pasta docs/ se ainda não existir
    RELATORIO.write_text("\n".join(partes) + "\n", encoding="utf-8")


# Este bloco só roda quando o arquivo é executado diretamente
# (python -m models.treinamento), e não quando é importado por outro módulo.
if __name__ == "__main__":
    np.random.seed(SEMENTE)
    treinar()
