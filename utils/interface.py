"""Peças de interface reaproveitadas pelas páginas do Streamlit.

Regra do projeto: a lógica de análise fica em modules/. Este arquivo só
MOSTRA os resultados na tela, para que a interface não misture regras de
negócio com apresentação (seção 5 do planejamento).
"""

import re
import uuid  # gera identificadores aleatórios (usado para a sessão anônima)

import streamlit as st

from modules.historico import Historico

# Cor de cada nível de risco. O Streamlit aceita cores no texto com a sintaxe :cor[texto].
# Mensagens usam legitima/suspeita/alto_risco e links usam baixo/atencao/alto.
CORES = {"legitima": "green", "baixo": "green", "suspeita": "orange", "atencao": "orange", "alto_risco": "red", "alto": "red"}

# Aviso mostrado em todo resultado (seção 12: não apresentar a análise como certeza).
AVISO = ("O resultado é **indicativo**. Baixo risco significa apenas que o CyberBot não encontrou sinais "
         "dentro dos critérios dele. Na dúvida, confirme por um canal oficial.")


def preparar_app():
    """Configuração comum a todas as páginas.

    É chamada uma vez pelo app.py a cada execução. Como a barra lateral é
    desenhada aqui (e não em cada página), as opções do usuário continuam
    marcadas quando ele troca de página.
    """
    st.set_page_config(page_title="CyberBot", page_icon="🛡️", layout="centered")

    # st.session_state guarda dados enquanto a aba do navegador estiver aberta.
    # Criamos um identificador anônimo para a sessão: assim o histórico funciona
    # sem cadastro e sem coletar nome ou e-mail (seção 8 do planejamento).
    # Quando o histórico está ligado, o identificador também vai para o endereço
    # da página (?s=...). Assim, se o app for reiniciado ou a página recarregada
    # nesse mesmo endereço, o usuário volta a ver as análises que salvou.
    if "sessao_id" not in st.session_state:
        da_url = st.query_params.get("s", "")
        st.session_state.sessao_id = da_url if re.fullmatch(r"[0-9a-f]{32}", da_url) else uuid.uuid4().hex

    with st.sidebar:
        st.markdown("### 🛡️ CyberBot")
        st.caption("Assistente de segurança digital")
        # O histórico começa DESLIGADO. O usuário escolhe se quer salvar (RF08).
        st.toggle("Salvar histórico desta sessão", key="salvar_historico",
                  help="Desligado por padrão. Salva só o resultado da análise, por até 30 dias.")
        # A opção de salvar o texto só aparece se o histórico estiver ligado.
        if st.session_state.get("salvar_historico"):
            if st.query_params.get("s") != st.session_state.sessao_id:
                st.query_params["s"] = st.session_state.sessao_id   # guarda a sessão no endereço da página
            st.checkbox("Salvar também o texto analisado", key="salvar_conteudo",
                        help="Números longos (CPF, cartão, telefone) e e-mails são mascarados e o texto é cortado em 300 caracteres.")
            st.caption("Salvando. Para voltar a este histórico depois, use o mesmo endereço da página.")
        else:
            st.caption("Histórico desligado: nada desta sessão é salvo. O que já foi salvo continua na página "
                       "Histórico até você apagar ou até completar 30 dias.")
        st.divider()
        st.caption("Nunca digite senhas, códigos ou dados do cartão. O CyberBot não pede esses dados.")


# @st.cache_resource faz o Streamlit criar o objeto uma vez só e reaproveitar
# entre as execuções, em vez de abrir uma conexão nova com o banco a cada clique.
@st.cache_resource
def historico() -> Historico:
    return Historico()


def registrar(tipo: str, classificacao: str, pontuacao: float, indicadores: list, conteudo: str):
    """Grava a análise no histórico, mas SÓ se o usuário tiver ligado essa opção."""
    if not st.session_state.get("salvar_historico"):
        return
    historico().registrar(st.session_state.sessao_id, tipo, classificacao, pontuacao, indicadores,
                          conteudo=conteudo, salvar_conteudo=st.session_state.get("salvar_conteudo", False))


def mostrar_resultado_mensagem(r):
    """Desenha na tela o resultado de modules.analise_mensagens.analisar_mensagem."""
    if r.erro:
        st.warning(r.erro)
        return
    # Título colorido com o nível (ex.: "Alto risco" em vermelho).
    st.markdown(f"#### :{CORES[r.nivel]}[{r.rotulo}]")
    # Limitações desta análise específica (texto cortado, outro idioma...).
    for aviso in r.avisos:
        st.info(aviso)
    # Barra de 0% a 100% com a chance estimada pelo modelo. min/max garantem o intervalo 0..1.
    st.progress(min(max(r.pontuacao, 0.0), 1.0), text=f"Chance estimada pelo modelo de ser golpe: {r.pontuacao:.0%}")
    # RF03: explicar quais indicadores levaram ao resultado.
    if r.indicadores:
        st.markdown("**Por que chegamos a esse resultado:**")
        for i in r.indicadores:
            st.markdown(f"- **{i['nome']}.** {i['explicacao']}")
    elif r.nivel != "legitima":
        # Nenhuma regra disparou: o nível veio só do classificador.
        st.markdown("Nenhuma regra específica disparou, mas o classificador achou a mensagem parecida com golpes "
                    "da base de treino. Confira pelo canal oficial antes de agir.")
    else:
        st.markdown("Não encontramos os sinais mais comuns de golpe nesta mensagem.")
    # Links encontrados dentro da mensagem aparecem em caixas que abrem e fecham.
    for l in r.links:
        with st.expander(f"Link encontrado: {l.dominio} ({l.rotulo})"):
            mostrar_resultado_link(l, titulo=False)
    # Detalhes técnicos para quem quiser entender o que o modelo calculou.
    with st.expander("Detalhes do modelo"):
        st.write(f"O classificador previu **{r.previsao_modelo}** com confiança de {r.confianca_modelo:.0%}. "
                 "O nível final é o mais alto entre a previsão do modelo e as regras.")
        st.json({k: round(v, 3) for k, v in r.probabilidades.items()})
    st.caption(AVISO)


def mostrar_resultado_link(r, titulo: bool = True):
    """Desenha na tela o resultado de modules.analise_links.analisar_link.

    titulo=False é usado quando o link aparece dentro do resultado de uma
    mensagem, onde o nível já está no título da caixa.
    """
    if r.erro:
        st.warning(r.erro)
        return
    if titulo:
        st.markdown(f"#### :{CORES[r.nivel]}[{r.rotulo}]")
    st.markdown(f"Domínio analisado: `{r.dominio}`")
    if r.indicadores:
        for i in r.indicadores:
            st.markdown(f"- {i.descricao}")
    else:
        st.markdown("- Nenhum sinal de alerta encontrado no endereço.")
    # Observações (ex.: "HTTPS não garante segurança") em letra menor.
    for o in r.observacoes:
        st.caption(o)
