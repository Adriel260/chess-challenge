---
name: revisar-pr
description: Revisa um PR do GitHub (código do Adriel, feito com Codex) usando o card da tarefa e o subagente revisor, mostra a prévia e só publica os comentários no PR após aprovação. Uso: /revisar-pr <número>
disable-model-invocation: true
---

Revise o PR número `$ARGUMENTS` do repositório deste projeto.

## 1. Coletar contexto
- `gh pr view $ARGUMENTS --json number,title,author,headRefName,baseRefName,headRefOid,body,files`
- Se a base não for `dev`, avise o João e pare.
- Encontre o card: procure em `docs/cards/*.md` a linha `**Branch:**` com o nome da branch do PR. Se não achar, pergunte qual card usar.
- Baixe a branch sem mexer no trabalho local: `git fetch origin <branch>` e use `git diff origin/dev...origin/<branch>` e `git show origin/<branch>:<arquivo>`. Não faça checkout se houver alterações locais não commitadas.

## 2. Revisar
Use o subagente `revisor` passando: número do PR, branch, card e a instrução de seguir `## Review guidelines` do `AGENTS.md`.
Para rodar o pytest da branch sem afetar o diretório atual, use um worktree temporário: `git worktree add ../revisao-pr-$ARGUMENTS origin/<branch>`, rode `<raiz>/.venv/Scripts/python.exe -m pytest` dentro dele e remova com `git worktree remove` ao final.

## 3. Prévia para aprovação (obrigatório)
Mostre ao João, sem publicar nada:
- Contagem `🔴 N · 🟡 N · 🔵 N` e o veredito derivado dela: algum 🔴 → `REQUEST_CHANGES`; só 🟡/🔵 → `COMMENT`; nenhum → `APPROVE`.
- Resumo geral do review (começa com a contagem e lista o que bloqueia).
- Comentários de linha agrupados por nível (🔴, 🟡, 🔵): `arquivo:linha` (lado novo do diff) e o texto, já com o prefixo do nível.
- Resultado do pytest.

Se o João mudar o nível de algum comentário, recalcule a contagem e o veredito.

Pergunte se pode publicar, e aceite ajustes nos textos antes.

## 4. Publicar (só após aprovação)
Monte um JSON gravado em UTF-8 (os emojis dos níveis quebram em outra codificação) e envie com:
`gh api repos/{owner}/{repo}/pulls/$ARGUMENTS/reviews -X POST --input <arquivo.json>`
```json
{
  "commit_id": "<headRefOid>",
  "event": "COMMENT | REQUEST_CHANGES | APPROVE",
  "body": "<resumo>",
  "comments": [{ "path": "src/...", "line": 42, "side": "RIGHT", "body": "..." }]
}
```
Regras dos textos publicados:
- Todo comentário começa com `🔴 [Bloqueante]`, `🟡 [Importante]` ou `🔵 [Nit]` (níveis definidos em `## Review guidelines` do `AGENTS.md`).
- Português, objetivos, com o cenário que quebra e a correção sugerida.
- **Nunca** mencionar IA, Claude, agente ou co-autoria. O review é do João.
- Apague o JSON temporário depois de publicar e mostre o link do review.
