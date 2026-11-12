"""Conexão com o banco de dados SQLite.

SQLite é um banco de dados que fica em um único arquivo (database/cyberbot.db).
Não precisa instalar nem configurar servidor, por isso é bom para o MVP.
"""

import os
import sqlite3
from pathlib import Path

# Local padrão do arquivo do banco: dentro da pasta database/.
CAMINHO_PADRAO = Path(__file__).resolve().parent / "cyberbot.db"


def conectar(caminho: str | os.PathLike | None = None) -> sqlite3.Connection:
    """Abre (ou cria, se não existir) o banco e devolve a conexão.

    Ordem de escolha do arquivo:
    1. o caminho passado como parâmetro (os testes usam um banco temporário);
    2. a variável de ambiente CYBERBOT_DB, se existir;
    3. o caminho padrão.
    """
    caminho = caminho or os.environ.get("CYBERBOT_DB", CAMINHO_PADRAO)
    # check_same_thread=False: o Streamlit pode usar a conexão em threads diferentes.
    conn = sqlite3.connect(caminho, check_same_thread=False)
    # Faz as consultas devolverem linhas que podem ser lidas pelo nome da coluna: linha["tipo"].
    conn.row_factory = sqlite3.Row
    # O SQLite só respeita chaves estrangeiras (FOREIGN KEY) se isso for ligado em cada conexão.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
