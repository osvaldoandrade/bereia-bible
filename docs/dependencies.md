# Política de dependências

## Código Go

**Zero dependências de terceiros.** Somente a biblioteca padrão.

- Guarda mecânica: `test ! -f go.sum` no alvo `make verify` (com zero deps o Go
  não gera `go.sum`; a existência do arquivo denuncia a regressão) + `depguard`
  no `.golangci.yml`.
- Adicionar uma dependência exige: ADR (ADR_TRIGGERS #1), consulta quartermaster
  + bastion, licença na allowlist de código (não confundir com a allowlist de
  fontes de dados).

## Audio Production Python runtime

Audio Production keeps its Python 3.12 runtime separate from the zero-dependency
Go code. `requirements.lock` pins every resolved package and hash for the local
macOS arm64 environment; ADR-0006 records the adoption decision.

| Direct dependency | Version | License | Owner | Reason | Last reviewed | Removal condition |
|---|---:|---|---|---|---|---|
| `mlx-audio` | 0.5.3 | MIT | Osvaldo Andrade | Run Chatterbox Multilingual through Apple MLX/Metal without CUDA or CPU inference. | 2026-09-09 | Remove with the local audio-production context. |

The runtime downloads but does not redistribute
`mlx-community/chatterbox-fp16@4923fcca09086356aeab5191a2348c5a17a23694`
(Apache-2.0) and
`mlx-community/S3TokenizerV2@e0c9886f0e1c35ae85b1f27277416fb19fc72bec`.
The tokenizer conversion omits a license field; its declared base model,
`FunAudioLLM/CosyVoice2-0.5B`, declares Apache-2.0. Publishing either weight set
requires a new license review.

System tools `codex` and FFmpeg remain operator-installed executables rather
than Python dependencies. The CLI verifies their presence and versions.

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
