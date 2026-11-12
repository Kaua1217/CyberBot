"""Testes da análise de mensagens, da base educativa e do histórico.

Rodar: python -m pytest
"""

import pytest

from database.conexao import conectar
from modules.analise_mensagens import analisar_mensagem, encontrar_indicadores
from modules.educacao_digital import responder
from modules.historico import Historico, mascarar


@pytest.mark.parametrize("texto", [
    "Mãe, troquei de número. Preciso de um Pix urgente de R$ 900, te devolvo amanhã.",
    "Seu cartão foi clonado. Um motoboy vai buscar o cartão, deixe a senha anotada.",
    "Informe o código de 6 dígitos que chegou por SMS para não perder sua conta.",
    "Pague a taxa de liberação de R$ 200 para receber seu empréstimo aprovado.",
])
def test_golpes_claros_sao_alto_risco(texto):
    """Golpes conhecidos (escritos de um jeito diferente da base de treino) dão alto risco."""
    assert analisar_mensagem(texto).nivel == "alto_risco"


@pytest.mark.parametrize("texto", [
    "Oi, vamos almoçar amanhã perto do trabalho?",
    "A reunião foi remarcada para segunda às 10h.",
    "Cheguei em casa, obrigado pela carona!",
])
def test_mensagens_comuns_sao_baixo_risco(texto):
    """Mensagens do dia a dia não podem ser tratadas como golpe."""
    assert analisar_mensagem(texto).nivel == "legitima"


def test_explica_os_indicadores():
    """RF03: o sistema diz quais sinais encontrou."""
    nomes = {i["nome"] for i in encontrar_indicadores("URGENTE: informe sua senha agora")}
    assert {"Pede senha ou código", "Pressa ou ameaça"} <= nomes   # <= quer dizer "está contido em"


def test_link_dentro_da_mensagem_e_analisado():
    r = analisar_mensagem("Sua encomenda está retida, pague em http://correios-taxa.xyz hoje")
    assert r.links and r.links[0].dominio == "correios-taxa.xyz"


@pytest.mark.parametrize("entrada", ["", "oi", None, "x" * 20000])
def test_entradas_estranhas_nao_quebram(entrada):
    """Vazio, muito curto, None ou gigante: nada disso pode derrubar o programa."""
    analisar_mensagem(entrada)


def test_base_educativa_responde_e_admite_nao_saber():
    assert responder("o que é phishing")[0]["id"] == "phishing"
    assert responder("cadeado no site garante que é seguro?")[0]["id"] == "https"
    # Fora do tema: o bot deve devolver lista vazia (não sabe), em vez de inventar.
    assert responder("qual a capital da França") == []


def test_historico_mascara_e_nao_salva_texto_por_padrao(tmp_path):
    """Regras de privacidade do histórico.

    tmp_path é uma pasta temporária criada pelo pytest, para não mexer no banco de verdade.
    """
    h = Historico(conectar(tmp_path / "t.db"))
    # 1ª análise: sem pedir para salvar o texto.
    h.registrar("s1", "mensagem", "alto_risco", 0.9, [{"descricao": "x", "categoria": "c"}], conteudo="meu cpf 123.456.789-00")
    # 2ª análise: pedindo para salvar o texto.
    h.registrar("s1", "mensagem", "alto_risco", 0.9, [], conteudo="meu cpf 123.456.789-00", salvar_conteudo=True)
    itens = h.listar("s1")                    # vem da mais nova para a mais antiga
    assert itens[1]["conteudo"] is None       # a 1ª não guardou texto
    assert "123" not in itens[0]["conteudo"]  # a 2ª guardou, mas com o CPF mascarado
    assert h.estatisticas()["total"] == 2
    assert h.apagar_sessao("s1") == 2


def test_mascarar():
    assert mascarar("ligue 11 98765-4321 ou ana@mail.com") == "ligue [número] ou [e-mail]"
