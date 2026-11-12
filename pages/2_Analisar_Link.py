"""Página "Analisar link" (RF04 e RF05). O link nunca é aberto (RNF07)."""

import streamlit as st

from modules.analise_links import analisar_link
from utils.interface import mostrar_resultado_link, registrar

st.title("Analisar link")
st.write("Cole um endereço. O CyberBot olha **só o texto do endereço** e nunca abre o site.")

# Formulário: a análise roda só ao apertar o botão.
with st.form("form_link"):
    url = st.text_input("Endereço", max_chars=2048, placeholder="Ex.: bit.ly/abc123 ou https://itau-seguranca.com/login")
    enviado = st.form_submit_button("Analisar", type="primary")

if enviado:
    r = analisar_link(url)
    mostrar_resultado_link(r)
    if not r.erro:
        registrar("link", r.nivel, r.pontuacao, [{"descricao": i.descricao, "categoria": i.categoria} for i in r.indicadores], url)

# Explicação dos critérios, para o usuário aprender a conferir sozinho.
with st.expander("O que o CyberBot verifica num link"):
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
