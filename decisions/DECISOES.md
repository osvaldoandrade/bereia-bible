# Diretrizes Editoriais (ER) — Bereia Version

Log apend-only do contexto Governança. Cada **Diretriz Editorial** (ER-NNNN) é uma
regra transversal vinculante: escopo, decisão, alternativas, justificativa, status.
Ratificações humanas (REVIEW → APPROVED) também são registradas aqui.
Terminologia: ER ≠ Adjudicação (por versículo, no registro) ≠ LexiconEntry (léxico).
Ver `docs/domain/governanca/glossary.md`.

---

## ER-0001 — Unidade de tradução = perícope (agregado)

- Data: 2026-08-11 · Escopo: pipeline · Status: ATIVA
- Decisão: perícope é o agregado editorial (ID = faixa OSIS, ex.: `Gen.1.1-5`);
  versículo é a entidade; consistência entre perícopes é eventual, via léxico + ER.
- Alternativas rejeitadas: versículo isolado (perde coesão intra-perícope);
  capítulo inteiro (transação editorial longa demais).
- Justificativa: consistência terminológica e sintática exige contexto literário mínimo.

## ER-0002 — Nomes divinos

- Data: 2026-08-11 · Escopo: léxico global · Status: ATIVA
- Decisão: política versionada em `pipeline/rules/NOMES-DIVINOS.md` v1.0.0
  (YHWH → SENHOR; Elohim → Deus; Adonai → Senhor; Adonai YHWH → Senhor DEUS).
- Alternativas rejeitadas: "Javé"/"Yahweh"; "o Eterno" (ver arquivo da política).
- Justificativa: convenção consolidada, auditável via lemma no registro.

## ER-0003 — Segunda pessoa (PROVISÓRIA)

- Data: 2026-08-11 · Escopo: editorial global · Status: PROVISÓRIA (revisar ao chegar a diálogo/Salmos)
- Decisão: você/vocês no discurso comum; tu em oração dirigida a Deus.
- Alternativas rejeitadas: tu/vós uniforme (arcaizante); você uniforme (choca uso litúrgico em oração).
- Justificativa: contemporaneidade preservando distinção de número (você × vocês).

## ER-0004 — Discurso direto com aspas duplas

- Data: 2026-08-11 · Escopo: editorial global · Status: ATIVA
- Decisão: dois-pontos + aspas duplas curvas; aspas simples para citação interna.
- Alternativas rejeitadas: travessão (quebra em diálogos intercalados com "disse X");
  ausência de marcação (ambíguo para TTS).

## ER-0005 — Controle pt-BR: Bíblia Livre substitui Almeida 1911

- Data: 2026-08-11 · Escopo: fontes/QA · Status: ATIVA (follow-ups F-0001, F-0006)
- Decisão: Bíblia Livre (linhagem Almeida 1819/TR) como controle histórico pt armazenado.
- Justificativa: Almeida 1911 e Tradução Brasileira 1917 não localizadas em fonte
  digital aberta confiável (getBible, eBible.org) em 2026-08-11.

## ER-0006 — Palavras supridas sem itálico

- Data: 2026-08-11 · Escopo: editorial global · Status: ATIVA
- Decisão: sem itálico; supridas listadas em `palavras_supridas` no registro.
- Alternativas rejeitadas: itálico (ruído tipográfico, ilegível em TTS).
- Justificativa: o registro estruturado dá transparência com mais precisão.

## ER-0007 — Idiomas dos artefatos

- Data: 2026-08-11 · Escopo: repositório · Status: ATIVA
- Decisão: código/comentários/commits em inglês; artefatos editoriais em pt-BR
  (campos JSON em pt-BR ASCII-only).
- Justificativa: artefatos editoriais são o produto auditado por revisores lusófonos.

---

## Follow-ups abertos

- F-0001: obter Almeida 1911 / Tradução Brasileira 1917 digitalizada e pinar no manifest. Dono: mantenedor.
- F-0002: decidir licença da BV (CC BY-SA 4.0 × CC BY 4.0). Dono: mantenedor.
- F-0003: fase NT — resolver quarentena OpenGNT (ADR-0001 §2); candidata PD: Nestle 1904. Dono: mantenedor.
- F-0004: pipeline programático (API Anthropic, temperatura 0) substituindo orquestração de sessão. Dono: mantenedor.
- F-0005: mutation testing das ferramentas Go quando tooling disponível. Dono: mantenedor.
- F-0006: verificar licença exata da Bíblia Livre na página eBible/da própria BLIVRE. Dono: mantenedor.
- F-0007: auditoria trimestral do manifest de fontes (docs/dependencies.md). Dono: mantenedor.
- F-0008: instalar hook local de secret-scan (gitleaks/git-secrets). Dono: mantenedor.
