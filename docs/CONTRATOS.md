# Contratos entre módulos

O código-fonte da verdade é `src/contratos.py`. Este documento explica o fluxo.

## Fluxo de um lance nosso
```
EstadoPartida ──► livro.consultar_livro(tabuleiro)          # até o meio-lance 10
      │              └─ se devolver lance: usa, log com origem="livro"
      ▼
tempo.calcular_orcamento(relogio, tabuleiro) ──► Orcamento(soft_s, hard_s)
      ▼
Motor.analisar(tabuleiro, orcamento) ──► ResultadoBusca(candidatos MultiPV, tempo_gasto_s)
      ▼
selecao.escolher_lance(tabuleiro, resultado, relogio) ──► Candidato
      ▼
LogPartida.registrar(RegistroLance) ; EstadoPartida.salvar()
```
Se qualquer etapa lançar exceção: usar o primeiro candidato disponível ou, em último caso, um lance legal qualquer (`origem="fallback"`). O programa nunca pode cair.

## Fluxo de um lance do adversário
`console.interpretar(texto, tabuleiro)` ──► `Comando(tipo="lance")` ──► aplica no tabuleiro ──► `EstadoPartida.salvar()` ──► log com `origem="adversario"`.

## Tipos
| Tipo | Campos | Observações |
|---|---|---|
| `Candidato` | lance, centipeoes, mate, pv, profundidade, nos | Avaliação do ponto de vista de quem joga; só um entre centipeoes/mate |
| `ResultadoBusca` | candidatos, tempo_gasto_s | Candidatos ordenados do melhor para o pior |
| `Orcamento` | soft_s, hard_s | `hard_s` nunca pode ser ultrapassado |
| `EstadoRelogio` | meu_ms, adversario_ms, incremento_ms | Corrigível pelo comando `relogio` |
| `RegistroLance` | numero, cor, lance_uci, profundidade, nos, avaliacao, pv, tempo_gasto_s, origem | Uma linha do log obrigatório |

## Comandos do console
| Entrada | Efeito |
|---|---|
| `e2e4`, `e7e8q` | Lance em UCI (validado contra o tabuleiro) |
| `desfazer` | Desfaz o último meio-lance |
| `fen <FEN>` | Sincroniza com o tabuleiro físico |
| `relogio <min:seg>` | Corrige nosso tempo restante pelo relógio físico |
| `status` | Mostra tabuleiro, relógio e último lance |
| `sair` | Salva e encerra |
