# Glossário — contexto Governança

Owner: Osvaldo Andrade (mantenedor) · Última revisão: 2026-08-11

| Termo | Definição | Exemplo | Sinônimos descartados |
|---|---|---|---|
| Diretriz Editorial (ER) | Regra transversal vinculante registrada em `decisions/DECISOES.md`, ID `ER-NNNN` | ER-0002 nomes divinos | **"decisão" (ambíguo)**, "policy" |
| ADR | Decisão arquitetural do repositório, em `docs/adr/` | ADR-0001 | — |
| Ratificação | Ato humano registrado que promove Registro REVIEW → APPROVED | "ER-0010 ratifica Gn 1:1-5" | "aprovação automática" |
| Follow-up (F) | Pendência numerada com dono, em DECISOES.md | F-0002 licença da BV | "TODO" |
| Quarentena | Escopo `analysis-only-quarantined` de fonte com licença incompatível | OpenGNT; não participa da cadeia produtiva do NT | — |

Invariantes: DECISOES.md é apend-only; ER nunca é editada retroativamente
(supersede com nova ER); toda ratificação nomeia o ratificador e a data; ADR
segue Contexto/Decisão/Consequências/Alternativas/Rollback.
