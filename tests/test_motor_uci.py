"""Testes do módulo de motor (MotorFalso e integração com Stockfish)."""

import os
from unittest.mock import MagicMock, patch
import pytest
import chess
import chess.engine

from contratos import Candidato, Orcamento
from motor.falso import MotorFalso
from motor.uci import Motor

CAMINHO_STOCKFISH = os.path.join("engines", "stockfish.exe")
STOCKFISH_DISPONIVEL = os.path.exists(CAMINHO_STOCKFISH)

skip_sem_stockfish = pytest.mark.skipif(
    not STOCKFISH_DISPONIVEL,
    reason="Stockfish não encontrado em engines/stockfish.exe",
)


def test_motor_falso_posicao_inicial() -> None:
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


def test_motor_falso_poucos_lances_legais() -> None:
    # Posição onde as pretas só têm 1 lance legal (a8b7)
    tabuleiro = chess.Board("k1R5/8/1P6/8/8/8/8/K7 b - - 0 1")
    orcamento = Orcamento(soft_s=1.0, hard_s=2.0)

    motor = MotorFalso(multipv=4)
    resultado = motor.analisar(tabuleiro, orcamento)

    total_legais = tabuleiro.legal_moves.count()
    assert len(resultado.candidatos) == total_legais
    for cand in resultado.candidatos:
        assert cand.lance in tabuleiro.legal_moves


def test_motor_falso_posicao_sem_lances_legais() -> None:
    # Posição de afogamento (pretas sem lances legais)
    tabuleiro = chess.Board("k7/8/1Q6/8/8/8/8/7K b - - 0 1")
    orcamento = Orcamento(soft_s=1.0, hard_s=2.0)

    motor = MotorFalso(multipv=4)
    resultado = motor.analisar(tabuleiro, orcamento)

    assert resultado.candidatos == []


def test_motor_falso_modo_erro() -> None:
    tabuleiro = chess.Board()
    orcamento = Orcamento(soft_s=1.0, hard_s=2.0)

    erro_simulado = RuntimeError("Simulação de falha no motor")
    motor = MotorFalso(erro=erro_simulado)

    with pytest.raises(RuntimeError) as exc_info:
        motor.analisar(tabuleiro, orcamento)

    assert "falha no motor" in str(exc_info.value)


def test_motor_falso_candidatos_por_fen() -> None:
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

    # Garantir que retorna cópia rasa e mutações não alteram o original
    resultado.candidatos.append(cand_custom)
    assert len(motor.candidatos_por_fen[fen]) == 1


def test_motor_falso_gerenciador_contexto_e_fechamento() -> None:
    tabuleiro = chess.Board()
    orcamento = Orcamento(soft_s=1.0, hard_s=2.0)

    with MotorFalso() as motor:
        res = motor.analisar(tabuleiro, orcamento)
        assert len(res.candidatos) > 0

    assert motor.fechado is True
    with pytest.raises(RuntimeError):
        motor.analisar(tabuleiro, orcamento)


def test_motor_uci_unitario_conversao_e_mate() -> None:
    # Teste unitário para validar conversão de mate e centipeões sem depender de binário externo
    mock_engine = MagicMock()
    lance = chess.Move.from_uci("e1e8")
    mock_info = {
        "pv": [lance],
        "depth": 10,
        "nodes": 500,
        "score": chess.engine.PovScore(chess.engine.Mate(1), chess.WHITE),
    }
    mock_engine.analyse.return_value = [mock_info]

    with patch("chess.engine.SimpleEngine.popen_uci", return_value=mock_engine):
        motor = Motor("dummy_path", multipv=1)
        tabuleiro = chess.Board("6k1/5ppp/8/8/8/8/5PPP/4Q1K1 w - - 0 1")
        orcamento = Orcamento(soft_s=0.5, hard_s=1.0)
        resultado = motor.analisar(tabuleiro, orcamento)

        assert len(resultado.candidatos) == 1
        candidato = resultado.candidatos[0]
        assert candidato.lance == lance
        assert candidato.mate == 1
        assert candidato.centipeoes is None
        assert candidato.profundidade == 10
        assert candidato.nos == 500
        motor.fechar()


