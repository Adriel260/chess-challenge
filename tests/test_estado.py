import os
import json
from unittest.mock import patch

import chess
import pytest

from contratos import EstadoRelogio
from jogo.estado import EstadoPartida


def _criar_json_valido(tmp_path):
    """Gera a base válida dos testes pelo método público de salvamento."""
    caminho = tmp_path / "estado.json"
    estado = EstadoPartida(
        tabuleiro=chess.Board(),
        minha_cor=chess.WHITE,
        relogio=EstadoRelogio(meu_ms=900000, adversario_ms=840000, incremento_ms=10000),
    )
    estado.salvar(str(caminho))
    return caminho, json.loads(caminho.read_text(encoding="utf-8"))


def _gravar_json(caminho, dados):
    """Grava os dados do teste com codificação UTF-8."""
    caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")


def test_salvar_carregar_10_meios_lances(tmp_path):
    """Garante a ida e volta perfeita de FEN, histórico, cor e relógio após 10 meios-lances."""
    caminho = tmp_path / "estado.json"
    relogio = EstadoRelogio(meu_ms=900000, adversario_ms=840000, incremento_ms=10000)
    estado = EstadoPartida(tabuleiro=chess.Board(), minha_cor=chess.WHITE, relogio=relogio)


    lances_uci = [
        "e2e4", "e7e5",
        "g1f3", "b8c6",
        "f1b5", "a7a6",
        "b5a4", "g8f6",
        "e1g1", "f8e7"
    ]

    for lance in lances_uci:
        estado.tabuleiro.push_uci(lance)

    estado.salvar(str(caminho))
    carregado = EstadoPartida.carregar(str(caminho))


    assert carregado.tabuleiro.fen() == estado.tabuleiro.fen()
    assert [m.uci() for m in carregado.tabuleiro.move_stack] == lances_uci


    assert carregado.minha_cor == chess.WHITE
    assert carregado.relogio.meu_ms == 900000
    assert carregado.relogio.adversario_ms == 840000
    assert carregado.relogio.incremento_ms == 10000


def test_lances_especiais_roque_en_passant_promocao(tmp_path):
    """Garante que lances especiais são perfeitamente restaurados."""
    caminho = tmp_path / "estado.json"
    relogio = EstadoRelogio(meu_ms=60000, adversario_ms=60000, incremento_ms=1000)


    estado_roque = EstadoPartida(tabuleiro=chess.Board(), minha_cor=chess.WHITE, relogio=relogio)
    for lance in ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6", "e1g1"]:
        estado_roque.tabuleiro.push_uci(lance)
    estado_roque.salvar(str(caminho))
    carregado = EstadoPartida.carregar(str(caminho))
    assert not carregado.tabuleiro.has_castling_rights(chess.WHITE)
    assert carregado.tabuleiro.piece_at(chess.G1).piece_type == chess.KING


    estado_ep = EstadoPartida(tabuleiro=chess.Board(), minha_cor=chess.BLACK, relogio=relogio)
    for lance in ["e2e4", "a7a6", "e4e5", "d7d5", "e5d6"]:
        estado_ep.tabuleiro.push_uci(lance)
    estado_ep.salvar(str(caminho))
    carregado = EstadoPartida.carregar(str(caminho))
    assert carregado.minha_cor == chess.BLACK
    assert carregado.tabuleiro.piece_at(chess.D5) is None
    assert carregado.tabuleiro.piece_at(chess.D6).piece_type == chess.PAWN


    fen_promocao = "8/P7/8/8/8/8/8/k1K5 w - - 0 1"
    estado_prom = EstadoPartida(tabuleiro=chess.Board(fen_promocao), minha_cor=chess.WHITE, relogio=relogio)
    estado_prom.tabuleiro.push_uci("a7a8q")
    estado_prom.salvar(str(caminho))
    carregado = EstadoPartida.carregar(str(caminho))
    assert carregado.tabuleiro.piece_at(chess.A8).piece_type == chess.QUEEN


def test_tripla_repeticao_detectavel(tmp_path):
    """Garante que carregar não perde o histórico de posições, essencial para draw por repetição."""
    caminho = tmp_path / "estado.json"
    relogio = EstadoRelogio(0, 0, 0)
    estado = EstadoPartida(tabuleiro=chess.Board(), minha_cor=chess.WHITE, relogio=relogio)


    lances = ["g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1", "f6g8"]
    for lance in lances:
        estado.tabuleiro.push_uci(lance)

    assert estado.tabuleiro.can_claim_threefold_repetition()

    estado.salvar(str(caminho))
    carregado = EstadoPartida.carregar(str(caminho))


    assert carregado.tabuleiro.can_claim_threefold_repetition()


def test_fen_inicial_personalizada(tmp_path):
    """Garante que partidas iniciadas de uma FEN arbitrária (comando fen) são retomáveis."""
    caminho = tmp_path / "estado.json"
    fen_custom = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
    estado = EstadoPartida(tabuleiro=chess.Board(fen_custom), minha_cor=chess.WHITE, relogio=EstadoRelogio(0,0,0))
    estado.tabuleiro.push_uci("f1b5")

    estado.salvar(str(caminho))
    carregado = EstadoPartida.carregar(str(caminho))

    assert carregado.tabuleiro.fen() == estado.tabuleiro.fen()

    assert len(carregado.tabuleiro.move_stack) == 1
    assert carregado.tabuleiro.move_stack[0].uci() == "f1b5"


