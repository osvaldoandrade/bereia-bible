# ADR-0005 — Adjudicação de objeções MATERIAIS com a KJV como baseline de sentido

Data: 2026-08-30 · Status: ACEITO (emendado no mesmo dia, §5) · Tier: T3 · Institui: ER-0020

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

### 5. INCONCLUSIVA — e a emenda do modo `final`

Redação original: nem toda objeção deve ser fechada por máquina; quando a
evidência não decide, o veredito é INCONCLUSIVA, o texto não muda e a objeção
permanece aberta aguardando o mantenedor.

**Emenda (2026-08-30, decisão do mantenedor):** a primeira rodada devolveu as
escaladas e o mantenedor determinou que o adjudicador **decida**, sem
escapatória. Institui-se o modo `final`, em que INCONCLUSIVA é recusada
mecanicamente (`persist_adjudication.py -final`).

O modo final retira o direito de não decidir; **não** afrouxa a evidência:

- PROCEDE segue exigindo `evidencia_original`. Original que não sustenta a
  correção resulta em IMPROCEDE, nunca em PROCEDE por desencargo.
- A barreira ao Textus Receptus continua: KJV divergindo da WEB resolve-se pela
  base pinada.
- **Crux decidido é crux documentado.** A leitura defensável que a decisão
  descarta vai em `leitura_rejeitada` e é persistida em
  `ambiguidades_preservadas` do registro, além de `alternativas_rejeitadas` na
  decisão. O texto passa a dizer uma coisa só; o registro continua sabendo que
  havia duas. Sem isso, forçar decisão apagaria a ambiguidade do original — o
  oposto do que o programa existe para preservar.
- Objeção que é trava de governança (tier DRAFT, paradigma de 2ª pessoa) e não
  reivindicação semântica resulta em IMPROCEDE, declarando que a questão é de
  processo.
- Desempate declarado: morfologia pinada > leitura que KJV e WEB sustentam
  juntas > texto atual da BV (ônus da prova é de quem objeta).

O verso escalado volta ao adjudicador **com o próprio raciocínio da escalada
anterior no pacote** (`inconclusiva_anterior`): ele decide com mais informação
do que tinha na primeira passada, não com menos.

Risco assumido e registrado: decisão de crux por agente, sem ratificação humana
prévia. Mitigação: evidência obrigatória, leitura descartada preservada,
status permanece DRAFT, commit por lote (`git revert`), e
`scripts/review_queue.py -secao procede` lista para o mantenedor todo verso cujo
sentido mudou.

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
- Com o modo `final` (§5), nenhuma objeção sobra por indecisão: o backlog
  humano deixa de existir como fila e passa a ser revisão a posteriori dos
  vereditos, via `scripts/review_queue.py`.
- Status permanece **DRAFT** em todos os casos: adjudicar objeção não promove
  verso. A FSM segue intacta.

## Alternativas rejeitadas

- **Afrouxar a guarda de `persist_review.py`** — daria poder de mudar sentido a
  toda a etapa de revisão. Rejeitada em favor de dois persistidores.
- **KJV como autoridade textual** — violaria a restrição nº 1 (justificável pelo
  original) e importaria o Textus Receptus por via indireta.
- **Adjudicação 100% humana** — é o estado atual; 241 objeções não avançaram.
- **Fechar toda objeção obrigatoriamente** — rejeitada na redação original por
  produzir decisão fabricada nos casos indecidíveis; **revertida pela emenda do
  §5**, com a mitigação de que a leitura descartada é preservada em
  `ambiguidades_preservadas` em vez de sumir.
