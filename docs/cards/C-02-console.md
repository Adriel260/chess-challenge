# C-02 — Console do operador

- **Dono:** Dev C — Adriel
- **Branch:** `feature/jogo-console`
- **Implementa com:** Codex
- **Testes e review com:** Claude Code (testes escritos pelo Dev A; review pelo subagente `revisor`)
- **Prazo:** 29/10
- **Depende de:** nada

## Objetivo
Converter o que o operador digita em comandos seguros. Um lance digitado errado nunca pode ser aplicado ao tabuleiro.

## Arquivos permitidos
- `src/jogo/console.py`
- `tests/test_console.py`

## Contrato
- `interpretar(texto, tabuleiro) -> Comando` (ver `docs/CONTRATOS.md`, tabela de comandos).
- Aceita espaços extras e maiúsculas (`E2E4` → `e2e4`).
- Lance em formato UCI válido mas ilegal na posição → `ValueError` com mensagem explicando o motivo.
- Promoção sem peça (`e7e8`) → `ValueError` pedindo a peça (`e7e8q`).
- `fen <FEN>` valida a FEN antes de devolver o comando.
- `relogio <min:seg>` aceita `12:34` e `5:07`; formato inválido → `ValueError`.

## Critérios de aceite
- [ ] Nenhum texto inválido gera `Comando(tipo="lance")`
- [ ] Mensagens de erro em português e curtas (lidas com o relógio correndo)
- [ ] `pytest` passa

## Testes a escrever (Dev A com Claude Code)
- Lances legais: normal, roque (`e1g1`), en passant, promoção
- Ilegais: peça cravada, roque sem direito, notação algébrica (`Nf3`), lixo
- Cada comando com argumento válido e inválido

## Fora do escopo
- Loop de leitura do teclado (fica no laço principal, A-02)
