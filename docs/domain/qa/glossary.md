# Glossário — contexto QA

Owner: Osvaldo Andrade (mantenedor) · Última revisão: 2026-08-11

| Termo | Definição | Exemplo | Sinônimos descartados |
|---|---|---|---|
| Similaridade n-gram | Fração de n-grams de palavras (3–5) do texto BV presentes num controle | 0.18 vs Livre | — |
| LCS | Maior subsequência comum de palavras entre BV e controle | 7 palavras | "overlap" |
| Contaminação | Coincidência extensa com tradução existente **não exigida** pelo original | — | "plágio" (juízo jurídico, não técnico) |
| Coincidência inevitável | Redação idêntica porque é a tradução natural do original; mantida e anotada | "E disse Deus" | — |
| Conformidade de schema | Registro validado contra `api/verse-record.schema.json` por `bvcheck` | exit 0 | "lint" |
| Controle armazenado | Tradução PD/CC-BY em `sources/` usada no QA mecânico | Bíblia Livre | — |
| QA qualitativo | Comparação por agente contra traduções protegidas SEM armazená-las | vs ARA/NVI/NAA/NTLH | — |

Invariantes: QA mecânico roda apenas sobre controles armazenados (nunca sobre
texto protegido); limiar de alerta é sinal para reavaliação fonte-primeiro, nunca
gatilho de reescrita automática; todo relatório de QA é commitado junto do registro.
