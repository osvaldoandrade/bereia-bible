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

- Data: 2026-08-11 · Escopo: editorial global (origem: verificação da perícope Gen.1.1-5, P2) · Status: **SUPERSEDIDA por ER-0011**
- Decisão: a inversão verbo-sujeito do hebraico é preservada apenas na fórmula de
  introdução de discurso direto ("E disse Deus:"); nos demais wayyiqtol narrativos,
  o português segue a ordem sujeito-verbo ("E Deus viu", "E Deus separou").
- Alternativas rejeitadas: V-S uniforme (arcaizante fora da fórmula de fala);
  S-V uniforme (apaga a fórmula introdutória, marca estilística do texto).
- Justificativa: naturalidade pt-BR com preservação da marca formular; a tradução
  literal de cada registro conserva a ordem original para auditoria.

## ER-0009 — Nomeação divina de entidades: maiúscula, sem aspas

- Data: 2026-08-11 · Escopo: editorial global (origem: verificação da perícope Gen.1.1-5, P5) · Status: **SUPERSEDIDA por ER-0012**
- Decisão: em fórmulas de nomeação (קרא ל), o nome recebe maiúscula e não recebe
  aspas: "chamou a luz de Dia". Reusar em Gn 1:8, 1:10 e paralelos.
- Alternativas rejeitadas: aspas ("chamou a luz de 'Dia'") — ruído tipográfico;
  minúscula — perde o ato de nomeação.

## ER-0010 — Re-pinagem de `fontes` em ciclo de reparo

- Data: 2026-08-11 · Escopo: pipeline (PIPELINE.md v1.0.1) · Status: ATIVA
- Decisão: todo ciclo de reparo/consistência re-pina todos os campos de `fontes`
  do registro para as versões efetivamente lidas no ciclo; preservar pin antigo é
  defeito de dados. Origem: bloqueador 3 da revisão inquisitor (Gen.1.4 pinava
  léxico 0.2.0 enquanto sua adjudicação citava a entrada H2822 do v0.3.0;
  corrigido com registro em qa/reports/gen-001-001-005.consistencia-resolucao.json).
- Também em 1.0.1: comandos de reprodução do PIPELINE corrigidos (`-pericope`,
  `-records`) e alvo `make packets-blind` documentado (bloqueadores 1–2).

## ER-0011 — Ordem S-V uniforme (supersede ER-0008)

- Data: 2026-08-11 · Escopo: editorial global · Origem: **revisão do mantenedor** · Status: ATIVA
- Decisão: ordem sujeito-verbo em todos os wayyiqtol do texto publicado, inclusive na
  fórmula de fala ("E Deus disse:"). A ordem V-S do hebraico permanece integralmente
  na `traducao_literal` de cada registro.
- Alternativas rejeitadas: exceção V-S na fórmula de fala (ER-0008) — o mantenedor
  avaliou que soa traduzido; a marca formular sobrevive na literal.

## ER-0012 — Nomeação em minúsculas (supersede ER-0009)

- Data: 2026-08-11 · Escopo: editorial global · Origem: **revisão do mantenedor** · Status: ATIVA
- Decisão: em fórmulas de nomeação (קרא ל), o nome vai em minúscula e sem aspas:
  "chamou a luz de dia". Maiúscula reservada a nomes próprios plenos
  (antropônimos, topônimos).
- Alternativas rejeitadas: maiúscula tipográfica (ER-0009) — atribui estatuto de
  nome próprio que o hebraico (sem recurso gráfico) não codifica.

## ER-0013 — Doutrina do calque: literal preserva, publicado normaliza

- Data: 2026-08-11 · Escopo: editorial global · Origem: **revisão do mantenedor**
  ("a tradução literal pode mantê-los; a BV publicada não precisa manter todos") · Status: ATIVA
- Decisão: calques estruturais do hebraico são SEMPRE preservados na
  `traducao_literal`; no texto publicado, são normalizados quando soarem artificiais,
  com adjudicação registrada por versículo. Cobertura inicial:
  1. **Waw inicial de versículo**: waw disjuntivo circunstancial (ex.: Gn 1:2
     וְהָאָרֶץ) não é vertido; wayyiqtol inicial é vertido "E" apenas quando a
     sequência discursiva o pedir (ex.: Gn 1:3 retomando a linha narrativa).
  2. **Repetição formular de sujeito** (ex.: אֱלֹהִים 2× em Gn 1:4): condensável
     quando redundante em português.
  3. **Quiasmo de ordem** (ex.: Gn 1:5 וְלַחֹשֶׁךְ fronteado): normalizável para
     paralelismo direto no publicado.
- Justificativa: prioridade 8 do goal (português compreensível) sem perda de
  auditoria — a camada literal carrega o calque; o registro documenta cada normalização.

## ER-0014 — RATIFICAÇÃO: Gênesis 1:1–5 → APPROVED

- Data: 2026-08-11 · Ratificador: **Osvaldo Andrade (mantenedor Bereia.org)** · Status: EXECUTADA
- Ato: os cinco registros da perícope `Gen.1.1-5` passam de REVIEW a **APPROVED**, com o
  texto revisado pelo mantenedor e processado pelo ciclo de ratificação
  (4 aplicadores + 4 refutadores de fidelidade, todos APROVA com 0 objeções +
  verificação de consistência da perícope aprovada em disco).
- Texto ratificado: "No princípio, Deus criou os céus e a terra. A terra era desolada
  e vazia, e havia escuridão sobre a face do abismo, e o Espírito de Deus pairava sobre
  a face das águas. E Deus disse: “Haja luz”; e houve luz. Deus viu que a luz era boa
  e separou a luz da escuridão. Deus chamou a luz de dia e chamou a escuridão de noite.
  E houve tarde e houve manhã: dia um."
