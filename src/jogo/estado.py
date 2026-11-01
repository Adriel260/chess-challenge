"""Estado da partida e persistência para retomada após falha (dono: Dev C)."""

import json
import os
from dataclasses import dataclass

import chess

from contratos import EstadoRelogio


def _validar_cor_e_relogio(minha_cor: object, relogio: object) -> None:
    """Valida os tipos da cor e dos campos do relógio."""
    if type(minha_cor) is not bool:
        raise ValueError("O campo 'minha_cor' deve ser um valor booleano.")

    if not isinstance(relogio, EstadoRelogio):
        raise ValueError("O campo 'relogio' deve ser um EstadoRelogio.")

    for campo in ("meu_ms", "adversario_ms", "incremento_ms"):
        valor = getattr(relogio, campo)
        if type(valor) is not int:
            raise ValueError(
                f"O campo 'relogio.{campo}' deve ser um número inteiro de milissegundos."
            )


def _validar_relogio_nao_negativo(relogio: EstadoRelogio) -> None:
    """Rejeita tempos negativos ao carregar um relógio persistido."""
    for campo in ("meu_ms", "adversario_ms", "incremento_ms"):
        valor = getattr(relogio, campo)
        if valor < 0:
            raise ValueError(
                f"O campo 'relogio.{campo}' deve ser um valor não negativo."
            )


@dataclass
class EstadoPartida:
    tabuleiro: chess.Board
    minha_cor: chess.Color
    relogio: EstadoRelogio

    def salvar(self, caminho: str) -> None:
        """Salva o estado em JSON atômico.

        Raises:
            ValueError: se a cor, os tempos ou a posição inicial forem inválidos.
            OSError: se não for possível gravar ou substituir o arquivo.
            Outras exceções da serialização: propagadas sem alteração.
        """
        _validar_cor_e_relogio(self.minha_cor, self.relogio)

        tabuleiro_inicial = self.tabuleiro.root()
        if not tabuleiro_inicial.is_valid():
            raise ValueError("A posição inicial é inválida.")

        dados = {
            "fen_inicial": tabuleiro_inicial.fen(),
            "lances_uci": [lance.uci() for lance in self.tabuleiro.move_stack],
            "minha_cor": self.minha_cor,
            "relogio": {
                "meu_ms": max(0, self.relogio.meu_ms),
                "adversario_ms": max(0, self.relogio.adversario_ms),
                "incremento_ms": max(0, self.relogio.incremento_ms),
            },
        }

        caminho_temporario = f"{caminho}.tmp"

        try:
            with open(caminho_temporario, "w", encoding="utf-8") as arquivo:
                json.dump(dados, arquivo, ensure_ascii=False, indent=2)

            os.replace(caminho_temporario, caminho)
        except BaseException:
            try:
                os.remove(caminho_temporario)
            except BaseException:
                # A limpeza é secundária; a exceção da gravação deve prevalecer.
                pass
            raise

    @classmethod
    def carregar(cls, caminho: str) -> "EstadoPartida":
        """Recupera a partida, preservando histórico, cor e relógio.

        Raises:
            FileNotFoundError: se o arquivo não existir.
            ValueError: se o arquivo não puder ser lido ou contiver dados inválidos.
        """
        try:
            with open(caminho, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except FileNotFoundError as erro:
            raise FileNotFoundError(
                f"Arquivo de partida não encontrado: {caminho}"
            ) from erro
        except OSError as erro:
            raise ValueError(
                f"Não foi possível ler o arquivo de partida '{caminho}': {erro}"
            ) from erro
        except (json.JSONDecodeError, UnicodeDecodeError, RecursionError) as erro:
            raise ValueError(
                "Arquivo de partida corrompido, JSON inválido ou codificação "
                f"UTF-8 inválida: {caminho}"
            ) from erro

        try:
            if not isinstance(dados, dict):
                raise ValueError("O conteúdo deve ser um objeto JSON.")

            for chave in ("fen_inicial", "lances_uci", "minha_cor", "relogio"):
                if chave not in dados:
                    raise ValueError(f"A chave obrigatória '{chave}' está ausente.")

            fen_inicial = dados["fen_inicial"]
            lances_uci = dados["lances_uci"]
            minha_cor = dados["minha_cor"]
            dados_relogio = dados["relogio"]

            if not isinstance(fen_inicial, str):
                raise ValueError("O campo 'fen_inicial' deve ser um texto.")

            if not isinstance(lances_uci, list):
                raise ValueError("O campo 'lances_uci' deve ser uma lista.")

            if not isinstance(dados_relogio, dict):
                raise ValueError("O campo 'relogio' deve ser um objeto JSON.")

            for campo in ("meu_ms", "adversario_ms", "incremento_ms"):
                if campo not in dados_relogio:
                    raise ValueError(
                        f"A chave obrigatória 'relogio.{campo}' está ausente."
                    )

            campos_relogio = {"meu_ms", "adversario_ms", "incremento_ms"}
            campos_desconhecidos = set(dados_relogio) - campos_relogio
            if campos_desconhecidos:
                desconhecidos = ", ".join(sorted(campos_desconhecidos))
                raise ValueError(
                    f"O campo 'relogio' contém chaves desconhecidas: {desconhecidos}."
                )

            try:
                relogio = EstadoRelogio(**dados_relogio)
            except TypeError as erro:
                raise ValueError(
                    f"O campo 'relogio' possui estrutura inválida: {erro}"
                ) from erro

            _validar_cor_e_relogio(minha_cor, relogio)
            _validar_relogio_nao_negativo(relogio)

            try:
                tabuleiro = chess.Board(fen_inicial)
            except ValueError as erro:
                raise ValueError(
                    "O campo 'fen_inicial' não contém uma FEN válida."
                ) from erro

            if not tabuleiro.is_valid():
                raise ValueError("A posição inicial é inválida.")

            for lance_uci in lances_uci:
                if not isinstance(lance_uci, str):
                    raise ValueError("Cada lance do histórico deve ser um texto UCI.")

                try:
                    lance = chess.Move.from_uci(lance_uci)
                except ValueError as erro:
                    raise ValueError(
                        f"Lance UCI inválido no histórico: {lance_uci}."
                    ) from erro

                if lance not in tabuleiro.legal_moves:
                    raise ValueError(f"Lance ilegal no histórico: {lance_uci}")

                tabuleiro.push(lance)

        except (TypeError, ValueError) as erro:
            raise ValueError(
                f"Arquivo de partida com dados inválidos ('{caminho}'): {erro}"
            ) from erro

        return cls(
            tabuleiro=tabuleiro,
            minha_cor=minha_cor,
            relogio=relogio,
        )
