"""Testes do formato e da persistência exigidos pelo card A-01."""

import builtins
from pathlib import Path
from unittest.mock import Mock

import pytest

from contratos import RegistroLance
from registro.log import LogPartida
import registro.log as modulo_log


@pytest.mark.parametrize("avaliacao", ["+0.35", "#3", "#-2"])
def test_linha_contem_todos_os_campos(tmp_path: Path, avaliacao: str) -> None:
    """Preserva a avaliação recebida e grava uma linha no formato do contrato."""
    caminho = tmp_path / "partida.log"
    log = LogPartida(str(caminho))
    registro = RegistroLance(
        numero=12,
        cor="brancas",
        lance_uci="e2e4",
        profundidade=22,
        nos=1534200,
        avaliacao=avaliacao,
        pv=["e2e4", "e7e5", "g1f3"],
        tempo_gasto_s=12.4,
        origem="motor",
    )

    log.registrar(registro)

    linhas = caminho.read_text(encoding="utf-8").splitlines()
    linhas_de_lances = [linha for linha in linhas if linha.startswith("lance=")]
    assert linhas_de_lances == [
        "lance=12 cor=brancas uci=e2e4 profundidade=22 nos=1534200 "
        f"avaliacao={avaliacao} pv=e2e4 e7e5 g1f3 tempo=12.40s origem=motor"
    ]


def test_lance_do_adversario_com_pv_vazia(tmp_path: Path) -> None:
    """Grava o lance adversário mesmo sem dados de busca ou PV."""
    caminho = tmp_path / "partida.log"
    log = LogPartida(str(caminho))
    registro = RegistroLance(
        numero=12,
        cor="pretas",
        lance_uci="e7e5",
        profundidade=0,
        nos=0,
        avaliacao="",
        pv=[],
        tempo_gasto_s=0.0,
        origem="adversario",
    )

    log.registrar(registro)

    linhas = caminho.read_text(encoding="utf-8").splitlines()
    linhas_de_lances = [linha for linha in linhas if linha.startswith("lance=")]
    assert linhas_de_lances == [
        "lance=12 cor=pretas uci=e7e5 profundidade=0 nos=0 "
        "avaliacao= pv= tempo=0.00s origem=adversario"
    ]


def test_reabrir_acrescenta_sem_apagar_e_preserva_numero_cheio(tmp_path: Path) -> None:
    """Preserva o conteúdo anterior e o número cheio nas duas cores."""
    caminho = tmp_path / "partida.log"
    log = LogPartida(str(caminho))
    log.registrar(RegistroLance(
        numero=12,
        cor="brancas",
        lance_uci="e2e4",
        profundidade=22,
        nos=1534200,
        avaliacao="+0.35",
        pv=["e2e4"],
        tempo_gasto_s=12.4,
    ))
    conteudo_anterior = caminho.read_text(encoding="utf-8")

    log_retomado = LogPartida(str(caminho))
    assert caminho.read_text(encoding="utf-8").startswith(conteudo_anterior)
    log_retomado.registrar(RegistroLance(
        numero=12,
        cor="pretas",
        lance_uci="e7e5",
        profundidade=0,
        nos=0,
        avaliacao="",
        origem="adversario",
    ))

    conteudo_final = caminho.read_text(encoding="utf-8")
    assert conteudo_final.startswith(conteudo_anterior)
    linhas_de_lances = [
        linha for linha in conteudo_final.splitlines() if linha.startswith("lance=")
    ]
    assert len(linhas_de_lances) == 2
    assert linhas_de_lances[0].startswith("lance=12 cor=brancas uci=e2e4 ")
    assert linhas_de_lances[1].startswith("lance=12 cor=pretas uci=e7e5 ")


