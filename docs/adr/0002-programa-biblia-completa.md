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

2. **Três tiers editoriais de registro** (campo `status` do schema):
   - **DRAFT** — pipeline enxuto de escala: 1 tradutor (informado pelo registro
     editorial ratificado + léxico) + 1 refutador de fidelidade/consistência
     (1 revisão se REPROVA) + finalizador. ~2–3 agentes/versículo. É o tier de
     cobertura em massa.
   - **REVIEW** — consenso pleno de 4 agentes + refutação adversarial + QA
     (o padrão do piloto). Aplicado sob demanda ou em versículos que o DRAFT sinalizar.
   - **APPROVED** — ratificação humana registrada (ER). Nunca automático.
   O bulk do programa produz **DRAFT**; promoção a REVIEW/APPROVED é dirigida pelo
   mantenedor (amostragem, trechos disputados, versículos sinalizados).

3. **Paralelismo de 5 threads por capítulo.** Um driver processa lotes de 5
   capítulos concorrentes; cada thread traduz seu capítulo versículo a versículo no
   tier DRAFT. A concorrência real é limitada pelo runtime (~10–14 agentes
   simultâneos); os 5 capítulos se auto-repartem nesse teto.

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
