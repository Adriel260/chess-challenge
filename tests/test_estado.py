import json
from pathlib import Path
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
        relogio=EstadoRelogio(
            meu_ms=900000,
            adversario_ms=840000,
            incremento_ms=10000,
        ),
    )
    estado.salvar(str(caminho))
    return caminho, json.loads(caminho.read_text(encoding="utf-8"))


def _gravar_json(caminho, dados):
    """Grava os dados do teste com codificação UTF-8."""
    caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")


def _assert_estado_equivalente(carregado, esperado):
    """Compara posição, origem, histórico, cor e cada campo do relógio."""
    assert carregado.tabuleiro.fen() == esperado.tabuleiro.fen()
    assert carregado.tabuleiro.root().fen() == esperado.tabuleiro.root().fen()
    assert [lance.uci() for lance in carregado.tabuleiro.move_stack] == [
        lance.uci() for lance in esperado.tabuleiro.move_stack
    ]
    assert carregado.minha_cor == esperado.minha_cor
    assert carregado.relogio.meu_ms == esperado.relogio.meu_ms
    assert carregado.relogio.adversario_ms == esperado.relogio.adversario_ms
    assert carregado.relogio.incremento_ms == esperado.relogio.incremento_ms


def test_salvar_carregar_10_meios_lances(tmp_path):
    """Garante a ida e volta perfeita após 10 meios-lances."""
    caminho = tmp_path / "estado.json"
    relogio = EstadoRelogio(meu_ms=900000, adversario_ms=840000, incremento_ms=10000)
    estado = EstadoPartida(
        tabuleiro=chess.Board(), minha_cor=chess.WHITE, relogio=relogio
    )
    lances_uci = [
        "e2e4", "e7e5", "g1f3", "b8c6", "f1b5",
        "a7a6", "b5a4", "g8f6", "e1g1", "f8e7",
    ]

    for lance in lances_uci:
        estado.tabuleiro.push_uci(lance)

    estado.salvar(str(caminho))
    carregado = EstadoPartida.carregar(str(caminho))

    _assert_estado_equivalente(carregado, estado)


def test_lances_especiais_roque_en_passant_promocao(tmp_path):
    """Compara o estado completo após roque, en passant e promoção."""
    caminho = tmp_path / "estado.json"
    casos = [
        (
            EstadoPartida(
                tabuleiro=chess.Board(),
                minha_cor=chess.WHITE,
                relogio=EstadoRelogio(60001, 60002, 1003),
            ),
            ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6", "e1g1"],
            lambda tabuleiro: (
                not tabuleiro.has_castling_rights(chess.WHITE)
                and tabuleiro.piece_at(chess.G1).piece_type == chess.KING
            ),
        ),
        (
            EstadoPartida(
                tabuleiro=chess.Board(),
                minha_cor=chess.BLACK,
                relogio=EstadoRelogio(70001, 70002, 2003),
            ),
            ["e2e4", "a7a6", "e4e5", "d7d5", "e5d6"],
            lambda tabuleiro: (
                tabuleiro.piece_at(chess.D5) is None
                and tabuleiro.piece_at(chess.D6).piece_type == chess.PAWN
            ),
        ),
        (
            EstadoPartida(
                tabuleiro=chess.Board("8/P7/8/8/8/8/8/k1K5 w - - 0 1"),
                minha_cor=chess.WHITE,
                relogio=EstadoRelogio(80001, 80002, 3003),
            ),
            ["a7a8q"],
            lambda tabuleiro: (
                tabuleiro.piece_at(chess.A8).piece_type == chess.QUEEN
            ),
        ),
    ]

    for esperado, lances_uci, verificar_regra_especial in casos:
        for lance in lances_uci:
            esperado.tabuleiro.push_uci(lance)

        esperado.salvar(str(caminho))
        carregado = EstadoPartida.carregar(str(caminho))

        _assert_estado_equivalente(carregado, esperado)
        assert verificar_regra_especial(carregado.tabuleiro)


