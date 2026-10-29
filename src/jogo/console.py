"""Entrada do operador no terminal (dono: Dev C).

Comandos: lance UCI (ex.: e2e4, e7e8q), desfazer, fen <FEN>, relogio <min:seg>, status, sair.
"""

from dataclasses import dataclass

import chess


@dataclass(frozen=True)
class Comando:
    tipo: str  # "lance", "desfazer", "fen", "relogio", "status" ou "sair"
    argumento: str | None = None


def interpretar(texto: str, tabuleiro: chess.Board) -> Comando:
    """Converte o texto digitado em Comando. Lance ilegal ou texto inválido gera ValueError."""
    raise NotImplementedError
