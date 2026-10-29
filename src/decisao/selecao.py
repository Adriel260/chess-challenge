"""Seleção de lance — componente de AUTORIA da equipe (dono: Dev B)."""

import chess

from contratos import Candidato, EstadoRelogio, ResultadoBusca


def escolher_lance(
    tabuleiro: chess.Board, resultado: ResultadoBusca, relogio: EstadoRelogio
) -> Candidato:
    """Escolhe um lance entre os candidatos do MultiPV.

    Só pode desviar do melhor candidato quando a diferença de avaliação for pequena.
    Sempre devolve um candidato que esteja em `resultado.candidatos`.
    """
    raise NotImplementedError
