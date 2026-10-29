# A-01 — Log obrigatório da partida

- **Dono:** Dev A — João
- **Branch:** `feature/registro-log`
- **Implementa com:** Claude Code
- **Testes e review com:** Codex
- **Prazo:** 29/10
- **Depende de:** nada

## Objetivo
Gravar em `logs/` um arquivo `.log` por partida com uma linha por lance, contendo tudo o que a organização exige.

## Arquivos permitidos
- `src/registro/log.py`
- `tests/test_log.py`

## Contrato
- `LogPartida(caminho: str)` cria o arquivo (e a pasta, se faltar) e escreve um cabeçalho com data/hora. Se o arquivo já existir (retomada), **acrescenta** em vez de sobrescrever.
- `LogPartida.registrar(registro: RegistroLance) -> None` escreve uma linha e faz `flush` + `os.fsync` imediatamente.
- Formato da linha (uma por lance, UTF-8):
  `lance=12 cor=brancas uci=e2e4 profundidade=22 nos=1534200 avaliacao=+0.35 pv=e2e4 e7e5 g1f3 tempo=12.40s origem=motor`
- Lances do adversário também são registrados (`origem=adversario`, profundidade e nós = 0, PV vazia).
- `registrar` nunca lança exceção para o chamador: em caso de erro de escrita, tenta de novo uma vez e depois escreve o erro em `stderr`.

## Critérios de aceite
- [ ] Todos os campos do FAQ aparecem: número do lance, cor, UCI, profundidade, nós, avaliação, PV e tempo gasto
- [ ] Retomada acrescenta ao arquivo existente
- [ ] Linha gravada mesmo se o processo morrer logo depois (flush + fsync)
- [ ] `pytest` passa

## Testes a escrever (Codex)
- Linha formatada com todos os campos, incluindo avaliação de mate (`#3`, `#-2`)
- PV vazia e lance do adversário
- Reabrir o mesmo caminho acrescenta, não apaga
- Caracteres acentuados no cabeçalho lidos corretamente com UTF-8

## Fora do escopo
- Decidir o nome do arquivo da partida (fica no laço principal, card A-02)
