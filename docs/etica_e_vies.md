# Viés algorítmico e responsabilidade social

Um verificador de golpes erra de dois jeitos, e cada erro tem um custo para uma pessoa real:

- **Falso positivo:** chamar de golpe uma mensagem verdadeira. A pessoa pode deixar de responder a um parente ou desconfiar de um aviso legítimo do banco.
- **Falso negativo:** dizer "baixo risco" para um golpe. A pessoa se sente segura e perde dinheiro.

O CyberBot foi pensado para errar para o lado da cautela, mas isso não elimina o viés. Abaixo estão os testes que fizemos e o que eles mostram.

## 1. De onde vem o viés

| Fonte | Situação no CyberBot |
|---|---|
| **Dados de treino** | 177 mensagens, **todas escritas pelo autor do projeto** (64 legítimas, 56 suspeitas, 57 de alto risco). O modelo aprende o jeito de escrever de uma pessoa só. |
| **Idioma** | Treinado só em português. Mensagens em outro idioma dependem apenas das regras (o app avisa). |
| **Regras escritas à mão** | Refletem os golpes que o autor conhece (Pix, falso parente, falsa central). Golpes novos ou de outras regiões podem ficar de fora. |
| **Marcas conhecidas** | A lista de domínios oficiais tem 25 marcas, a maioria grandes empresas do Sudeste. Bancos e lojas regionais não estão na lista. |

## 2. Testes de viés

Mensagens escritas para este teste, fora da base de treino, analisadas pela função `analisar_mensagem` (23/11/2026).

**Mensagens legítimas que usam palavras comuns em golpes** (Pix, banco, código, "troquei de número"): **3 de 10 marcadas como golpe ou atenção.**

| Mensagem | Resultado |
|---|---|
| "Pai, troquei de número, salva esse aqui. Te ligo à noite pra explicar." | Alto risco |
| "Me passa sua chave Pix que eu te devolvo o dinheiro do lanche." | Alto risco |
| "Clique no link do Classroom que a professora mandou para ver a atividade." | Atenção |
| "Fiz o Pix do churrasco, confere aí se chegou." | Baixo risco |
| "O código da sala de aula é 4521, entra lá." | Baixo risco |

**Mensagens legítimas em escrita informal ou regional** ("vc", "oxe", "meu fi", "kkkkk"): **2 de 8 marcadas como atenção.** Exemplos: "kkkkk mano esqueci a chave de casa de novo" e "tô chegando, guarda um prato pra mim". Quem escreve de um jeito diferente do autor tem mais chance de receber um alerta falso.

**Golpes em escrita informal:** 3 de 4 detectados. Passou como baixo risco: "amigo me empresta 200 no pix q to sem acesso no app, te devolvo amanha".

### O que isso mostra

1. O sistema associa palavras a golpe, não intenções. "Troquei de número" é um sinal forte de golpe, mas também acontece de verdade.
2. A base escrita por uma pessoa só favorece um jeito de escrever. Escrita informal, abreviada ou regional gera mais alertas falsos.
3. Pedidos de dinheiro sem urgência nem palavras típicas podem escapar.

São poucos exemplos, então os números indicam tendências, não medidas precisas.

## 3. Impactos e responsabilidade social

- **Quem é mais afetado:** idosos e pessoas com menos familiaridade com tecnologia, que são o público principal. Para elas, um "baixo risco" pode soar como garantia. Por isso o app nunca diz "seguro", mostra "Isso não é garantia" e sempre orienta a confirmar pelo canal oficial.
- **Autonomia:** o bot explica os sinais e sugere passos, mas a decisão é da pessoa. O objetivo é ensinar a reconhecer o golpe, não criar dependência do aplicativo (por isso existem a página educativa e o quiz).
- **Privacidade:** mensagens podem ter dados de terceiros. O histórico é desligado por padrão, CPF, cartão e senha são bloqueados, e o texto só é guardado se o usuário pedir, mascarado e por até 30 dias.
- **Segurança:** links nunca são abertos, para não expor o usuário nem o servidor.
- **Transparência:** o código, os dados de treino, as métricas e este relatório estão no repositório.

## 4. O que já fazemos para reduzir o viés

- Nível final = o mais cauteloso entre modelo e regras, sempre com explicação dos sinais.
- Peso baixo para palavras que aparecem em mensagens normais (Pix e nomes de bancos valem 1 ponto).
- A regra de senha só dispara com um pedido ("envie", "informe"), não com qualquer menção a senha.
- Aviso automático quando a mensagem parece estar em outro idioma ou foi cortada.
- Linguagem que não culpa a vítima e não promete certeza.

## 5. Próximos passos

1. Aumentar a base para 300 a 500 mensagens, com **mensagens reais anonimizadas** de pessoas de várias regiões, idades e níveis de escolaridade.
2. Medir os falsos positivos por grupo (escrita formal x informal, regiões) num conjunto separado do treino.
3. Incluir bancos digitais e lojas regionais na lista de domínios oficiais.
4. Testar a interface com idosos para conferir se "Atenção" e "Baixo risco" são entendidos do jeito certo.
