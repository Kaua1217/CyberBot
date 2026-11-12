"""Página "Histórico" (RF08, RF09 e RF10): análises da sessão e estatísticas gerais."""

import pandas as pd
import streamlit as st

from utils.interface import historico

# Nome amigável de cada nível. Mensagens e links usam nomes internos diferentes,
# então juntamos os dois aqui para a tabela e o gráfico ficarem uniformes.
NOMES_NIVEIS = {"legitima": "Baixo risco", "baixo": "Baixo risco", "suspeita": "Atenção", "atencao": "Atenção",
                "alto_risco": "Alto risco", "alto": "Alto risco"}

st.title("Histórico e estatísticas")

h = historico()

# ------------------------- Histórico da sessão (RF09) -------------------------
st.subheader("Suas análises nesta sessão")
if not st.session_state.get("salvar_historico"):
    st.info("O histórico está desligado. Ative em **Salvar histórico desta sessão**, na barra lateral, para guardar os resultados por até 30 dias.")
itens = h.listar(st.session_state.sessao_id)
if itens:
    # Monta uma tabela (DataFrame do pandas) com uma linha por análise.
    df = pd.DataFrame([{"Quando": i["data_analise"], "Tipo": i["tipo"],
                        "Resultado": NOMES_NIVEIS.get(i["classificacao"], i["classificacao"]),
                        "Pontuação": i["pontuacao"], "Sinais": "; ".join(i["indicadores"]),
                        "Texto (mascarado)": i["conteudo"] or "não salvo"} for i in itens])
    st.dataframe(df, hide_index=True, use_container_width=True)
    # O usuário pode apagar o próprio histórico a qualquer momento.
    if st.button("Apagar meu histórico"):
        h.apagar_sessao(st.session_state.sessao_id)
        st.rerun()
else:
    st.caption("Nenhuma análise salva nesta sessão.")

# ------------------------- Estatísticas gerais (RF10) -------------------------
st.subheader("Estatísticas gerais")
st.caption("Números agregados de todos os usuários, sem nenhum texto analisado.")
est = h.estatisticas()

# Três números lado a lado.
c1, c2, c3 = st.columns(3)
c1.metric("Análises", est["total"])
c2.metric("Mensagens", est["por_tipo"].get("mensagem", 0))
c3.metric("Links", est["por_tipo"].get("link", 0))

# Gráfico de barras: quantidade por nível de risco, separado por tipo.
if est["por_nivel"]:
    df_nivel = pd.DataFrame(est["por_nivel"], columns=["tipo", "nível", "quantidade"])
    df_nivel["nível"] = df_nivel["nível"].map(NOMES_NIVEIS).fillna(df_nivel["nível"])
    # Depois de traduzir os nomes, soma as linhas que ficaram com o mesmo nível.
    df_nivel = df_nivel.groupby(["tipo", "nível"], as_index=False)["quantidade"].sum()
    st.bar_chart(df_nivel, x="nível", y="quantidade", color="tipo")

# Gráfico horizontal com os sinais de alerta mais comuns.
if est["indicadores"]:
    st.markdown("**Sinais mais encontrados**")
    st.bar_chart(pd.DataFrame(est["indicadores"], columns=["categoria", "quantidade"]), x="categoria", y="quantidade", horizontal=True)
