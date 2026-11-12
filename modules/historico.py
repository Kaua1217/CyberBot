"""Módulo 4: histórico e estatísticas (RF08, RF09 e RF10).

Política de privacidade aplicada aqui (seção 12 do planejamento):
- Nada é salvo se o usuário não ativar o histórico (o controle fica na interface).
- Por padrão salva só o resultado (tipo, nível, pontuação e indicadores), não o texto.
- O texto só é salvo se o usuário marcar a opção, e mesmo assim com números longos
  (CPF, cartão, telefone) e e-mails mascarados, e cortado em 300 caracteres.
- Registros com mais de DIAS_RETENCAO dias são apagados automaticamente.
"""

import re

from database.conexao import conectar
from database.criar_tabelas import criar_tabelas

DIAS_RETENCAO = 30       # por quantos dias um registro fica guardado
LIMITE_CONTEUDO = 300    # tamanho máximo do texto salvo
# Sequência de pelo menos 8 caracteres que começa e termina com dígito e só tem
# dígitos, pontos, hífens, barras e espaços no meio: pega CPF, cartão, telefone, CNPJ.
_RE_NUMEROS_LONGOS = re.compile(r"\d[\d.\-\s/]{6,}\d")
_RE_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")


def mascarar(texto: str) -> str:
    """Esconde dados pessoais antes de salvar.

    Exemplo: "meu cpf 123.456.789-00" -> "meu cpf [número]"
    """
    texto = _RE_EMAIL.sub("[e-mail]", texto)
    texto = _RE_NUMEROS_LONGOS.sub("[número]", texto)
    return texto[:LIMITE_CONTEUDO]


class Historico:
    """Lê e grava análises no banco SQLite."""

    def __init__(self, conn=None):
        # Permite passar outra conexão (os testes usam um banco temporário).
        self.conn = conn or conectar()
        criar_tabelas(self.conn)     # garante que as tabelas existem
        self.limpar_antigos()        # aplica a regra de retenção ao abrir

    def limpar_antigos(self, dias: int = DIAS_RETENCAO) -> int:
        """Apaga análises mais antigas que o prazo. Devolve quantas foram apagadas."""
        # datetime('now', '-30 days') é uma função do SQLite que calcula a data de 30 dias atrás.
        # Os "?" são parâmetros: o SQLite insere os valores com segurança (evita SQL injection).
        cur = self.conn.execute("DELETE FROM analises WHERE data_analise < datetime('now', ?)", (f"-{int(dias)} days",))
        self.conn.commit()
        return cur.rowcount

    def registrar(self, sessao_id: str, tipo: str, classificacao: str, pontuacao: float,
                  indicadores: list, conteudo: str | None = None, salvar_conteudo: bool = False) -> int:
        """Grava uma análise e seus indicadores. Devolve o id da análise criada."""
        # O texto só é guardado se o usuário pediu, e sempre mascarado.
        texto = mascarar(conteudo) if (salvar_conteudo and conteudo) else None
        cur = self.conn.execute(
            "INSERT INTO analises (sessao_id, tipo, conteudo, classificacao, pontuacao) VALUES (?, ?, ?, ?, ?)",
            (sessao_id, tipo, texto, classificacao, pontuacao))
        analise_id = cur.lastrowid   # id gerado automaticamente pelo banco
        # executemany grava todos os indicadores de uma vez, ligados à análise pelo analise_id.
        self.conn.executemany("INSERT INTO indicadores (analise_id, descricao, categoria) VALUES (?, ?, ?)",
                              [(analise_id, i["descricao"], i.get("categoria")) for i in indicadores])
        self.conn.commit()
        return analise_id

    def listar(self, sessao_id: str, limite: int = 50) -> list:
        """Análises de uma sessão, da mais nova para a mais antiga (RF09)."""
        linhas = self.conn.execute(
            "SELECT id, tipo, conteudo, classificacao, pontuacao, data_analise FROM analises "
            "WHERE sessao_id = ? ORDER BY id DESC LIMIT ?", (sessao_id, limite)).fetchall()
        resultado = []
        for l in linhas:
            # Busca os indicadores de cada análise.
            ind = self.conn.execute("SELECT descricao FROM indicadores WHERE analise_id = ?", (l["id"],)).fetchall()
            resultado.append({**dict(l), "indicadores": [i["descricao"] for i in ind]})
        return resultado

    def apagar_sessao(self, sessao_id: str) -> int:
        """Apaga todo o histórico de uma sessão (o usuário pode limpar o próprio histórico).

        Os indicadores são apagados junto por causa do ON DELETE CASCADE da tabela.
        """
        cur = self.conn.execute("DELETE FROM analises WHERE sessao_id = ?", (sessao_id,))
        self.conn.commit()
        return cur.rowcount

    def estatisticas(self) -> dict:
        """Números agregados de todas as sessões, sem nenhum conteúdo (RF10)."""
        c = self.conn
        # Quantas análises de cada tipo (mensagem / link).
        por_tipo = dict(c.execute("SELECT tipo, COUNT(*) FROM analises GROUP BY tipo").fetchall())
        # Quantas de cada nível, separadas por tipo.
        por_nivel = [tuple(r) for r in c.execute(
            "SELECT tipo, classificacao, COUNT(*) FROM analises GROUP BY tipo, classificacao").fetchall()]
        # As 8 categorias de indicador que mais aparecem.
        top_ind = [tuple(r) for r in c.execute(
            "SELECT categoria, COUNT(*) AS n FROM indicadores GROUP BY categoria ORDER BY n DESC LIMIT 8").fetchall()]
        # Período: quantas análises nos últimos 7 dias e a data da mais antiga guardada.
        ultimos_7 = c.execute("SELECT COUNT(*) FROM analises WHERE data_analise >= datetime('now', '-7 days')").fetchone()[0]
        desde = c.execute("SELECT MIN(date(data_analise)) FROM analises").fetchone()[0]
        return {"total": sum(por_tipo.values()), "por_tipo": por_tipo, "por_nivel": por_nivel, "indicadores": top_ind,
                "ultimos_7_dias": ultimos_7, "desde": desde}
