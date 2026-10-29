"""Tipos compartilhados entre os módulos.

Este arquivo é o contrato entre as partes do sistema. Mudanças aqui
afetam todo mundo: só altere com PR revisado pela equipe inteira.
"""

from dataclasses import dataclass, field

import chess


@dataclass(frozen=True)
class Candidato:
    """Um lance sugerido pelo motor (uma linha do MultiPV).

    A avaliação é sempre do ponto de vista do lado que vai jogar.
    Exatamente um entre `centipeoes` e `mate` é preenchido.
    """

    lance: chess.Move
    centipeoes: int | None
    mate: int | None
    pv: list[chess.Move]
    profundidade: int
    nos: int


@dataclass(frozen=True)
class ResultadoBusca:
    """Saída de uma análise do motor. `candidatos` vem ordenado do melhor para o pior."""

    candidatos: list[Candidato]
    tempo_gasto_s: float


@dataclass(frozen=True)
class Orcamento:
    """Quanto tempo pensar no lance atual.

    `soft_s`: tempo alvo. `hard_s`: limite que nunca pode ser ultrapassado.
    """

    soft_s: float
    hard_s: float


@dataclass
class EstadoRelogio:
    """Tempo restante de cada lado, em milissegundos."""

    meu_ms: int
    adversario_ms: int
    incremento_ms: int


@dataclass(frozen=True)
class RegistroLance:
    """Uma linha do log obrigatório da competição."""

    numero: int
    cor: str  # "brancas" ou "pretas"
    lance_uci: str
    profundidade: int
    nos: int
    avaliacao: str  # ex.: "+0.35" ou "#3"
    pv: list[str] = field(default_factory=list)
    tempo_gasto_s: float = 0.0
    origem: str = "motor"  # "motor", "livro", "fallback" ou "adversario"
