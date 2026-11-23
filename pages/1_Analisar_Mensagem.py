"""Página "Analisar mensagem" (RF01, RF02 e RF03)."""

import streamlit as st

from modules.analise_mensagens import analisar_mensagem
from utils.interface import cabecalho, mostrar_resultado_mensagem, registrar

cabecalho("Checar mensagem", "Cola aqui o que chegou para você",
          "SMS, WhatsApp ou e-mail. Eu procuro os sinais de golpe e explico o que encontrei.")
# Lembrete de privacidade antes de o usuário colar qualquer coisa.
st.caption("Dica: antes de colar, apague nomes, CPFs e outros dados pessoais da mensagem.")

# st.form agrupa os campos: a análise só roda quando o botão é apertado,
# e não a cada letra digitada.
with st.form("form_mensagem"):
    texto = st.text_area("A mensagem", height=160, max_chars=5000,
                         placeholder="Ex.: Sua conta será bloqueada hoje. Confirme seus dados em ...")
    enviado = st.form_submit_button("Checar mensagem", type="primary")

if enviado:
    r = analisar_mensagem(texto)
    mostrar_resultado_mensagem(r)
    # Grava no histórico (só acontece se o usuário ligou essa opção).
    if not r.erro:
        registrar("mensagem", r.nivel, r.pontuacao, [{"descricao": i["nome"], "categoria": i["categoria"]} for i in r.indicadores if i["peso"] > 0], texto)
