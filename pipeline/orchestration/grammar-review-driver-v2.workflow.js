// Lean grammar/cohesion review driver for the OT (ER-0028, v1.1.0).
//
// Re-review of the whole OT after ER-0026 found and fixed a confirmed false
// negative in the NT sibling cycle (João 1.3, "traço estilístico" excusing
// actual calque). A heuristic sweep of all 23213 OT verses found no
// equivalent case (Hebrew narrative/poetry leans on repetition as
// structure far more than NT Greek prose, so the old standard usually
// judged correctly) — but the maintainer asked for the OT to go through
// the same rigor pass regardless, so every kept repetition is audited to
// the same standard, not just presumed safe by genre. RULES below add the
// same three guards as the NT's ER-0026: (1) skepticism test before any
// "it's stylistic" verdict stands — named figure (parallelism, chiasm,
// inclusio, anaphora, cognate accusative), real information the Hebrew
// itself repeats, a real distinction requiring variation, or audible
// emphasis, or it's calque and gets corrected; (2) a verse-seam check for
// connectives continuing a clause from further back than the immediately
// preceding verse; (3) paragraph/strophe-level (not just adjacent-verse)
// cohesion judgment.
//
// Same lean contract otherwise — ONE Read (digest) + ONE Write
// (review-out), inline distilled rules, up to 16 parallel threads. Token
// economics unchanged from v2 (see prior history in this file's git log).
//
// Doubt that would require consulting DECISOES.md or lexicon.json is not
// resolved by the agent: it becomes an EDITORIAL objection (adjudicated
// later), which is cheaper and safer than re-reading 50 KB per chapter.
//
// Distilled from pipeline/prompts/revisor-gramatical.md v1.1.0 and
// pipeline/rules/EDITORIAL.md v1.2.0 (Bible-wide, unchanged) — re-distill
// here if either changes.
//
// Persistence unchanged: scripts/ship_review_batch.py -status APPROVED
// -er ER-0028 -modelo <model>, same guards (exact OSIS coverage, MATERIAL
// => text unchanged, every edit logged in mudancas).
//
// args = { chapters: [ { book_dir, chapter } ... up to 16 ], model }
export const meta = {
  name: 'bv-grammar-review-driver-v2',
  description: 'Stricter re-review of the OT for cohesion — same rigor pass as the NT ER-0026 (ER-0028 v1.1.0)',
  phases: [{ title: 'Revisar', detail: 'até 16 threads; 1 Read + 1 Write por capítulo, regras inline' }],
}
const REPO = '/Users/ova/GolandProjects/bereia-bible'
let A = args || {}
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
// Model is provenance-bearing: must equal the -modelo passed to
// scripts/ship_review_batch.py (ER-0010 re-pin of `fontes`).
const MODEL = A.model || 'sonnet'
const CHAPTERS = (A.chapters || []).slice(0, 16)

const S = { type: 'string' }
const I = { type: 'integer' }
const SUMMARY = {
  type: 'object',
  additionalProperties: true,
  required: ['book_dir', 'chapter', 'revisados', 'sem_alteracao', 'objecoes_materiais'],
  properties: { book_dir: S, chapter: I, revisados: I, sem_alteracao: I, objecoes_materiais: I },
}

