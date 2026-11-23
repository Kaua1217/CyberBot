# Especificação do CyberBot

## 1. Problema e público

Golpes por SMS, WhatsApp e e-mail (falso parente, falsa central, Pix, falso prêmio, links falsos) atingem principalmente quem tem pouca familiaridade com tecnologia. O CyberBot é um assistente que ajuda a pessoa a **parar e conferir** antes de clicar, pagar ou responder: ela cola a mensagem ou o link, e o bot explica o que encontrou e o que fazer.

Público: qualquer pessoa que usa celular no Brasil, com atenção especial a idosos e familiares que ajudam outras pessoas a conferir mensagens.

## 2. O CyberBot como agente

O CyberBot segue o ciclo de um agente de IA: **percebe** a entrada, **decide** o que fazer e **age** com a ferramenta certa, explicando o resultado.

```
entrada do usuário
      │
      ▼
 [Percepção]  bloqueia dados sensíveis (CPF, cartão, senha) · detecta entrada sem palavras
      │
      ▼
 [Decisão]    é um link? uma pergunta? uma mensagem recebida?   (pages/0_Conversar.py → decidir)
      │
      ├── link ──────► Ferramenta 1: análise estática de URL      (modules/analise_links.py)
      ├── mensagem ──► Ferramenta 2: classificador + regras       (modules/analise_mensagens.py)
      └── pergunta ──► Ferramenta 3: busca na base educativa      (modules/educacao_digital.py)
      │
      ▼
 [Ação]       cartão com conclusão, sinais encontrados e "o que eu faria agora"
      │
      ▼
 [Memória]    histórico opcional em SQLite, só com consentimento  (modules/historico.py)
```

Escolhas de projeto:
- **Sem IA generativa nas respostas.** O bot não inventa texto: a análise vem de um modelo treinado e de regras, e as orientações vêm de uma base revisada. Isso evita respostas erradas sobre segurança e mantém o projeto sem API paga (RNF02).
- **Sempre explicável.** Toda conclusão mostra os sinais que levaram a ela.
- **Cauteloso.** O nível final é o mais alto entre o modelo e as regras.

## 3. Ferramentas

| Ferramenta | O que faz | Técnica |
|---|---|---|
| Análise de mensagens | Classifica em baixo risco, atenção ou alto risco e lista os sinais | TF-IDF de n-gramas de caracteres + Regressão Logística (comparada com Naive Bayes), mais 14 regras explicáveis |
| Análise de links | Avalia o endereço **sem abrir o site** | Leitura das partes da URL: IP, `@`, punycode, encurtador, marca fora do domínio oficial, troca de letras por números, subdomínios, TLD, palavras-isca |
| Base educativa | Responde dúvidas | Busca por similaridade (TF-IDF + cosseno) em 16 conteúdos revisados; abaixo do limiar, admite que não sabe |
| Quiz | 6 situações do dia a dia com explicação | Base JSON |
| Histórico | Guarda resultados se o usuário ligar | SQLite, texto mascarado, retenção de 30 dias, estatísticas agregadas |

Tecnologias: Python 3.10+, Streamlit, scikit-learn, pandas, SQLite e pytest.

## 4. Requisitos funcionais

| Código | Requisito | Onde está | Situação |
|---|---|---|---|
| RF01 | Permitir inserir mensagens para análise | Chat e página Checar mensagem | Atendido |
| RF02 | Classificar mensagens conforme indicadores de risco | `modules/analise_mensagens.py` | Atendido |
| RF03 | Exibir indicadores identificados | Cartão "O que me chamou a atenção" | Atendido |
| RF04 | Permitir inserir URLs para análise | Chat e página Checar link | Atendido |
| RF05 | Identificar características suspeitas nos links | `modules/analise_links.py` | Atendido |
| RF06 | Apresentar orientações de segurança digital | Página Aprender sobre golpes e respostas do chat | Atendido |
| RF07 | Disponibilizar questionários educativos | Página Quiz | Atendido |
| RF08 | Registrar histórico, quando habilitado | `modules/historico.py` | Atendido |
| RF09 | Consultar resultados anteriores | Página Meu histórico | Atendido |
| RF10 | Apresentar estatísticas de utilização | Página Meu histórico | Atendido |

## 5. Requisitos não funcionais

| Código | Requisito | Como foi atendido |
|---|---|---|
| RNF01 | Interface simples e intuitiva | Chat único que decide sozinho o que fazer; linguagem do dia a dia; testado em celular |
| RNF02 | Sem API paga | Tudo roda localmente com bibliotecas livres |
| RNF03 | Tempo adequado | Análise em milissegundos; modelo carregado uma vez só |
| RNF04 | Armazenamento seguro | Consultas parametrizadas no SQLite; texto só se o usuário pedir, mascarado e cortado |
| RNF05 | Não coletar dados desnecessários | Sem cadastro; CPF, cartão ou senha digitados são bloqueados e não são salvos |
| RNF06 | Mostrar limitações e incertezas | "Baixo risco" nunca vira "seguro"; aviso em todo resultado; chance estimada pelo modelo |
| RNF07 | Não abrir links | Nenhuma requisição de rede; há um teste que falha se a análise tentar acessar a internet |
| RNF08 | Atualizar a base de conhecimento | Editar `data/base_educativa.json` e `data/mensagens_treinamento.csv` e rodar `python -m models.treinamento` |

## 6. Como foi validado

- 85 testes automáticos (`python -m pytest`), incluindo os 46 casos do Plano de Testes: [resultado_plano_de_testes.md](resultado_plano_de_testes.md).
- Métricas do modelo por classe e matriz de confusão: [relatorio_modelo.md](relatorio_modelo.md).
- Análise de viés e impactos éticos: [etica_e_vies.md](etica_e_vies.md).
