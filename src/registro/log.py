"""Log obrigatório da competição (dono: Dev A).

Cada lance registra: número, cor, lance UCI, profundidade, nós, avaliação, PV e tempo gasto.
"""

import os
import sys
from datetime import datetime

from contratos import RegistroLance

# Uma falha de escrita é tentada de novo uma vez antes de desistir.
TENTATIVAS_DE_ESCRITA = 2


class LogPartida:
    """Arquivo de log de uma partida. Cada linha gravada vai para o disco na hora."""

    def __init__(self, caminho: str):
        """Cria a pasta e o arquivo se faltarem e escreve o cabeçalho.

        Se o arquivo já existir (retomada), acrescenta ao final em vez de apagar.
        """
        self.caminho = caminho
        pasta = os.path.dirname(caminho)
        if pasta:
            os.makedirs(pasta, exist_ok=True)

        retomada = os.path.exists(caminho) and os.path.getsize(caminho) > 0
        situacao = "retomada" if retomada else "iniciada"
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        erro = self._gravar(f"# Chess Challenge III — sessão {situacao} em {agora}\n")
        if erro is not None:
            raise erro

    def registrar(self, registro: RegistroLance) -> None:
        """Escreve uma linha no arquivo e garante que ela chegou ao disco.

        Nunca lança exceção: se a escrita falhar, tenta mais uma vez e,
        se falhar de novo, avisa em stderr e segue o jogo.
        """
        try:
            erro = self._gravar(formatar_linha(registro) + "\n")
        except Exception as erro_inesperado:
            erro = erro_inesperado

        if erro is not None:
            try:
                print(f"ERRO: não foi possível gravar o lance no log {self.caminho}: {erro}", file=sys.stderr)
            except Exception:
                pass

    def _gravar(self, texto: str) -> Exception | None:
        """Acrescenta o texto ao arquivo e força a gravação no disco (flush + fsync).

        O arquivo é aberto e fechado a cada escrita: se o programa cair logo
        depois, o texto já está no disco. Tenta até TENTATIVAS_DE_ESCRITA vezes
        e nunca escreve o mesmo texto duas vezes. Devolve None se deu certo ou
        o último erro se todas as tentativas falharam.
        """
        ultimo_erro: Exception | None = None
        for tentativa in range(TENTATIVAS_DE_ESCRITA):
            try:
                # "a+": escreve sempre no fim do arquivo, mas também permite lê-lo.
                with open(self.caminho, "a+", encoding="utf-8") as arquivo:
                    # A tentativa anterior pode ter gravado o texto antes de falhar
                    # (ex.: o flush ou o fsync falhou, mas o fechamento do arquivo
                    # descarregou os dados). Na repetição, só escreve se o texto
                    # ainda não estiver no fim do arquivo.
                    ja_gravado = False
                    if tentativa > 0:
                        arquivo.seek(0)
                        ja_gravado = arquivo.read().endswith(texto)
                    if not ja_gravado:
                        arquivo.write(texto)
                        arquivo.flush()
                    os.fsync(arquivo.fileno())
                return None
            except Exception as erro:
                ultimo_erro = erro
        return ultimo_erro


def formatar_linha(registro: RegistroLance) -> str:
    """Monta a linha do log no formato exigido, sem a quebra de linha final."""
    return (
        f"lance={registro.numero} cor={registro.cor} uci={registro.lance_uci} "
        f"profundidade={registro.profundidade} nos={registro.nos} "
        f"avaliacao={registro.avaliacao} pv={' '.join(registro.pv)} "
        f"tempo={registro.tempo_gasto_s:.2f}s origem={registro.origem}"
    )
