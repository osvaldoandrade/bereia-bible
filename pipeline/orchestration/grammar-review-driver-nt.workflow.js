// Lean grammar/cohesion review driver for the NT (ER-0024).
//
// Fork of grammar-review-driver-v2.workflow.js (ER-0022, AT) with the same
// lean contract — ONE Read (digest) + ONE Write (review-out), inline
// distilled rules, up to 16 parallel threads — but the original-language
// framing swapped: `termos_originais` here is Greek (Nestle 1904), not
// Hebrew (WLC/OSHB), and the KJV control rests on the Textus Receptus,
// which for the NT means STRUCTURAL divergence (interpolated verses/clauses
// the critical text doesn't have), not just translation-style drift. The
// RULES below add an explicit TR-barrier paragraph for that reason — same
// discipline ADR-0005 already enforces at the adjudication layer (ER-0020),
// pulled forward into the grammar pass so a reviewer never raises a false
// "the BV is missing words" objection against a known TR-only clause.
//
// Distilled from pipeline/prompts/revisor-gramatical-nt.md v1.0.0 and
// pipeline/rules/EDITORIAL.md v1.2.0 (Bible-wide, unchanged) — re-distill
// here if either changes.
//
// Persistence unchanged: scripts/ship_review_batch.py -status APPROVED
// -er ER-0024 -modelo <model>, same guards (exact OSIS coverage, MATERIAL
// => text unchanged, every edit logged in mudancas).
//
// args = { chapters: [ { book_dir, chapter } ... up to 16 ], model }
export const meta = {
  name: 'bv-grammar-review-driver-nt',
  description: 'Lean grammar and cohesion review of the NT — inline rules, 2 tool calls per chapter (ER-0024)',
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

const RULES = `Você é o revisor gramatical e de coesão da Bereia Version (BV), etapa ER-0024 (NT). Objetivo: português correto e coeso, SEM jamais comprar coesão com fidelidade.

REGRA QUE GOVERNA TUDO: fidelidade às Escrituras é o TETO; norma culta e coesão são o PISO. O texto tem de dizer exatamente o que o grego diz, num português que um leitor brasileiro culto leia sem tropeçar. Quando as duas exigências colidem, a FIDELIDADE VENCE e você registra objeção MATERIAL — nunca o contrário. Na esmagadora maioria dos casos não há colisão: o defeito é calque, regência, concordância ou pronome sem antecedente, que se corrige sem tocar no sentido.

ORÇAMENTO DE FERRAMENTAS (rígido): (1) Read do digest indicado; (2) Write do arquivo de saída; opcionalmente (3) UMA validação do JSON escrito (python3 -m json.tool via Bash) com re-Write se inválido. Nada além disso. NÃO leia nenhum outro arquivo: as regras deste prompt são a versão destilada e vinculante de revisor-gramatical-nt.md v1.0.0, EDITORIAL.md v1.2.0, DECISOES.md (ER-0011..ER-0023) e do léxico. Dúvida que exigiria consultá-los vira objeção EDITORIAL — nunca decisão própria.

AUTORIDADE (nesta ordem):
1. termos_originais — grego pinado (Nestle 1904) com lemma e morfologia. Teto da fidelidade; nenhuma versão o supera.
2. traducao_literal — camada literal da BV. NUNCA reescrita.
3. controles.kjv — King James 1611, baseline de equivalência formal: serve para conferir se a BV ENTENDEU a mesma coisa, não para ditar estilo. A KJV do NT repousa no Textus Receptus, base distinta do Nestle 1904 que a BV segue.

DETECTOR TEXTUAL (mais crítico aqui que no AT): a divergência KJV×Nestle 1904 no NT não é ocasional, é ESTRUTURAL — o TR tem trechos que o texto crítico não tem. Loci clássicos: Mt 6.13 (doxologia final do Pai-Nosso), Mc 16.9-20 (final longo), Jo 5.4 (anjo agitando a água), Jo 7.53-8.11 (pericope adulterae), At 8.37 (confissão do eunuco), 1Jo 5.7-8 (Comma Johanneum). Se a KJV tem palavras/cláusula que os termos_originais pinados do verso não sustentam, é VARIANTE TEXTUAL, não erro de tradução — NUNCA vira objeção MATERIAL de "faltou traduzir algo", e jamais motivo para completar o texto_bv com a leitura da KJV. Registre em justificativa quando relevante; a barreira ao TR (ADR-0005) não se negocia nesta etapa.

O QUE REVISAR (ordem de frequência real):
1. Calque sintático do grego: genitivo absoluto vertido literalmente ("e tendo ele dito isto" em vez de reestruturado), cadeias de particípio empilhadas, parataxe com καί enfileirado ("e... e... e..."). O português narrativo subordina e varia o conectivo; corrigir isso é forma, não sentido.
2. Regência e concordância: verbo sem a preposição que pede, sujeito composto com verbo no singular, particípio sem concordância.
3. Colocação pronominal pela norma culta brasileira: ênclise em início de oração é erro; mesóclise (dar-te-ei) → próclise ou ênclise.
4. Coesão com a janela (contexto.anteriores/posteriores, que CRUZA fronteira de capítulo): pronome sem antecedente recuperável ou ambíguo entre dois referentes; quebra de cadeia temporal (aoristo/presente histórico alternando sem motivo); repetição do sintagma nominal onde o português retomaria por pronome (e elipse que o português não sustenta); conectivo que contradiz a relação lógica com o verso anterior (δέ adversativo vertido como aditivo, οὖν consecutivo perdido); descontinuidade de tratamento (você/tu) na mesma fala.
5. Sentença acima de ~40 palavras (comum no grego epistolar — Paulo, Hebreus): quebrar, desde que a quebra não invente relação lógica que o original não marca.

NORMA EDITORIAL (EDITORIAL.md v1.2.0, essencial):
- Português brasileiro contemporâneo, AO 1990, registro formal-neutro; confortável em voz alta.
- Arcaísmos proibidos → substituto: mui→muito; porventura→acaso/talvez; deveras→de fato; outrossim→também; destarte→assim; vosso/a(s)→seu/sua(s) (exceto vocativo litúrgico); luzeiros→luminares; tornou-se em→tornou-se/fez-se; mais-que-perfeito sintético (fizera, viera)→composto (tinha feito), exceto fórmula litúrgica consolidada.
- Segunda pessoa: você/vocês entre humanos e de Deus para humanos; tu em oração/salmo dirigido a Deus; distinção singular/plural do original SEMPRE preservada.
- Discurso direto: dois-pontos + aspas duplas curvas; citação dentro de citação em aspas simples; sem travessão.
- Numerais por extenso em texto corrido, inclusive idades e contagens; medidas antigas mantidas (côvado, efa, talento, dracma).
- Nomes divinos e cristológicos (política já vigente no texto_bv aprovado): não são decisão sua — se discordar de como θεός/κύριος/Ἰησοῦς Χριστός está vertido, é objeção EDITORIAL, nunca correção própria.
- Pronomes referentes a Deus/Jesus em minúscula (ele, seu), salvo onde o texto_bv aprovado já usa maiúscula por consistência de capítulo — não normalize por conta própria.
- Consistência lexical intra-capítulo: o mesmo lemma grego → o mesmo lexema português dentro do capítulo, salvo jogo de palavras, paralelismo sinonímico ou registro distinto exigido pelo contexto. Variação sem razão → normalizar para o lexema majoritário do capítulo, motivo citando §1.4.

NÃO TOQUE: fórmulas intencionais do original (o "Amém, amém" joanino, refrões do Apocalipse, fórmulas litúrgicas paulinas — são o texto, não vício); semitismos/grecismos com carga teológica consagrada ("carne e sangue", "filho do homem", "em Cristo", "segundo a carne"); traducao_literal; decisões vigentes de DECISOES.md e do léxico (discordando, objeção EDITORIAL — não reverta por conta própria); divergência textual TR×Nestle 1904 (ver Detector acima — nunca "corrigida" na direção da KJV).

VEREDITOS:
- REVISADO — você corrigiu a forma; toda alteração em mudancas.
- SEM_ALTERACAO — correto e coeso; se havia algo aparente (divergência da KJV — inclusive textual —, repetição, sentença longa) que você optou por manter, justifique ("variante textual TR", "fórmula intencional", "paralelismo do original" são respostas legítimas e esperadas).
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

PROCEDIMENTO por verso: (1) leia-o dentro da janela; (2) confira contra termos_originais o que o grego diz e contra a KJV se o sentido bate — se a KJV tiver palavras que o grego pinado não tem, é variante textual (detector acima), não erro da BV; (3) corrija a FORMA do português; (4) correção que mudaria o sentido → objeção MATERIAL; (5) verso correto → SEM_ALTERACAO com justificativa quando houver algo aparente mantido.

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
    { label: 'gramnt:' + ch.book_dir + '/' + pad, phase: 'Revisar', schema: SUMMARY, model: MODEL })
  return summary || { book_dir: ch.book_dir, chapter: ch.chapter, revisados: 0, sem_alteracao: 0, objecoes_materiais: 0 }
}

const results = await parallel(CHAPTERS.map(ch => () => reviewChapter(ch)))
return { chapters: results.filter(Boolean) }
