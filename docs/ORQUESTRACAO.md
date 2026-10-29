# Orquestração de agentes

## Princípios
1. **Quem revisa nunca é o modelo que implementou.** O mesmo vale para os testes: o modelo que escreve os testes do contrato não é o que implementa.
2. **Humano aprova duas vezes:** o plano antes de qualquer código e o commit antes de ele acontecer.
3. **Sem co-autoria de IA** em commits, PRs ou arquivos.
4. **Um card, uma branch, um agente.** Os módulos não se sobrepõem, então os três trabalham em paralelo.
5. **Contexto mínimo:** o agente recebe `AGENTS.md`, o card, `docs/CONTRATOS.md` e os arquivos do módulo. Nada de "olhe o projeto todo".

## Papéis
| Papel | O que faz | Quem |
|---|---|---|
| Planejador | Escreve o card a partir do cronograma | Dev A com Claude Code |
| Testador | Escreve testes a partir do contrato, antes da implementação | Modelo ≠ implementador |
| Implementador | Apresenta o plano, espera aprovação, implementa até os testes passarem | Ferramenta do dono do módulo |
| Revisor | Revisa o PR: bugs, regras da competição, clareza para a arguição | Modelo ≠ implementador |
| QA de partidas | Self-play em 25+0 e 15+10, travamento e retomada | Dev A com Claude Code |

## Matriz de revisão
A ferramenta é fixa por pessoa, então não é preciso marcar nada no PR.

| Pessoa | Implementa com | Testes e review com | Como o review é feito |
|---|---|---|---|
| João (Dev A) | Claude Code | Codex | `@codex review` no PR |
| Lucas (Dev B) | Gemini | Codex | `@codex review` no PR |
| Adriel (Dev C) | Codex | Claude Code | João roda `/revisar-pr <número>` |

O review automático é a primeira passada. O review humano do João continua obrigatório antes do merge.

## Níveis dos apontamentos
| Nível | Significa | O que o dono do PR faz |
|---|---|---|
| 🔴 **Bloqueante** | Quebra regra da competição ou contrato, ou derruba/perde partida | Corrige. O PR não entra antes disso |
| 🟡 **Importante** | Bug de caso de borda, critério sem teste, fora do escopo, lógica difícil de explicar | Corrige ou responde no comentário justificando |
| 🔵 **Nit** | Melhoria opcional (máximo 5 por PR) | Decide se aplica |

O resumo do review mostra a contagem (`🔴 1 · 🟡 2 · 🔵 3`). Com algum 🔴 o review sai como "Request changes"; sem 🔴, como "Comment"; sem apontamentos, "Approve". Detalhes em `## Review guidelines` do `AGENTS.md`.

## Review no GitHub
### Codex (PRs do João e do Lucas)
1. Em chatgpt.com/codex, conecte o GitHub e dê acesso ao repositório `Adriel260/chess-challenge`. Como o Adriel é o dono, ele pode precisar aprovar a instalação do app do Codex no repositório.
2. Nas configurações do Codex, ative **Code review** para o repositório. **Não** ligue o review automático de todos os PRs: os PRs do Adriel são feitos com Codex e devem ser revisados pelo Claude.
3. No PR, comente `@codex review`. O Codex segue a seção `## Review guidelines` do `AGENTS.md`.
4. Os comentários aparecem na conta do bot do Codex. Se quiser tudo no seu nome, rode `/review` no Codex CLI local e publique os apontamentos você mesmo.

### Claude Code (PRs do Adriel)
1. No Claude Code, na raiz do projeto: `/revisar-pr <número>`.
2. Ele baixa o PR, encontra o card pela branch, roda o subagente `revisor` e **mostra a prévia dos comentários**.
3. Só publica no PR (na sua conta, sem menção a IA) depois da sua aprovação.

## Pipeline de um card
```
1. Card em docs/cards/ (Dev A)
2. Testes do contrato              — modelo X
3. Plano de implementação          — modelo Y  →  APROVAÇÃO DO DONO
4. Implementação + pytest local    — modelo Y
5. Proposta de commit              — modelo Y  →  APROVAÇÃO DO DONO (sem co-autoria)
6. PR para dev + review            — modelo ≠ Y
7. Dono corrige os apontamentos
8. Review humano do Dev A + dono explica a lógica em 2 minutos
9. Merge na dev (Dev A)
```
Se o dono não consegue explicar a lógica no passo 8, o PR não entra, mesmo com os testes passando.

## Como pedir cada etapa ao agente
- **Testes:** "Leia `AGENTS.md` e `docs/cards/<card>.md`. Escreva apenas os testes descritos no card, a partir do contrato. Não implemente o módulo. Mostre o plano antes."
- **Implementação:** "Leia `AGENTS.md` e `docs/cards/<card>.md`. Apresente o plano completo de implementação e espere minha aprovação. Depois implemente até `pytest` passar. Não commite sem perguntar."
- **Review:** "Revise a branch `<branch>` contra `dev` usando `docs/cards/<card>.md` e `AGENTS.md`. Aponte bugs, violações das regras da competição e trechos difíceis de explicar. Não altere arquivos."
  - No Claude Code: use o subagente `revisor`.
