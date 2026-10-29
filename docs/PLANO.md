# Plano — Chess Challenge III (entrega 04/11/2026, evento 06/11)

## Contexto
Equipe de 3 devs, 7 dias (28/10 → 04/11).
Regras que guiam a arquitetura (FAQ da organização):
- Tudo local/offline; notebook Windows 16 GB de um dos colegas.
- Relógio: seguimos o edital (25 min por jogador, sem incremento) como padrão. O FAQ cita 15 min + 10 s; por isso tempo e incremento são **parâmetros de CLI** (`--tempo`, `--inc`) e a gestão de tempo é testada nos dois cenários — trocar é só mudar o argumento. Estouro de tempo ou travamento = derrota.
- Autoria própria obrigatória em ≥1 componente decisório (avaliação, busca/seleção ou gestão de tempo), defendido em arguição.
- Log .txt/.log por lance: nº, cor, UCI, profundidade, nós, avaliação, PV, tempo gasto.
- Lances do adversário chegam por voz em UCI → digitados à mão; tabuleiro físico é a verdade.
- Book ≤ 10 meios-lances; tablebases ≤ 5 peças; dependências declaradas.

## Decisão de arquitetura
**Controlador em Python + Stockfish local via UCI**, com **dois componentes de autoria da equipe**:
1. **Gestão de tempo** (`decisao/tempo.py`) — orçamento por lance, genérico para qualquer tempo base + incremento (padrão 25+0).
2. **Seleção de lance** (`decisao/selecao.py`) — Stockfish devolve MultiPV; heurística própria escolhe entre lances próximos (anti-repetição quando ganhando, complexidade quando à frente no relógio, segurança quando atrás).

Reaproveitar da python-chess (não reinventar): `chess.Board` (estado/legalidade), `chess.engine.SimpleEngine.popen_uci` + `analyse(..., multipv=N)` (UCI, depth/nodes/score/pv já vêm no `info`), `chess.polyglot` (book), `chess.syzygy` só se usarmos tablebases.

Ter dois componentes autorais (não só um) reforça a defesa de "modificação significativa" na arguição. Se a banca questionar o uso do Stockfish, os módulos de I/O, log, estado e tempo continuam valendo em um eventual fork.

## Estrutura de módulos (src/)
```
src/
  main.py              # CLI: --cor white|black, --tempo 1500 (s), --inc 0 (s), --retomar
  contratos.py         # dataclasses compartilhadas (definidas no dia 1, congeladas)
  jogo/estado.py       # Board + relógios + persistência JSON a cada meio-lance; retomada
  jogo/console.py      # entrada: lance UCI validado + comandos (desfazer, fen, relogio, status, sair)
  motor/uci.py         # wrapper Stockfish: config (Threads, Hash, MultiPV), analisar(board, limite)
  motor/livro.py       # Polyglot, só até ply 10
  decisao/tempo.py     # AUTORIA: calcula orçamento (soft/hard) do lance
  decisao/selecao.py   # AUTORIA: escolhe lance entre candidatos MultiPV
  registro/log.py      # log obrigatório em logs/<partida>.log
tests/                 # pytest por módulo + testes de integração
engines/               # stockfish.exe (ignorado no git; versão declarada no README)
```
Contratos principais (`contratos.py`): `Candidato(lance, score_cp|mate, pv, depth, nodes)`, `ResultadoBusca(candidatos, tempo_gasto)`, `Orcamento(soft_s, hard_s)`, `EstadoRelogio(meu_ms, adv_ms, inc_ms)`, `RegistroLance(n, cor, uci, depth, nodes, aval, pv, tempo)`.
Robustez obrigatória: estado salvo a cada lance → `--retomar` reabre a partida após crash; comando `fen` sincroniza com o tabuleiro físico; `relogio` corrige o tempo restante pelo relógio físico; nunca encerrar por exceção (try/except no laço com fallback = melhor lance do Stockfish / lance legal).

## Divisão de funções
| Pessoa | Papel | Módulos | Defende na arguição |
|---|---|---|---|
| **Dev A** | Integração, log, book, QA e review final; dono do fluxo de agentes | `main.py` (laço do jogo), `registro/log.py`, `motor/livro.py`, `contratos.py`, harness de self-play, merges dev→main | Arquitetura, robustez e log |
| **Dev B** | Motor e seleção | `motor/uci.py` (+ `MotorFalso` para testes), `decisao/selecao.py` | Seleção de lance |
| **Dev C (dono do notebook)** | Tempo e operação | `decisao/tempo.py`, `jogo/estado.py`, `jogo/console.py`, setup do notebook (Stockfish, offline) | Gestão de tempo |

## Cronograma
| Data | Marco |
|---|---|
| 28/10 (qua) | Aprovar plano; A cria `dev`, `contratos.py`, AGENTS.md, esqueleto de pastas; B/C baixam Stockfish (verificar AVX2 no notebook do C) e book |
| 29/10 | A: `log.py` + esqueleto do laço em `main.py` com `MotorFalso`. B: `uci.py` + `MotorFalso`. C: `estado.py` + `console.py` |
| 30/10 | **M1 — MVP jogável ponta a ponta** (tempo fixo por lance, sem book) merge em `dev` |
| 31/10 | B: `selecao.py`. C: `tempo.py`. A: `livro.py` + self-play em tempo acelerado (escala de 25+0 e de 15+10) |
| 01/11 | **M2 — feature complete**; `dev`→`main`; torneio interno contra Stockfish com Skill Level reduzido |
| 02/11 | Ajuste fino de tempo/seleção, testes de crash/retomada, lances inválidos; extras se sobrar (ponder, Syzygy 5 peças) |
| 03/11 | **Code freeze** (só bugfix). Ensaio no notebook do C: Wi-Fi off, tabuleiro físico, relógio, protocolo de anúncio, partida 25 min inteira (+ uma em 15+10 se der tempo) |
| 04/11 | README com declarações (versão/commit Stockfish, origem do book, licença), `requirements.txt` final, envio do Git |

## Fluxo de Git
- `main` (só marcos M2 e entrega) ← `dev` (integração diária) ← `feature/<area>-<descricao>` (ex.: `feature/tempo-orcamento`).
- Branches curtas (≤1 dia), PR para `dev` com review do A; ninguém faz push direto em `main`/`dev`.
- PR precisa: testes passando (`pytest`), descrição em palavras próprias do dono explicando a lógica (prepara a arguição).

## Orquestração de agentes
Detalhada em `docs/ORQUESTRACAO.md`; cards em `docs/cards/`.

## Verificação
- `.\.venv\Scripts\python.exe -m pytest` passa com stubs.
- `.\.venv\Scripts\python.exe src/main.py --help` funciona.
- Marcos M1/M2 verificados por partida completa simulada (script do A jogando contra Stockfish fraco), checando log com todos os campos, nenhum estouro de tempo (em 25+0 e 15+10), e retomada após matar o processo no meio.
