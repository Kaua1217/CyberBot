"""Testes da análise de links (modules/analise_links.py).

Rodar: python -m pytest
"""

import pytest

from modules.analise_links import analisar_link


# @pytest.mark.parametrize roda o mesmo teste várias vezes, uma para cada valor da lista.
@pytest.mark.parametrize("url", ["https://www.itau.com.br", "https://www.gov.br/receitafederal", "https://www.caixa.gov.br/"])
def test_sites_oficiais_baixo_risco(url):
    """Sites oficiais não podem ser marcados como perigosos (evita falso positivo)."""
    assert analisar_link(url).nivel == "baixo"


@pytest.mark.parametrize("url", [
    "itau-desbloqueio.com/login",        # marca falsa + palavras-isca
    "https://xn--ita-boa.com",           # "itaú.com" em punycode
    "http://192.168.0.1/banco/login",    # IP no lugar do nome
    "https://google.com@golpe.xyz",      # @ disfarçando o destino
    "nubank-seguranca.site/token",       # marca falsa + TLD suspeito
])
def test_enderecos_perigosos_alto_risco(url):
    """Golpes clássicos precisam dar alto risco (evita falso negativo)."""
    assert analisar_link(url).nivel == "alto"


def test_encurtador_gera_atencao():
    r = analisar_link("bit.ly/abc123")
    assert r.nivel == "atencao"
    assert any("encurtado" in i.descricao for i in r.indicadores)


def test_https_nao_e_garantia():
    """HTTPS não pode deixar um link falso com cara de seguro (seção 12)."""
    r = analisar_link("https://itau-seguranca.com")
    assert r.nivel != "baixo"
    assert any("HTTPS" in o for o in r.observacoes)


@pytest.mark.parametrize("entrada", ["", "   ", "nada", "http://exemplo .com", None, "a" * 3000, "http://site.com:99999"])
def test_entradas_malformadas_nao_quebram(entrada):
    """Entradas estranhas devolvem uma mensagem de erro, sem derrubar o programa."""
    r = analisar_link(entrada)
    assert r.erro


def test_nunca_acessa_a_rede(monkeypatch):
    """Garante o RNF07: a análise não abre conexão com a internet.

    monkeypatch troca temporariamente as funções de conexão por uma que dá erro.
    Se a análise tentasse acessar o site, o teste falharia.
    """
    import socket

    def proibido(*a, **k):
        raise AssertionError("a análise não pode acessar a rede")

    monkeypatch.setattr(socket, "create_connection", proibido)
    monkeypatch.setattr(socket.socket, "connect", proibido)
    analisar_link("https://qualquer-site.com/login")
