"""Opening book Polyglot (dono: Dev B). Usar `chess.polyglot`."""

import chess

# Regra da competição: book só nos 10 primeiros meios-lances.
LIMITE_MEIOS_LANCES = 10


def consultar_livro(tabuleiro: chess.Board, caminho_livro: str) -> chess.Move | None:
    """Devolve um lance do book ou None (fora do book ou além do limite de meios-lances)."""
    raise NotImplementedError
