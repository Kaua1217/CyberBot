"""Página do chat (página inicial do CyberBot).

O chat decide sozinho o que fazer com o que o usuário escreve:
- só um endereço  -> análise de link
- mensagem longa  -> análise de mensagem
- pergunta curta  -> resposta da base educativa
"""

import re

import streamlit as st

from modules.analise_links import analisar_link
from modules.analise_mensagens import analisar_mensagem
from modules.educacao_digital import responder
from utils.interface import mostrar_resultado_link, mostrar_resultado_mensagem, registrar

# A entrada inteira é um endereço? Ex.: "bit.ly/abc", "https://site.com/login"
_RE_SO_LINK = re.compile(r"^\s*(https?://)?[\w.-]+\.[a-z]{2,}(:\d+)?(/\S*)?\s*$", re.I)
# Dados que o usuário NÃO deveria digitar: CPF (000.000.000-00), número de cartão
# (13 a 19 dígitos seguidos) ou a expressão "minha senha".
_RE_DADO_SENSIVEL = re.compile(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}|\b\d{13,19}\b|minha senha", re.I)

# Textos fixos do chat.
SAUDACAO = ("Oi! Eu sou o **CyberBot**. Posso:\n\n"
            "- **analisar uma mensagem** suspeita: é só colar o texto aqui;\n"
            "- **avaliar um link** sem abri-lo: cole só o endereço;\n"
            "- **tirar dúvidas** sobre golpes, como *\"o que é phishing?\"* ou *\"caí num golpe, e agora?\"*.")
NAO_SEI = ("Ainda não sei responder isso. Tente perguntar sobre phishing, WhatsApp, senhas, links, boletos "
           "ou o que fazer depois de cair num golpe. Você também pode colar uma mensagem para eu analisar.")
# Botões de exemplo: rótulo do botão -> texto enviado ao chat.
EXEMPLOS = {
    "Exemplo de mensagem": "Mãe, troquei de número. Me faz um Pix urgente de R$ 800? Te devolvo amanhã.",
    "Exemplo de link": "itau-desbloqueio.com/login",
    "Exemplo de pergunta": "Caí num golpe, e agora?",
}


def decidir(texto: str) -> str:
    """Escolhe o tipo de resposta com regras simples.

    - Se o texto é só um endereço, é link.
    - Se tem 9 palavras ou mais, ou contém "http", tratamos como mensagem a analisar.
    - O resto (textos curtos) é tratado como pergunta para a base educativa.
    """
    if _RE_SO_LINK.match(texto):
        return "link"
    if len(texto.split()) >= 9 or "http" in texto.lower():
        return "mensagem"
    return "pergunta"


def processar(texto: str) -> dict:
    """Analisa uma entrada UMA vez e devolve o resultado.

    Guardamos o resultado na conversa para não analisar de novo a cada
    execução do Streamlit (senão o histórico gravaria a mesma análise várias vezes).
    """
    # Proteção de privacidade: se parece dado sensível, não analisa nem salva nada.
    if _RE_DADO_SENSIVEL.search(texto):
        return {"tipo": "sensivel"}
    tipo = decidir(texto)
    if tipo == "link":
        r = analisar_link(texto)
        if not r.erro:
            registrar("link", r.nivel, r.pontuacao, [{"descricao": i.descricao, "categoria": i.categoria} for i in r.indicadores], texto)
        return {"tipo": "link", "r": r}
    if tipo == "mensagem":
        r = analisar_mensagem(texto)
        if not r.erro:
            registrar("mensagem", r.nivel, r.pontuacao, [{"descricao": i["nome"], "categoria": i["categoria"]} for i in r.indicadores], texto)
        return {"tipo": "mensagem", "r": r}
    # Pergunta: busca os 2 conteúdos mais parecidos na base educativa.
    return {"tipo": "pergunta", "achados": responder(texto, n=2)}


def mostrar(resp: dict):
    """Desenha a resposta do bot de acordo com o tipo."""
    if resp["tipo"] == "sensivel":
        st.warning("Parece que você digitou um CPF, número de cartão ou senha. Não compartilhe esses dados em nenhum chat. "
                   "Se alguém pediu isso, é provável que seja golpe. Nada foi analisado nem salvo.")
    elif resp["tipo"] == "link":
        st.markdown("Analisei o endereço **sem abri-lo**:")
        mostrar_resultado_link(resp["r"])
    elif resp["tipo"] == "mensagem":
        st.markdown("Analisei a mensagem:")
        mostrar_resultado_mensagem(resp["r"])
    elif not resp["achados"]:
        # Nenhum conteúdo parecido o suficiente: o bot admite que não sabe.
        st.markdown(NAO_SEI)
    else:
        principal = resp["achados"][0]
        st.markdown(f"**{principal['titulo']}**\n\n{principal['conteudo']}")
        if len(resp["achados"]) > 1:
            st.caption(f"Veja também: {resp['achados'][1]['titulo']} (página Educação Digital).")


# ----------------------------- Montagem da página -----------------------------

st.title("🛡️ CyberBot")
st.caption("Análise de mensagens, avaliação de links e dicas de segurança digital.")

# A conversa fica no session_state para sobreviver às novas execuções do script.
# Cada item é uma dupla: (texto do usuário, resposta já processada).
conversa = st.session_state.setdefault("conversa", [])

# Mensagem de boas-vindas com os botões de exemplo.
with st.chat_message("assistant"):
    st.markdown(SAUDACAO)
    escolhido = None
    for col, (rotulo, exemplo) in zip(st.columns(3), EXEMPLOS.items()):
        if col.button(rotulo, use_container_width=True):
            escolhido = exemplo

# A entrada pode vir da caixa de texto ou de um botão de exemplo.
entrada = st.chat_input("Cole uma mensagem, um link ou faça uma pergunta") or escolhido
if entrada:
    entrada = entrada.strip()[:5000]   # limita o tamanho da entrada
    conversa.append((entrada, processar(entrada)))

# Mostra toda a conversa, em ordem.
for texto, resp in conversa:
    with st.chat_message("user"):
        # st.text mostra o texto puro (sem interpretar Markdown), mais seguro para conteúdo do usuário.
        # Se havia dado sensível, nem repetimos o que foi digitado.
        st.text(texto if resp["tipo"] != "sensivel" else "[mensagem ocultada: continha dado sensível]")
    with st.chat_message("assistant"):
        mostrar(resp)

if conversa and st.button("Limpar conversa"):
    conversa.clear()
    st.rerun()   # roda a página de novo para ela aparecer vazia