def test_carregar_arquivo_inexistente(tmp_path):
    """Informa em português que o arquivo não existe."""
    caminho = tmp_path / "arquivo_fantasma.json"

    with pytest.raises(
        FileNotFoundError,
        match=r"(?i)(encontrado|inexistente|arquivo|falha)",
    ):
        EstadoPartida.carregar(str(caminho))


def test_carregar_json_invalido(tmp_path):
    """Garante que carregar arquivo corrompido gera erro em português, sem derrubar o parser silenciosamente."""
    caminho = tmp_path / "corrompido.json"
    caminho.write_text("{ isso_nao_e_json_valido: verdadeiro }", encoding="utf-8")

    with pytest.raises(ValueError, match=r"(?i)(inválido|invalido|corrompido|erro)"):
        EstadoPartida.carregar(str(caminho))


def test_salvar_atomico_falha_na_escrita(tmp_path):
    """Garante que se json.dump falhar (ex: disco cheio), o arquivo original intacto é preservado."""
    caminho = tmp_path / "estado.json"
    caminho.write_text("DADOS_ANTIGOS_IMPORTANTES", encoding="utf-8")

    estado = EstadoPartida(tabuleiro=chess.Board(), minha_cor=chess.WHITE, relogio=EstadoRelogio(0,0,0))


    with patch("json.dump", side_effect=OSError("Disco cheio")):
        with pytest.raises(OSError):
            estado.salvar(str(caminho))

    assert caminho.read_text(encoding="utf-8") == "DADOS_ANTIGOS_IMPORTANTES"


def test_salvar_atomico_falha_no_replace(tmp_path):
    """Garante que se os.replace falhar (ex: lock do SO), o arquivo original não é perdido."""
    caminho = tmp_path / "estado.json"
    caminho.write_text("DADOS_ANTIGOS_IMPORTANTES", encoding="utf-8")

    estado = EstadoPartida(tabuleiro=chess.Board(), minha_cor=chess.WHITE, relogio=EstadoRelogio(0,0,0))

    with patch("os.replace", side_effect=OSError("Arquivo travado pelo SO")):
        with pytest.raises(OSError):
            estado.salvar(str(caminho))

    assert caminho.read_text(encoding="utf-8") == "DADOS_ANTIGOS_IMPORTANTES"


@pytest.mark.parametrize("chave", ["fen_inicial", "lances_uci", "minha_cor", "relogio"])
def test_carregar_chave_obrigatoria_ausente(tmp_path, chave):
    caminho, dados = _criar_json_valido(tmp_path)
    del dados[chave]
    _gravar_json(caminho, dados)

    with pytest.raises(ValueError, match="Arquivo de partida com dados inválidos"):
        EstadoPartida.carregar(str(caminho))


def test_carregar_minha_cor_numerica(tmp_path):
    caminho, dados = _criar_json_valido(tmp_path)
    dados["minha_cor"] = 1
    _gravar_json(caminho, dados)

    with pytest.raises(ValueError, match="Arquivo de partida com dados inválidos"):
        EstadoPartida.carregar(str(caminho))


@pytest.mark.parametrize(
    "campo, valor",
    [("meu_ms", -1), ("adversario_ms", True)],
)
def test_carregar_relogio_com_valor_invalido(tmp_path, campo, valor):
    caminho, dados = _criar_json_valido(tmp_path)
    dados["relogio"][campo] = valor
    _gravar_json(caminho, dados)

    with pytest.raises(ValueError, match="Arquivo de partida com dados inválidos"):
        EstadoPartida.carregar(str(caminho))


@pytest.mark.parametrize(
    "fen",
    [
        "FEN malformada",
        "8/8/8/8/8/8/8/8 w - - 0 1",
    ],
)
def test_carregar_fen_malformada_ou_posicao_invalida(tmp_path, fen):
    caminho, dados = _criar_json_valido(tmp_path)
    dados["fen_inicial"] = fen
    _gravar_json(caminho, dados)

    with pytest.raises(ValueError, match="Arquivo de partida com dados inválidos"):
        EstadoPartida.carregar(str(caminho))


def test_carregar_historico_com_tipo_invalido(tmp_path):
    caminho, dados = _criar_json_valido(tmp_path)
    dados["lances_uci"] = "e2e4"
    _gravar_json(caminho, dados)

    with pytest.raises(ValueError, match="Arquivo de partida com dados inválidos"):
        EstadoPartida.carregar(str(caminho))


@pytest.mark.parametrize("lance", ["e2e9", "e2e5", "0000"])
def test_carregar_historico_com_lance_uci_invalido(tmp_path, lance):
    caminho, dados = _criar_json_valido(tmp_path)
    dados["lances_uci"] = [lance]
    _gravar_json(caminho, dados)

    with pytest.raises(ValueError, match="Arquivo de partida com dados inválidos"):
        EstadoPartida.carregar(str(caminho))
