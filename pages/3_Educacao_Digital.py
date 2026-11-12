"""Página "Educação digital" (RF06): perguntas e lista de temas."""

import streamlit as st

from modules.educacao_digital import listar_conteudos, responder

st.title("Educação digital")

# Busca por pergunta livre na base educativa.
pergunta = st.text_input("Faça uma pergunta", placeholder="Ex.: cadeado no site garante que é seguro?")
if pergunta:
    achados = responder(pergunta, n=1)   # pega só o conteúdo mais parecido
    if achados:
        st.success(f"**{achados[0]['titulo']}**")
        st.markdown(achados[0]["conteudo"])
    else:
        # Nada parecido o suficiente: em vez de inventar, mostramos os temas disponíveis.
        st.warning("Não encontrei esse assunto na base. Veja a lista de temas abaixo.")

# Todos os temas da base, em caixas que abrem ao clicar.
st.subheader("Todos os temas")
for c in listar_conteudos():
    with st.expander(c["titulo"]):
        st.markdown(c["conteudo"])