def test_cria_pastas_e_cabecalho_com_acentos_em_utf8(tmp_path: Path) -> None:
    """Cria os diretórios ausentes e um cabeçalho legível em UTF-8."""
    caminho = tmp_path / "logs" / "torneio" / "partida.log"
    assert not caminho.parent.exists()

    log = LogPartida(str(caminho))

    assert caminho.is_file()
    cabecalho = caminho.read_text(encoding="utf-8")
    assert cabecalho.strip()
    assert any(letra in cabecalho for letra in "áàâãéêíóôõúüçÁÀÂÃÉÊÍÓÔÕÚÜÇ")
    assert "\ufffd" not in cabecalho


@pytest.fixture
def registro_exemplo() -> RegistroLance:
    """Fornece um lance para os cenários de persistência e recuperação."""
    return RegistroLance(
        numero=12, cor="brancas", lance_uci="e2e4", profundidade=22,
        nos=1534200, avaliacao="+0.35", pv=["e2e4"], tempo_gasto_s=12.4,
    )


def test_falha_transitoria_de_fsync_nao_duplica_lance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str], registro_exemplo: RegistroLance,
) -> None:
    """Repete a sincronização sem acrescentar o mesmo lance novamente."""
    caminho = tmp_path / "partida.log"
    log = LogPartida(str(caminho))
    sincronizar_original = modulo_log.os.fsync
    descritores = []

    def sincronizar(descritor: int) -> None:
        descritores.append(descritor)
        if len(descritores) == 1:
            raise OSError("falha transitória de sincronização")
        sincronizar_original(descritor)

    monkeypatch.setattr(modulo_log.os, "fsync", sincronizar)

    assert log.registrar(registro_exemplo) is None

    linhas = caminho.read_text(encoding="utf-8").splitlines()
    assert len([linha for linha in linhas if linha.startswith("lance=")]) == 1
    assert len(descritores) == 2
    assert capsys.readouterr().err == ""


def test_falha_de_flush_apos_descarregar_nao_duplica_lance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    registro_exemplo: RegistroLance,
) -> None:
    """Preserva uma única linha quando o flush falha após descarregar os dados."""
    caminho = tmp_path / "partida.log"
    log = LogPartida(str(caminho))
    abrir_original = builtins.open
    falhas_injetadas = []

    def abrir_com_flush_falho(*argumentos, **opcoes):
        arquivo = abrir_original(*argumentos, **opcoes)
        observado = Mock(wraps=arquivo)
        observado.__enter__ = Mock(return_value=observado)
        observado.__exit__ = Mock(side_effect=arquivo.__exit__)

        def descarregar() -> None:
            arquivo.flush()
            if not falhas_injetadas:
                falhas_injetadas.append(True)
                raise OSError("falha após descarregar os dados do lance")

        observado.flush.side_effect = descarregar
        return observado

    with monkeypatch.context() as contexto:
        contexto.setattr(builtins, "open", abrir_com_flush_falho)

        assert log.registrar(registro_exemplo) is None

    assert len(falhas_injetadas) == 1
    linhas_de_lances = [
        linha for linha in caminho.read_text(encoding="utf-8").splitlines()
        if linha.startswith("lance=")
    ]
    assert linhas_de_lances == [
        "lance=12 cor=brancas uci=e2e4 profundidade=22 nos=1534200 "
        "avaliacao=+0.35 pv=e2e4 tempo=12.40s origem=motor"
    ]


