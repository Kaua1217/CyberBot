"""Página "Analisar mensagem" (RF01, RF02 e RF03)."""

import streamlit as st

from modules.analise_mensagens import analisar_mensagem
from utils.interface import mostrar_resultado_mensagem, registrar

st.title("Analisar mensagem")
st.write("Cole o texto de um SMS, WhatsApp ou e-mail. O CyberBot procura sinais de golpe e explica o que encontrou.")
# Lembrete de privacidade antes de o usuário colar qualquer coisa.
st.info("Antes de colar, apague nomes, CPFs ou outros dados pessoais que estejam na mensagem.", icon="🔒")

# st.form agrupa os campos: a análise só roda quando o botão é apertado,
# e não a cada letra digitada.
with st.form("form_mensagem"):
    texto = st.text_area("Mensagem", height=160, max_chars=5000,
                         placeholder="Ex.: Sua conta será bloqueada hoje. Confirme seus dados em ...")
    enviado = st.form_submit_button("Analisar", type="primary")

if enviado:
    r = analisar_mensagem(texto)
    mostrar_resultado_mensagem(r)
    # Grava no histórico (só acontece se o usuário ligou essa opção).
    if not r.erro:
        registrar("mensagem", r.nivel, r.pontuacao, [{"descricao": i["nome"], "categoria": i["categoria"]} for i in r.indicadores], texto)
