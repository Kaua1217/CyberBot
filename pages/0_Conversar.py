"""Página do chat (página inicial do CyberBot).

O chat decide sozinho o que fazer com o que o usuário escreve:
- só um endereço  -> análise de link
- mensagem longa  -> análise de mensagem
- pergunta curta  -> resposta da base educativa
"""

import re

import streamlit as st
import streamlit.components.v1 as components

from utils.processamento_texto import TAMANHO_MAXIMO, normalizar

from modules.analise_links import analisar_link
from modules.analise_mensagens import analisar_mensagem
from modules.educacao_digital import responder
from utils.interface import AVATAR_BOT, AVATAR_VOCE, cabecalho, e, mostrar_resultado_link, mostrar_resultado_mensagem, registrar

# A entrada inteira é um endereço? Ex.: "bit.ly/abc", "https://site.com/login"
_RE_SO_LINK = re.compile(r"^\s*(https?://)?[\w.-]+\.[a-z]{2,}(:\d+)?(/\S*)?\s*$", re.I)
# Esquemas que não são web, mas o usuário pode colar achando que é link (ex.: "javascript:alert(1)").
_RE_ESQUEMA_ESTRANHO = re.compile(r"^(javascript|data|vbscript|file|ftp|blob):", re.I)
# Dados que o usuário NÃO deveria digitar: CPF (000.000.000-00), número de cartão
# (13 a 19 dígitos seguidos) ou uma senha escrita ("minha senha é...", "senha: ...").
# Perguntas como "o banco pode pedir minha senha?" NÃO são bloqueadas.
_RE_DADO_SENSIVEL = re.compile(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}|\b\d{13,19}\b|minha senha (e|é)\b|\bsenha\s*[:=]\s*\S", re.I)
# Pelo menos uma palavra (duas letras seguidas). Sem isso não há o que analisar.
_RE_PALAVRA = re.compile(r"[^\W\d_]{2,}")
# Começos típicos de pergunta (texto já sem acento e em minúsculas).
_RE_INICIO_PERGUNTA = re.compile(r"^(como|o que|oque|qual|quais|quando|onde|por que|porque|pq|posso|devo|pode|e seguro|existe|vale a pena|tem como)\b")

# Textos fixos do chat. Escritos como uma pessoa falaria, sem jargão.
SAUDACAO = ("Oi! Chegou alguma mensagem estranha, um link esquisito ou ficou com dúvida se é golpe? "
            "Me manda aqui que eu dou uma olhada com você.\n\n"
            "Pode **colar a mensagem inteira**, **só o link** (eu nunca abro o site) ou **fazer uma pergunta**, "
            "tipo *\"o banco pode pedir minha senha?\"*.")
NAO_SEI = ("Hmm, essa eu ainda não sei responder. Consigo falar sobre phishing, WhatsApp, senhas, links, boletos, "
           "Pix e o que fazer depois de cair num golpe. Se quiser, cole aqui a mensagem que você recebeu.")
# Atalhos de exemplo: texto do botão -> texto enviado ao chat.
EXEMPLOS = {
    "“Mãe, troquei de número…”": "Mãe, troquei de número. Me faz um Pix urgente de R$ 800? Te devolvo amanhã.",
    "itau-desbloqueio.com/login": "itau-desbloqueio.com/login",
    "Caí num golpe, e agora?": "Caí num golpe, e agora?",
}


def eh_pergunta(texto: str) -> bool:
    """Uma frase só, terminada em "?" ou começando com palavra de pergunta.

    Mensagens de golpe também podem ter "?" ("me faz um Pix?"), por isso só
    contamos como pergunta quando há UMA frase e menos de 25 palavras.
    """
    t = normalizar(texto)
    uma_frase = not re.search(r"[.!?]\s", t)          # nenhum fim de frase no meio do texto
    curta = len(t.split()) < 25
    return uma_frase and curta and "http" not in t and (t.endswith("?") or bool(_RE_INICIO_PERGUNTA.match(t)))


def decidir(texto: str) -> str:
    """Escolhe o tipo de resposta com regras simples.

    - Sem nenhuma palavra (só números, símbolos ou emojis): não há o que analisar.
    - Uma "palavra" só, sem espaços, que parece endereço (tem "://", termina em
      .com, .br... ou começa com "javascript:"): é link.
    - Pergunta (ver eh_pergunta): base educativa.
    - Com 9 palavras ou mais, ou com "http": mensagem a analisar.
    - O resto (textos curtos) é tratado como pergunta.
    """
    texto = texto.strip()
    if not _RE_PALAVRA.search(texto):
        return "vazio"
    if " " not in texto and ("://" in texto or _RE_SO_LINK.match(texto) or _RE_ESQUEMA_ESTRANHO.match(texto)):
        return "link"
    if eh_pergunta(texto):
        return "pergunta"
    if len(texto.split()) >= 9 or "http" in texto.lower():
        return "mensagem"
    return "pergunta"


def processar_mensagem(texto: str) -> dict:
    """Analisa o texto como mensagem recebida e grava no histórico (se ativado)."""
    r = analisar_mensagem(texto)
    if not r.erro:
        registrar("mensagem", r.nivel, r.pontuacao, [{"descricao": i["nome"], "categoria": i["categoria"]} for i in r.indicadores if i["peso"] > 0], texto)
    return {"tipo": "mensagem", "r": r}


