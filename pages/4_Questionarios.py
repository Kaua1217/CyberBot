"""Página "Questionário" (RF07): perguntas de múltipla escolha com explicação."""

import streamlit as st

from modules.educacao_digital import corrigir, listar_questionario

st.title("Questionário: você reconhece um golpe?")

perguntas = listar_questionario()
# Guarda se cada pergunta foi acertada: {número da pergunta: True/False}.
respostas = st.session_state.setdefault("quiz", {})

for i, q in enumerate(perguntas):
    st.markdown(f"**{i + 1}. {q['pergunta']}**")
    # index=None deixa nenhuma alternativa marcada no início.
    # key diferente para cada pergunta, senão o Streamlit confunde os campos.
    escolha = st.radio("Sua resposta", q["alternativas"], index=None, key=f"q{i}", label_visibility="collapsed")
    if escolha is not None:
        c = corrigir(i, q["alternativas"].index(escolha))
        respostas[i] = c["correta"]
        # Caixa verde se acertou, vermelha se errou, sempre com a explicação.
        (st.success if c["correta"] else st.error)(
            ("Certo! " if c["correta"] else f"Não. A resposta é: {c['resposta_correta']}. ") + c["explicacao"])
    st.divider()

# Quando todas as perguntas foram respondidas, mostra a nota.
if len(respostas) == len(perguntas):
    acertos = sum(respostas.values())   # True conta como 1 e False como 0
    st.metric("Seu resultado", f"{acertos} de {len(perguntas)}")
