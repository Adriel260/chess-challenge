# AGENTS.md — Convenções do projeto (fonte única para Claude, Codex e Gemini)

## O projeto
Motor de xadrez para o III Chess Challenge (ICEV). Entrega do código via Git: **04/11/2026**. Evento: **06/11/2026**.
Arquitetura: controlador em Python (python-chess) + Stockfish local via UCI. Plano completo em `docs/PLANO.md`; contratos em `docs/CONTRATOS.md` e `src/contratos.py`.

## Regras da competição que o código NUNCA pode violar
- Tudo roda offline. Nenhuma requisição de rede, nenhuma API externa.
- Travar ou estourar o tempo = derrota. O laço do jogo não pode encerrar por exceção.
- Relógio configurável por CLI (`--tempo`, `--inc`). Padrão: 25 min sem incremento (edital); também deve funcionar em 15+10.
- Log obrigatório por lance (`logs/`): número, cor, lance UCI, profundidade, nós, avaliação, PV e tempo gasto.
- Opening book só nos 10 primeiros meios-lances. Tablebases no máximo 5 peças.
- Componentes de autoria da equipe: `src/decisao/tempo.py` e `src/decisao/selecao.py`. Eles precisam ser explicáveis linha a linha na arguição técnica: prefira lógica simples e comentada a truques.

## Estrutura e donos
| Módulo | Dono |
|---|---|
| `src/main.py` (laço do jogo), `src/registro/log.py`, `src/motor/livro.py`, `src/contratos.py`, harness de self-play | Dev A — João |
| `src/motor/uci.py` (+ `MotorFalso` para testes), `src/decisao/selecao.py` | Dev B — Lucas |
| `src/decisao/tempo.py`, `src/jogo/estado.py`, `src/jogo/console.py` | Dev C — Adriel |

Cada tarefa é um card em `docs/cards/`. O pipeline completo (testes → implementação → review cruzado → review humano) está em `docs/ORQUESTRACAO.md`.

## Regras obrigatórias de aprovação
- **Plano antes de código:** antes de criar ou alterar qualquer arquivo, apresente o plano completo de implementação (arquivos, funções, testes, riscos) e **espere aprovação explícita** do humano.
- **Commit só com permissão:** antes de cada commit, mostre os arquivos e a mensagem proposta e **pergunte se pode commitar**. O mesmo vale para push, merge e abertura de PR.
- **Sem co-autoria de IA:** nunca adicione `Co-Authored-By`, "Generated with ...", assinatura ou qualquer menção a IA em commits, PRs, comentários ou arquivos. A autoria é sempre do humano que fez o commit.

## Regras para agentes
1. Altere **apenas os arquivos listados no card**. Se precisar mexer em outro, pare e explique o motivo.
2. **Não altere `src/contratos.py`** sem pedido explícito: ele é o contrato entre os módulos.
3. Reaproveite a python-chess em vez de reimplementar: `chess.Board`, `chess.engine`, `chess.polyglot`, `chess.syzygy`.
4. Todo comportamento novo vem com teste em `tests/test_<modulo>.py`. Testes não podem depender do Stockfish instalado, a menos que sejam marcados como integração.
5. Antes de terminar, rode: `.venv\Scripts\python.exe -m pytest` (Windows) e garanta que tudo passa.
6. Ao revisar, nunca revise código que você mesmo (o mesmo modelo) implementou: veja a matriz em `docs/ORQUESTRACAO.md`.
7. Não adicione dependência sem declarar em `requirements.txt` com versão fixa.

## Estilo
- Nomes de variáveis, funções e mensagens em **português**, sem abreviações obscuras.
- Type hints nas funções públicas. Docstring curta dizendo o que a função garante.
- Arquivos sempre lidos e escritos com `encoding="utf-8"`.
- Imports a partir de `src/` (ex.: `from contratos import Orcamento`); o `pytest.ini` já põe `src` no path.

## Git
- `main` ← `dev` ← `feature/<area>-<descricao>` (ex.: `feature/tempo-orcamento`).
- PR sempre para `dev`, revisado pelo Dev A. Nunca push direto em `main` ou `dev`.
- Descrição do PR escrita pelo dono, explicando a lógica com as próprias palavras.

## Review guidelines
Usadas pelo Codex ao revisar PRs (`@codex review`) e pelo subagente `revisor` do Claude Code.

- Leia o card da tarefa em `docs/cards/` (o nome da branch está no campo **Branch** do card) e compare a implementação com o contrato e os critérios de aceite.
- Classifique **todo** comentário em um dos três níveis e comece o texto com o prefixo exato:

| Nível | Prefixo | Quando usar | Efeito no merge |
|---|---|---|---|
| Bloqueante | `🔴 [Bloqueante]` | Requisição de rede ou serviço externo; caminho em que o laço do jogo encerra por exceção; risco de ultrapassar `Orcamento.hard_s` ou estourar o relógio; log sem campo obrigatório (número, cor, UCI, profundidade, nós, avaliação, PV, tempo); book depois do meio-lance 10; `src/contratos.py` alterado sem aprovação; menção a IA ou co-autoria; bug que derruba ou perde partida | Não entra até ser corrigido |
| Importante | `🟡 [Importante]` | Bug em caso de borda (promoção, roque, en passant, mate, afogamento, posição sem lances, tempo quase zerado); critério de aceite sem teste; arquivo fora do escopo do card; teste que depende do Stockfish sem `@pytest.mark.integracao`; trecho de `src/decisao/tempo.py` ou `src/decisao/selecao.py` difícil de explicar na arguição | Corrigir ou responder justificando no comentário |
| Nit | `🔵 [Nit]` | Nome confuso, docstring faltando, simplificação opcional | Opcional, o dono decide |

- No máximo **5 nits** por PR. Priorize os que mais ajudam na arguição.
- O comentário geral do review começa com a contagem e a lista do que bloqueia, por exemplo: `🔴 1 · 🟡 2 · 🔵 3`.
- Cada comentário traz o cenário concreto que quebra (ou o motivo) e a correção sugerida. Em português, objetivo. Não comente estilo que não afete correção ou clareza.
