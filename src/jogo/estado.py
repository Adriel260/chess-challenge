"""Estado da partida e persistência para retomada após falha (dono: Dev C)."""
import json
import os
from dataclasses import dataclass

import chess

from contratos import EstadoRelogio

@dataclass
class EstadoPartida:
    tabuleiro: chess.Board
    minha_cor: chess.Color
    relogio: EstadoRelogio

    def salvar(self, caminho: str) -> None:
        """Salva a partida em JSON usando um arquivo temporário."""
        dados = {
            "fen_inicial": self.tabuleiro.root().fen(),
            "lances_uci": [
                lance.uci() for lance in self.tabuleiro.move_stack
            ],
            "minha_cor": self.minha_cor,
            "relogio": {
                "meu_ms": self.relogio.meu_ms,
                "adversario_ms": self.relogio.adversario_ms,
                "incremento_ms": self.relogio.incremento_ms,
            },
        }

        caminho_temporario = f"{caminho}.tmp"

        with open(caminho_temporario, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)

        os.replace(caminho_temporario, caminho)

    @classmethod
    def carregar(cls, caminho: str) -> "EstadoPartida":
        """Recupera a partida, preservando histórico, cor e relógio."""
        try:
            with open(caminho, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except FileNotFoundError as erro:
            raise FileNotFoundError(
                f"Arquivo de partida não encontrado: {caminho}"
            ) from erro
        except (json.JSONDecodeError, UnicodeDecodeError) as erro:
            raise ValueError(
                f"Arquivo de partida corrompido ou JSON inválido: {caminho}"
            ) from erro

        try:
            if not isinstance(dados, dict):
                raise ValueError("O conteúdo deve ser um objeto JSON.")

            fen_inicial = dados["fen_inicial"]
            lances_uci = dados["lances_uci"]
            minha_cor = dados["minha_cor"]

            if not isinstance(fen_inicial, str):
                raise ValueError("A FEN inicial deve ser um texto.")

            if not isinstance(lances_uci, list):
                raise ValueError("O histórico deve ser uma lista.")

            if type(minha_cor) is not bool:
                raise ValueError("A cor deve ser um valor booleano.")

            relogio = EstadoRelogio(**dados["relogio"])

            for valor in (
                relogio.meu_ms,
                relogio.adversario_ms,
                relogio.incremento_ms,
            ):
                if type(valor) is not int or valor < 0:
                    raise ValueError(
                        "Os tempos devem ser inteiros não negativos."
                    )

            tabuleiro = chess.Board(fen_inicial)

            if not tabuleiro.is_valid():
                raise ValueError("A posição inicial é inválida.")

            for lance_uci in lances_uci:
                if not isinstance(lance_uci, str):
                    raise ValueError("Cada lance deve ser um texto UCI.")

                lance = chess.Move.from_uci(lance_uci)

                if lance not in tabuleiro.legal_moves:
                    raise ValueError(f"Lance ilegal no histórico: {lance_uci}")

                tabuleiro.push(lance)

        except (KeyError, TypeError, ValueError) as erro:
            raise ValueError(
                f"Arquivo de partida com dados inválidos: {caminho}"
            ) from erro

        return cls(
            tabuleiro=tabuleiro,
            minha_cor=minha_cor,
            relogio=relogio,
        )
