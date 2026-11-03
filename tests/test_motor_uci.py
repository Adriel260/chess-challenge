"""Testes do módulo de motor (MotorFalso, testes unitários com mock e integração com Stockfish)."""

import os
import sys
import threading
import time
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
    assert total_legais == 1
    assert len(resultado.candidatos) == total_legais
    assert resultado.candidatos[0].lance == chess.Move.from_uci("a8b7")
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
    # Teste unitário para validar conversão de mate, centipeões e passagem de multipv
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
        motor = Motor("dummy_path", multipv=3)
        tabuleiro = chess.Board("6k1/5ppp/8/8/8/8/5PPP/4Q1K1 w - - 0 1")
        orcamento = Orcamento(soft_s=0.5, hard_s=1.0)
        resultado = motor.analisar(tabuleiro, orcamento)

        assert mock_engine.analyse.call_args.kwargs["multipv"] == 3
        assert len(resultado.candidatos) == 1
        candidato = resultado.candidatos[0]
        assert candidato.lance == lance
        assert candidato.mate == 1
        assert candidato.centipeoes is None
        assert candidato.profundidade == 10
        assert candidato.nos == 500
        motor.fechar()


def test_motor_uci_unitario_avaliacao_vez_das_pretas_e_mate_sofrido() -> None:
    # Verifica que score.pov(chess.BLACK) converte do ponto de vista das pretas e preserva mate negativo
    mock_engine = MagicMock()
    lance1 = chess.Move.from_uci("e7e5")
    lance2 = chess.Move.from_uci("a7a6")

    # Do ponto de vista das brancas é -80 cp (logo +80 cp para as pretas)
    # Na segunda linha, as pretas sofrem mate em 2 (Mate(-2) na perspectiva das pretas)
    mock_info_cp = {
        "pv": [lance1],
        "depth": 12,
        "nodes": 1200,
        "score": chess.engine.PovScore(chess.engine.Cp(-80), chess.WHITE),
    }
    mock_info_mate_sofrido = {
        "pv": [lance2],
        "depth": 12,
        "nodes": 1200,
        "score": chess.engine.PovScore(chess.engine.Mate(-2), chess.BLACK),
    }
    mock_engine.analyse.return_value = [mock_info_cp, mock_info_mate_sofrido]

    with patch("chess.engine.SimpleEngine.popen_uci", return_value=mock_engine):
        motor = Motor("dummy_path", multipv=2)
        tabuleiro = chess.Board("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1")
        orcamento = Orcamento(soft_s=0.5, hard_s=1.0)
        resultado = motor.analisar(tabuleiro, orcamento)

        assert mock_engine.analyse.call_args.kwargs["multipv"] == 2
        assert len(resultado.candidatos) == 2
        assert resultado.candidatos[0].centipeoes == 80
        assert resultado.candidatos[0].mate is None
        assert resultado.candidatos[1].mate == -2
        assert resultado.candidatos[1].centipeoes is None
        motor.fechar()


def test_motor_uci_unitario_posicao_sem_lances_nao_chama_engine() -> None:
    mock_engine = MagicMock()
    with patch("chess.engine.SimpleEngine.popen_uci", return_value=mock_engine):
        motor = Motor("dummy_path")
        tabuleiro = chess.Board("k7/8/1Q6/8/8/8/8/7K b - - 0 1")
        orcamento = Orcamento(soft_s=0.5, hard_s=1.0)
        resultado = motor.analisar(tabuleiro, orcamento)

        assert resultado.candidatos == []
        assert resultado.tempo_gasto_s == 0.0
        mock_engine.analyse.assert_not_called()
        motor.fechar()


