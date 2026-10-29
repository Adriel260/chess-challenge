"""Comunicação com o Stockfish local via UCI (dono: Dev B).

Usa `chess.engine.SimpleEngine.popen_uci` e `analyse(..., multipv=N)` da python-chess.
"""

import time
import chess
import chess.engine

from contratos import Candidato, Orcamento, ResultadoBusca


class Motor:
    """Controlador do motor de xadrez via protocolo UCI."""

    def __init__(
        self,
        caminho: str,
        threads: int = 4,
        hash_mb: int = 512,
        multipv: int = 4,
    ) -> None:
        """Inicializa o motor com as configurações UCI especificadas."""
        self.caminho = caminho
        self.threads = threads
        self.hash_mb = hash_mb
        self.multipv = multipv
        self._engine: chess.engine.SimpleEngine | None = None
        self._iniciar_engine()

    def _iniciar_engine(self) -> None:
        """Inicializa ou reinicializa o processo UCI e configura Threads e Hash."""
        if self._engine is not None:
            try:
                self._engine.close()
            except Exception:
                pass
            self._engine = None

        self._engine = chess.engine.SimpleEngine.popen_uci(self.caminho)
        self._engine.configure({"Threads": self.threads, "Hash": self.hash_mb})

    def analisar(self, tabuleiro: chess.Board, orcamento: Orcamento) -> ResultadoBusca:
        """Analisa a posição respeitando o orçamento e devolve os candidatos do MultiPV."""
        if not list(tabuleiro.legal_moves):
            return ResultadoBusca(candidatos=[], tempo_gasto_s=0.0)

        tentativas = 2
        while tentativas > 0:
            tentativas -= 1
            if self._engine is None:
                self._iniciar_engine()

            try:
                assert self._engine is not None
                if orcamento.hard_s > orcamento.soft_s:
                    self._engine.timeout = orcamento.hard_s - orcamento.soft_s
                else:
                    self._engine.timeout = 0.05

                inicio = time.perf_counter()
                resultado_engine = self._engine.analyse(
                    tabuleiro,
                    chess.engine.Limit(time=orcamento.soft_s),
                    multipv=self.multipv,
                )
                tempo_gasto = time.perf_counter() - inicio

                if isinstance(resultado_engine, dict):
                    linhas = [resultado_engine]
                else:
                    linhas = list(resultado_engine)

                candidatos: list[Candidato] = []
                for info in linhas:
                    pv = info.get("pv")
                    if not pv:
                        continue
                    pv_lista = list(pv)
                    lance = pv_lista[0]

                    score_info = info.get("score")
                    if score_info is not None:
                        score_pov = score_info.pov(tabuleiro.turn)
                        if score_pov.is_mate():
                            mate = score_pov.mate()
                            centipeoes = None
                        else:
                            mate = None
                            centipeoes = score_pov.score()
                    else:
                        mate = None
                        centipeoes = 0

                    candidatos.append(
                        Candidato(
                            lance=lance,
                            centipeoes=centipeoes,
                            mate=mate,
                            pv=pv_lista,
                            profundidade=int(info.get("depth", 0)),
                            nos=int(info.get("nodes", 0)),
                        )
                    )

                return ResultadoBusca(candidatos=candidatos, tempo_gasto_s=tempo_gasto)

            except (chess.engine.EngineTerminatedError, chess.engine.EngineError) as erro:
                if self._engine is not None:
                    try:
                        self._engine.close()
                    except Exception:
                        pass
                    self._engine = None
                if tentativas == 0:
                    raise erro

        return ResultadoBusca(candidatos=[], tempo_gasto_s=0.0)

    def fechar(self) -> None:
        """Encerra o processo do motor UCI de forma limpa."""
        if self._engine is not None:
            try:
                self._engine.quit()
            except Exception:
                try:
                    self._engine.close()
                except Exception:
                    pass
            finally:
                self._engine = None

    def __enter__(self) -> "Motor":
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.fechar()
