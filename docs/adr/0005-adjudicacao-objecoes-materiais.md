# ADR-0005 — Adjudicação de objeções MATERIAIS com a KJV como baseline de sentido

Data: 2026-08-30 · Status: ACEITO · Tier: T3 · Institui: ER-0020

## Contexto

A revisão editorial ER-0019 varreu os 1189 capítulos e deixou **241 objeções
MATERIAIS abertas em 222 registros**. Por construção, o revisor não podia
resolvê-las: seu escopo é FORMA, e toda correção que exigisse mudar o sentido
virava objeção e congelava o texto (`persist_review.py`, guarda "objeção
MATERIAL exige texto inalterado").

Essas objeções são hoje o gargalo do programa: enquanto abertas, bloqueiam
`APPROVED` (guarda F-0011) e portanto travam a promoção DRAFT→REVIEW.

O mantenedor determinou (2026-08-30) que sejam adjudicadas por agente, com a
**King James como baseline de sentido**.

## Decisão

Criar a etapa **ER-0020 — adjudicação**, separada da revisão, com autoridade
para alterar sentido, mas **somente** em verso que já carregue objeção aberta.

### 1. A guarda da revisão não é enfraquecida

`persist_review.py` fica intocado. A adjudicação tem persistidor próprio,
`persist_adjudication.py`, com guardas próprias. Motivo: afrouxar a guarda da
revisão permitiria que qualquer agente revisor mudasse sentido em qualquer
verso — exatamente o que ER-0019 existe para impedir. Duas etapas, dois
poderes, dois persistidores.

### 2. Hierarquia de autoridade

1. `termos_originais` do registro — hebraico/grego pinado (WLC/OSHB,
   Nestle 1904) com lemma Strong e morfologia. **Autoridade.**
2. `traducao_literal` da própria BV.
3. **KJV — baseline de sentido** (decisão do mantenedor).
4. WEB — segundo controle inglês.

A KJV entra como testemunha qualificada, não como autoridade. Isso preserva a
restrição nº 1 do programa: toda escolha tem de ser justificável pelo
hebraico/grego. `persist_adjudication.py` torna isso mecânico — veredito
PROCEDE **exige** `evidencia_original` não vazia.

### 3. Detector de divergência textual (mitigação do risco da KJV)

A KJV repousa no **Textus Receptus / Ben Chayyim**; a BV, em WLC/OSHB e
Nestle 1904. Adotá-la como árbitro cru importaria leituras que a BV
deliberadamente não segue: Comma Johanneum (1Jo 5:7-8), final longo de Marcos,
anjo em Jo 5:4, At 8:37, doxologia de Mt 6:13.

Mitigação: o pacote traz **KJV e WEB juntas**. A WEB tem base crítica moderna,
então **KJV ≠ WEB é assinatura de divergência textual, não semântica**. Nesse
caso o veredito é IMPROCEDE ou INCONCLUSIVA, com `controles_divergem: true` e a
variante descrita em `nota_textual`. Leitura TR nunca entra no `texto_bv`.

### 4. Versificação

WLC/OSHB diverge da tradição inglesa (sobrescrições de Salmos, Joel, Malaquias,
partes de Êxodo). O pacote entrega, junto de cada verso de controle, os
**vizinhos v-1 e v+1**, e o prompt exige confirmação de alinhamento pelo
conteúdo antes de usar o controle como evidência. Desalinhamento vira
`nota_textual`, não vira decisão.

### 5. INCONCLUSIVA é veredito de primeira classe

Nem toda objeção deve ser fechada por máquina. Quando a evidência não decide,
quando a escolha é confessionalmente carregada, ou quando os controles estão
desalinhados, o veredito é INCONCLUSIVA: o texto não muda e **a objeção
permanece aberta**, seguindo bloqueando APPROVED e aguardando o mantenedor.
Palpite persistido é pior que objeção aberta.

### 6. Escopo de uso da KJV no manifest

`sources/manifest.json` declara a KJV como `usage_scope: qa-control-only`. O uso
nesta etapa é mais amplo que controle de QA: ela informa decisão editorial. O
escopo passa a `qa-control-and-adjudication-baseline`, para que o manifest
continue dizendo a verdade sobre como a fonte é usada.

## Consequências

- 241 objeções deixam de ser um backlog manual intransponível.
- O texto da BV passa a poder mudar de sentido por decisão de agente — mitigado
  por: evidência do original obrigatória, reconstrução do texto a partir de
  `mudancas` (edição não registrada é recusada), DRAFT-only, e commit por
  capítulo (rollback = `git revert`).
- O que sobrar como INCONCLUSIVA é o backlog humano real, agora menor e
  qualificado.
- Status permanece **DRAFT** em todos os casos: adjudicar objeção não promove
  verso. A FSM segue intacta.

## Alternativas rejeitadas

- **Afrouxar a guarda de `persist_review.py`** — daria poder de mudar sentido a
  toda a etapa de revisão. Rejeitada em favor de dois persistidores.
- **KJV como autoridade textual** — violaria a restrição nº 1 (justificável pelo
  original) e importaria o Textus Receptus por via indireta.
- **Adjudicação 100% humana** — é o estado atual; 241 objeções não avançaram.
- **Fechar toda objeção obrigatoriamente** — produziria decisão fabricada nos
  casos genuinamente indecidíveis. Daí INCONCLUSIVA.
