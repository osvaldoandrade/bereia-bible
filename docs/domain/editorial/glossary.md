# Glossário — contexto Editorial

Owner: Osvaldo Andrade (mantenedor) · Última revisão: 2026-08-11

| Termo | Definição | Exemplo | Sinônimos descartados |
|---|---|---|---|
| Perícope | **Agregado**: unidade literária, fronteira transacional das decisões editoriais; ID = faixa OSIS | `Gen.1.1-5` | "trecho", "passagem" |
| Versículo | **Entidade** dentro da perícope; ID OSIS; materializa-se como Registro | `Gen.1.2` | — |
| Registro (VerseRecord) | Artefato JSON por versículo conforme `api/verse-record.schema.json` | `translation/01-gn/001/Gen.1.1.json` | "output", "resultado" |
| Proposta (Rendering) | Tradução independente produzida por um dos 4 agentes | — | "versão", "draft" |
| Consolidação | Comparação palavra a palavra das 4 propostas contra a fonte, com resolução por evidência | — | "merge" |
| Refutação | Ataque adversarial à consolidação por uma das 4 lentes | — | "review" |
| Adjudicação | Decisão de tradução por versículo, com alternativas rejeitadas e evidência (`decisoes[]` no Registro) | "escuridão vs trevas" | **"decisão" (ambíguo)** |
| LexiconEntry | Entrada terminológica vinculante em `lexicon/lexicon.json` | H430 → "Deus" | "glosa global" |
| Ambiguidade preservada | Ambiguidade real do original mantida deliberadamente no texto BV | Gn 1:2 rûach | — |

Comandos (imperativo) → Eventos (particípio): ProporTraducao→TraducaoProposta;
ConsolidarPropostas→PropostasConsolidadas; RefutarConsolidacao→ConsolidacaoRefutada;
AdjudicarDivergencia→DivergenciaAdjudicada; SubmeterParaRevisao→SubmetidoParaRevisao;
RatificarRegistro→RegistroRatificado; SupersederLexiconEntry→LexiconEntrySuperseded.

Invariantes do agregado Perícope: terminologia interna consistente (mesmo lexema
→ mesma glosa dentro da perícope, salvo adjudicação registrada); nenhum registro
sai da perícope sem ciclo completo; consistência com outras perícopes é eventual,
propagada SOMENTE via LexiconEntry e Diretriz ER.