def test_motor_uci_unitario_imposicao_hard_s_em_qualquer_relacao() -> None:
    # Testa soft < hard, soft == hard e hard < soft garantindo timeout + limit.time <= hard_s
    orcamentos = [
        Orcamento(soft_s=0.2, hard_s=0.5),
        Orcamento(soft_s=0.3, hard_s=0.3),
        Orcamento(soft_s=0.5, hard_s=0.1),
    ]
    lance = chess.Move.from_uci("e2e4")
    mock_info = {
        "pv": [lance],
        "depth": 5,
        "nodes": 100,
        "score": chess.engine.PovScore(chess.engine.Cp(15), chess.WHITE),
    }

    for orc in orcamentos:
        mock_engine = MagicMock()
        mock_engine.analyse.return_value = [mock_info]
        with patch("chess.engine.SimpleEngine.popen_uci", return_value=mock_engine):
            motor = Motor("dummy_path")
            tabuleiro = chess.Board()
            motor.analisar(tabuleiro, orc)

            args, _ = mock_engine.analyse.call_args
            limit_usado = args[1]
            assert limit_usado.time is not None
            assert mock_engine.timeout is not None
            assert limit_usado.time > 0
            assert limit_usado.time + mock_engine.timeout <= orc.hard_s + 1e-9
            motor.fechar()


def test_motor_uci_unitario_reabertura_apos_queda() -> None:
    # Valida tolerância a EngineTerminatedError descontando o tempo gasto antes da queda
    mock_engine1 = MagicMock()

    def _falhar_apos_atraso(*_args: object, **_kwargs: object) -> None:
        time.sleep(0.2)
        raise chess.engine.EngineTerminatedError("Motor caiu")

    mock_engine1.analyse.side_effect = _falhar_apos_atraso

    mock_engine2 = MagicMock()
    lance = chess.Move.from_uci("e2e4")
    mock_info = {
        "pv": [lance],
        "depth": 8,
        "nodes": 200,
        "score": chess.engine.PovScore(chess.engine.Cp(25), chess.WHITE),
    }
    mock_engine2.analyse.return_value = [mock_info]

    with patch("chess.engine.SimpleEngine.popen_uci", side_effect=[mock_engine1, mock_engine2]) as mock_popen:
        motor = Motor("dummy_path")
        tabuleiro = chess.Board()
        orcamento = Orcamento(soft_s=0.3, hard_s=0.5)
        resultado = motor.analisar(tabuleiro, orcamento)

        assert len(resultado.candidatos) == 1
        assert resultado.candidatos[0].lance == lance
        assert resultado.candidatos[0].centipeoes == 25
        assert resultado.candidatos[0].mate is None
        assert resultado.tempo_gasto_s >= 0.2

        # Verifica que popen_uci na reabertura recebeu timeout limitado ao restante
        timeout_reabertura = mock_popen.call_args_list[1].kwargs.get("timeout")
        assert timeout_reabertura is not None
        assert timeout_reabertura <= 0.5 - 0.2 + 0.05

        # Verifica que na 2ª tentativa limit.time + timeout respeita o restante
        args2, _ = mock_engine2.analyse.call_args
        limit_usado2 = args2[1]
        assert limit_usado2.time + mock_engine2.timeout <= 0.5 - 0.2 + 1e-9

        mock_engine1.close.assert_called_once()
        mock_engine2.ping.assert_called_once()
        motor.fechar()


def test_motor_uci_unitario_queda_sem_orcamento_para_reabrir_propaga_erro_original() -> None:
    # Caso 1: Queda após estourar hard_s (0.25s gastos com hard_s=0.2)
    mock_engine1 = MagicMock()

    def _queda_apos_estouro(*_args: object, **_kwargs: object) -> None:
        time.sleep(0.25)
        raise chess.engine.EngineTerminatedError("Queda após estouro")

    mock_engine1.analyse.side_effect = _queda_apos_estouro

    with patch("chess.engine.SimpleEngine.popen_uci", return_value=mock_engine1) as mock_popen:
        motor = Motor("dummy_path")
        tabuleiro = chess.Board()
        orcamento = Orcamento(soft_s=0.1, hard_s=0.2)

        with pytest.raises(chess.engine.EngineTerminatedError):
            motor.analisar(tabuleiro, orcamento)

        assert mock_popen.call_count == 1
        assert motor._engine is None

    # Caso 2: Queda sobrando menos que ESTIMATIVA_REABERTURA_S (0.32s gastos com hard_s=0.4)
    mock_engine_curto = MagicMock()

    def _queda_orcamento_curto(*_args: object, **_kwargs: object) -> None:
        time.sleep(0.32)
        raise chess.engine.EngineTerminatedError("Queda com pouco tempo restante")

    mock_engine_curto.analyse.side_effect = _queda_orcamento_curto

    with patch("chess.engine.SimpleEngine.popen_uci", return_value=mock_engine_curto) as mock_popen_curto:
        motor2 = Motor("dummy_path")
        tabuleiro = chess.Board()
        orcamento_curto = Orcamento(soft_s=0.3, hard_s=0.4)

        with pytest.raises(chess.engine.EngineTerminatedError):
            motor2.analisar(tabuleiro, orcamento_curto)

        assert mock_popen_curto.call_count == 1
        assert motor2._engine is None


