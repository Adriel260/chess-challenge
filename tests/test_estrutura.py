import importlib

import pytest

MODULOS = [
    "contratos",
    "decisao.tempo",
    "decisao.selecao",
    "motor.uci",
    "motor.livro",
    "registro.log",
    "jogo.estado",
    "jogo.console",
    "main",
]


@pytest.mark.parametrize("nome", MODULOS)
def test_modulo_importa(nome):
    importlib.import_module(nome)


def test_livro_respeita_limite_da_competicao():
    from motor.livro import LIMITE_MEIOS_LANCES

    assert LIMITE_MEIOS_LANCES <= 10
