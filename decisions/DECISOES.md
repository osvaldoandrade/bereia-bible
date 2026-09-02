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

## ER-0017 — DRAFT por capítulo (revisão do custo do programa)

- Data: 2026-08-12 · Escopo: programa · Origem: **mantenedor** ("por que tão pesado?") · Status: ATIVA
- Problema: o tier DRAFT por-versículo (~2 agentes/verso) tornava o AT ~46.000 agentes;
  um único lote de 5 capítulos (Gn 2-6, 129 vv) esgotou o limite de gasto.
- Decisão: DRAFT passa a **1 agente por capítulo** (`draft-chapter-driver.workflow.js`);
  o agente produz só o julgamento por versículo; morfologia palavra-a-palavra é montada
  mecanicamente do packet pinado (`scripts/persist_chapter_draft.py`, F-0015). Redução ~50×
  (Gn 2-6: ~5 agentes; AT: ~929). Consenso pleno (4 agentes/verso) fica **só sob demanda**,
  em passagens priorizadas pelo mantenedor. Schema v1.1.0: `translit`/`glosa` opcionais
  em `termos_originais` (preenchidos na promoção). ADR-0002 revisado.
- Validado a seco (sem agentes) com journal-mock + packet real de Gn 2: registros montados
  passam bvcheck; surface/lemma/morfologia vêm do OSHB, não redigitados.

## ER-0018 — Autoridade textual e cobertura do Novo Testamento

- Data: 2026-08-13 · Escopo: programa · Origem: meta do mantenedor de concluir a
  Bíblia inteira · Status: ATIVA · ADR: 0003
- Decisão: adotar o CSV `Nestle1904.csv` do Biblical Humanities como autoridade
  textual do NT: texto-base Nestle 1904 declarado em domínio público; morfologia,
  lematização e Strong sob CC0 1.0; commit e SHA-256 pinados no manifest.
- O OpenGNT permanece `analysis-only-quarantined` e não participa dos packets,
  julgamentos ou registros do NT. Esta diretriz supersede somente a cláusula de
  bloqueio do NT em ER-0016; o tier DRAFT por capítulo de ER-0017 continua ativo.
- `internal/nestle1904` preserva texto, morfologia funcional/formal, lema, Strong,
  normalização, lacunas da numeração crítica e a leitura curta de Marcos 16 como
  aparato de 16:20. Controles com fronteira mista são omitidos ou mapeados por
  regra explícita, nunca divididos por inferência.
- O driver/persistidor torna-se fonte-neutro e registros do NT pinam
  `nestle1904@713f28a3`. Versão agregada dos prompts: 1.1.0; processo: 1.1.0.

## ER-0019 — Revisão editorial do tier DRAFT sobre hot-spots estáticos

- Data: 2026-08-23 · Escopo: programa · Origem: meta do mantenedor (legibilidade
  pt-BR do DRAFT) · Status: ATIVA
- Problema: a cobertura DRAFT (ER-0016/0017: 1 agente por capítulo, foco em
  fidelidade e auditabilidade) produziu texto de tradução em geral correto mas de
  leitura difícil em pt-BR: calques paratáticos ("e aconteceu que", "eis que"),
  arcaísmos vedados (EDITORIAL §1.2), paradigma vós em discurso Deus→humano
  (§3/D-0003 pede você/vocês), redundâncias internas e sentenças acima de
  40 palavras (§1.3). A normalização editorial prevista no §6.2 nunca foi executada
  porque não existia como etapa.
- Decisão: etapa de **revisão editorial** sobre hot-spots, em três passos
  (PIPELINE.md v1.2.0):
  1. triagem estática `scripts/qa_linguistico.py` (marcadores mecânicos — ARC-1,
     LEN-1, VOS-1, RAT-1, RED-1, CAL-1/2, PRO-1, PAS-1 — sem agentes; saída
     `qa/reports/hotspots.*` + digest por capítulo hot);
  2. 1 agente revisor por capítulo hot
     (`pipeline/orchestration/review-chapter-driver.workflow.js`, prompt canônico
     `pipeline/prompts/revisor-editorial-draft.md`), até 16 em paralelo;
  3. persistência in-place `scripts/persist_review.py` + commit por capítulo.
