# PLAN — Bootstrap Bereia Version (BV) + piloto Gênesis 1:1–5

Status: ACTIVE · Tier: **T3** · Data: 2026-08-11 · Autor: pipeline BV (sessão Claude Code)

## Goal

Criar o repositório auditável da **Bereia Version (BV)** — tradução bíblica em
português brasileiro derivada diretamente de WLC/OSHB (AT) e OpenGNT (NT) — com:
fontes pinadas por hash, pipeline multiagente de consenso versionado, ferramentas
Go de extração e QA de similaridade, e um **piloto executado de ponta a ponta em
Gênesis 1:1–5** produzindo registros por versículo no schema definido.

## Non-goals

- Traduzir além de Gn 1:1–5 nesta iteração.
- Pipeline programático chamando a API Anthropic (fase futura; esta iteração usa
  orquestração multiagente da sessão, com prompts versionados em arquivo).
- Site/publicação, decisão final de licença da BV (opções documentadas, decisão fica aberta).
- Baixar/normalizar o cânon completo das fontes (apenas o necessário + pin de versão).

## Constraints

1. Nenhum texto de tradução protegida (ARA/NVI/NAA/NTLH) é armazenado no repositório.
2. Toda escolha de tradução deve ser justificável pelo hebraico/grego (auditável até WLC/OpenGNT).
3. Fontes pinadas: URL + commit SHA (quando GitHub) + SHA-256 do arquivo em `sources/manifest.json`.
4. Determinismo por artefatos: prompts, regras, léxico e decisões versionados; não-determinismo
   do sampler documentado como limitação; versículo aprovado só muda com diff + nova revisão.
5. Ferramentas Go **sem dependências de terceiros** (stdlib apenas).
6. Idiomas: código/comentários em inglês; artefatos editoriais (regras, prompts, decisões,
   registros de versículo) em pt-BR, pois são o produto editorial auditado por revisores brasileiros.

## Acceptance criteria

- [ ] `sources/manifest.json` com ≥ 4 fontes pinadas (OSHB, OpenGNT, WEB, KJV; +1 controle pt PD se disponível).
- [ ] `cmd/bvsrc` extrai Gn 1:1–5 do XML OSIS do OSHB com morfologia por palavra; saída bate com o texto conhecido.
- [ ] `cmd/bvqa` calcula similaridade n-grama e maior sequência comum entre BV e controles pt armazenados.
- [ ] `go build ./... && go vet ./... && go test ./...` verdes; cobertura ≥ 90% nas linhas alteradas dos pacotes `internal/`.
- [ ] Piloto Gn 1:1–5: 4 agentes independentes → consolidação → rodada de refutação → registro final por versículo
      validado contra `api/verse-record.schema.json`, status `REVIEW`.
- [ ] QA de contaminação executado (mecânico vs. controles PD + qualitativo vs. protegidas, sem armazená-las).
- [ ] ADR-0001 em `docs/adr/`; PIPELINE.md com FSM de status e diagrama; commits convencionais.

## Layout proposto

```
bereia-bible/
├── README.md                     # visão geral, como auditar
├── PLAN.md                       # este arquivo + ledger
├── go.mod                        # module bereia.org/bible (stdlib only)
├── cmd/bvsrc/                    # extração OSIS→JSON (packets por versículo)
├── cmd/bvqa/                     # QA de similaridade (n-grams, LCS)
├── internal/oshb/                # parser OSIS/WLC com morfologia
├── internal/similarity/          # n-gram + longest common word sequence
├── sources/                      # fontes baixadas e pinadas (manifest.json)
│   ├── manifest.json
│   ├── oshb/  opengnt/  web/  kjv/  pt-pd/
├── pipeline/
│   ├── PIPELINE.md               # processo v1.0.0: agentes, consenso, FSM, determinismo
│   ├── prompts/                  # agente1..4, consolidador, refutador, finalizador (versionados)
│   ├── rules/EDITORIAL.md        # estilo pt-BR, nomes divinos, pontuação
│   ├── rules/TEOLOGIA.md         # guardrails: neutralidade > viés; quando lean reformado é legítimo
│   └── schema/verse-record.schema.json
├── lexicon/lexicon.json          # decisões terminológicas persistidas (versionado)
├── decisions/DECISOES.md         # log de decisões de tradução transversais
├── translation/01-gn/            # registros por capítulo/versículo (JSON) + render MD
├── pipeline/packets/                # packets de entrada por unidade (gerados por bvsrc; commitados p/ auditoria)
└── docs/adr/ docs/LICENSING.md
```

## Design choices (para validação dos consultores)

1. **Unidade de tradução = perícope** (não versículo isolado): piloto = Gn 1:1–5 (dia um).
2. **IDs OSIS** (`Gen.1.1`) como chave canônica; nomes pt-BR na apresentação.
3. **Consenso**: 4 propostas independentes → consolidação com tabela de divergências e
   justificativa lexical → refutação adversarial pelos 4 papéis → adjudicação por evidência
   (sem votação) → N ≤ 3 ciclos → registro final `REVIEW`. `APPROVED` exige ratificação humana.
4. **FSM de status**: DRAFT → REVIEW → APPROVED; APPROVED → REVIEW somente via diff + justificativa
   + novo ciclo completo (transições ilegais rejeitadas; tabela em PIPELINE.md).
5. **QA de contaminação**: mecânico (`bvqa`, n-gram 3–5 + LCS) somente contra traduções PD
   armazenadas (pt); qualitativo contra ARA/NVI/NAA/NTLH via agente (conhecimento de modelo,
   citação mínima, nada persistido dessas versões).
