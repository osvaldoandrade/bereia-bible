// Editorial review driver for DRAFT hot-spots (ER-0019, PIPELINE.md v1.2.0).
// ONE agent per hot chapter, up to 16 chapters in parallel. Each agent reads
// the canonical prompt (pipeline/prompts/revisor-editorial-draft.md v1.0.0),
// the chapter digest produced by scripts/qa_linguistico.py
// (qa/reports/review-input/<book_dir>-<cap>.json — carries texto_bv,
// traducao_literal and the static findings), adjudicates each finding
// (FORM-only fixes; intentional formulas kept; meaning changes forbidden and
// reported as MATERIAL objections), then WRITES its output to
// qa/reports/review-out/<book_dir>-<cap>.json and returns only a small
// summary. Persistence is mechanical (scripts/persist_review.py) and enforces
// the hard guards (exact OSIS coverage, MATERIAL => text unchanged, DRAFT-only).
// Agents write their own output files, so a hung aggregation (F-0014) never
// loses work — recovery = rerun persist on the files already on disk.
//
// args = { chapters: [ { book_dir, chapter } ... up to 16 ] }
export const meta = {
  name: 'bv-review-chapter-driver',
  description: 'Editorial review of DRAFT hot-spot chapters, 1 agent/chapter, up to 16 in parallel (ER-0019)',
  phases: [{ title: 'Revisar', detail: 'até 16 threads; um agente por capítulo hot' }],
}
const REPO = '/Users/ova/GolandProjects/bereia-bible'
let A = args || {}
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
const CHAPTERS = (A.chapters || []).slice(0, 16)

const S = { type: 'string' }
const I = { type: 'integer' }
const SUMMARY = {
  type: 'object',
  additionalProperties: true,
  required: ['book_dir', 'chapter', 'revisados', 'sem_alteracao', 'objecoes_materiais'],
  properties: { book_dir: S, chapter: I, revisados: I, sem_alteracao: I, objecoes_materiais: I },
}

const preamble = 'Você é o revisor editorial da Bereia Version (BV), etapa de revisão do tier DRAFT (ER-0019, PIPELINE.md v1.2.0). Sua mudança é somente de FORMA — nunca de sentido.\n' +
  'LEIA, nesta ordem: ' + REPO + '/pipeline/prompts/revisor-editorial-draft.md (v1.0.0, seu papel e regras duras de saída); ' + REPO + '/pipeline/rules/EDITORIAL.md (v1.1.0, autoridade de forma); ' + REPO + '/decisions/DECISOES.md (ER-0011..ER-0019, vinculantes); ' + REPO + '/lexicon/lexicon.json (só se precisar de consistência terminológica).\n' +
  'Regras duras: (1) correção que exija mudança de sentido vira objeção MATERIAL — o texto NÃO muda; (2) fórmulas intencionais do original (refrões, paralelismo, quiasmos, repetições formularies) são MANTIDAS mesmo quando a triagem as flagrou; (3) traducao_literal nunca é reescrita; (4) cobertura OSIS idêntica ao digest.\n'

async function reviewChapter(ch) {
  const pad = String(ch.chapter).padStart(3, '0')
  const digest = REPO + '/qa/reports/review-input/' + ch.book_dir + '-' + pad + '.json'
  const out = REPO + '/qa/reports/review-out/' + ch.book_dir + '-' + pad + '.json'
  const summary = await agent(preamble +
    'CAPÍTULO: ' + ch.book_dir + '/' + pad + '. Leia o digest ' + digest + ': ele traz TODOS os versículos DRAFT do capítulo (osis, texto_bv atual, traducao_literal), cada um com sua lista de achados da triagem estática (vazia quando nada foi flagrado).\n' +
    'Adjudique cada achado: aplique correção editorial de forma (texto_bv_revisto + mudancas com antes/depois/motivo) OU mantenha o texto (fórmula intencional, achado falso-positivo) OU registre objeção (MATERIAL se a correção exigiria mudar sentido; EDITORIAL se for melhoria que você opta por não aplicar agora, com problema+evidência). Versículo sem achado: mantenha como está.\n' +
    'Escreva o JSON de saída COMPLETO no arquivo ' + out + ' usando a ferramenta Write, no formato definido no prompt canônico: { "book_dir": "' + ch.book_dir + '", "chapter": ' + ch.chapter + ', "versos": [ { osis, texto_bv_revisto, mudancas, objecoes, veredito } ... ] } com TODOS os versículos do digest, na mesma ordem.\n' +
    'Depois de escrever o arquivo, retorne APENAS o resumo: { book_dir: "' + ch.book_dir + '", chapter: ' + ch.chapter + ', revisados: <nº de versos com mudancas aplicadas>, sem_alteracao: <nº de versos mantidos>, objecoes_materiais: <nº de objeções MATERIAL> }.',
    { label: 'rev:' + ch.book_dir + '/' + pad, phase: 'Revisar', schema: SUMMARY })
  return summary || { book_dir: ch.book_dir, chapter: ch.chapter, revisados: 0, sem_alteracao: 0, objecoes_materiais: 0 }
}

const results = await parallel(CHAPTERS.map(ch => () => reviewChapter(ch)))
return { chapters: results.filter(Boolean) }