def processar(texto: str) -> dict:
    """Analisa uma entrada UMA vez e devolve o resultado.

    Guardamos o resultado na conversa para não analisar de novo a cada
    execução do Streamlit (senão o histórico gravaria a mesma análise várias vezes).
    """
    # Proteção de privacidade: se parece dado sensível, não analisa nem salva nada.
    if _RE_DADO_SENSIVEL.search(texto):
        return {"tipo": "sensivel"}
    tipo = decidir(texto)
    if tipo == "vazio":
        return {"tipo": "vazio"}
    if tipo == "link":
        r = analisar_link(texto)
        if not r.erro:
            registrar("link", r.nivel, r.pontuacao, [{"descricao": i.descricao, "categoria": i.categoria} for i in r.indicadores], texto)
        return {"tipo": "link", "r": r}
    if tipo == "mensagem":
        return processar_mensagem(texto)
    # Pergunta: busca os 2 conteúdos mais parecidos na base educativa.
    achados = responder(texto, n=2)
    if not achados and len(texto.split()) >= 9:
        # Não era uma pergunta conhecida, mas é um texto longo: analisa como mensagem.
        return processar_mensagem(texto)
    return {"tipo": "pergunta", "achados": achados}


def mostrar(resp: dict):
    """Desenha a resposta do bot de acordo com o tipo."""
    if resp["tipo"] == "sensivel":
        st.warning("Opa, parece que tem um CPF, número de cartão ou senha aí. Tirei da conversa e não analisei nem "
                   "salvei nada. Não mande esses dados por chat para ninguém, nem para mim. Se alguém pediu, "
                   "provavelmente é golpe.")
    elif resp["tipo"] == "vazio":
        st.markdown("Não achei nenhuma palavra aqui, só números, símbolos ou emojis. "
                    "Cola a mensagem inteira que chegou para você?")
    elif resp["tipo"] == "link":
        st.caption("Olhei só o endereço, sem abrir o site.")
        mostrar_resultado_link(resp["r"])
    elif resp["tipo"] == "mensagem":
        mostrar_resultado_mensagem(resp["r"])
    elif not resp["achados"]:
        # Nenhum conteúdo parecido o suficiente: o bot admite que não sabe.
        st.markdown(NAO_SEI)
    else:
        principal = resp["achados"][0]
        st.markdown(f'<div class="cb-resposta-titulo">{e(principal["titulo"])}</div>', unsafe_allow_html=True)
        st.markdown(principal["conteudo"])
        if len(resp["achados"]) > 1:
            st.caption(f"Tem mais sobre isso em \"{resp['achados'][1]['titulo']}\", na página Aprender sobre golpes.")


# ----------------------------- Montagem da página -----------------------------

cabecalho("Conversar", "Recebeu algo estranho?",
          "Mensagem, link ou dúvida: eu explico o que vejo e o que eu faria no seu lugar.")

# A conversa fica no session_state para sobreviver às novas execuções do script.
# Cada item é uma dupla: (texto do usuário, resposta já processada).
conversa = st.session_state.setdefault("conversa", [])

# Mensagem de boas-vindas com os atalhos de exemplo.
with st.chat_message("assistant", avatar=AVATAR_BOT):
    st.markdown(SAUDACAO)
    st.caption("Quer ver como funciona? Toque num exemplo:")
    escolhido = None
    for col, (rotulo, exemplo) in zip(st.columns(3), EXEMPLOS.items()):
        if col.button(rotulo, use_container_width=True):
            escolhido = exemplo

# A entrada pode vir da caixa de texto ou de um botão de exemplo.
entrada = st.chat_input("Cole a mensagem, o link ou escreva sua dúvida") or escolhido
if entrada:
    entrada = entrada.strip()
    tamanho_original = len(entrada)
    entrada = entrada[:TAMANHO_MAXIMO]   # limita o tamanho da entrada
    resposta = processar(entrada)
    if tamanho_original > TAMANHO_MAXIMO:
        resposta["cortado"] = tamanho_original   # para avisar o usuário
    conversa.append((entrada, resposta))

# Mostra toda a conversa, em ordem.
for texto, resp in conversa:
    with st.chat_message("user", avatar=AVATAR_VOCE):
        # st.text mostra o texto puro (sem interpretar Markdown), mais seguro para conteúdo do usuário.
        # Se havia dado sensível, nem repetimos o que foi digitado.
        st.text(texto if resp["tipo"] != "sensivel" else "[mensagem escondida: tinha um dado pessoal]")
    with st.chat_message("assistant", avatar=AVATAR_BOT):
        if resp.get("cortado"):
            st.info(f"Seu texto tinha {resp['cortado']:,} caracteres. Analisei só os primeiros {TAMANHO_MAXIMO:,}.".replace(",", "."))
        mostrar(resp)

# Quando a entrada vem de um botão de exemplo, o Streamlit não rola a página
# sozinho (ele só faz isso para a caixa de texto). Sem isso a resposta ficava
# lá embaixo, fora da tela, e parecia que o botão não tinha funcionado.
# O script roda num quadro invisível e rola até a mensagem que acabou de entrar.
if escolhido:
    components.html(
        f"""<script>
        // n={len(conversa)}: muda a cada nova mensagem, para o script rodar de novo.
        const doc = window.parent.document;
        const rolar = () => {{
            const msgs = doc.querySelectorAll('[data-testid="stChatMessage"]');
            // Para na pergunta do usuário (penúltima mensagem), com a resposta logo abaixo.
            const alvo = msgs[Math.max(msgs.length - 2, 0)];
            if (alvo) alvo.scrollIntoView({{behavior: "smooth", block: "start"}});
        }};
        setTimeout(rolar, 150);
        setTimeout(rolar, 600);
        </script>""",
        height=0,
    )

if conversa and st.button("Começar de novo"):
    conversa.clear()
    st.rerun()   # roda a página de novo para ela aparecer vazia
