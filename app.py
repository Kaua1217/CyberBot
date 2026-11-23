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
# default=True indica a página que abre primeiro. Os ícones são do Material Symbols
# (biblioteca de ícones que o Streamlit já traz) e url_path é o endereço de cada página.
paginas = st.navigation([
    st.Page("pages/0_Conversar.py", title="Conversar", icon=":material/forum:", default=True),
    st.Page("pages/1_Analisar_Mensagem.py", title="Checar mensagem", icon=":material/sms:", url_path="mensagem"),
    st.Page("pages/2_Analisar_Link.py", title="Checar link", icon=":material/link:", url_path="link"),
    st.Page("pages/3_Educacao_Digital.py", title="Aprender sobre golpes", icon=":material/menu_book:", url_path="aprender"),
    st.Page("pages/4_Questionarios.py", title="Quiz", icon=":material/quiz:", url_path="quiz"),
    st.Page("pages/5_Historico.py", title="Meu histórico", icon=":material/history:", url_path="historico"),
])
# Executa a página escolhida pelo usuário no menu.
paginas.run()