def test_motor_uci_unitario_queda_dupla_propaga_erro() -> None:
    mock_engine1 = MagicMock()
    mock_engine1.analyse.side_effect = chess.engine.EngineTerminatedError("Queda 1")
    mock_engine2 = MagicMock()
    mock_engine2.analyse.side_effect = chess.engine.EngineTerminatedError("Queda 2")

    with patch("chess.engine.SimpleEngine.popen_uci", side_effect=[mock_engine1, mock_engine2]) as mock_popen:
        motor = Motor("dummy_path")
        tabuleiro = chess.Board()
        orcamento = Orcamento(soft_s=0.2, hard_s=0.5)

        with pytest.raises(chess.engine.EngineTerminatedError):
            motor.analisar(tabuleiro, orcamento)

        assert mock_popen.call_count == 2
        mock_engine1.close.assert_called_once()
        mock_engine2.close.assert_called_once()
        assert motor._engine is None


def test_motor_uci_unitario_descarte_sem_score_ou_pv_e_erro_sem_candidatos() -> None:
    mock_engine = MagicMock()
    lance_valido = chess.Move.from_uci("d2d4")
    lance_sem_score = chess.Move.from_uci("e2e4")

    # Testa lista com linha sem pv, linha sem score e linha válida
    mock_engine.analyse.return_value = [
        {"depth": 5, "nodes": 50, "score": chess.engine.PovScore(chess.engine.Cp(10), chess.WHITE)},
        {"pv": [lance_sem_score], "depth": 5, "nodes": 50},
        {
            "pv": [lance_valido],
            "depth": 6,
            "nodes": 120,
            "score": chess.engine.PovScore(chess.engine.Cp(30), chess.WHITE),
        },
    ]

    with patch("chess.engine.SimpleEngine.popen_uci", return_value=mock_engine):
        motor = Motor("dummy_path", multipv=4)
        tabuleiro = chess.Board()
        orcamento = Orcamento(soft_s=0.2, hard_s=0.5)
        resultado = motor.analisar(tabuleiro, orcamento)

        assert len(resultado.candidatos) == 1
        assert resultado.candidatos[0].lance == lance_valido
        assert resultado.candidatos[0].centipeoes == 30

        # Quando nenhuma linha possui pv e score válidos, deve levantar EngineError
        mock_engine.analyse.return_value = [
            {"depth": 5, "nodes": 50},
            {"pv": [], "depth": 5, "nodes": 50, "score": chess.engine.PovScore(chess.engine.Cp(10), chess.WHITE)},
        ]
        with pytest.raises(chess.engine.EngineError):
            motor.analisar(tabuleiro, orcamento)

        motor.fechar()