const RULES = `Você é o revisor gramatical e de coesão da Bereia Version (BV), etapa ER-0028 (AT, re-revisão). Objetivo: português correto e coeso, SEM jamais comprar coesão com fidelidade.

POR QUE ESTE CICLO EXISTE: o irmão deste ciclo no NT (ER-0024) deixou passar defeito real, corrigido no ER-0026 — João 1.3 publicado como "...nada foi feito do que foi feito" (calque morfológico do grego ἐγένετο...γέγονεν), excusado como "traço estilístico joanino" e mantido. Uma varredura heurística do AT não achou caso equivalente (o hebraico depende de repetição como técnica central muito mais que a prosa grega do NT), mas toda repetição mantida precisa passar no mesmo teste explícito abaixo, não ser presumida segura só pelo gênero.

REGRA QUE GOVERNA TUDO: fidelidade às Escrituras é o TETO; norma culta e coesão são o PISO. O texto tem de dizer exatamente o que o hebraico diz, num português que um leitor brasileiro culto leia sem tropeçar. Quando as duas exigências colidem, a FIDELIDADE VENCE e você registra objeção MATERIAL — nunca o contrário. Na esmagadora maioria dos casos não há colisão: o defeito é calque, regência, concordância ou pronome sem antecedente, que se corrige sem tocar no sentido.

CETICISMO CONTRA "TRAÇO ESTILÍSTICO": o hebraico narrativo/poético repete raiz/lexema com muito mais frequência e propósito que o grego do NT — paralelismo é a espinha dorsal da poesia hebraica, refrão/inclusio/fórmula genealógica são centrais à narrativa — mas isso não autoriza presumir toda repetição intencional sem prova. Antes de escrever SEM_ALTERACAO justificando repetição como "estilo" ou "ênfase do original", ela precisa passar em PELO MENOS UM destes testes: (1) é uma figura NOMEÁVEL e reconhecível — paralelismo sinonímico/antitético, quiasmo, inclusio, anáfora, refrão, acusativo cognato (figura etymologica — ex. "arderá um incêndio como incêndio de fogo", Is 10.16, refletindo יֵקַד יְקֹד כִּיקוֹד), fórmula genealógica, dobra enfática de imperativo/vocativo ("Responde-me, SENHOR, responde-me", 1Rs 18.37) — não apenas "o hebraico repete a raiz"; se você não consegue nomear a figura, não é uma; (2) a palavra repetida É o conteúdo do verso — quando o hebraico pinado repete o mesmo substantivo várias vezes porque o referente concreto exige (ex. "degraus" 5× em Is 38.8, contando degraus específicos), reduzir apagaria informação, não só estilo; (3) remover a repetição apagaria distinção real que o hebraico marca (aspecto verbal) — motivo para VARIAR a segunda ocorrência, não repetir a mesma palavra sem função; (4) soa como ênfase real em português lida em voz alta, não só "existe no hebraico e é visível na página". Nenhum teste passa → é calque morfológico: corrija, variando o verbo/palavra (nunca inventando nuance teológica nova), preferindo precedente já estabelecido na tradição de tradução em português (ARA/ACF/NVI) quando houver.

COSTURA DE VERSÍCULO: quando um verso abre com conectivo minúsculo ("e", "mas", "porque") continuando a oração de um verso anterior que NÃO é o imediatamente precedente (verso anterior fecha citação direta ou parêntese, oração retomada vem de mais atrás), confirme pelo CONTEÚDO que o antecedente pretendido é mesmo esse. Não reescreva pontuação/divisão de versículo por conta própria; é para checar que a leitura não induz o leitor a conectar ao verso errado.

COESÃO DE PARÁGRAFO: contexto.anteriores/posteriores existe para julgar o verso dentro da unidade narrativa/estrófica, não só contra o vizinho imediato. Um verso pode estar perfeito isolado e ainda quebrar o fluxo do parágrafo/estrofe (retomada tardia, conectivo que faz mais sentido com um verso três posições atrás). Julgue nesse nível também.

ORÇAMENTO DE FERRAMENTAS (rígido): (1) Read do digest indicado; (2) Write do arquivo de saída; opcionalmente (3) UMA validação do JSON escrito (python3 -m json.tool via Bash) com re-Write se inválido. Nada além disso. NÃO leia nenhum outro arquivo: as regras deste prompt são a versão destilada e vinculante de revisor-gramatical.md v1.1.0, EDITORIAL.md v1.2.0, DECISOES.md (ER-0011..ER-0027) e do léxico. Dúvida que exigiria consultá-los vira objeção EDITORIAL — nunca decisão própria.

AUTORIDADE (nesta ordem):
1. termos_originais — hebraico pinado (WLC/OSHB) com lemma Strong e morfologia. Teto da fidelidade; nenhuma versão o supera.
2. traducao_literal — camada literal da BV. NUNCA reescrita.
3. controles.kjv — King James 1611, baseline de equivalência formal: serve para conferir se a BV ENTENDEU a mesma coisa, não para ditar estilo. A KJV repousa no Textus Receptus/Ben Chayyim; divergindo da morfologia pinada, a morfologia vence e você anota em nota_textual. Confirme pelo CONTEÚDO dos vizinhos que a KJV está no mesmo versículo — a versificação inglesa diverge da WLC em Salmos, Joel, Malaquias e partes de Êxodo.

O QUE REVISAR (ordem de frequência real):
1. Calque sintático do hebraico: "E aconteceu que", "e eis que", cadeias de waw consecutivo viradas em "e... e... e...". O português narrativo subordina e varia o conectivo; corrigir isso é forma, não sentido.
2. Regência e concordância: verbo sem a preposição que pede, sujeito composto com verbo no singular, particípio sem concordância.
3. Colocação pronominal pela norma culta brasileira: ênclise em início de oração é erro; mesóclise (dar-te-ei) → próclise ou ênclise.
4. Coesão com a janela (contexto.anteriores/posteriores, que CRUZA fronteira de capítulo): pronome sem antecedente recuperável ou ambíguo entre dois referentes; quebra de cadeia temporal (perfeito/imperfeito alternando sem motivo); repetição do sintagma nominal onde o português retomaria por pronome (e elipse que o português não sustenta); conectivo que contradiz a relação lógica com o verso anterior; descontinuidade de tratamento (você/tu) na mesma fala.
5. Sentença acima de ~40 palavras: quebrar, desde que a quebra não invente relação lógica que o hebraico não marca.

NORMA EDITORIAL (EDITORIAL.md v1.2.0, essencial):
- Português brasileiro contemporâneo, AO 1990, registro formal-neutro; confortável em voz alta.
- Arcaísmos proibidos → substituto: mui→muito; porventura→acaso/talvez; deveras→de fato; outrossim→também; destarte→assim; vosso/a(s)→seu/sua(s) (exceto vocativo litúrgico); luzeiros→luminares; tornou-se em→tornou-se/fez-se; mais-que-perfeito sintético (fizera, viera)→composto (tinha feito), exceto fórmula litúrgica consolidada.
- Segunda pessoa: você/vocês entre humanos e de Deus para humanos; tu em oração/salmo dirigido a Deus; distinção singular/plural do original SEMPRE preservada.
- Discurso direto: dois-pontos + aspas duplas curvas; citação dentro de citação em aspas simples; sem travessão.
- Pontuação segue a sintaxe do português, não os acentos massoréticos (o atnach informa, não obriga vírgula).
- Numerais por extenso em texto corrido, inclusive idades e contagens; medidas antigas mantidas (côvado, efa).
- Nomes divinos (política pinada): YHWH→SENHOR; Elohim (Deus de Israel)→Deus; Adonai→Senhor; Adonai YHWH→Senhor DEUS. Desvio observado = objeção, nunca correção própria.
- Pronomes referentes a Deus em minúscula (ele, seu).
- Consistência lexical intra-capítulo: o mesmo lemma hebraico → o mesmo lexema português dentro do capítulo, salvo jogo de palavras, paralelismo sinonímico ou registro distinto exigido pelo contexto. Variação sem razão → normalizar para o lexema majoritário do capítulo, motivo citando §1.4.

NÃO TOQUE: fórmulas intencionais do original (refrões, paralelismo, quiasmo, repetição formular — os refrões dos Salmos são o texto, não vício); semitismos com carga teológica consagrada ("carne e sangue", "filho do homem", "face do SENHOR"); traducao_literal; decisões vigentes de DECISOES.md e do léxico (discordando, objeção EDITORIAL — não reverta por conta própria).

VEREDITOS:
- REVISADO — você corrigiu a forma; toda alteração em mudancas.
- SEM_ALTERACAO — correto e coeso; se havia algo aparente (divergência da KJV, repetição, sentença longa) que você optou por manter, justifique passando pelo teste do CETICISMO acima quando for repetição — nomear a figura ("paralelismo sinonímico", "quiasmo", "acusativo cognato") é resposta legítima; "traço estilístico" sem nomear a figura não é.
- Objeção MATERIAL — a correção só seria possível mudando o sentido; o texto NÃO muda; descreva problema e evidência. É o mecanismo de proteção da fidelidade: use sem hesitar.
- Objeção EDITORIAL — melhoria real que você opta por não aplicar (colide com decisão vigente, exige mudança em vizinho ou em cadeia de capítulos).

REGRAS DURAS DE SAÍDA:
1. JSON estritamente VÁLIDO (escape aspas internas em strings).
2. Preserve as aspas curvas “ ” ‘ ’ do digest — nunca troque por retas.
3. TODA alteração vai em mudancas {tipo, antes, depois, motivo}, tipo em [calque, regencia, concordancia, colocacao, coesao, pontuacao, extensao] — edição não registrada é descartada na persistência.
4. Cobertura exata: um objeto de saída por verso do digest, na mesma ordem.
5. Verso com objeção MATERIAL tem texto_bv_revisto IDÊNTICO à entrada.
6. Cada objeção é {"gravidade", "problema", "evidencia"} com gravidade exatamente "MATERIAL" ou "EDITORIAL" — o campo chama-se gravidade, NÃO tipo (tipo classifica a MUDANÇA); objeção sem gravidade é recusada na persistência.
7. Você vê o contexto para JULGAR, mas só edita o verso corrente — correção que exigiria mexer no vizinho vira objeção EDITORIAL dizendo qual.

PROCEDIMENTO por verso: (1) leia-o dentro da janela; (2) confira contra termos_originais o que o hebraico diz e contra a KJV se o sentido bate; (3) corrija a FORMA do português; (4) correção que mudaria o sentido → objeção MATERIAL; (5) verso correto → SEM_ALTERACAO com justificativa quando houver algo aparente mantido.

`

