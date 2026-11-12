# Resultado do Plano de Testes do CyberBot

Execução: 12/11/2026, na versão do branch `plano-de-testes`.
Como foi executado: cada entrada do plano foi enviada ao chat (página **Conversar**) com o
`AppTest` do Streamlit, que roda o app de verdade sem navegador. Os casos de histórico e o S01
também foram conferidos no navegador (Chromium). Todos os casos estão automatizados em
`tests/test_plano.py` e podem ser repetidos com `python -m pytest`.

Nenhum endereço do plano foi aberto: a análise de links só lê o texto (há um teste que bloqueia a
rede). Nenhum dado pessoal real foi usado.

## Resumo

| Categoria | Total | Aprovados | Reprovados | Não executados |
|---|---|---|---|---|
| Mensagens | 12 | 12 | 0 | 0 |
| Links | 10 | 10 | 0 | 0 |
| Assistente educativo | 10 | 10 | 0 | 0 |
| Segurança | 8 | 8 | 0 | 0 |
| Histórico/SQLite | 6 | 6 | 0 | 0 |
| **Total** | **46** | **46 (100%)** | **0** | **0** |

Esse resultado vale **depois das correções** descritas abaixo. Na primeira rodada vários casos
falharam ou passaram só em parte (coluna "Correção" das tabelas). Como o próprio plano diz, os 46
casos são uma bateria inicial: não provam a segurança completa nem a qualidade estatística do
modelo, que continua com F1 macro de cerca de 0,77 numa base pequena (ver `docs/relatorio_modelo.md`).

## 1. Análise de mensagens

| ID | Resultado obtido | Status | Correção feita nesta rodada |
|---|---|---|---|
| M01 | Alto risco. Sinais: pede dados, pressa ou ameaça ("foi bloqueada", "imediatamente"), imita banco, link suspeito (banco-seguranca-login.com com termos de banco em domínio não confirmado). | Aprovado | "foi bloqueada" passou a contar como ameaça; link ganhou o sinal de termos bancários. |
| M02 | Alto risco. Sinais: prêmio ou ganho fácil, taxa antecipada. | Aprovado | — |
| M03 | Alto risco. Sinais: taxa antecipada, link suspeito (rastreamento-pacote.net usa termos de entrega e não é domínio conhecido). | Aprovado | Antes o link aparecia como "nenhum sinal"; agora termos de entrega/rastreio contam e todo link em mensagem é marcado como não verificado. |
| M04 | Alto risco. Sinal: pede senha ou código. | Aprovado | — |
| M05 | Alto risco. Sinais: pede depósito, taxa antecipada (pagar para liberar cadastro). | Aprovado | — |
| M06 | Alto risco. Sinais: número novo, pede Pix, pressa. | Aprovado | — |
| M07 | Alto risco. Sinais: pressa ("últimas horas"), chamada para clicar, oferta boa demais (iPhone por R$ 199). | Aprovado | Antes dava alto risco só pelo modelo, sem explicação. Novas regras: "Chamada para clicar" e "Oferta boa demais". |
| M08 | Alto risco. Sinais: alerta de compra, contato por canal não verificado ("ligue para este número"), pressa. | Aprovado | Antes só apontava pressa. Novas regras: "Alerta de compra ou acesso" e "Contato por canal não verificado". |
| M09 | Baixo risco, sem sinais (modelo: legítima, 76%). | Aprovado | — |
| M10 | Baixo risco, sem sinais (modelo: legítima, 72%). | Aprovado | — |
| M11 | Baixo risco, sem sinais (modelo: legítima, 78%). | Aprovado | — |
| M12 | Baixo risco, sem sinais (modelo: legítima, 78%), com o aviso de confirmar pelo canal oficial. | Aprovado | Antes dava **Atenção** (falso positivo) porque a regra disparava com qualquer "senha". Agora ela exige um pedido ("envie", "informe", "digite"... perto de senha/código) e ignora "não compartilhe". |

Todo resultado mostra a chance estimada pelo modelo, os sinais encontrados e o aviso de que a
análise é indicativa. Quando nenhuma regra dispara mas o modelo aponta risco, a tela agora diz isso
em vez de "não encontramos sinais".

## 2. Análise de links

