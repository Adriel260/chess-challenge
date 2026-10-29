"""Log obrigatório da competição (dono: Dev B).

Cada lance registra: número, cor, lance UCI, profundidade, nós, avaliação, PV e tempo gasto.
"""

from contratos import RegistroLance


class LogPartida:
    def __init__(self, caminho: str):
        raise NotImplementedError

    def registrar(self, registro: RegistroLance) -> None:
        """Escreve uma linha no arquivo e faz flush imediato (o programa pode cair a qualquer momento)."""
        raise NotImplementedError