def test_tripla_repeticao_detectavel(tmp_path):
    """Garante que carregar mantém o histórico necessário para detectar repetição."""
    caminho = tmp_path / "estado.json"
    estado = EstadoPartida(
        tabuleiro=chess.Board(),
        minha_cor=chess.WHITE,
        relogio=EstadoRelogio(0, 0, 0),
    )
    lances = [
        "g1f3", "g8f6", "f3g1", "f6g8",
        "g1f3", "g8f6", "f3g1", "f6g8",
    ]
    for lance in lances:
        estado.tabuleiro.push_uci(lance)

    assert estado.tabuleiro.can_claim_threefold_repetition()

    estado.salvar(str(caminho))
    carregado = EstadoPartida.carregar(str(caminho))

    assert carregado.tabuleiro.can_claim_threefold_repetition()
    _assert_estado_equivalente(carregado, estado)


def test_fen_inicial_personalizada(tmp_path):
    """Garante que partidas iniciadas de uma FEN arbitrária são retomáveis."""
    caminho = tmp_path / "estado.json"
    fen_custom = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
    estado = EstadoPartida(
        tabuleiro=chess.Board(fen_custom),
        minha_cor=chess.WHITE,
        relogio=EstadoRelogio(11, 22, 3),
    )
    estado.tabuleiro.push_uci("f1b5")

    estado.salvar(str(caminho))
    carregado = EstadoPartida.carregar(str(caminho))

    _assert_estado_equivalente(carregado, estado)


def test_carregar_arquivo_inexistente(tmp_path):
    """Informa em português que o arquivo não foi encontrado."""
    caminho = tmp_path / "arquivo_fantasma.json"

    with pytest.raises(FileNotFoundError, match=r"(?i)não encontrado"):
        EstadoPartida.carregar(str(caminho))


@pytest.mark.parametrize("conteudo", [
    "{ isso_nao_e_json_valido: verdadeiro }",
    '{"fen_inicial": "rnbq',
    "",
])
def test_carregar_json_truncado_ou_vazio(tmp_path, conteudo):
    """Rejeita JSON malformado, realmente truncado e arquivo vazio."""
    caminho = tmp_path / "corrompido.json"
    caminho.write_text(conteudo, encoding="utf-8")

    with pytest.raises(ValueError, match=r"(?i)(corrompido|inválido|utf-8)"):
        EstadoPartida.carregar(str(caminho))


def test_carregar_bytes_incompativeis_com_utf8(tmp_path):
    """Transforma bytes que não são UTF-8 em erro de dados claro."""
    caminho = tmp_path / "codificacao-invalida.json"
    caminho.write_bytes(b"\xff\xfe\xfa")

    with pytest.raises(ValueError, match=r"(?i)utf-8"):
        EstadoPartida.carregar(str(caminho))


def test_carregar_erro_de_leitura(tmp_path):
    """Converte erros de leitura do sistema em ValueError claro em português."""
    caminho, _ = _criar_json_valido(tmp_path)

    with patch("builtins.open", side_effect=PermissionError("sem permissão")):
        with pytest.raises(ValueError, match=r"(?i)não foi possível ler"):
            EstadoPartida.carregar(str(caminho))


def test_carregar_recursion_error_no_json(tmp_path):
    """Converte recursão excessiva durante a leitura do JSON em erro claro."""
    caminho, _ = _criar_json_valido(tmp_path)

    with patch("json.load", side_effect=RecursionError("profundidade excessiva")):
        with pytest.raises(ValueError, match=r"(?i)json inválido"):
            EstadoPartida.carregar(str(caminho))


@pytest.mark.parametrize(
    "chave",
    ["fen_inicial", "lances_uci", "minha_cor", "relogio"],
)
def test_carregar_chave_obrigatoria_ausente(tmp_path, chave):
    caminho, dados = _criar_json_valido(tmp_path)
    del dados[chave]
    _gravar_json(caminho, dados)

    with pytest.raises(ValueError, match="Arquivo de partida com dados inválidos") as erro:
        EstadoPartida.carregar(str(caminho))

    assert chave in str(erro.value)
    assert "ausente" in str(erro.value)