| ID | Resultado obtido | Status | Correção feita nesta rodada |
|---|---|---|---|
| L01 | Baixo risco. "google.com é um domínio oficial conhecido. Mesmo assim, confira o endereço completo... não encontrar sinais não garante que é seguro." | Aprovado | Aviso de que baixo risco não é garantia. |
| L02 | Atenção. IP de rede local no lugar do nome ("sozinho não prova golpe"), palavra "login", HTTP sem S. | Aprovado | Antes o chat tratava como mensagem e dava alto risco. Rota corrigida e IP local pesa menos que IP público. |
| L03 | Atenção. Vários hífens, termos de banco em domínio não confirmado, palavras "login" e "seguranca". | Aprovado | Novo sinal de termos bancários/atendimento fora de domínio conhecido. |
| L04 | Alto risco. "O endereço começa com 'google.com', mas o domínio que vale é o do final: login-seguro.net." | Aprovado | Antes dava baixo risco. Novo sinal de domínio conhecido usado como disfarce no começo do endereço. |
| L05 | Alto risco. "Troca letras por números para imitar a marca 'google'... isso não quer dizer que o site exista." | Aprovado | Antes dava baixo risco. Comparação com marcas agora desfaz trocas como 0→o e 1→i; Google, Facebook, Microsoft, PayPal, Amazon e Apple entraram na lista. |
| L06 | Atenção. Palavras "confirmar" e "dados" ("sozinho isso não prova golpe"), HTTP sem S. | Aprovado | Texto deixa claro que não é prova de fraude. |
| L07 | Atenção. "O destino final não pode ser confirmado sem abrir o link, e o CyberBot não abre links." | Aprovado | Texto mais claro. |
| L08 | Baixo risco, com aviso de que domínio oficial não garante segurança. | Aprovado | Aviso de não garantia. |
| L09 | Alto risco. Domínio analisado: malicioso.net. "O navegador ignora o que vem antes dele ('site.com'): o destino real é malicioso.net." | Aprovado | Antes o chat tratava como mensagem e dava baixo risco. Rota corrigida e o '@' passou a peso 5. |
| L10 | Recusado: "O esquema 'javascript:' não é um endereço web (http ou https) e não foi analisado... não abra nem clique." | Aprovado | Antes respondia "não sei". Agora esquemas fora de http/https são recusados e nada é executado. |

## 3. Assistente educativo

| ID | Conteúdo respondido | Status | Correção feita nesta rodada |
|---|---|---|---|
| E01 | Golpes no WhatsApp (falso parente, código de 6 dígitos, confirmação em duas etapas). | Aprovado | — |
| E02 | **Novo:** "O banco pode pedir minha senha?" Não; não passe senha, código ou token; fale pelos canais oficiais. | Aprovado | Antes a pergunta era bloqueada como "dado sensível" por conter "minha senha". O bloqueio agora pega só "minha senha é..." ou "senha: ...". |
| E03 | Cliquei num link suspeito: não digitar nada e fechar, trocar senha, avisar o banco, antivírus, acompanhar extratos. | Aprovado | Antes o chat analisava a pergunta como mensagem. Conteúdo ampliado. |
| E04 | Phishing: remetente, links, anexos, pressa, pedidos incomuns e "não confie só em erros de português". | Aprovado | Conteúdo ampliado com remetente, anexos e erros de escrita. |
| E05 | Engenharia social: manipulação de pessoas usando medo, pressa, ganância, afeto e autoridade. | Aprovado | — |
| E06 | **Novo:** Golpe do falso Pix (comprovante falso ou agendado, Pix "por engano", falsa central; "há outras" formas). | Aprovado | Antes respondia com "Caí num golpe". |
| E07 | **Novo:** Não compartilhe códigos recebidos por SMS. | Aprovado | Antes respondia com o conteúdo de HTTPS. |
| E08 | Senhas: frase longa, única, gerenciador, verificação em duas etapas (autenticação multifator). | Aprovado | — |
| E09 | Caí num golpe: avisar o banco, MED do Pix, boletim de ocorrência, guardar provas, Registrato, denunciar. | Aprovado | Antes o chat analisava a pergunta como mensagem. |
| E10 | **Novo:** Como verificar se um site é confiável (domínio exato, caminho oficial, reputação, cadeado não garante). | Aprovado | Antes respondia só sobre HTTPS. |

A base educativa passou de 12 para 16 conteúdos. As respostas continuam vindo só da base revisada
(não há geração livre de texto).

## 4. Segurança e entradas inesperadas

