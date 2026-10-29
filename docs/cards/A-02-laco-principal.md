# A-02 — Esqueleto do laço principal

- **Dono:** Dev A — João
- **Branch:** `feature/jogo-laco-principal`
- **Implementa com:** Claude Code
- **Testes e review com:** Codex
- **Prazo:** 29/10 (esqueleto) → 30/10 integração real (M1)
- **Depende de:** B-01 (`MotorFalso`), A-01. Usa interfaces de C-01 e C-02; enquanto não chegam, usar implementações mínimas dentro dos testes.

## Objetivo
`main.py` joga uma partida inteira: alterna entre lance nosso (motor) e lance do adversário (digitado), registra no log e salva o estado a cada meio-lance. No M1 o tempo por lance é fixo (sem `decisao/tempo.py`) e o lance escolhido é o primeiro candidato (sem `decisao/selecao.py`).

## Arquivos permitidos
- `src/main.py`
- `tests/test_main.py`

## Contrato
- Fluxo de um lance nosso e do adversário conforme `docs/CONTRATOS.md`.
- `jogar_partida(estado, motor, entrada, saida, log)`: recebe dependências por parâmetro (para testar com `MotorFalso` e entrada simulada).
- Nunca encerra por exceção: qualquer erro no nosso lance cai em fallback (primeiro candidato disponível ou primeiro lance legal), registrado com `origem=fallback`.
- Lance anunciado em voz alta impresso em destaque, em UCI.
- Fim de jogo (mate, afogamento, repetição, 50 lances, material insuficiente) detectado pela python-chess e informado.

## Critérios de aceite
- [ ] Partida completa contra entrada simulada termina sem exceção, como brancas e como pretas
- [ ] Motor que lança exceção não derruba o programa
- [ ] Log tem uma linha por meio-lance
- [ ] `pytest` passa sem Stockfish

## Testes a escrever (Codex)
- Partida curta simulada (ex.: mate do pastor) jogando de pretas
- `MotorFalso` configurado para lançar exceção → fallback
- Comando inválido do adversário não avança o jogo

## Fora do escopo
- Gestão de tempo real (C-03, 31/10), seleção de lance (B-02, 31/10), book (A-03, 31/10), ponder
