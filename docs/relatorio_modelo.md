# Relatório do modelo de classificação de mensagens

Gerado em 12/11/2026 13:04 por `models/treinamento.py`.

## Dados

- Total: 177 mensagens únicas, todas criadas para o projeto (coluna `origem`).
- Por classe: legitima: 64, suspeita: 56, alto_risco: 57.
- Divisão estratificada: 132 para treino e 45 para teste (25%), semente 42.
- Duplicatas exatas removidas antes da divisão.

## Comparação dos modelos

| Modelo | F1 macro (validação cruzada 5 partes, treino) | Acurácia (teste) | F1 macro (teste) |
|---|---|---|---|
| Naive Bayes | 0.674 | 0.756 | 0.742 |
| Regressão Logística (escolhido) | 0.770 | 0.778 | 0.773 |

O modelo é escolhido pelo F1 da validação cruzada, sem olhar o conjunto de teste. Depois ele é retreinado com todos os dados para uso no aplicativo.

## Naive Bayes: métricas por classe (teste)

```
              precision    recall  f1-score   support

    legitima       0.87      0.81      0.84        16
    suspeita       0.78      0.50      0.61        14
  alto_risco       0.67      0.93      0.78        15

    accuracy                           0.76        45
   macro avg       0.77      0.75      0.74        45
weighted avg       0.77      0.76      0.75        45
```

Matriz de confusão (linhas = classe real):

| real \ previsto | legitima | suspeita | alto_risco |
|---|---|---|---|
| **legitima** | 13 | 2 | 1 |
| **suspeita** | 1 | 7 | 6 |
| **alto_risco** | 1 | 0 | 14 |

## Regressão Logística: métricas por classe (teste)

```
              precision    recall  f1-score   support

    legitima       0.76      0.81      0.79        16
    suspeita       0.75      0.64      0.69        14
  alto_risco       0.81      0.87      0.84        15

    accuracy                           0.78        45
   macro avg       0.78      0.77      0.77        45
weighted avg       0.78      0.78      0.78        45
```

Matriz de confusão (linhas = classe real):

| real \ previsto | legitima | suspeita | alto_risco |
|---|---|---|---|
| **legitima** | 13 | 2 | 1 |
| **suspeita** | 3 | 9 | 2 |
| **alto_risco** | 1 | 1 | 13 |

## Limitações

- A base é pequena e foi escrita para o projeto. As métricas servem como ponto de partida e não representam o desempenho com mensagens reais.
- Com poucos exemplos de teste, uma única mensagem errada muda bastante a porcentagem.
- Golpes novos, com palavras que o modelo nunca viu, podem passar como legítimos. Por isso o aplicativo combina o modelo com regras explicáveis.
- Próximo passo: chegar a 300 a 500 mensagens, incluindo mensagens reais anonimizadas e conjuntos públicos, respeitando as licenças.