- Guardas (vinculantes):
  - mudança somente de **FORMA**; correção que altere sentido é proibida — vira
    objeção MATERIAL registrada em `objecoes_nao_resolvidas` (bloqueia APPROVED;
    o texto não muda);
  - cobertura OSIS exata: nenhum verso inventado, omitido ou renumerado;
  - cada mudança aplicada é registrada em `decisoes` com `diretriz_ref: ER-0019`;
  - re-pin de `fontes` no ciclo (ER-0010): `prompts_versao` 1.2.0 (review),
    regras e léxico nas versões efetivamente lidas, modelo do ciclo;
  - status **permanece DRAFT** — promoção a REVIEW segue exigindo consenso pleno
    + QA de contaminação (FSM inalterada);
  - fórmulas intencionais do original (refrões, paralelismo, quiasmos) são
    mantidas pelo revisor; a triagem estática apenas flagra, não decide;
  - normalização do paradigma vós→vocês (§3/D-0003) aplica-se ao capítulo
    INTEIRO de forma coerente (prompt canônico v1.1.0, item 10); oração a Deus
    permanece em tu.
- Primeira execução (2026-08-23): 31142 versos DRAFT varridos; 5705 com achados
  (18,3%); 506 capítulos hot no limiar score ≥ 8.
- Piloto (2026-08-23, Gn 24 / Êx 12 / Mc 4): 17 versos revisados + 1 objeção
  MATERIAL (Gen.24.7) persistidos e commitados (fc329f7f, 6410e600, 662e0158).
  Achado do piloto: Êx 12 emprega paradigma vós (comereis, vossas, guardai) em
  discurso de Deus, não flagrado pelos marcadores originais — marcador VOS-1
  adicionado nesta data e prompt canônico elevado a v1.1.0 (normalização
  coordenada do capítulo inteiro; `prompts_versao` do ciclo passa a 1.2.1).
- Execução em massa (2026-08-23): `scripts/ship_review_batch.py` — reparo
  mecânico (quote-swap incidental), recuperação verificada de saídas
  malformadas (`--recover`: blocos consertados por máquina de estados de
  aspas e validados contra registro+mudancas; `--regen-noop`), persistência,
  bvcheck e commit por capítulo em um comando. Warts recorrentes dos agentes
  (aspas curvas emitidas retas sem escape; edições não registradas em
  mudancas — estas são descartadas, o texto é reconstruído só com as mudancas
  registradas) levaram o prompt canônico a v1.1.1; `prompts_versao` 1.2.2.
- **v2 (2026-08-29, 42ea172e)**: comparação guiada. O digest passa a carregar as
  referências paralelas NTLH/ARA/NVIPT por versículo (`scripts/qa_linguistico.py
  -refs`, schema v2) e o revisor deve confrontá-las antes de concluir
  SEM_ALTERACAO — divergência das três referências em palavra-chave exige
  investigar arcaísmo/inconsistência (EDITORIAL §1.2-tabela, §1.4). As
  referências são de uso editorial local e não são commitadas (.gitignore;
  NOTICE.md). Prompt canônico v1.2.0; processo PIPELINE.md v1.2.0.
- **v3 (2026-08-29/30)**: escopo estendido do recorte por score para **a Bíblia
  inteira**. A triagem roda com `threshold 0` e os 1189 capítulos tornam-se
  elegíveis, não apenas os 506 hot-spots com score >= 8 — o score deixa de ser
  porta de entrada e vira apenas ordenação. Motivo: o recorte por marcador
  mecânico não captura arcaísmo/inconsistência que só a comparação com as
  referências (v2) revela, e essa comparação não existia quando o limiar foi
  fixado. Digests commitados em `qa/reports/review-input/` (entrada exata lida
  por cada agente).
- Modelo do ciclo é **proveniência**, não configuração. Verificado nos journals
  de agente: os lotes de 2026-08-29 rodaram de fato em `qwen3.7-max` e os de
  2026-08-30 em `claude-sonnet-5` — os dois valores gravados em `fontes` estão
  corretos e **não devem ser reescritos**; o registro diz qual modelo produziu
  aquele texto, não qual modelo o programa usa hoje.
  O driver deixou de fixar `MODEL` no código (`args.model`, default sonnet) não
  porque o valor estivesse errado, mas porque proveniência hardcoded diverge em
  silêncio assim que o alias de modelos muda — foi o que ocorreu quando qwen
  saiu do alias (2026-08-30). Parametrizado, o valor acompanha a execução real.
