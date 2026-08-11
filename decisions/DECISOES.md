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

## ER-0008 — Ordem verbo-sujeito nos wayyiqtol narrativos

- Data: 2026-08-11 · Escopo: editorial global (origem: verificação da perícope Gen.1.1-5, P2) · Status: ATIVA
- Decisão: a inversão verbo-sujeito do hebraico é preservada apenas na fórmula de
  introdução de discurso direto ("E disse Deus:"); nos demais wayyiqtol narrativos,
  o português segue a ordem sujeito-verbo ("E Deus viu", "E Deus separou").
- Alternativas rejeitadas: V-S uniforme (arcaizante fora da fórmula de fala);
  S-V uniforme (apaga a fórmula introdutória, marca estilística do texto).
- Justificativa: naturalidade pt-BR com preservação da marca formular; a tradução
  literal de cada registro conserva a ordem original para auditoria.

## ER-0009 — Nomeação divina de entidades: maiúscula, sem aspas

- Data: 2026-08-11 · Escopo: editorial global (origem: verificação da perícope Gen.1.1-5, P5) · Status: ATIVA
- Decisão: em fórmulas de nomeação (קרא ל), o nome recebe maiúscula e não recebe
  aspas: "chamou a luz de Dia". Reusar em Gn 1:8, 1:10 e paralelos.
- Alternativas rejeitadas: aspas ("chamou a luz de 'Dia'") — ruído tipográfico;
  minúscula — perde o ato de nomeação.

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
