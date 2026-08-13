# Mapa de contextos — bereia-bible

Data: 2026-08-11 · Fonte: ADR-0001 · Escopo: repositório completo (Go + conteúdo)

```mermaid
flowchart LR
    subgraph EXT[Extração — src]
      SRC[sources/ + manifest]
      OSHB[internal/oshb ACL p/ OSIS-WLC]
      N1904[internal/nestle1904 ACL p/ CSV grego]
      BVSRC[cmd/bvsrc]
    end
    subgraph EDI[Editorial]
      PKT[pipeline/packets/]
      PIPE[pipeline/ prompts+rules]
      LEX[lexicon/]
      TR[translation/]
    end
    subgraph GOV[Governança]
      ER[decisions/DECISOES.md ER-*]
      ADR[docs/adr/]
    end
    subgraph QA[QA]
      SIM[internal/similarity]
      BVQA[cmd/bvqa]
      CHK[internal/schemavalidate + cmd/bvcheck]
    end
    SRC --> OSHB --> BVSRC -->|file handoff| PKT
    SRC --> N1904 --> BVSRC
    PKT --> PIPE -->|registros| TR
    LEX <--> PIPE
    ER -->|diretrizes vinculantes| PIPE
    TR -->|file handoff| BVQA
    SIM --> BVQA
    TR --> CHK
    ER -->|ratificação REVIEW→APPROVED| TR
```

## Contextos e integração

| Contexto | Conteúdo | Vocabulário próprio | Integração |
|---|---|---|---|
| **Extração** (`src`) | `sources/`, `internal/oshb`, `internal/nestle1904`, `cmd/bvsrc` | fonte, manifest, packet, palavra, lemma, morfologia | → Editorial via arquivo (packet JSON) |
| **Editorial** | `pipeline/`, `lexicon/`, `translation/` | perícope (agregado), versículo (entidade), proposta, consolidação, refutação, adjudicação, LexiconEntry | ← packets; → registros; lê diretrizes ER |
| **Governança** | `decisions/`, `docs/adr/` | Diretriz Editorial (ER-*), ADR, ratificação | vincula Editorial; registra ratificações |
| **QA** | `internal/similarity`, `internal/schemavalidate`, `cmd/bvqa`, `cmd/bvcheck` | similaridade, n-gram, LCS, contaminação, conformidade de schema | ← registros/controles via arquivo |

Todas as integrações são **file handoff** (sem rede, sem RPC). Owner de todos os
contextos: Osvaldo Andrade (mantenedor). Glossários: `docs/domain/<contexto>/glossary.md`.

## Decisões estruturais (registradas em ADR-0001)

- Hexagonal porta/adaptador **não aplicado**: não há serviço em runtime; `cmd/` é a
  porta de condução; arquivos são o lado conduzido. `internal/` plano.
- `internal/oshb` e `internal/nestle1904` são ACLs distintas: OSIS-WLC para o AT,
  CSV grego para o NT. Nenhum parser genérico mistura as duas morfologias.
- Perícope = agregado (fronteira transacional editorial); versículo = entidade
  (ID OSIS); ID do agregado = faixa OSIS (`Gen.1.1-5`). Consistência entre
  perícopes é **eventual**, propagada exclusivamente via `lexicon/` e `decisions/`.
- `internal/oshb` e `internal/similarity` não se importam mutuamente (depguard).