def test_registrar_escreve_flush_e_fsync_antes_de_retornar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    registro_exemplo: RegistroLance,
) -> None:
    """Sincroniza o descritor do log após escrita e flush explícitos."""
    caminho = tmp_path / "partida.log"
    log = LogPartida(str(caminho))
    abrir_original = builtins.open
    sincronizar_original = modulo_log.os.fsync
    eventos = []
    arquivos_abertos = []

    def abrir_observado(*argumentos, **opcoes):
        arquivo = abrir_original(*argumentos, **opcoes)
        assert Path(argumentos[0]) == caminho
        arquivos_abertos.append(arquivo)
        descritor = arquivo.fileno()
        observado = Mock(wraps=arquivo)
        observado.__enter__ = Mock(return_value=observado)
        observado.__exit__ = Mock(side_effect=arquivo.__exit__)

        def escrever(texto: str) -> int:
            eventos.append(("write", descritor))
            return arquivo.write(texto)

        def descarregar() -> None:
            eventos.append(("flush", descritor))
            arquivo.flush()

        observado.write.side_effect = escrever
        observado.flush.side_effect = descarregar
        return observado

    def sincronizar(descritor: int) -> None:
        assert not arquivos_abertos[-1].closed
        assert descritor == arquivos_abertos[-1].fileno()
        eventos.append(("fsync", descritor))
        sincronizar_original(descritor)

    monkeypatch.setattr(builtins, "open", abrir_observado)
    monkeypatch.setattr(modulo_log.os, "fsync", sincronizar)

    assert log.registrar(registro_exemplo) is None
    eventos.append(("retorno", None))

    assert len(arquivos_abertos) == 1
    descritor = eventos[0][1]
    assert eventos == [
        ("write", descritor), ("flush", descritor),
        ("fsync", descritor), ("retorno", None),
    ]


def test_falha_inicial_de_abertura_repete_e_grava_sem_erro(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str], registro_exemplo: RegistroLance,
) -> None:
    """Recupera uma falha de abertura com uma única repetição silenciosa."""
    caminho = tmp_path / "partida.log"
    log = LogPartida(str(caminho))
    abrir_original = builtins.open
    tentativas = []

    def abrir_com_falha(*argumentos, **opcoes):
        assert Path(argumentos[0]) == caminho
        tentativas.append(argumentos[0])
        if len(tentativas) == 1:
            raise OSError("falha transitória de abertura")
        return abrir_original(*argumentos, **opcoes)

    monkeypatch.setattr(builtins, "open", abrir_com_falha)

    assert log.registrar(registro_exemplo) is None

    assert len(tentativas) == 2
    linhas = caminho.read_text(encoding="utf-8").splitlines()
    assert len([linha for linha in linhas if linha.startswith("lance=")]) == 1
    assert capsys.readouterr().err == ""


def test_falha_persistente_limita_tentativas_e_avisa_em_stderr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str], registro_exemplo: RegistroLance,
) -> None:
    """Desiste após duas falhas de abertura e informa o erro sem propagá-lo."""
    caminho = tmp_path / "partida.log"
    log = LogPartida(str(caminho))
    abrir_com_falha = Mock(side_effect=OSError("disco indisponível"))
    monkeypatch.setattr(builtins, "open", abrir_com_falha)

    assert log.registrar(registro_exemplo) is None

    assert abrir_com_falha.call_count == 2
    assert all(Path(chamada.args[0]) == caminho for chamada in abrir_com_falha.call_args_list)
    assert "disco indisponível" in capsys.readouterr().err
    assert not any(
        linha.startswith("lance=")
        for linha in caminho.read_text(encoding="utf-8").splitlines()
    )


def test_falha_de_escrita_em_stderr_nao_propaga_excecao(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    registro_exemplo: RegistroLance,
) -> None:
    """Mantém o retorno normal mesmo quando o aviso de erro também falha."""
    caminho = tmp_path / "partida.log"
    log = LogPartida(str(caminho))
    abrir_com_falha = Mock(side_effect=OSError("disco indisponível"))
    saida_com_falha = Mock()
    saida_com_falha.write.side_effect = OSError("stderr indisponível")

    with monkeypatch.context() as contexto:
        contexto.setattr(builtins, "open", abrir_com_falha)
        contexto.setattr(modulo_log.sys, "stderr", saida_com_falha)

        assert log.registrar(registro_exemplo) is None

    assert abrir_com_falha.call_count == 2
    saida_com_falha.write.assert_called()