def test_motor_uci_unitario_configure_falha_fecha_processo_e_timeout_nao_repete() -> None:
    # Se configure falhar na inicialização, o processo recém-aberto deve ser fechado
    mock_engine_falho = MagicMock()
    mock_engine_falho.configure.side_effect = chess.engine.EngineError("Erro no configure")

    with patch("chess.engine.SimpleEngine.popen_uci", return_value=mock_engine_falho):
        with pytest.raises(chess.engine.EngineError):
            Motor("dummy_path", threads=2, hash_mb=128)
        mock_engine_falho.close.assert_called_once()

    # Verifica configure + ping normal, TimeoutError sem repetir busca e bloqueio após fechar()
    mock_engine_ok = MagicMock()
    mock_engine_ok.analyse.side_effect = TimeoutError("Estourou tempo")

    with patch("chess.engine.SimpleEngine.popen_uci", return_value=mock_engine_ok) as mock_popen:
        motor = Motor("dummy_path", threads=2, hash_mb=256)
        mock_engine_ok.configure.assert_called_once_with({"Threads": 2, "Hash": 256})
        mock_engine_ok.ping.assert_called_once()

        tabuleiro = chess.Board()
        orcamento = Orcamento(soft_s=0.2, hard_s=0.5)

        with pytest.raises(TimeoutError):
            motor.analisar(tabuleiro, orcamento)

        # Não deve tentar reabrir nem repetir a busca em caso de TimeoutError
        assert mock_popen.call_count == 1
        mock_engine_ok.close.assert_called_once()
        assert motor._engine is None

        motor.fechar()
        with pytest.raises(RuntimeError):
            motor.analisar(tabuleiro, orcamento)


def test_motor_uci_unitario_timeout_encerra_thread_de_fundo(capsys: pytest.CaptureFixture[str]) -> None:
    codigo_motor_travado = (
        "import sys, time\n"
        "for linha in sys.stdin:\n"
        "    cmd = linha.strip()\n"
        "    if cmd == 'uci':\n"
        "        print('id name MotorTravado', flush=True)\n"
        "        print('option name Threads type spin default 1 min 1 max 512', flush=True)\n"
        "        print('option name Hash type spin default 16 min 1 max 33554432', flush=True)\n"
        "        print('option name MultiPV type spin default 1 min 1 max 500', flush=True)\n"
        "        print('uciok', flush=True)\n"
        "    elif cmd == 'isready':\n"
        "        print('readyok', flush=True)\n"
        "    elif cmd.startswith('go'):\n"
        "        time.sleep(10)\n"
        "    elif cmd == 'quit':\n"
        "        break\n"
    )
    comando = [sys.executable, "-u", "-c", codigo_motor_travado]
    motor = Motor(comando, threads=1, hash_mb=16, multipv=1)
    tabuleiro = chess.Board()

    with pytest.raises(TimeoutError):
        motor.analisar(tabuleiro, Orcamento(soft_s=0.05, hard_s=0.1))

    motor.fechar()

    prazo = time.perf_counter() + 1.0
    threads_engine: list[threading.Thread] = []
    while time.perf_counter() < prazo:
        threads_engine = [
            t for t in threading.enumerate()
            if t.is_alive() and "SimpleEngine" in t.name
        ]
        if not threads_engine:
            break
        time.sleep(0.02)

    assert not threads_engine
    capturado = capsys.readouterr()
    assert "InvalidStateError" not in capturado.err


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
        # Força soft_s > hard_s para validar que hard_s corta a busca a tempo
        orcamento = Orcamento(soft_s=1.0, hard_s=0.2)
        resultado = motor.analisar(tabuleiro, orcamento)

        assert len(resultado.candidatos) > 0
        assert resultado.tempo_gasto_s <= orcamento.hard_s


@pytest.mark.integracao
@skip_sem_stockfish
def test_motor_real_reabertura_apos_queda() -> None:
    with Motor(CAMINHO_STOCKFISH, multipv=2) as motor:
        tabuleiro = chess.Board()
        orcamento = Orcamento(soft_s=0.1, hard_s=3.0)

        # Encerra propositalmente o processo do motor
        assert motor._engine is not None
        motor._engine.close()

        # O método analisar deve reabrir o motor e responder com sucesso
        resultado = motor.analisar(tabuleiro, orcamento)
        assert len(resultado.candidatos) > 0
        assert resultado.candidatos[0].lance in tabuleiro.legal_moves
