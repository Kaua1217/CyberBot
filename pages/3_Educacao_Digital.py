"""Página "Educação digital" (RF06): perguntas e lista de temas."""

import streamlit as st

from modules.educacao_digital import listar_conteudos, responder
from utils.interface import cabecalho, e

cabecalho("Aprender sobre golpes", "O que vale saber antes do golpe chegar",
          "Textos curtos, revisados, sobre os golpes mais comuns no Brasil e o que fazer em cada caso.")

# Busca por pergunta livre na base educativa.
pergunta = st.text_input("Procure um assunto", placeholder="Ex.: cadeado no site garante que é seguro?")
if pergunta:
    achados = responder(pergunta, n=1)   # pega só o conteúdo mais parecido
    if achados:
        with st.container(border=True):
            st.markdown(f'<div class="cb-resposta-titulo">{e(achados[0]["titulo"])}</div>', unsafe_allow_html=True)
            st.markdown(achados[0]["conteudo"])
    else:
        # Nada parecido o suficiente: em vez de inventar, mostramos os temas disponíveis.
        st.warning("Não achei esse assunto por aqui. Dá uma olhada na lista de temas abaixo.")

# Todos os temas da base, em caixas que abrem ao clicar.
st.subheader("Todos os temas")
for c in listar_conteudos():
    with st.expander(c["titulo"]):
        st.markdown(c["conteudo"])
