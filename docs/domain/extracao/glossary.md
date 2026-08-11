# Glossário — contexto Extração (src)

Owner: Osvaldo Andrade (mantenedor) · Última revisão: 2026-08-11

| Termo | Definição | Exemplo | Sinônimos descartados |
|---|---|---|---|
| Fonte | Obra textual pinada em `sources/manifest.json` com SHA-256, licença e escopo de uso | OSHB Gen.xml | "corpus", "base" |
| Manifest | Contrato de fontes (`api/manifest.schema.json`); única porta de entrada de dados externos | `sources/manifest.json` | "lock file" |
| Packet | JSON por perícope gerado por `bvsrc`: original palavra a palavra + morfologia + controles | `pipeline/packets/gen-001-001-005.json` | "bundle", "input" |
| Palavra | Segmento anotado do texto-fonte (surface + lemma + morfologia) | בְּרֵאשִׁ֖ית `b/7225` `HR/Ncfsa` | "token" |
| Lemma | Código de lema OSHB (Strong estendido) | `1254 a` | "strong" |
| Controle | Tradução PD/CC-BY embutida no packet só para detecção de divergência | WEB, KJV, Bíblia Livre | "referência" |

Invariantes: packet só referencia fontes presentes no manifest; extração nunca
altera texto (transcrição programática, jamais manual); `bvsrc` é determinístico
(mesma fonte → mesmo packet byte a byte).
