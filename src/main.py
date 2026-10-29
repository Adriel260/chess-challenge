import argparse

import chess


def ler_argumentos():
    parser = argparse.ArgumentParser(description="Chess Challenge III")
    parser.add_argument("--cor", choices=["brancas", "pretas"], required=False, help="cor da nossa equipe")
    parser.add_argument("--tempo", type=int, default=1500, help="tempo base em segundos (padrão: 1500 = 25 min)")
    parser.add_argument("--inc", type=int, default=0, help="incremento por lance em segundos (padrão: 0)")
    parser.add_argument("--retomar", action="store_true", help="retoma a última partida salva")
    return parser.parse_args()


def main():
    argumentos = ler_argumentos()
    tabuleiro = chess.Board()

    print("Chess Challenge III")
    print(f"Tempo: {argumentos.tempo}s + {argumentos.inc}s")
    print()
    print(tabuleiro)


if __name__ == "__main__":
    main()
