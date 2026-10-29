# B-01 — Motor UCI (Stockfish) e MotorFalso

- **Dono:** Dev B — Lucas
- **Branch:** `feature/motor-uci`
- **Implementa com:** Gemini
- **Testes e review com:** Codex
- **Prazo:** 29/10 — **`MotorFalso` primeiro (de manhã)**, pois A-02 depende dele
- **Depende de:** nada

## Objetivo
Encapsular o Stockfish local para devolver os melhores candidatos (MultiPV) de uma posição dentro de um orçamento de tempo, e oferecer um `MotorFalso` com a mesma interface para os testes.

## Arquivos permitidos
- `src/motor/uci.py`
- `src/motor/falso.py`
- `tests/test_motor_uci.py`

## Contrato
- `Motor(caminho, threads=4, hash_mb=512, multipv=4)` abre o Stockfish com `chess.engine.SimpleEngine.popen_uci`.
- `Motor.analisar(tabuleiro, orcamento) -> ResultadoBusca`:
  - usa `analyse(..., multipv=N)` com limite de tempo `orcamento.soft_s` e **garante não passar de `orcamento.hard_s`**;
  - converte cada linha em `Candidato`, com avaliação do ponto de vista de quem joga;
  - se houver menos lances legais que N, devolve só os que existem.
- Se o processo do Stockfish morrer, `analisar` tenta reabrir uma vez antes de lançar exceção.
- `MotorFalso(candidatos_por_fen=None, erro=None)`: mesma interface; sem configuração, devolve os primeiros lances legais com avaliação fixa; com `erro`, lança essa exceção (para testar o fallback).

## Critérios de aceite
- [ ] `MotorFalso` usável por A-02 sem Stockfish instalado
- [ ] Testes com Stockfish real marcados com `@pytest.mark.integracao` e pulados se `engines/stockfish.exe` não existir
- [ ] Análise de posição de mate em 1 devolve `mate=1` no primeiro candidato
- [ ] `pytest` passa

## Testes a escrever (Codex)
- `MotorFalso`: candidatos legais, posição com 1 lance legal, modo erro
- Integração: posição inicial, mate em 1, respeito ao `hard_s` (tempo medido)
- Reabertura após matar o processo

## Fora do escopo
- Escolher entre os candidatos (B-02), decidir o tempo (C-03), ponder
