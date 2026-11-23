"""Página "Analisar link" (RF04 e RF05). O link nunca é aberto (RNF07)."""

import streamlit as st

from modules.analise_links import analisar_link
from utils.interface import cabecalho, mostrar_resultado_link, registrar

cabecalho("Checar link", "Antes de clicar, me mostra o link",
          "Eu leio só o texto do endereço. O site nunca é aberto, então você pode colar sem medo.")

# Formulário: a análise roda só ao apertar o botão.
with st.form("form_link"):
    url = st.text_input("O link", max_chars=2048, placeholder="Ex.: bit.ly/abc123 ou https://itau-seguranca.com/login")
    enviado = st.form_submit_button("Checar link", type="primary")

if enviado:
    r = analisar_link(url)
    mostrar_resultado_link(r)
    if not r.erro:
        registrar("link", r.nivel, r.pontuacao, [{"descricao": i.descricao, "categoria": i.categoria} for i in r.indicadores], url)

# Explicação dos critérios, para o usuário aprender a conferir sozinho.
with st.expander("O que eu olho num link (dá para você conferir sozinho também)"):
    st.markdown("""
- Número IP no lugar do nome do site
- `@` antes do domínio, que disfarça o destino
- Caracteres de outros alfabetos (ataque de homógrafos, `xn--`)
- Encurtadores como bit.ly
- Nome de marca conhecida fora do domínio oficial
- Muitos subdomínios, hífens ou números misturados no nome
- Terminações muito usadas em golpes (.xyz, .top, .click...)
- Portas incomuns, endereços muito longos e palavras-isca (login, desbloqueio, prêmio)
- HTTP sem S. O HTTPS é registrado, mas **não** conta como prova de segurança.
""")
