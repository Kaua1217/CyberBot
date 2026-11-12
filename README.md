# CyberBot

Assistente de segurança digital que ajuda a reconhecer golpes. Projeto acadêmico, sem API paga.

- **Analisa mensagens** suspeitas (SMS, WhatsApp, e-mail) com um classificador próprio (TF-IDF + Regressão Logística) e regras que explicam o resultado.
- **Avalia links** só pelo texto do endereço, sem nunca abrir o site.
- **Responde dúvidas** a partir de uma base educativa revisada, e tem um questionário.
- **Histórico opcional** em SQLite, desligado por padrão, com estatísticas agregadas.

## Como rodar

Precisa de Python 3.10 ou mais novo.

```bash
cd CyberBot
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt

python -m models.treinamento   # treina o modelo com a sua versão do scikit-learn
streamlit run app.py
```

O navegador abre em `http://localhost:8501`. Para rodar os testes: `python -m pytest`.

O resultado do Plano de Testes (46 casos) está em [docs/resultado_plano_de_testes.md](docs/resultado_plano_de_testes.md), e os casos estão automatizados em `tests/test_plano.py`.

## Estrutura

```
app.py                     ponto de entrada: barra lateral e menu
pages/                     uma página por funcionalidade (0_Conversar é o chat)
modules/
  analise_mensagens.py     modelo + regras explicáveis -> nível de risco
  analise_links.py         análise estática de URLs (IP, @, punycode, encurtador, marca falsa...)
  educacao_digital.py      busca na base educativa e correção do questionário
  historico.py             gravação opcional, mascaramento e estatísticas
models/
  treinamento.py           treina e compara Naive Bayes x Regressão Logística
  classificador.pkl        modelo escolhido
  vectorizer.pkl           vetorizador TF-IDF
data/
  mensagens_treinamento.csv  mensagens rotuladas (legitima, suspeita, alto_risco)
  base_educativa.json        conteúdos e questionário
database/                  conexão e criação das tabelas SQLite
utils/                     pré-processamento de texto, validação de URL e peças da interface
tests/                     testes automatizados (pytest)
docs/relatorio_modelo.md   métricas por classe e matriz de confusão
```

## Como o resultado é calculado

1. O classificador estima a categoria da mensagem (legítima, suspeita ou alto risco).
2. Regras procuram sinais concretos: pedido de senha ou código, pressa, Pix, taxa antecipada, número novo, chamada para clicar, oferta boa demais, contato por número da própria mensagem, acesso remoto etc.
3. Links dentro da mensagem passam pela análise de links.
4. O nível final é o **mais alto** entre o modelo e as regras. Assim um golpe com palavras novas ainda é pego pelas regras, e o usuário sempre vê por que chegamos ao resultado.

Na tela os níveis aparecem como **Baixo risco**, **Atenção** e **Alto risco**. Baixo risco significa só que não encontramos sinais dentro dos critérios do sistema.

## Resultados do modelo

Base atual: 177 mensagens escritas para o projeto. A Regressão Logística com n-gramas de caracteres teve F1 macro de cerca de 0,77 tanto na validação cruzada quanto no teste. O Naive Bayes ficou abaixo. Detalhes, matriz de confusão e limitações em [docs/relatorio_modelo.md](docs/relatorio_modelo.md).

Para melhorar: aumentar a base para 300 a 500 mensagens (com mensagens reais anonimizadas e conjuntos públicos, respeitando as licenças) e rodar `python -m models.treinamento` de novo.

## Privacidade e limitações

- O CyberBot não pede senhas, códigos, dados bancários ou documentos. Se o usuário digitar CPF, cartão ou senha no chat, a entrada é bloqueada e não é analisada nem salva.
- O histórico só grava se o usuário ativar. Com ele ligado, o código anônimo da sessão vai para o endereço da página (`?s=...`), para o usuário reencontrar o histórico depois de recarregar ou reiniciar o app; quem tiver esse endereço vê os resultados daquela sessão. Por padrão grava só o resultado, não o texto. O texto só é salvo se o usuário marcar a opção, com números longos e e-mails mascarados e corte em 300 caracteres. Registros com mais de 30 dias são apagados.
- Links nunca são acessados (há um teste que garante isso). Endereços que não são http/https, como `javascript:`, são recusados.
- HTTPS não é tratado como prova de segurança.
- A análise é indicativa e pode errar. O app sempre orienta confirmar pelo canal oficial.
- O modelo foi treinado só com mensagens em português. Mensagens em outro idioma recebem um aviso e contam principalmente com as regras.

## Projetos de referência

Estes projetos públicos serviram de inspiração. O código do CyberBot foi escrito do zero; nada foi copiado deles.

| Projeto | O que analisa | Técnica principal | Interface |
|---|---|---|---|
| [sanchitdangi/phishing-email-detection](https://github.com/sanchitdangi/phishing-email-detection) | E-mails | TF-IDF + atributos do e-mail; compara Regressão Logística, Naive Bayes, Random Forest e LightGBM; explicação com SHAP | FastAPI e Streamlit |
| [anujp-0709/phishing-url-detector](https://github.com/anujp-0709/phishing-url-detector) | URLs | Atributos extraídos da URL (tamanho, subdomínios, palavras-chave) com scikit-learn | Streamlit |
| [alfred-abraham/phishing_detection_capstone](https://github.com/alfred-abraham/phishing_detection_capstone) | E-mails e URLs | Compara cinco modelos; TF-IDF + Random Forest para e-mails | Streamlit |
| [rocky-2904/NeuroPhish](https://github.com/rocky-2904/NeuroPhish) | E-mails | TF-IDF + regras manuais (urgência, links com IP) com Random Forest | Streamlit |
| [ARAGALAGOVARDHANREDDY/phishing-url-detection](https://github.com/ARAGALAGOVARDHANREDDY/phishing-url-detection) | URLs e a página | Árvore de decisão com atributos da URL e da página, mais regras de segurança | Streamlit |

### O que o CyberBot aproveita dessas ideias

- **TF-IDF + modelo clássico comparado com outros** (como nos projetos 1, 3 e 4), com Naive Bayes e Regressão Logística.
- **Modelo + regras explicáveis** (como nos projetos 1, 4 e 5): o usuário vê por que o resultado saiu assim.
- **Atributos da URL** (como nos projetos 2 e 5): IP, subdomínios, encurtadores, palavras-isca.
- **Interface em Streamlit**, usada em todos os cinco.

### O que o CyberBot faz diferente

- **Foco no Brasil e em português:** golpes do Pix, falso parente no WhatsApp, falsa central, marcas e órgãos brasileiros. Os cinco projetos trabalham com textos em inglês.
- **Junta mensagem, link e educação num chat só**, com base educativa e questionário.
- **Nunca abre o link.** O projeto 5 acessa a página ao vivo; o CyberBot olha só o texto do endereço, por segurança (RNF07).
- **Privacidade:** histórico desligado por padrão, dados pessoais mascarados e retenção de 30 dias.
- **Métricas honestas para uma base pequena:** com 177 mensagens o F1 fica em torno de 0,77. Projetos com bases grandes do Kaggle chegam a 96–98%, e um deles relata 100%, que o próprio autor diz valer só para aquela divisão dos dados. Aumentar a base é o próximo passo.
