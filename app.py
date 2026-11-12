"""CyberBot: ponto de entrada do aplicativo.

Rodar (na pasta CyberBot):
    streamlit run app.py

Este arquivo só monta a barra lateral e o menu de páginas. Cada página fica
em pages/ e toda a lógica de análise fica em modules/ (seção 5 do planejamento:
a interface não deve conter a lógica de classificação).

Como o Streamlit funciona: a cada clique ou texto enviado, o script inteiro
roda de novo, de cima para baixo. O que precisa ser lembrado entre essas
execuções fica guardado em st.session_state.
"""

import streamlit as st

from utils.interface import preparar_app

# Configura a página e desenha a barra lateral (comum a todas as páginas).
preparar_app()

# Define o menu. Cada st.Page aponta para um arquivo da pasta pages/.
# default=True indica a página que abre primeiro.
paginas = st.navigation([
    st.Page("pages/0_Conversar.py", title="Conversar", icon="💬", default=True),
    st.Page("pages/1_Analisar_Mensagem.py", title="Analisar mensagem", icon="✉️"),
    st.Page("pages/2_Analisar_Link.py", title="Analisar link", icon="🔗"),
    st.Page("pages/3_Educacao_Digital.py", title="Educação digital", icon="📚"),
    st.Page("pages/4_Questionarios.py", title="Questionário", icon="❓"),
    st.Page("pages/5_Historico.py", title="Histórico", icon="📊"),
])
# Executa a página escolhida pelo usuário no menu.
paginas.run()
