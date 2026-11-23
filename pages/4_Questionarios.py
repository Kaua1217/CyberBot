"""Página "Questionário" (RF07): perguntas de múltipla escolha com explicação."""

import streamlit as st

from modules.educacao_digital import corrigir, listar_questionario
from utils.interface import cabecalho

cabecalho("Quiz", "Você cairia nessa?",
          "Seis situações do dia a dia. Responda sem pressa: em cada uma eu explico o porquê.")

perguntas = listar_questionario()
# Guarda se cada pergunta foi acertada: {número da pergunta: True/False}.
respostas = st.session_state.setdefault("quiz", {})

for i, q in enumerate(perguntas):
    st.markdown(f"**{i + 1} de {len(perguntas)}.** {q['pergunta']}")
    # index=None deixa nenhuma alternativa marcada no início.
    # key diferente para cada pergunta, senão o Streamlit confunde os campos.
    escolha = st.radio("Sua resposta", q["alternativas"], index=None, key=f"q{i}", label_visibility="collapsed")
    if escolha is not None:
        c = corrigir(i, q["alternativas"].index(escolha))
        respostas[i] = c["correta"]
        # Caixa verde se acertou, vermelha se errou, sempre com a explicação.
        (st.success if c["correta"] else st.error)(
            ("Isso mesmo! " if c["correta"] else f"Quase. A resposta certa é: {c['resposta_correta']}. ") + c["explicacao"])
    st.divider()

# Quando todas as perguntas foram respondidas, mostra a nota.
if len(respostas) == len(perguntas):
    acertos = sum(respostas.values())   # True conta como 1 e False como 0
    st.metric("Você acertou", f"{acertos} de {len(perguntas)}")
    if acertos == len(perguntas):
        st.markdown("Mandou muito bem! Que tal mandar este quiz para alguém da família?")
    elif acertos >= len(perguntas) / 2:
        st.markdown("Bom resultado. Vale reler as explicações das que você errou.")
    else:
        st.markdown("Golpista conta com a pressa. Releia as explicações com calma e tente de novo.")
