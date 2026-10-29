"""Estado da partida e persistência para retomada após falha (dono: Dev C)."""

from dataclasses import dataclass

import chess

from contratos import EstadoRelogio


@dataclass
class EstadoPartida:
    tabuleiro: chess.Board
    minha_cor: chess.Color
    relogio: EstadoRelogio

    def salvar(self, caminho: str) -> None:
        """Grava o estado em JSON (FEN inicial + lances UCI + relógio) de forma atômica."""
        raise NotImplementedError

    @classmethod
    def carregar(cls, caminho: str) -> "EstadoPartida":
        raise NotImplementedError
