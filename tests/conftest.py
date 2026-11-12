"""Configuração do pytest.

Coloca a pasta CyberBot no caminho de importação do Python, para os testes
conseguirem fazer "from modules... import ..." de qualquer lugar.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
