# Bereia Version (BV) — Bíblia em português brasileiro auditável

Tradução bíblica pt-BR do [Bereia.org](https://bereia.org), derivada diretamente
dos textos-fonte — **WLC/OSHB** (AT) e **Nestle 1904** (NT) — com cada
decisão de tradução rastreável até a fonte pinada. Nenhuma redação deriva de
traduções protegidas (ARA/NVI/NAA/NTLH).

## Como auditar um versículo

1. Abra o registro: `translation/01-gn/001/Gen.1.1.json`
   (contrato: `api/verse-record.schema.json`).
2. `fontes.texto_fonte` aponta a fonte + commit; `fontes.manifest_sha256` pina o
   manifesto usado.
3. O packet de entrada (original palavra a palavra + morfologia) está em
   `pipeline/packets/` e é regenerável com `bvsrc` a partir de `sources/`.
4. `sources/manifest.json` liga cada arquivo a URL upstream, commit git e SHA-256:
   `cd sources && shasum -a 256 -c manifest.sha256`.
5. Adjudicações, alternativas rejeitadas, variantes e ambiguidades preservadas
   estão no próprio registro; diretrizes transversais em `decisions/DECISOES.md`;
   terminologia em `lexicon/lexicon.json`.

## Estrutura

```
api/          contratos JSON Schema (verse-record, manifest) + exemplos executáveis
sources/      fontes pinadas (OSHB/Nestle 1904; OpenGNT em quarentena)
pipeline/     processo multiagente: PIPELINE.md, prompts/, rules/, packets/
lexicon/      terminologia vinculante (LexiconEntry)
decisions/    diretrizes editoriais ER-* e ratificações (Governança)
translation/  registros por versículo (produto)
cmd/ internal/  ferramentas Go (stdlib only): bvsrc, bvqa, bvcheck
docs/         ADRs, licenciamento, mapa de contextos, glossários
```

## Processo (resumo)

Quatro agentes independentes (línguas originais, tradutor "cego", revisor
linguístico, revisor exegético) → consolidação com divergências palavra a palavra
→ refutação adversarial → adjudicação por evidência (votação é proibida) →
registro `REVIEW` → QA de contaminação (n-gram/LCS vs. controles PD + qualitativo
vs. protegidas sem armazená-las) → ratificação humana → `APPROVED`.
Detalhes: `pipeline/PIPELINE.md`. Guardrails teológicos: `pipeline/rules/TEOLOGIA.md`
(viés confessional nunca controla a tradução; desempates registrados).

## Verificação

```
make verify   # gofmt + go build + go vet + go test -cover + zero-dep guard + checksums
```

## Status

- Programa Bíblia completa em andamento; cobertura atual em `translation/PROGRESS.md`.
- Autoridades textuais pinadas: OSHB (AT) e Nestle 1904 PD/CC0 (NT).
- Licença do produto: em decisão (F-0002); fontes: `docs/LICENSING.md` + `NOTICE.md`.
