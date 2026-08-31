// Grammar/cohesion review driver for the OT (ER-0022).
// ONE agent per chapter, up to 16 in parallel. Each agent reads the canonical
// prompt (pipeline/prompts/revisor-gramatical.md v1.0.0) and the digest built
// by scripts/build_grammar_review_input.py — which carries texto_bv,
// traducao_literal, the PINNED termos_originais (fidelity ceiling), a context
// window of N verses each side CROSSING chapter boundaries, and the KJV as
// English formal-equivalence control — then fixes Portuguese form, writes its
// output to qa/reports/review-out/<book_dir>-<cap>.json and returns a summary.
//
// Persistence reuses scripts/ship_review_batch.py -status APPROVED: the
// output contract is the ER-0019 one (mudancas/objecoes/veredito), so the
// same guards apply — exact OSIS coverage, MATERIAL => text unchanged, every
// edit logged in mudancas. The corpus is APPROVED since ER-0021, hence the
// explicit status scope.
//
// args = { chapters: [ { book_dir, chapter } ... up to 16 ], model }
export const meta = {
  name: 'bv-grammar-review-driver',
  description: 'Grammar and cohesion review of the OT against the pinned Hebrew, with context window and KJV control (ER-0022)',
  phases: [{ title: 'Revisar', detail: 'até 16 threads; um agente por capítulo, janela de contexto ±N e KJV' }],
}
const REPO = '/Users/ova/GolandProjects/bereia-bible'
let A = args || {}
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
// Model is provenance-bearing: must equal the -modelo passed to
// scripts/ship_review_batch.py (ER-0010 re-pin of `fontes`).
const MODEL = A.model || 'fable'
const CHAPTERS = (A.chapters || []).slice(0, 16)

const S = { type: 'string' }
const I = { type: 'integer' }
const SUMMARY = {
  type: 'object',
  additionalProperties: true,
  required: ['book_dir', 'chapter', 'revisados', 'sem_alteracao', 'objecoes_materiais'],
  properties: { book_dir: S, chapter: I, revisados: I, sem_alteracao: I, objecoes_materiais: I },
}

const preamble = 'Você é o revisor gramatical e de coesão da Bereia Version (BV), etapa ER-0022. Objetivo: português correto e coeso, SEM jamais comprar coesão com fidelidade.\n' +
  'REGRA QUE GOVERNA TUDO: fidelidade às Escrituras é o TETO; norma culta e coesão são o PISO. O texto tem de dizer exatamente o que o hebraico diz, num português que um leitor brasileiro culto leia sem tropeçar. Quando as duas exigências colidem, a FIDELIDADE VENCE e você registra objeção MATERIAL — nunca o contrário. Mas na esmagadora maioria dos casos não há colisão: o defeito é calque sintático, regência, concordância ou pronome sem antecedente, que se corrige sem tocar no sentido.\n' +
  'LEIA, nesta ordem: ' + REPO + '/pipeline/prompts/revisor-gramatical.md (v1.0.0 — seu papel, o que revisar, o que não tocar, vereditos, regras duras de saída); ' + REPO + '/pipeline/rules/EDITORIAL.md (autoridade de forma); ' + REPO + '/decisions/DECISOES.md (ER-0011..ER-0021, vinculantes); ' + REPO + '/lexicon/lexicon.json (consistência terminológica).\n' +
  'AUTORIDADE: `termos_originais` do digest é o hebraico pinado (WLC/OSHB) com lemma Strong e morfologia — é o teto da fidelidade. `controles.kjv` é baseline de equivalência formal para conferir se a BV ENTENDEU a mesma coisa, não para ditar estilo: o inglês de 1611 não é modelo de português de 2026. A KJV repousa no Textus Receptus/Ben Chayyim; divergindo da morfologia pinada, a morfologia vence e você anota em `nota_textual`. Confirme pelo CONTEÚDO dos `vizinhos` que a KJV está no mesmo versículo antes de usá-la — a versificação WLC diverge da inglesa em Salmos, Joel, Malaquias e partes de Êxodo.\n' +
  'CONTEXTO: cada verso traz `contexto.anteriores` e `contexto.posteriores` (janela de N versos, que CRUZA fronteira de capítulo). Use-os para julgar coesão: pronome sem antecedente recuperável ou ambíguo entre dois referentes; quebra de cadeia temporal (perfeito/imperfeito alternando sem motivo); repetição do sintagma nominal onde o português retomaria por pronome; conectivo que contradiz a relação lógica com o verso anterior; descontinuidade de tratamento (você/tu) na mesma fala. Você vê o contexto para JULGAR, mas só edita o verso corrente — se a correção exigir mexer no vizinho, registre objeção EDITORIAL dizendo qual.\n' +
  'NÃO TOQUE: fórmulas intencionais do original (refrões, paralelismo, quiasmo, repetição formular — os refrões dos Salmos são o texto, não vício de redação); semitismos com carga teológica consagrada ("carne e sangue", "filho do homem", "face do SENHOR"); `traducao_literal`; decisões já tomadas em DECISOES.md e no léxico (discordando, objeção EDITORIAL — não reverta por conta própria).\n' +
  'REGRAS DURAS: (1) JSON estritamente VÁLIDO; (2) preserve as aspas curvas “ ” ‘ ’ — nunca troque por retas; (3) TODA alteração vai em `mudancas` {tipo, antes, depois, motivo}, com tipo em [calque, regencia, concordancia, colocacao, coesao, pontuacao, extensao] — edição não registrada é descartada na persistência; (4) cobertura exata: um objeto de saída por verso do digest, na mesma ordem; (5) verso com objeção MATERIAL tem `texto_bv_revisto` IDÊNTICO à entrada; (6) cada objeção é o objeto {"gravidade", "problema", "evidencia"} com gravidade exatamente "MATERIAL" ou "EDITORIAL" — o campo chama-se `gravidade`, NÃO `tipo` (`tipo` classifica a MUDANÇA, é outra coisa); objeção sem `gravidade` é recusada na persistência.\n'