async function reviewChapter(ch) {
  const pad = String(ch.chapter).padStart(3, '0')
  const digest = REPO + '/qa/reports/grammar-input/' + ch.book_dir + '-' + pad + '.json'
  const out = REPO + '/qa/reports/review-out/' + ch.book_dir + '-' + pad + '.json'
  const summary = await agent(RULES +
    'CAPÍTULO: ' + ch.book_dir + '/' + pad + '.\n' +
    '1) Read do digest ' + digest + ' (osis, texto_bv, traducao_literal, termos_originais, contexto, controles.kjv por verso).\n' +
    '2) Write do JSON de saída COMPLETO em ' + out + ': { "book_dir": "' + ch.book_dir + '", "chapter": ' + ch.chapter + ', "versos": [ { osis, texto_bv_revisto, mudancas, objecoes, justificativa, veredito } ... ] } — TODOS os versos do digest, na mesma ordem.\n' +
    '3) Retorne APENAS o resumo: { book_dir: "' + ch.book_dir + '", chapter: ' + ch.chapter + ', revisados: <versos com mudancas>, sem_alteracao: <mantidos>, objecoes_materiais: <nº MATERIAL> }.',
    { label: 'gram:' + ch.book_dir + '/' + pad, phase: 'Revisar', schema: SUMMARY, model: MODEL })
  return summary || { book_dir: ch.book_dir, chapter: ch.chapter, revisados: 0, sem_alteracao: 0, objecoes_materiais: 0 }
}

const results = await parallel(CHAPTERS.map(ch => () => reviewChapter(ch)))
return { chapters: results.filter(Boolean) }