- Execução v3 **COMPLETA em 2026-08-30**: 1189/1189 capítulos com revisão
  editorial persistida — cobertura de 100% da Bíblia, AT e NT. A sessão de
  2026-08-30 processou 402 capítulos (Sl 67 → Ap 22) em 26 lotes de até 16
  agentes paralelos, modelo `claude-sonnet-5`: **402 agentes, 0 erros, 0
  resultados vazios**. Total do dia: 742 versos revisados e 89 objeções
  MATERIAIS registradas.
- Estado ao fim do ciclo: 31155 registros, 194 com `objecoes_nao_resolvidas`
  não-vazio (0,62%). Todos permanecem DRAFT — a objeção MATERIAL bloqueia
  APPROVED por construção (bvcheck/F-0011), e a promoção continua exigindo
  consenso pleno + QA de contaminação. A revisão editorial **não** promove
  status; ela só normaliza forma.
- Reincidência do wart de **edição não registrada** com sonnet (Sl 79.1: a
  sobrescrição "Salmo de Asafe." foi apagada sob veredito SEM_ALTERACAO). O
  guard de `ship_review_batch.py` abortou o lote antes de qualquer escrita e o
  texto do registro foi restaurado. Confirma a política: o texto é reconstruído
  só a partir de `mudancas`; o que o agente escreve em `texto_bv_revisto` sem
  registrar é descartado, nunca persistido.
- **F-0018 RESOLVIDO em 2026-08-30**: os 94 capítulos revisados antes do v2
  passaram pela re-revisão sob o prompt v1.2.0, em 6 lotes (94 agentes, 0 erros).
  Resultado: **285 versos revisados e 28 objeções MATERIAIS** — densidade de
  ~3,0 versos/capítulo contra ~1,8 da primeira passada v3, confirmando que a
  comparação guiada NTLH/ARA/NVIPT encontra o que o marcador mecânico não vê
  (Ez 26: 15 revisões em 21 versos; Jr 49: 12; Dn 3: 9). Nenhum capítulo do
  cânon permanece sem comparação guiada.
- Modelos do F-0018 (proveniência por lote, verificada nos journals de agente):
  lotes 1–4 em `claude-sonnet-5`; lotes 5–6 em `claude-fable-5` (troca pedida
  pelo mantenedor a meio caminho). Os registros gravam o modelo que de fato
  produziu cada texto — a divisão é intencional, não um defeito.

## ER-0020 — Adjudicação das objeções MATERIAIS (ADR-0005)

- Data: 2026-08-30 · Escopo: programa · Origem: determinação do mantenedor ·
  Status: **CONCLUÍDA**
- Problema: o ER-0019 fechou a revisão editorial dos 1189 capítulos deixando
  241 objeções MATERIAIS abertas em 222 registros. Por construção o revisor não
  podia resolvê-las (escopo = forma), e enquanto abertas elas bloqueavam
  APPROVED (F-0011) e travavam a promoção DRAFT→REVIEW.
- Decisão: etapa própria de adjudicação, com poder de alterar sentido mas só em
  verso que já carregue objeção aberta; **KJV como baseline de sentido**
  (determinação do mantenedor) e WEB como segundo controle; autoridade textual
  permanece em `termos_originais` (WLC/OSHB, Nestle 1904). Detalhes e riscos em
  docs/adr/0005-adjudicacao-objecoes-materiais.md.
- Modo `final` (emenda do mesmo dia): INCONCLUSIVA proibida — toda objeção sai
  decidida. A trava que torna isso auditável: a leitura defensável descartada
  vai para `ambiguidades_preservadas` e `alternativas_rejeitadas`.
- **Resultado: 241/241 objeções resolvidas — zero abertas em 31155 registros.**
  227 decisões ER-0020 gravadas: 101 procedentes (sentido corrigido) e
  121 improcedentes (texto mantido). 160 registros ganharam leitura rejeitada
  preservada — a decisão estreitou o texto sem apagar o crux.
- A barreira ao Textus Receptus segurou. Caso de prova: At 7.46, onde KJV e WEB
  concordam ENTRE SI em θεῷ Ἰακώβ (bizantino/TR) contra o οἴκῳ Ἰακώβ do
  Nestle 1904 pinado — o adjudicador registrou que ali os controles não servem
  como evidência e votou IMPROCEDE. Mesma recusa em At 13.20 (450 anos do TR) e
  Jo 17.20 (particípio futuro πιστευσόντων). Nenhuma leitura TR entrou no texto.