6. **Licenças das fontes**: OSHB CC BY 4.0 (ok). OpenGNT CC BY-NC-SA 4.0 → **flag**: implicação
   sobre licença do NT da BV documentada em LICENSING.md; decisão adiada para a fase NT
   (alternativas: Nestle 1904 PD / SBLGNT). Piloto é AT, não bloqueia.
7. **Go stdlib only**; parser OSIS mínimo (somente o que Gn exige, com testes); sem goroutines
   além do main linear (sem primitivas de concorrência).

## Test plan

- Table-driven tests: `internal/oshb` (parse de fixture real de Gn 1 com maqqef, sof pasuq,
  ketiv/qere ausente → casos negativos), `internal/similarity` (n-grams, LCS, normalização pt).
- Validação do schema dos registros do piloto (estrutural, via saída tipada do workflow).
- Verificação manual do texto extraído vs. WLC impresso (Gn 1:1–5).

## Verification commands

```
gofmt -l . && go build ./... && go vet ./... && go test ./... -cover
(cd sources && shasum -a 256 -c manifest.sha256)
./bin/bvsrc -book Gen -from 1:1 -to 1:5 | diff - pipeline/packets/gen-001-001-005.json
./bin/bvqa -bv translation/01-gn/001.md -controls sources/pt-pd/
```

## Rollback

Repositório local recém-criado, sem efeitos externos: `git reset --hard <sha>` ou
remoção do diretório. Nenhum dado de produção, nenhum serviço, nenhuma publicação.

## Riscos

| Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|
| Fonte indisponível/URL mudou | média | médio | fallbacks (getBible API, mirrors GitHub); manifest registra o que faltou |
| Licença OpenGNT (NC-SA) restringe NT | alta | alto (fase NT) | flag em LICENSING.md + ADR; alternativas PD listadas; decisão do usuário |
| Contaminação de redação protegida | baixa | alto | processo fonte-primeiro + QA duplo (mecânico PD, qualitativo protegidas) |
| Não-determinismo do sampler | certa | médio | decisões persistidas (léxico/decisions) são a camada determinística; mudanças só via diff |
| Transcrição hebraica incorreta | baixa | alto | extração programática do XML pinado, nunca digitação manual |

---

## code-workflow ledger

- classification: tier=T3, signals=[files≈35>20→T3, authored-LOC≈2000>800→T3;
  risco: API=none, persistence=local-new-files, network=fetch-only, security=none,
  blast-radius=self, rollback=trivial → todos T0], time=2026-08-11T00:00Z
- auto-promotes: nenhum aplicável (sem migrations/auth/CI de serviço; go.mod novo sem deps de terceiros)
- etapas T3 **não aplicáveis** (sem serviço em runtime): migrator (não há dado vivo a migrar),
  helmsman/beacon/release-captain/chaos/signaler/sentry/topologist/oracle/ledger/usher/pathfinder
  (sem serviço, sem UI, sem concorrência, sem alertas). steward aplicado inline (FSM de status
  em PIPELINE.md). cartographer aplicado inline (diagrama Mermaid em PIPELINE.md).
- consult 1: architect — NEEDS-INFO→resolvido: schema movido p/ `api/`, packets p/ `pipeline/packets/`,
  `.golangci.yml` c/ depguard, `docs/architecture/context-map.md`, PIPELINE.md declara perícope=agregado
  (ID = faixa OSIS `Gen.1.1-5`), verso=entidade, consistência inter-perícope eventual via léxico+diretrizes.
  `internal/oshb` mantido (parser é específico do OSHB; NT usa CSV, não OSIS) — registrado no ADR.
- consult 2: curator — NEEDS-INFO→resolvido: glossários em `docs/domain/{extracao,editorial,governanca,qa}/`,
  invariantes do léxico em `lexicon/lexicon.schema.json` + `internal/lexicon` validado em `go test`,
  colisão do termo "decisão" resolvida (LexiconEntry / Diretriz Editorial ER- / Adjudicação por versículo),
  NOMES-DIVINOS.md separado com SemVer, vocabulário comando/evento em PIPELINE.md, owner em toda entrada.
- consult 3: herald — NEEDS-INFO→resolvido: política file-per-major ($id …/verse-record/1, pattern ^1\.),
  `api/manifest.schema.json`, exemplos válido+inválido em `api/examples/` validados em `go test`,
  rename ASCII `objecoes_nao_resolvidas`, horizonte de compatibilidade N-1, tabela de mapeamento no ADR.
- consult 4: bastion — **GO** c/ follow-ups: LICENSING por fonte (SPDX+atribuição+implicação), NOTICE.md,
  quarentena OpenGNT c/ README, higiene de download documentada, seção de risco residual de contaminação.
- consult 5: quartermaster — **GO** c/ bloqueios aplicados: manifest estendido (owner, SPDX, mirrors,
  usage_scope, retirement_condition…), allowlist de licenças, carve-out OpenGNT no ADR-0001 (agora),
  guarda mecânica zero-dep (`test ! -f go.sum` + depguard), docs/dependencies.md.
- consult 6: forge — **GO**: thresholds no .golangci.yml, schema do packet fixado antes das struct tags,
  fuzz em ParseVerse e Normalize (guard-rail #10).
- gate ADR: ADR-0001 em docs/adr/ (bootstrap: fontes, quarentena OpenGNT, agregado perícope,
  hexagonal-não-aplicado, política de schema, resolução terminológica, zero-dep)
- DoD progress: em execução; validação final na seção de verificação da resposta