@pytest.mark.parametrize("campo", ["meu_ms", "adversario_ms", "incremento_ms"])
def test_carregar_chave_obrigatoria_do_relogio_ausente(tmp_path, campo):
    caminho, dados = _criar_json_valido(tmp_path)
    del dados["relogio"][campo]
    _gravar_json(caminho, dados)

    with pytest.raises(ValueError) as erro:
        EstadoPartida.carregar(str(caminho))

    assert f"relogio.{campo}" in str(erro.value)
    assert "ausente" in str(erro.value)


def test_carregar_chave_desconhecida_no_relogio(tmp_path):
    caminho, dados = _criar_json_valido(tmp_path)
    dados["relogio"]["tempo_extra"] = 5
    _gravar_json(caminho, dados)

    with pytest.raises(ValueError, match=r"relogio.*chaves desconhecidas.*tempo_extra"):
        EstadoPartida.carregar(str(caminho))


@pytest.mark.parametrize("minha_cor", [1, 0, "true", None, [], {}])
def test_carregar_minha_cor_com_tipo_invalido(tmp_path, minha_cor):
    caminho, dados = _criar_json_valido(tmp_path)
    dados["minha_cor"] = minha_cor
    _gravar_json(caminho, dados)

    with pytest.raises(ValueError, match=r"minha_cor.*booleano"):
        EstadoPartida.carregar(str(caminho))


@pytest.mark.parametrize("valor", [-1, True, 1.5, "900000", None, [], {}])
@pytest.mark.parametrize("campo", ["meu_ms", "adversario_ms", "incremento_ms"])
def test_carregar_relogio_com_tipo_ou_valor_invalido(tmp_path, campo, valor):
    caminho, dados = _criar_json_valido(tmp_path)
    dados["relogio"][campo] = valor
    _gravar_json(caminho, dados)

    with pytest.raises(ValueError) as erro:
        EstadoPartida.carregar(str(caminho))

    assert f"relogio.{campo}" in str(erro.value)


@pytest.mark.parametrize("relogio", [None, [], "inválido", 4])
def test_carregar_relogio_com_estrutura_invalida(tmp_path, relogio):
    caminho, dados = _criar_json_valido(tmp_path)
    dados["relogio"] = relogio
    _gravar_json(caminho, dados)

    with pytest.raises(ValueError, match=r"relogio.*(objeto|estrutura)"):
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


@pytest.mark.parametrize("minha_cor", [1, 0, "true", None, [], {}])
def test_salvar_rejeita_cor_invalida_antes_de_abrir_temporario(
    tmp_path, minha_cor
):
    caminho = tmp_path / "estado.json"
    temporario = Path(f"{caminho}.tmp")
    conteudo_anterior = "DADOS_ANTIGOS_IMPORTANTES"
    caminho.write_text(conteudo_anterior, encoding="utf-8")
    estado = EstadoPartida(
        tabuleiro=chess.Board(),
        minha_cor=minha_cor,
        relogio=EstadoRelogio(0, 0, 0),
    )

    with patch("builtins.open", side_effect=AssertionError("abriu o temporário")):
        with pytest.raises(ValueError, match="minha_cor.*booleano"):
            estado.salvar(str(caminho))

    assert caminho.read_text(encoding="utf-8") == conteudo_anterior
    assert not temporario.exists()