async function reviewChapter(ch) {
  const pad = String(ch.chapter).padStart(3, '0')
  const digest = REPO + '/qa/reports/grammar-input/' + ch.book_dir + '-' + pad + '.json'
  const out = REPO + '/qa/reports/review-out/' + ch.book_dir + '-' + pad + '.json'
  const summary = await agent(preamble +
    'CAPÍTULO: ' + ch.book_dir + '/' + pad + '. Leia o digest ' + digest + ': traz TODOS os versículos do capítulo com osis, texto_bv, traducao_literal, termos_originais, contexto (anteriores/posteriores) e controles.kjv.\n' +
    'Para cada verso: (1) leia-o dentro da janela de contexto; (2) confira contra `termos_originais` o que o hebraico realmente diz e contra a KJV se o sentido bate; (3) corrija a FORMA do português — calque sintático, regência, concordância, colocação pronominal, coesão com os vizinhos, pontuação, sentenças acima de ~40 palavras; (4) se a correção exigir mudar o sentido, NÃO mude: registre objeção MATERIAL com problema e evidência; (5) verso já correto e coeso fica SEM_ALTERACAO — e se havia algo aparente (divergência da KJV, repetição, sentença longa) que você optou por manter, justifique (fórmula intencional e paralelismo do original são respostas legítimas e esperadas).\n' +
    'Escreva o JSON de saída COMPLETO no arquivo ' + out + ' usando a ferramenta Write: { "book_dir": "' + ch.book_dir + '", "chapter": ' + ch.chapter + ', "versos": [ { osis, texto_bv_revisto, mudancas, objecoes, justificativa, veredito } ... ] } com TODOS os versículos do digest, na mesma ordem.\n' +
    'Depois de escrever o arquivo, retorne APENAS o resumo: { book_dir: "' + ch.book_dir + '", chapter: ' + ch.chapter + ', revisados: <nº de versos com mudancas aplicadas>, sem_alteracao: <nº mantidos>, objecoes_materiais: <nº de objeções MATERIAL> }.',
    { label: 'gram:' + ch.book_dir + '/' + pad, phase: 'Revisar', schema: SUMMARY, model: MODEL })
  return summary || { book_dir: ch.book_dir, chapter: ch.chapter, revisados: 0, sem_alteracao: 0, objecoes_materiais: 0 }
}

const results = await parallel(CHAPTERS.map(ch => () => reviewChapter(ch)))
return { chapters: results.filter(Boolean) }
