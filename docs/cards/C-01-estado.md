# C-01 — Estado da partida e retomada

- **Dono:** Dev C — Adriel
- **Branch:** `feature/jogo-estado`
- **Implementa com:** Codex
- **Testes e review com:** Claude Code (subagente `revisor`)
- **Prazo:** 29/10
- **Depende de:** nada

## Objetivo
Salvar o estado da partida a cada meio-lance para que, se o programa travar, `--retomar` volte exatamente para a mesma posição e relógio.

## Arquivos permitidos
- `src/jogo/estado.py`
- `tests/test_estado.py`

## Contrato
- `EstadoPartida.salvar(caminho)`: grava JSON com FEN inicial, lista de lances UCI, nossa cor e relógio. Escrita **atômica**: escreve em `<caminho>.tmp` e usa `os.replace`.
- `EstadoPartida.carregar(caminho) -> EstadoPartida`: reconstrói o tabuleiro aplicando os lances a partir da FEN inicial (mantém histórico, necessário para detectar repetição).
- Arquivo corrompido ou inexistente gera erro claro (`ValueError` / `FileNotFoundError`) com mensagem em português.

## Critérios de aceite
- [ ] Salvar → carregar devolve mesma FEN, mesmo histórico, mesma cor e mesmo relógio
- [ ] Repetição de posição continua detectável após carregar
- [ ] Partida iniciada de FEN personalizada (comando `fen`) também é retomável
- [ ] `pytest` passa

## Testes a escrever (Claude Code)
- Ida e volta após 10 meios-lances, incluindo roque, en passant e promoção
- Tripla repetição detectada após carregar
- JSON truncado gera erro claro
- Escrita atômica: arquivo anterior intacto se a escrita falhar

## Fora do escopo
- Interpretar comandos do operador (C-02), decidir onde salvar (A-02)
