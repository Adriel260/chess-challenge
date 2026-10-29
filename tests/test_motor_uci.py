"""Testes do módulo de motor (MotorFalso e integração com Stockfish)."""

import os
import pytest
import chess

from contratos import Candidato, Orcamento
from motor.falso import MotorFalso
from motor.uci import Motor


def test_motor_falso_posicao_inicial():
    tabuleiro = chess.Board()
    orcamento = Orcamento(soft_s=1.0, hard_s=2.0)

    motor = MotorFalso(multipv=3)
    resultado = motor.analisar(tabuleiro, orcamento)

    assert len(resultado.candidatos) == 3
    assert resultado.tempo_gasto_s > 0

    primeiro = resultado.candidatos[0]
    assert isinstance(primeiro, Candidato)
    assert primeiro.lance in tabuleiro.legal_moves
    assert primeiro.mate is None
    assert primeiro.centipeoes is not None
    assert primeiro.profundidade >= 1
    assert primeiro.nos >= 1


def test_motor_falso_poucos_lances_legais():
    # Posição onde as pretas só têm 1 lance legal (a8b7)
    tabuleiro = chess.Board("k1R5/8/1P6/8/8/8/8/K7 b - - 0 1")
    orcamento = Orcamento(soft_s=1.0, hard_s=2.0)

    motor = MotorFalso(multipv=4)
    resultado = motor.analisar(tabuleiro, orcamento)

    total_legais = tabuleiro.legal_moves.count()
    assert len(resultado.candidatos) == total_legais
    for cand in resultado.candidatos:
        assert cand.lance in tabuleiro.legal_moves


def test_motor_falso_modo_erro():
    tabuleiro = chess.Board()
    orcamento = Orcamento(soft_s=1.0, hard_s=2.0)

    erro_simulado = RuntimeError("Simulação de falha no motor")
    motor = MotorFalso(erro=erro_simulado)

    with pytest.raises(RuntimeError) as exc_info:
        motor.analisar(tabuleiro, orcamento)

    assert "falha no motor" in str(exc_info.value)


def test_motor_falso_candidatos_por_fen():
    tabuleiro = chess.Board()
    orcamento = Orcamento(soft_s=1.0, hard_s=2.0)

    lance_custom = chess.Move.from_uci("e2e4")
    cand_custom = Candidato(
        lance=lance_custom,
        centipeoes=50,
        mate=None,
        pv=[lance_custom],
        profundidade=5,
        nos=100,
    )
    fen = tabuleiro.fen()

    motor = MotorFalso(candidatos_por_fen={fen: [cand_custom]})
    resultado = motor.analisar(tabuleiro, orcamento)

    assert len(resultado.candidatos) == 1
    assert resultado.candidatos[0].lance == lance_custom
    assert resultado.candidatos[0].centipeoes == 50


def test_motor_falso_gerenciador_contexto_e_fechamento():
    tabuleiro = chess.Board()
    orcamento = Orcamento(soft_s=1.0, hard_s=2.0)

    with MotorFalso() as motor:
        res = motor.analisar(tabuleiro, orcamento)
        assert len(res.candidatos) > 0

    assert motor.fechado is True
    with pytest.raises(RuntimeError):
        motor.analisar(tabuleiro, orcamento)


@pytest.mark.integracao
def test_motor_real_stockfish():
    caminho_stockfish = os.path.join("engines", "stockfish.exe")
    if not os.path.exists(caminho_stockfish):
        pytest.skip("Stockfish não encontrado em engines/stockfish.exe")

    with Motor(caminho_stockfish) as motor:
        tabuleiro = chess.Board()
        orcamento = Orcamento(soft_s=0.2, hard_s=0.5)
        resultado = motor.analisar(tabuleiro, orcamento)
        assert len(resultado.candidatos) > 0
