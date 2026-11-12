"""Cria as tabelas do CyberBot (seção 8 do planejamento).

Uso: python -m database.criar_tabelas
(O aplicativo também chama criar_tabelas() sozinho ao iniciar.)
"""

import json
from pathlib import Path

from database.conexao import conectar

# Comandos SQL que criam as tabelas. "IF NOT EXISTS" evita erro se elas já existirem,
# então este código pode rodar quantas vezes for preciso.
ESQUEMA = """
-- Usuários: o cadastro é opcional. O MVP funciona sem ele, usando a sessão anônima.
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,                 -- opcional
    email TEXT,                -- opcional
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Cada análise feita (mensagem ou link).
CREATE TABLE IF NOT EXISTS analises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- Se o usuário for apagado, a análise fica sem dono (SET NULL) em vez de sumir.
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    sessao_id TEXT,            -- identifica a sessão anônima do navegador
    -- CHECK garante que só entram os dois tipos válidos.
    tipo TEXT NOT NULL CHECK (tipo IN ('mensagem', 'link')),
    conteudo TEXT,             -- só é salvo se o usuário pedir, mascarado e cortado
    classificacao TEXT NOT NULL,
    pontuacao REAL,
    data_analise DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indicadores encontrados em cada análise (uma análise pode ter vários).
CREATE TABLE IF NOT EXISTS indicadores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- ON DELETE CASCADE: ao apagar a análise, os indicadores dela são apagados junto.
    analise_id INTEGER NOT NULL REFERENCES analises(id) ON DELETE CASCADE,
    descricao TEXT NOT NULL,
    categoria TEXT
);

-- Conteúdos educativos (cópia do data/base_educativa.json).
CREATE TABLE IF NOT EXISTS conteudos_educativos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    categoria TEXT,
    conteudo TEXT NOT NULL
);

-- Perguntas do questionário.
CREATE TABLE IF NOT EXISTS questionarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pergunta TEXT NOT NULL,
    alternativas TEXT NOT NULL,    -- lista guardada como texto em formato JSON
    resposta_correta TEXT NOT NULL,
    explicacao TEXT
);

-- Índices deixam mais rápidas as buscas por sessão e por data.
CREATE INDEX IF NOT EXISTS idx_analises_sessao ON analises(sessao_id);
CREATE INDEX IF NOT EXISTS idx_analises_data ON analises(data_analise);
"""


def criar_tabelas(conn=None) -> None:
    """Cria as tabelas (se faltarem) e carrega a base educativa na primeira vez."""
    conn = conn or conectar()
    conn.executescript(ESQUEMA)   # executa vários comandos SQL de uma vez
    _carregar_conteudos(conn)
    conn.commit()                 # confirma as alterações no arquivo


def _carregar_conteudos(conn) -> None:
    """Copia a base educativa do JSON para o banco na primeira execução.

    Se a tabela já tiver conteúdo, não faz nada (evita duplicar).
    """
    if conn.execute("SELECT COUNT(*) FROM conteudos_educativos").fetchone()[0]:
        return
    base = json.loads((Path(__file__).resolve().parent.parent / "data" / "base_educativa.json").read_text(encoding="utf-8"))
    conn.executemany("INSERT INTO conteudos_educativos (titulo, categoria, conteudo) VALUES (?, ?, ?)",
                     [(c["titulo"], c["categoria"], c["conteudo"]) for c in base["conteudos"]])
    conn.executemany("INSERT INTO questionarios (pergunta, alternativas, resposta_correta, explicacao) VALUES (?, ?, ?, ?)",
                     [(q["pergunta"], json.dumps(q["alternativas"], ensure_ascii=False),
                       q["alternativas"][q["resposta_correta"]], q["explicacao"]) for q in base["questionarios"]])


# Permite rodar este arquivo sozinho: python -m database.criar_tabelas
if __name__ == "__main__":
    criar_tabelas()
    print("Tabelas criadas.")
