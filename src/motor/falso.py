"""Motor falso para testes e desenvolvimento offline sem Stockfish (dono: Dev B)."""

import chess
from contratos import Candidato, Orcamento, ResultadoBusca


class MotorFalso:
    """Emula o comportamento do Motor UCI para testes e fallback.

    Permite simular respostas determinísticas por FEN ou disparar
    exceções para testar a resiliência do laço principal.
    """

    def __init__(
        self,
        candidatos_por_fen: dict[str, list[Candidato]] | None = None,
        erro: Exception | None = None,
        multipv: int = 4,
    ) -> None:
        self.candidatos_por_fen = candidatos_por_fen or {}
        self.erro = erro
        self.multipv = multipv
        self.fechado = False

    def analisar(self, tabuleiro: chess.Board, orcamento: Orcamento) -> ResultadoBusca:
        """Devolve candidatos simulados ou lança exceção se configurado."""
        if self.fechado:
            raise RuntimeError("Tentativa de analisar com motor já fechado.")

        if self.erro is not None:
            raise self.erro

        fen_atual = tabuleiro.fen()
        if fen_atual in self.candidatos_por_fen:
            return ResultadoBusca(
                candidatos=self.candidatos_por_fen[fen_atual],
                tempo_gasto_s=0.01,
            )

        lances_legais = list(tabuleiro.legal_moves)
        candidatos: list[Candidato] = []

        limite = min(self.multipv, len(lances_legais))
        for i in range(limite):
            lance = lances_legais[i]
            candidatos.append(
                Candidato(
                    lance=lance,
                    centipeoes=10 - (i * 2),
                    mate=None,
                    pv=[lance],
                    profundidade=1,
                    nos=10,
                )
            )

        return ResultadoBusca(candidatos=candidatos, tempo_gasto_s=0.01)

    def fechar(self) -> None:
        """Marca o motor como fechado."""
        self.fechado = True

    def __enter__(self) -> "MotorFalso":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.fechar()
