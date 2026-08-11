# Política de dependências

## Código Go

**Zero dependências de terceiros.** Somente a biblioteca padrão.

- Guarda mecânica: `test ! -f go.sum` no alvo `make verify` (com zero deps o Go
  não gera `go.sum`; a existência do arquivo denuncia a regressão) + `depguard`
  no `.golangci.yml`.
- Adicionar uma dependência exige: ADR (ADR_TRIGGERS #1), consulta quartermaster
  + bastion, licença na allowlist de código (não confundir com a allowlist de
  fontes de dados).

## Fontes de dados (dependências de conteúdo)

Registradas em `sources/manifest.json` (contrato: `api/manifest.schema.json`),
cada uma com: URL canônica https, mirrors, commit git quando aplicável, SHA-256,
tamanho, SPDX, atribuição, **escopo de uso** (`usage_scope`), condição de
retirada, owner e data de obtenção.

Escopos válidos e allowlist: `docs/licenses/allowlist.txt`. Fonte nova sem os
17 campos do schema não entra (validação em `go test` via `internal/schemavalidate`).

## Auditoria periódica (F-0007)

Trimestral: re-checar URL canônica, comparar HEAD upstream vs. commit pinado,
verificar mudança de licença upstream, testar mirrors. Registrar resultado em
`decisions/DECISOES.md`.
