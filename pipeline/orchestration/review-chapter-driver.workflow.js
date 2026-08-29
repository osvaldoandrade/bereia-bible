// Editorial review driver for DRAFT hot-spots (ER-0019 v2, PIPELINE.md v1.2.0).
// ONE agent per hot chapter, up to 16 chapters in parallel. Each agent reads
// the canonical prompt (pipeline/prompts/revisor-editorial-draft.md v1.2.0),
// the chapter digest produced by scripts/qa_linguistico.py -refs
// (qa/reports/review-input/<book_dir>-<cap>.json — carries texto_bv,
// traducao_literal, static findings, AND parallel PT-BR references from
// NTLH/ARA/NVIPT), adjudicates each finding AND reference divergence
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
  description: 'Editorial review of DRAFT hot-spot chapters with PT-BR reference comparison (ER-0019 v2)',
  phases: [{ title: 'Revisar', detail: 'até 16 threads; um agente por capítulo hot, comparação guiada por NTLH/ARA/NVIPT' }],
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

const preamble = 'Você é o revisor editorial da Bereia Version (BV), etapa de revisão do tier DRAFT (ER-0019 v2, PIPELINE.md v1.2.0). Sua mudança é somente de FORMA — nunca de sentido.\n' +
  'LEIA, nesta ordem: ' + REPO + '/pipeline/prompts/revisor-editorial-draft.md (v1.2.0, seu papel, regras duras de saída E comparação guiada com NTLH/ARA/NVIPT); ' + REPO + '/pipeline/rules/EDITORIAL.md (v1.2.0, autoridade de forma — incl. §1.2-tabela de arcaísmos e §1.4 de consistência lexical); ' + REPO + '/decisions/DECISOES.md (ER-0011..ER-0019, vinculantes); ' + REPO + '/lexicon/lexicon.json (só se precisar de consistência terminológica).\n' +
  'Paradigma de 2ª pessoa (§3/D-0003): humano↔humano e Deus→humano = você/vocês; oração a Deus = tu. Se o capítulo usa vós onde §3 pede vocês, normalize o capítulo INTEIRO coerentemente (item 10 do prompt canônico).\n' +
  'Saída: JSON estritamente VÁLIDO; preserve as aspas curvas “ ” ‘ ’ do digest (nunca as troque por aspas retas); TODA alteração deve estar registrada em mudancas — edição não registrada é descartada na persistência.\n' +
  'Regras duras: (1) correção que exija mudança de sentido vira objeção MATERIAL — o texto NÃO muda; (2) fórmulas intencionais do original (refrões, paralelismo, quiasmos, repetições formularies) são MANTIDAS mesmo quando a triagem as flagrou; (3) traducao_literal nunca é reescrita; (4) cobertura OSIS idêntica ao digest.\n' +
  'NOVO v1.2 — comparação guiada: cada verso do digest traz "referencias": { NTLH, ARA, NVIPT }. ANTES de decidir SEM_ALTERACAO, compare: se as 3 referências divergem da BV, investigue arcaísmo/inconsistência. Exemplo: Gn 1.14 "luzeiros" (BV) vs "luminares" (ARA/NVIPT) / "luzes" (NTLH) — mudar para "luminares" (EDITORIAL §1.4). Anti-rubber-stamp: verso com achado ativo OU divergência significativa das refs exige justificativa se você optar por SEM_ALTERACAO.\n'

async function reviewChapter(ch) {
  const pad = String(ch.chapter).padStart(3, '0')
  const digest = REPO + '/qa/reports/review-input/' + ch.book_dir + '-' + pad + '.json'
  const out = REPO + '/qa/reports/review-out/' + ch.book_dir + '-' + pad + '.json'
  const summary = await agent(preamble +
    'CAPÍTULO: ' + ch.book_dir + '/' + pad + '. Leia o digest ' + digest + ': ele traz TODOS os versículos DRAFT do capítulo (osis, texto_bv atual, traducao_literal, achados da triagem estática, E referencias NTLH/ARA/NVIPT — schema v2).\n' +
    'Para cada verso: (1) adjudique os achados da triagem; (2) COMPARE com as referências NTLH/ARA/NVIPT — se as 3 divergem da BV em palavra-chave, investigar arcaísmo/inconsistência (ver EDITORIAL §1.2-tabela e §1.4); (3) aplique correção de forma OU mantenha o texto com justificativa adequada (fórmula intencional, achado falso-positivo, etc.) OU registre objeção (MATERIAL se a correção exigiria mudar sentido; EDITORIAL se for melhoria que você opta por não aplicar agora, com problema+evidência). Versículo sem achado E sem divergência das refs: mantenha como está (SEM_ALTERACAO).\n' +
    'Escreva o JSON de saída COMPLETO no arquivo ' + out + ' usando a ferramenta Write, no formato definido no prompt canônico v1.2: { "book_dir": "' + ch.book_dir + '", "chapter": ' + ch.chapter + ', "versos": [ { osis, texto_bv_revisto, mudancas, objecoes, justificativa (obrigatório quando há achado OU divergência das refs e veredito é SEM_ALTERACAO), veredito } ... ] } com TODOS os versículos do digest, na mesma ordem.\n' +
    'Depois de escrever o arquivo, retorne APENAS o resumo: { book_dir: "' + ch.book_dir + '", chapter: ' + ch.chapter + ', revisados: <nº de versos com mudancas aplicadas>, sem_alteracao: <nº de versos mantidos>, objecoes_materiais: <nº de objeções MATERIAL> }.',
    { label: 'rev:' + ch.book_dir + '/' + pad, phase: 'Revisar', schema: SUMMARY })
  return summary || { book_dir: ch.book_dir, chapter: ch.chapter, revisados: 0, sem_alteracao: 0, objecoes_materiais: 0 }
}

const results = await parallel(CHAPTERS.map(ch => () => reviewChapter(ch)))
return { chapters: results.filter(Boolean) }