| ID | Resultado obtido | Status | Correção feita nesta rodada |
|---|---|---|---|
| S01 | No chat, Enter com o campo vazio não envia nada. Na página "Analisar mensagem", o formulário vazio mostra "Cole uma mensagem com pelo menos algumas palavras." | Aprovado | — |
| S02 | "Não encontrei palavras para analisar (só números, símbolos ou emojis)..." | Aprovado | Antes respondia "não sei responder". |
| S03 | Mesma resposta do S02. | Aprovado | Idem. |
| S04 | Analisado sem travar, com o aviso "Seu texto tinha 9.999 caracteres. Analisei só os primeiros 5.000." | Aprovado | Antes cortava em silêncio. |
| S05 | Alto risco pelas regras (senha, pressa, clique) e o aviso "A mensagem parece estar em inglês. O modelo foi treinado só com mensagens em português..." | Aprovado | Antes dava baixo risco. Regras com termos em inglês e aviso de idioma. |
| S06 | Mesma resposta do S02. | Aprovado | Idem. |
| S07 | O texto aparece literalmente como `<script>alert(1)</script>` e nada é executado (o chat usa `st.text`). | Aprovado | — |
| S08 | "Ainda não sei responder isso..." Nenhuma instrução interna é revelada: o CyberBot não usa modelo de linguagem, só regras, classificador e uma base fixa. | Aprovado | — |

## 5. Histórico e SQLite

| ID | Resultado obtido | Status | Correção feita nesta rodada |
|---|---|---|---|
| H01 | Com o histórico desligado, a análise de `https://bit.ly/3example` não gerou nenhuma linha no banco (conferido no SQLite). | Aprovado | — |
| H02 | Ao ligar, a barra lateral mostra "Salvando..." e a opção de salvar o texto. Gravou tipo, nível, pontuação e sinais; o texto ficou vazio (não marcado). | Aprovado | Mensagem de estado mais clara na barra lateral. |
| H03 | Cinco análises (3 links e 2 mensagens) geraram exatamente 5 registros; estatísticas: total 5, links 3, mensagens 2. | Aprovado | — |
| H04 | Depois de reiniciar o servidor e abrir o mesmo endereço, a página Histórico mostrou as 3 análises da sessão (conferido no navegador). | Aprovado | Antes a sessão se perdia ao reiniciar ou recarregar. Agora, com o histórico ligado, o código anônimo da sessão vai para o endereço da página (`?s=...`). |
| H05 | Desligando, novas análises não são gravadas. A barra lateral e a página Histórico explicam que os registros antigos ficam até serem apagados ou completarem 30 dias. | Aprovado | Texto sobre os registros antigos. |
| H06 | Estatísticas só com números agregados: total, por tipo, por nível, categorias de sinais, "Últimos 7 dias" e a data do registro mais antigo. Nenhum texto aparece. | Aprovado | Novo número "Últimos 7 dias" e o período coberto. |

Observação sobre o H04: quem tiver o endereço com `?s=...` vê as análises daquela sessão (só
resultados, sem texto, a não ser que o usuário tenha marcado "salvar também o texto"). Para um MVP
sem cadastro isso é aceitável; numa versão com login, a sessão deve ficar ligada ao usuário.

## 6. Critérios gerais

| Critério | Atendido |
|---|---|
| Não apresentar erros ou travamentos | Sim (nenhuma exceção nos 46 casos) |
| Diferenciar mensagens suspeitas de comuns, reconhecendo que é probabilístico | Sim |
| Explicar quais elementos contribuíram | Sim |
| Identificar características suspeitas em links sem acessá-los | Sim |
| Não afirmar que um link é seguro só porque não achou sinais | Sim (aviso em todo resultado de baixo risco) |
| Respostas educativas corretas e compreensíveis | Sim |
| Tratar entradas vazias, longas, simbólicas ou inesperadas | Sim |
| Histórico desligado por padrão | Sim |
| Estatísticas coerentes e agregadas | Sim |
| Informar limitações e evitar certeza indevida | Sim |

## 7. Testes automáticos

`python -m pytest` roda 85 testes: os 34 que já existiam e 51 novos em `tests/test_plano.py`, um ou
mais por caso do plano. Resultado: 85 aprovados.

Limitações dos testes:
- O `AppTest` do Streamlit não consegue clicar no botão da barra lateral quando o app usa
  `st.navigation`; nos testes o botão é ligado pelo valor. O clique de verdade foi conferido no
  navegador.
- As perguntas educativas são encontradas por semelhança de palavras. Perguntas escritas de um jeito
  muito diferente podem cair no "não sei responder".
- Os testes do plano usam as mesmas frases do plano. Para medir o modelo de verdade, o próximo
  passo continua sendo um conjunto rotulado separado, com matriz de confusão, precisão, recall e F1
  (como sugere a seção 8 do plano).
