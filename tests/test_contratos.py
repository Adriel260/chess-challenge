import chess

from contratos import Candidato, EstadoRelogio, Orcamento, RegistroLance, ResultadoBusca


def test_candidato_guarda_lance_e_pv():
    lance = chess.Move.from_uci("e2e4")
    candidato = Candidato(lance=lance, centipeoes=30, mate=None, pv=[lance], profundidade=12, nos=1000)
    resultado = ResultadoBusca(candidatos=[candidato], tempo_gasto_s=0.5)

    assert resultado.candidatos[0].lance == lance
    assert resultado.candidatos[0].mate is None


def test_orcamento_e_relogio():
    orcamento = Orcamento(soft_s=10.0, hard_s=20.0)
    relogio = EstadoRelogio(meu_ms=1_500_000, adversario_ms=1_500_000, incremento_ms=0)

    assert orcamento.soft_s <= orcamento.hard_s
    relogio.meu_ms -= 10_000
    assert relogio.meu_ms == 1_490_000


def test_registro_lance_tem_campos_do_log_obrigatorio():
    registro = RegistroLance(
        numero=1, cor="brancas", lance_uci="e2e4", profundidade=20, nos=500_000,
        avaliacao="+0.30", pv=["e2e4", "e7e5"], tempo_gasto_s=12.3,
    )

    assert registro.origem == "motor"
    assert registro.pv == ["e2e4", "e7e5"]