- Decisões discutidas e fechadas pelo mantenedor: (a) תֹהוּ וָבֹהוּ → "desolada e vazia"
  (adjetival no publicado; substantivos na literal e no léxico); (b) יוֹם אֶחָד → "dia um"
  (cardinal preservado; assimetria com os ordinais dos dias 2–6).
- Diretrizes aplicadas: ER-0011 (S-V), ER-0012 (minúsculas), ER-0013 (doutrina do calque);
  "Espírito" maiúsculo em 1:2 por decisão exegética documentada no registro (EDITORIAL §10),
  com alternativas preservadas.
- Notas de provenance: Gen.1.1 mantém pins originais (regras 1.0.0/léxico 0.2.0) por não
  ter passado por ciclo novo (texto inalterado); os demais pinam regras 1.1.0/léxico 0.4.0;
  o léxico recebeu patch de alinhamento 0.4.1 posterior ao ciclo (H559/H7121/H3915/H7307) —
  pins honestos conforme ER-0010.
- Reabertura futura de qualquer destes versículos: somente via diff + justificativa +
  novo ciclo multiagente completo (FSM, PIPELINE.md).

## ER-0015 — RATIFICAÇÃO: Gênesis 1:6–8 → APPROVED (e glosa de רָקִיעַ)

- Data: 2026-08-11 · Ratificador: **Osvaldo Andrade (mantenedor Bereia.org)** · Status: EXECUTADA
- Decisão consciente (categoria "dia um"): **רָקִיעַ (H7549) → "firmamento"**, fixado no
  léxico como APPROVED. Alternativas discutidas e rejeitadas: "expansão" (nome de processo
  em pt-BR vivo, colapsa como entidade em Sl 19:2/Ez 1:22); "abóbada" (importa forma
  arquitetônica que o lexema não codifica). A materialidade (superfície sólida da
  cosmologia antiga — Jó 37:18; Ez 1:22 — vs. vão estendido) permanece PRESERVADA como
  ambiguidade nos registros, nunca afirmada no texto publicado (TEOLOGIA §1.5).
- Ato: os três registros da perícope `Gen.1.6-8` passam de REVIEW a **APPROVED** após o
  ciclo de ratificação (aplicação das decisões + correções mecânicas + refutação de
  fidelidade + verificação de consistência interna e contra Gen.1.1-5 APPROVED).
- Correção mecânica aplicada (não-decisão do mantenedor): 1:6 uniformiza os dois volitivos
  — "Haja um firmamento… e separe águas de águas" (queda do "que" assimétrico), preservando
  a perífrase durativa היה+particípio na traducao_literal (ER-0013).
- Confirmação de decisão anterior: "segundo dia" (ordinal שֵׁנִי, H8145) apoia-se a "dia um"
  (cardinal, 1:5) — a assimetria cardinal/ordinal do hebraico agora é visível na própria BV.
- Texto ratificado: "E Deus disse: “Haja um firmamento no meio das águas, e separe águas de
  águas.” Deus fez o firmamento e separou as águas que estavam debaixo do firmamento das
  águas que estavam acima do firmamento; e assim foi. Deus chamou o firmamento de céus.
  E houve tarde e houve manhã: segundo dia."
- Reabertura futura: somente via diff + justificativa + novo ciclo multiagente completo (FSM).

## ER-0016 — Programa da Bíblia completa: 5 threads por capítulo, tier DRAFT

- Data: 2026-08-11 · Escopo: programa · Origem: meta do mantenedor · Status: ATIVA
- Decisão: traduzir o AT (OSHB pinado) processando 5 capítulos em paralelo; bulk em
  tier **DRAFT** (pipeline enxuto: tradutor + refutador de fidelidade + finalizador,
  confianca ≤ 0,80), com REVIEW (consenso pleno) e APPROVED (ratificação humana)
  reservados para promoção dirigida pelo mantenedor. Detalhes: ADR-0002.
- NT permanece bloqueado (F-0003, quarentena OpenGNT) — nenhum versículo do NT é produzido.
- Progresso rastreado em `translation/PROGRESS.md` (`python3 scripts/progress.py`);
  commit por capítulo; retomável entre sessões.
- Gn 1:1-8 permanece APPROVED (ER-0014/0015); Gn 1:9-13 segue o piloto (REVIEW→ratificação);
  de Gn 1:14 em diante, tier DRAFT salvo pedido de promoção.

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
- F-0009: `internal/schemavalidate` — rejeitar keyword desconhecida no schema (guarda
  contra subvalidação silenciosa se um schema evoluir para oneOf/$ref/maxLength);
  tornar a lista "NOT supported" exaustiva por construção. Dono: mantenedor.
- F-0010: `bvqa` — flag `-fail-on-alert` (exit ≠ 0) e sinalização explícita de
  controle ausente (`controle_ausente`) em vez de comparar contra vazio. Dono: mantenedor.
- F-0011: `bvcheck` — checagem cruzada `objecoes_nao_resolvidas` não-vazio ⇒ status
  nunca APPROVED (guarda mecânica da FSM antes da primeira ratificação); flags de
  caminho de schema para remover acoplamento ao CWD. Dono: mantenedor.
- F-0012: pinar golangci-lint compatível com go 1.26.4 (hoje: instalado porém falha
  por mismatch de toolchain; exceção ativa com WARNING explícito no `make lint`;
  depguard/cyclop/funlen ainda não executaram — gates duros são gofmt+vet+test). Dono: mantenedor.
- F-0013: higiene de código apontada pela revisão: `sort.Strings` em vez de insertion
  sort manual (oshb.go), unificar idioma das chaves JSON do wire-struct de oshb,
  remover `Capitulo` não usado em qa. Dono: mantenedor.
