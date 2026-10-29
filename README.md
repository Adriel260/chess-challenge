# Chess Challenge III — ICEV 2026

Motor de xadrez da equipe para o III Chess Challenge. Controlador em Python (python-chess) + Stockfish local via UCI, com gestão de tempo e seleção de lance de autoria da equipe.

- Plano e cronograma: `docs/PLANO.md`
- Contratos entre módulos: `docs/CONTRATOS.md`
- Fluxo de trabalho e review: `docs/ORQUESTRACAO.md`
- Tarefas: `docs/cards/`
- Regras para agentes e convenções: `AGENTS.md`

## Instalação (Windows)
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```
Baixe o Stockfish para Windows e coloque o executável em `engines/stockfish.exe` (a pasta é ignorada pelo git; a versão usada será declarada aqui antes da entrega).

## Uso
```powershell
.\.venv\Scripts\python.exe src/main.py --help
.\.venv\Scripts\python.exe src/main.py --cor brancas --tempo 1500 --inc 0
```
Padrão: 25 min sem incremento (edital). Para 15+10: `--tempo 900 --inc 10`.

## Testes
```powershell
.\.venv\Scripts\python.exe -m pytest
```
Testes que precisam do Stockfish real são marcados com `@pytest.mark.integracao`.

## Fluxo de Git
`main` ← `dev` ← `feature/<area>-<descricao>`. PR sempre para `dev`.
