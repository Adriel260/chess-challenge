"""Gestão de tempo — componente de AUTORIA da equipe (dono: Dev C)."""

import chess

from contratos import EstadoRelogio, Orcamento


def calcular_orcamento(relogio: EstadoRelogio, tabuleiro: chess.Board) -> Orcamento:
    """Decide quanto tempo pensar no lance atual.

    Deve funcionar para qualquer tempo base + incremento (padrão 25+0, alternativo 15+10)
    e nunca devolver `hard_s` que coloque o relógio em risco.
    """
    raise NotImplementedError