def test_motor_uci_unitario_reabertura_apos_queda() -> None:
    # Teste unitário para validar tolerância a EngineTerminatedError com reabertura
    mock_engine1 = MagicMock()
    mock_engine1.analyse.side_effect = chess.engine.EngineTerminatedError("Motor caiu")

    mock_engine2 = MagicMock()
    lance = chess.Move.from_uci("e2e4")
    mock_info = {
        "pv": [lance],
        "depth": 8,
        "nodes": 200,
        "score": chess.engine.PovScore(chess.engine.Cp(25), chess.WHITE),
    }
    mock_engine2.analyse.return_value = [mock_info]

    with patch("chess.engine.SimpleEngine.popen_uci", side_effect=[mock_engine1, mock_engine2]):
        motor = Motor("dummy_path")
        tabuleiro = chess.Board()
        orcamento = Orcamento(soft_s=0.5, hard_s=1.0)
        resultado = motor.analisar(tabuleiro, orcamento)

        assert len(resultado.candidatos) == 1
        assert resultado.candidatos[0].lance == lance
        assert resultado.candidatos[0].centipeoes == 25
        assert resultado.candidatos[0].mate is None
        motor.fechar()


@pytest.mark.integracao
@skip_sem_stockfish
def test_motor_real_posicao_inicial() -> None:
    with Motor(CAMINHO_STOCKFISH, multipv=3) as motor:
        tabuleiro = chess.Board()
        orcamento = Orcamento(soft_s=0.2, hard_s=0.5)
        resultado = motor.analisar(tabuleiro, orcamento)

        assert len(resultado.candidatos) >= 1
        assert resultado.tempo_gasto_s > 0.0
        for cand in resultado.candidatos:
            assert cand.lance in tabuleiro.legal_moves
            assert cand.profundidade >= 1
            assert cand.nos >= 1


@pytest.mark.integracao
@skip_sem_stockfish
def test_motor_real_mate_em_1() -> None:
    # Posição onde Qe8# é xeque-mate em 1
    tabuleiro = chess.Board("6k1/5ppp/8/8/8/8/5PPP/4Q1K1 w - - 0 1")
    with Motor(CAMINHO_STOCKFISH, multipv=1) as motor:
        orcamento = Orcamento(soft_s=0.2, hard_s=0.5)
        resultado = motor.analisar(tabuleiro, orcamento)

        assert len(resultado.candidatos) > 0
        melhor = resultado.candidatos[0]
        assert melhor.lance == chess.Move.from_uci("e1e8")
        assert melhor.mate == 1
        assert melhor.centipeoes is None


@pytest.mark.integracao
@skip_sem_stockfish
def test_motor_real_respeita_hard_s() -> None:
    with Motor(CAMINHO_STOCKFISH, multipv=2) as motor:
        tabuleiro = chess.Board()
        orcamento = Orcamento(soft_s=0.1, hard_s=0.3)
        resultado = motor.analisar(tabuleiro, orcamento)

        assert len(resultado.candidatos) > 0
        # O tempo não deve estourar o limite hard com folga
        assert resultado.tempo_gasto_s <= orcamento.hard_s + 0.15


@pytest.mark.integracao
@skip_sem_stockfish
def test_motor_real_reabertura_apos_queda() -> None:
    with Motor(CAMINHO_STOCKFISH, multipv=2) as motor:
        tabuleiro = chess.Board()
        orcamento = Orcamento(soft_s=0.1, hard_s=0.3)

        # Encerra propositalmente o processo do motor
        assert motor._engine is not None
        motor._engine.close()

        # O método analisar deve reabrir o motor e responder com sucesso
        resultado = motor.analisar(tabuleiro, orcamento)
        assert len(resultado.candidatos) > 0
        assert resultado.candidatos[0].lance in tabuleiro.legal_moves