- Achados de peso: Jo 8.25 não vertia dez palavras do original
  (Ἔλεγον οὖν αὐτῷ Σὺ τίς εἶ; εἶπεν αὐτοῖς ὁ Ἰησοῦς) — omissão, não escolha;
  2Sm 9.11 tinha pontuação que fazia שֻׁלְחָנִי ser a mesa de Ziba, contra o
  referente de Davi nos vv. 7 e 10; Gn 27.39 vertia מִן como locativo ("nas"),
  e a correção adotada ("das") não é a que a objeção pedia (privativa "longe
  das"), registrada como rejeitada.
- Modelos (proveniência verificada nos journals): lotes normais 1–3 e todos os
  lotes do modo final em `claude-fable-5`.
- Status permanece **DRAFT** em todo o cânon: adjudicar objeção não promove
  verso. A FSM segue intacta e a promoção continua exigindo consenso pleno +
  QA de contaminação.

## ER-0021 — Promoção do cânon a APPROVED por determinação do mantenedor

- Data: 2026-08-31 · Escopo: programa · Origem: determinação do mantenedor ·
  Status: **EXECUTADA**
- Decisão: os 31155 registros passam de DRAFT a APPROVED. O mantenedor aprovou
  integralmente os ciclos ER-0019 (revisão editorial de 1189/1189 capítulos) e
  ER-0020 (adjudicação de 241/241 objeções MATERIAIS) e determinou a promoção,
  dispensando o caminho ordinário DRAFT→REVIEW por consenso pleno + QA de
  contaminação. A ratificação humana que a FSM exige para APPROVED é esta
  entrada.
- Execução: `scripts/promote_status.py`, em duas transições
  (DRAFT→REVIEW→APPROVED), gravando em cada registro a autoridade que autorizou
  o movimento. 0 registros bloqueados — nenhum tinha objeção aberta, porque o
  ER-0020 já as havia zerado.
- Correção de pipeline que a promoção expôs: `scripts/qa_linguistico.py` filtrava
  registros por `status == DRAFT` no código. Com o cânon promovido a triagem
  passou a varrer **zero** versos — a superfície de QA ficava cega exatamente
  quando o texto vira publicável. O filtro passou a ser parâmetro (`-status`,
  default = todos): triagem é sobre o texto, não sobre o estado em que o texto
  está estacionado.
- Guarda que permanece: `promote_status.py` recusa promover a APPROVED um verso
  com `objecoes_nao_resolvidas` não vazio (F-0011). Não é trava de processo, é
  de coerência — "tem objeção pendente" e "é publicável" não podem ser ambos
  verdadeiros no mesmo registro. `-force` sobrepõe e grava a sobreposição.
- Nota de auditoria herdada: `fontes.manifest_sha256` continua notacional
  (F-0007/registro do bootstrap) e o QA de contaminação (`bvqa`) não foi
  executado sobre o texto revisto — permanecem como follow-ups, agora sobre
  corpus APPROVED.

## ER-0022 — Revisão gramatical e de coesão do Antigo Testamento

- Data: 2026-08-31 · Escopo: AT (livros 1–39) · Origem: determinação do
  mantenedor · Status: EM EXECUÇÃO
- Regra que governa a etapa: **fidelidade às Escrituras é o teto; norma culta e
  coesão são o piso.** Colidindo, a fidelidade vence e vira objeção MATERIAL —
  nunca o contrário. Na maioria dos casos não há colisão: o defeito é calque
  sintático, regência, concordância ou pronome sem antecedente.
- Novidade de processo — **janela de contexto**. O digest passa a trazer, por
  verso, N versos anteriores e posteriores em ordem de leitura, **cruzando
  fronteira de capítulo**. Motivo: a BV foi redigida um capítulo por vez, então
  as costuras de coesão estão exatamente nas emendas entre capítulos, e uma
  janela que parasse na borda seria cega justamente ali. Coesão não é julgável
  em verso isolado — antecedente pronominal, cadeia temporal, conectivo e
  continuidade de sujeito vivem entre versos.
- **KJV como controle de sentido** (mesma escolha do ER-0020): serve para
  conferir se a BV entendeu a mesma coisa, não para ditar estilo — o inglês de
  1611 não é modelo de português de 2026. Divergindo da morfologia pinada, a
  morfologia vence.
- Correção de pipeline que a etapa exigiu: `persist_review.py` e
  `ship_review_batch.py` fixavam `status == DRAFT` no código. Como o cânon foi
  promovido a APPROVED (ER-0021), o revisor não persistiria nada. O escopo
  virou parâmetro (`-status`, default DRAFT). Fixar o estado tornava o revisor
  inútil no momento em que o texto vira publicável — que é quando revisar mais
  importa.
- Escopo mecânico: 929 capítulos, 23213 versículos, janela ±2.
- Modelo: `claude-fable-5`.
- Correção de custo (driver v2, a partir de Gn 41): o driver v1 mandava cada
  agente reler ~60 KB de regras por capítulo (DECISOES.md + lexicon.json +
  EDITORIAL.md + prompt canônico) num loop agêntico aberto — ~400-600 KB de
  transcript por capítulo. O v2
  (`pipeline/orchestration/grammar-review-driver-v2.workflow.js`) embute as
  regras destiladas no prompt e fixa o orçamento de ferramentas: 1 Read
  (digest) + 1 Write (saída) + no máximo 1 validação de JSON. Dúvida que
  exigiria consultar DECISOES.md/léxico vira objeção EDITORIAL, não leitura.
  Medido em Gn 41 (maior digest do AT, 197 KB): 113k tokens totais, transcript
  de 288 KB dos quais ~197 KB são o próprio digest — o overhead virou
  marginal. O contrato de saída e as guardas do ship não mudaram; a
  destilação referencia revisor-gramatical.md v1.0.0 e EDITORIAL.md v1.2.0 e
  deve ser re-destilada se eles mudarem.
- Correção de proveniência (a partir de Gn 49): `ship_review_batch.py` fixava
  no código a diretriz da mensagem de commit (`ER-0019`), porque foi escrito
  para aquela etapa. O rótulo virou parâmetro (`-er`, default `ER-0019`) e
  este ciclo ship a com `-er ER-0022`. Consequência registrada e **não
  reescrita**: Gn 33-48 é conteúdo ER-0022 já pushado sob mensagens
  `(ER-0019)` — o conteúdo do `review-out` (campo `justificativa`, vereditos
  gramaticais) e o `fontes.modelo` do registro são a proveniência real
  desses capítulos; a mensagem de commit, ali, mente. Gn 1-16 e 17-32, que
  foram commitados à mão, trazem o rótulo certo.
- Segunda correção de proveniência, mais profunda (a partir de Lv 7):
  `persist_review.py:apply_chapter` também fixava `ER-0019` no código, e não
  só na mensagem de commit — em `decisoes[].diretriz_ref` de CADA registro de
  versículo tocado, e no texto de `justificativa`/`objecoes_nao_resolvidas`.
  Ganhou o mesmo parâmetro (`-er` no `main()` de `persist_review.py`, default
  `ER-0019`; `ship_review_batch.py` repassa `args.er`). **Não reescrito**:
  todo registro de versículo já shipado sob ER-0022 até este fix (Gn 49-50,
  Ex 1-40, Lv 1-22) carrega `diretriz_ref: "ER-0019"` embutido em
  `decisoes[]`, apesar de a revisão real ser ER-0022. Proveniência
  verdadeira desses registros: `fontes.modelo` (correto) + o `review-out`
  correspondente em `qa/reports/review-out/` (correto) + a mensagem de
  commit a partir de Gn 49 (correta, `-er` já existia para o commit desde a
  correção anterior). Só o campo interno `diretriz_ref` mente, e só até
  Lv 6.
- Modelo trocado de `claude-fable-5` para `claude-sonnet-5` a partir de
  Ex 31 (créditos de fable esgotados na conta) — mesmo par autorizado em
  [[revisao-er0019-usar-sonnet]]. Confirmado por leitura do journal
  (`agent-*.jsonl`, campo `message.model`) antes de cada persist a partir
  daqui, não só do `meta.json` do driver.
- Defeito de schema pré-existente encontrado em 2Sm 9 (bloqueou o `bvcheck`
  ao aplicar a revisão do capítulo): `2Sam.9.11.json` tinha
  `decisoes[].alternativas_rejeitadas` como string solta em vez de
  `{opcao, motivo}` (schema exige objeto). Não é defeito do ER-0022 — a
  entrada vem de uma adjudicação ER-0020 anterior a esta sessão. Reparado
  neste registro (string dividida nas duas alternativas que ela já
  enumerava como "(1)"/"(2)", conteúdo preservado verbatim, só a forma
  virou objeto) e commitado junto com a revisão gramatical do capítulo.
  Varredura de todo `translation/` mostrou que **não é caso isolado: 160
  registros** em livros de AT e NT (Esdras, Neemias, Lamentações, Jeremias,
  Oseias, 1Co, 1Tm, Tiago, Efésios, entre outros) têm o mesmo defeito,
  todos originados do mesmo padrão de escrita em ER-0020. Fora do escopo
  do ER-0022 (que só toca capítulo por capítulo conforme avança); vira
  F-0023 no backlog abaixo — reparo requer leitura humana ou agente por
  entrada para dividir a string em opção/motivo sem perder conteúdo, não é
  mecânico como os fixes de proveniência acima.

---

## Follow-ups abertos

- F-0001: obter Almeida 1911 / Tradução Brasileira 1917 digitalizada e pinar no manifest. Dono: mantenedor.
- F-0002: decidir licença da BV (CC BY-SA 4.0 × CC BY 4.0). Dono: mantenedor.
- F-0003: **RESOLVIDO em 2026-08-13** pelo ADR-0003/ER-0018: Nestle 1904 PD + morfologia CC0.
- F-0004: pipeline programático (API Anthropic, temperatura 0) substituindo orquestração de sessão. Dono: mantenedor.
- F-0005: mutation testing das ferramentas Go quando tooling disponível. Dono: mantenedor.
- F-0006: verificar licença exata da Bíblia Livre na página eBible/da própria BLIVRE. Dono: mantenedor.
- F-0007: auditoria trimestral do manifest de fontes (docs/dependencies.md). Dono: mantenedor.
- F-0008: instalar hook local de secret-scan (gitleaks/git-secrets). Dono: mantenedor.
- F-0014: workflows longos travam na agregação final (dia três: agente de consistência
  preso em retry; DRAFT driver: hang no return). Mitigação em uso: recuperar registros do
  journal.jsonl + TaskStop. Padrão do programa: sempre recuperar do journal, não esperar output.
- F-0015: surface hebraico dos `termos_originais` DEVE ser re-injetado do packet pinado
  (nunca redigitado pelo agente) — elimina corrupção de glifo. Aplicado manualmente em
  Gn 1:14-31; tornar passo padrão do pipeline de persistência (script reutilizável).
- F-0016: um verso DRAFT de Gn 1:14-31 teve REPROVA material do refutador (surface corrompido,
  já sanado por F-0015); a revisão automática não rodou (hang). DRAFT não é publicável;
  consenso pleno + revisão ocorrem na promoção.
- F-0017: driver de workflow recebe `args` como string JSON — o script faz JSON.parse defensivo.
- F-0019: **RESOLVIDO em 2026-08-31.** Tinha duas faces, e a segunda só apareceu na
  varredura do backfill: (a) palavra suprida pela correção entrava no `texto_bv` sem
  ser declarada (Êx 4.25 "com ele"; 1Rs 10.16/29 "siclos"); (b) pior, reescrever o
  texto deixava **órfã** a entrada declarada num ciclo anterior — 9 registros
  afirmavam suprimento que não estava mais lá ("unidades" depois de virar "siclos",
  "Alguém" depois da voz passiva, "entre" depois de virar "sobre"). O persistidor
  passou a recusar entrada órfã e aceita `palavras_supridas_removidas`; os 9
  registros foram reconciliados. `supplied_head()` respeita a convenção do projeto
  (`palavra — justificativa`, `palavra (nota)`, `"palavra", justificativa`), que a
  primeira versão da guarda tratava como token nu.
- F-0018: **RESOLVIDO em 2026-08-30** — os 94 capítulos pré-v2 foram re-revistos sob o
  prompt v1.2.0 (285 vv revisados, 28 objeções MATERIAIS). Cobertura da comparação
  guiada: 1189/1189.
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
- F-0023: **160 registros** em `translation/` (AT e NT — Esdras, Neemias, Lamentações,
  Jeremias, Oseias, 1Co, 1Tm, Tiago, Efésios e outros) têm
  `decisoes[].alternativas_rejeitadas` como string solta em vez de `{opcao, motivo}`
  exigido pelo schema (`api/verse-record.schema.json`) — todos originados de
  adjudicações ER-0020 anteriores a esta sessão, não do ER-0022. Achado ao shipar
  2Sm 9 (ER-0022): `bvcheck` rejeitou `2Sam.9.11.json` por essa causa; reparado
  isoladamente (string dividida nas duas alternativas que já enumerava, conteúdo
  preservado). Os outros 159 seguem malformados — bloqueiam qualquer `bvcheck` futuro
  sobre esses capítulos até reparados. Reparo não é mecânico (a string mistura
  prosa argumentativa de 1+ alternativas; separar opção/motivo por entrada exige
  leitura humana ou agente dedicado, não regex). Dono: mantenedor.
