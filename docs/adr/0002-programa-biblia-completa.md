# ADR-0002 — Programa de tradução da Bíblia completa (5 threads por capítulo)

Data: 2026-08-11 · Status: ACEITO · Tier: T3 · Autor: pipeline BV · Diretriz: ER-0016

## Contexto

O mantenedor definiu como meta traduzir a Bíblia inteira, processando **5 capítulos
em paralelo** ("5 threads, uma por capítulo"), avançando até fechar. O rigor do
piloto (4 agentes + consenso + refutação + ratificação humana por versículo) é
inviável em escala de cânon (~1.189 capítulos, ~31.000 versículos): milhões de
invocações de agente. Além disso, a conta já atingiu limite de gasto uma vez.

## Decisões

1. **Fronteira do escopo automatizável (agora): somente o Antigo Testamento**, a
   partir do OSHB pinado. O Novo Testamento permanece **bloqueado** pela quarentena
   de licença do OpenGNT (ADR-0001 §2; F-0003) até o mantenedor decidir a fonte grega
   de domínio público (candidata: Nestle 1904). Livros do AT além de Gênesis são
   baixados do MESMO commit OSHB pinado e adicionados ao manifest quando processados.

2. **Dois tiers editoriais de registro** (campo `status` do schema)
   — REVISADO 2026-08-12 pelo mantenedor (ver ER-0017):
   - **DRAFT** — cobertura em massa: **1 agente por capítulo** que traduz o
     capítulo inteiro de uma vez (aplica o registro editorial, produz por
     versículo apenas o julgamento: texto_bv, traducao_literal, decisoes,
     justificativa, confianca ≤ 0,80). A morfologia palavra-a-palavra NÃO é
     reemitida pelo agente — é montada mecanicamente do packet pinado
     (`scripts/persist_chapter_draft.py`; palavra/lemma/morfologia do OSHB,
     F-0015). ~1 agente/capítulo (era ~2–3/versículo — redução de ~50×).
   - **REVIEW/APPROVED** — consenso pleno de 4 agentes + refutação adversarial
     por versículo + QA + ratificação humana. Aplicado **somente sob demanda**,
     em passagens que o mantenedor prioriza (não em todo versículo).
   O bulk produz **DRAFT**; promoção é dirigida pelo mantenedor.
   O tier intermediário "DRAFT por-versículo" (translator+refutador/verso) foi
   DESCARTADO — custo alto demais para o cânon; `draft-driver.workflow.js` removido.

3. **Paralelismo de 5 threads por capítulo.** `draft-chapter-driver.workflow.js`
   processa lotes de até 5 capítulos concorrentes, **1 agente por capítulo**
   (5 threads = 5 agentes/lote). Custo do AT: ~929 agentes (vs. ~46.000 no
   design por-versículo). A morfologia autoritativa nunca depende do agente.

4. **Resumibilidade entre sessões.** Cada capítulo concluído é commitado
   individualmente e marcado em `translation/PROGRESS.md`. Interrupção por limite de
   gasto/contexto é retomável do cache do workflow (resumeFromRunId) e do ledger de
   progresso. O limite de gasto é bloqueio do mantenedor, não falha do pipeline.

5. **Invariantes preservados no tier DRAFT.** Fonte pinada (auditabilidade),
   registro editorial ratificado (ER-0011..0015), léxico como fonte terminológica,
   guardas teológicas (TEOLOGIA.md), calques na `traducao_literal`. O que o DRAFT
   NÃO tem: as 4 vozes independentes e a rodada adversarial completa — por isso
   `confianca` do DRAFT é teto 0,80 e o status jamais passa de DRAFT sem um ciclo
   REVIEW.

## Consequências

- Cobertura do AT torna-se viável em múltiplas sessões, com rastreabilidade intacta.
- Qualidade do DRAFT é inferior ao REVIEW; o texto publicável exige promoção.
- O NT fica explicitamente fora até F-0003 — nenhuma tradução do NT é produzida.
- Estrutura canônica (nº de capítulos/versículos por livro) vem do próprio OSHB.

## Alternativas rejeitadas

- Consenso pleno de 4 agentes para todo o cânon: inviável (custo/tempo).
- Traduzir o NT do OpenGNT já: viola a quarentena de licença (ADR-0001).
- Um único workflow gigante para o cânon todo: irrecuperável, estoura limites; o
  batching por 5 capítulos com commit por capítulo é a unidade resumível.

## Rollback

Repositório local; `git revert` por capítulo. Nenhum efeito externo.