@pytest.mark.parametrize("relogio", [None, [], "inválido", 4])
def test_salvar_rejeita_estrutura_de_relogio_invalida(tmp_path, relogio):
    caminho = tmp_path / "estado.json"
    temporario = Path(f"{caminho}.tmp")
    conteudo_anterior = "DADOS_ANTIGOS_IMPORTANTES"
    caminho.write_text(conteudo_anterior, encoding="utf-8")
    estado = EstadoPartida(
        tabuleiro=chess.Board(), minha_cor=chess.WHITE, relogio=relogio
    )

    with patch("builtins.open", side_effect=AssertionError("abriu o temporário")):
        with pytest.raises(ValueError, match=r"relogio.*EstadoRelogio"):
            estado.salvar(str(caminho))

    assert caminho.read_text(encoding="utf-8") == conteudo_anterior
    assert not temporario.exists()


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("meu_ms", -1),
        ("meu_ms", True),
        ("adversario_ms", 1.5),
        ("adversario_ms", "100"),
        ("incremento_ms", None),
        ("incremento_ms", []),
    ],
)
def test_salvar_rejeita_relogio_invalido_antes_de_abrir_temporario(
    tmp_path, campo, valor
):
    caminho = tmp_path / "estado.json"
    temporario = Path(f"{caminho}.tmp")
    conteudo_anterior = "DADOS_ANTIGOS_IMPORTANTES"
    caminho.write_text(conteudo_anterior, encoding="utf-8")
    relogio = EstadoRelogio(0, 0, 0)
    setattr(relogio, campo, valor)
    estado = EstadoPartida(
        tabuleiro=chess.Board(), minha_cor=chess.WHITE, relogio=relogio
    )

    with patch("builtins.open", side_effect=AssertionError("abriu o temporário")):
        with pytest.raises(ValueError, match=f"relogio\\.{campo}"):
            estado.salvar(str(caminho))

    assert caminho.read_text(encoding="utf-8") == conteudo_anterior
    assert not temporario.exists()


def test_salvar_atomico_falha_na_escrita_e_limpa_temporario(tmp_path):
    """Mantém o destino e remove o temporário quando a gravação falha."""
    caminho = tmp_path / "estado.json"
    temporario = Path(f"{caminho}.tmp")
    conteudo_anterior = "DADOS_ANTIGOS_IMPORTANTES"
    caminho.write_text(conteudo_anterior, encoding="utf-8")
    estado = EstadoPartida(
        tabuleiro=chess.Board(),
        minha_cor=chess.WHITE,
        relogio=EstadoRelogio(0, 0, 0),
    )

    with patch("json.dump", side_effect=OSError("Disco cheio")):
        with pytest.raises(OSError, match="Disco cheio"):
            estado.salvar(str(caminho))

    assert caminho.read_text(encoding="utf-8") == conteudo_anterior
    assert not temporario.exists()


def test_salvar_atomico_falha_no_replace_e_limpa_temporario(tmp_path):
    """Mantém o destino e remove o temporário quando a substituição falha."""
    caminho = tmp_path / "estado.json"
    temporario = Path(f"{caminho}.tmp")
    conteudo_anterior = "DADOS_ANTIGOS_IMPORTANTES"
    caminho.write_text(conteudo_anterior, encoding="utf-8")
    estado = EstadoPartida(
        tabuleiro=chess.Board(),
        minha_cor=chess.WHITE,
        relogio=EstadoRelogio(0, 0, 0),
    )

    with patch("os.replace", side_effect=OSError("Arquivo travado pelo SO")):
        with pytest.raises(OSError, match="Arquivo travado pelo SO"):
            estado.salvar(str(caminho))

    assert caminho.read_text(encoding="utf-8") == conteudo_anterior
    assert not temporario.exists()


def test_salvar_preserva_excecao_original_se_limpeza_falhar(tmp_path):
    """Mantém a exceção da gravação quando a remoção do temporário também falha."""
    caminho = tmp_path / "estado.json"
    temporario = Path(f"{caminho}.tmp")
    conteudo_anterior = "DADOS_ANTIGOS_IMPORTANTES"
    caminho.write_text(conteudo_anterior, encoding="utf-8")
    estado = EstadoPartida(
        tabuleiro=chess.Board(),
        minha_cor=chess.WHITE,
        relogio=EstadoRelogio(0, 0, 0),
    )
    falha_original = OSError("Falha original de gravação")

    with (
        patch("json.dump", side_effect=falha_original),
        patch("os.remove", side_effect=PermissionError("Falha ao limpar")),
    ):
        with pytest.raises(OSError) as erro:
            estado.salvar(str(caminho))

    assert erro.value is falha_original
    assert str(erro.value) == "Falha original de gravação"
    assert caminho.read_text(encoding="utf-8") == conteudo_anterior
    assert temporario.exists()
    temporario.unlink()
