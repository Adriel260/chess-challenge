"""Comunicação com o Stockfish local via UCI (dono: Dev B).

Usar `chess.engine.SimpleEngine.popen_uci` e `analyse(..., multipv=N)` da python-chess.
"""

import chess

from contratos import Orcamento, ResultadoBusca
from motor.falso import MotorFalso


class Motor:
    def __init__(self, caminho: str, threads: int = 4, hash_mb: int = 512, multipv: int = 4):
        raise NotImplementedError

    def analisar(self, tabuleiro: chess.Board, orcamento: Orcamento) -> ResultadoBusca:
        """Analisa a posição respeitando o orçamento e devolve os candidatos do MultiPV."""
        raise NotImplementedError

    def fechar(self) -> None:
        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.fechar()
