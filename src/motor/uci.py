"""Comunicação com o Stockfish local via UCI (dono: Dev B).

Usa `chess.engine.SimpleEngine.popen_uci` e `analyse(..., multipv=N)` da python-chess.
"""

import time
import chess
import chess.engine

from contratos import Candidato, Orcamento, ResultadoBusca

FOLGA_HARD_S = 0.05  # Margem reservada para parada do motor antes de estourar hard_s
TEMPO_MINIMO_BUSCA_S = 0.001  # Piso mínimo pois python-chess envia ao menos movetime 1ms


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
        self._fechado: bool = False
        self._iniciar_engine()

    def _fechar_engine_silencioso(self) -> None:
        """Fecha o processo do motor ignorando eventuais falhas e zera a referência."""
        if self._engine is not None:
            try:
                self._engine.close()
            except Exception:
                pass
            self._engine = None

    def _iniciar_engine(self) -> None:
        """Inicializa ou reinicializa o processo UCI e configura Threads e Hash."""
        self._fechar_engine_silencioso()

        motor = chess.engine.SimpleEngine.popen_uci(self.caminho)
        try:
            motor.configure({"Threads": self.threads, "Hash": self.hash_mb})
        except Exception:
            try:
                motor.close()
            except Exception:
                pass
            raise
        self._engine = motor

    def analisar(self, tabuleiro: chess.Board, orcamento: Orcamento) -> ResultadoBusca:
        """Analisa a posição respeitando o orçamento e devolve os candidatos do MultiPV.

        Em posições sem lances legais (xeque-mate ou afogamento), devolve `candidatos=[]`.
        """
        if self._fechado:
            raise RuntimeError("Tentativa de analisar com motor já fechado.")

        if not any(tabuleiro.legal_moves):
            return ResultadoBusca(candidatos=[], tempo_gasto_s=0.0)

        inicio_total = time.perf_counter()
        ultimo_erro: Exception | None = None

        for tentativa in range(2):
            restante = orcamento.hard_s - (time.perf_counter() - inicio_total)
            if restante < TEMPO_MINIMO_BUSCA_S:
                if ultimo_erro is not None:
                    raise ultimo_erro
                raise TimeoutError("Orçamento de tempo esgotado antes de concluir a análise.")

            try:
                if self._engine is None:
                    self._iniciar_engine()

                # Recalcula o tempo restante após eventual reabertura do motor
                restante = orcamento.hard_s - (time.perf_counter() - inicio_total)
                if restante < TEMPO_MINIMO_BUSCA_S:
                    raise TimeoutError("Orçamento de tempo esgotado antes de concluir a análise.")

                tempo_busca = min(
                    orcamento.soft_s,
                    max(TEMPO_MINIMO_BUSCA_S, restante - FOLGA_HARD_S),
                )
                self._engine.timeout = max(0.0, restante - tempo_busca)

                resultado_engine = self._engine.analyse(
                    tabuleiro,
                    chess.engine.Limit(time=tempo_busca),
                    multipv=self.multipv,
                )
                tempo_gasto = time.perf_counter() - inicio_total

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
                    if score_info is None:
                        continue

                    score_pov = score_info.pov(tabuleiro.turn)
                    if score_pov.is_mate():
                        mate = score_pov.mate()
                        centipeoes = None
                    else:
                        mate = None
                        centipeoes = score_pov.score()

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

            except TimeoutError:
                self._fechar_engine_silencioso()
                raise

            except (chess.engine.EngineTerminatedError, chess.engine.EngineError) as erro:
                ultimo_erro = erro
                self._fechar_engine_silencioso()
                if tentativa == 1:
                    raise

    def fechar(self) -> None:
        """Encerra o processo do motor UCI de forma limpa."""
        self._fechado = True
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
