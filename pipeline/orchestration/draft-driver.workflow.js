// DRAFT-tier driver: translate up to 5 chapters in parallel (5 threads), each
// verse through a lean pipeline (translator -> fidelity refuter -> 1 revision
// if reproved). Produces status=DRAFT records (ADR-0002/ER-0016). Returns
// records grouped by chapter; the caller persists, updates lexicon/PROGRESS,
// and commits per chapter.
//
// args = { fontes:{...}, chapters:[ { book, chapter, from, to, packet } ... up to 5 ] }
export const meta = {
  name: 'bv-draft-driver',
  description: 'DRAFT-tier translation of up to 5 chapters in parallel (OT, OSHB)',
  phases: [{ title: 'Traduzir', detail: '5 threads de capítulo; versículos no tier DRAFT' }],
}
const REPO = '/Users/ova/GolandProjects/bereia-bible'
const RULES = REPO + '/pipeline/rules'
const PROMPTS = REPO + '/pipeline/prompts'
let A = args || {}
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
const FONTES = A.fontes || {
  texto_fonte: 'oshb@3d15126f',
  manifest_sha256: 'a89a122f983e9953398176492f7dcc53debf80ebf072e5f5841113a51a2c824d',
  prompts_versao: '1.0.0', regras_versao: '1.1.0', lexico_versao: '0.5.1', modelo: 'claude-fable-5',
}
const CHAPTERS = (A.chapters || []).slice(0, 5)

const S = { type: 'string' }, B = { type: 'boolean' }
const arr = (i) => ({ type: 'array', items: i })
const obj = (p, r) => ({ type: 'object', additionalProperties: true, required: r, properties: p })
const RECORD = obj({}, ['schema_version', 'referencia', 'texto_bv', 'traducao_literal', 'termos_originais', 'variantes_textuais', 'decisoes', 'justificativa', 'confianca', 'status', 'ciclos_consenso', 'fontes'])
const DRAFT = obj({ registro: RECORD, notas: S }, ['registro', 'notas'])
const VERDICT = obj({ veredito: { enum: ['APROVA', 'REPROVA'] }, objecoes: arr(obj({ alvo: S, gravidade: { enum: ['MATERIAL', 'EDITORIAL'] }, problema: S, evidencia: S }, ['alvo', 'gravidade', 'problema', 'evidencia'])) }, ['veredito', 'objecoes'])

const preamble = 'Você é agente do pipeline da Bereia Version (BV), tradução bíblica pt-BR auditável até o hebraico pinado (OSHB).\n' +
  'LEIA: ' + RULES + '/EDITORIAL.md (v1.1.0); ' + RULES + '/TEOLOGIA.md; ' + RULES + '/MORFOLOGIA-OSHB.md; ' + RULES + '/NOMES-DIVINOS.md; ' + REPO + '/decisions/DECISOES.md (ER-0011..0016 VINCULANTES); ' + REPO + '/lexicon/lexicon.json.\n' +
  'REGISTRO EDITORIAL RATIFICADO (aplique sempre): S-V uniforme incl. "E Deus disse:" (ER-0011); nomeação minúscula "chamou X de y" (ER-0012); doutrina do calque (ER-0013: traducao_literal preserva TODOS os calques — waw integral, repetição de sujeito, quiasmos, ordem V-S — e o publicado normaliza com registro); fórmula de aprovação "Deus viu que era bom" (כי completivo "que"); refrão de dia com ordinal a partir do 2º; distinção criar(H1254a)/fazer(H6213); nomes divinos ER-0002; מִין por valor lexical sem concordismo (TEOLOGIA §2).\n' +
  'TIER DRAFT (ADR-0002/ER-0016): rigor de rascunho auditável — confianca MÁXIMA 0,80; status "DRAFT"; ciclos_consenso 1. Sem as 4 vozes independentes; por isso o texto é rascunho, não publicável.\n'

async function draftVerse(ch, n) {
  const osis = ch.book + '.' + ch.chapter + '.' + n
  const ctx = preamble +
    'FONTE: leia o packet ' + ch.packet + ' e traduza SOMENTE ' + osis + ' (os demais versos são contexto). As perícopes já APROVADAS estão em ' + REPO + '/translation/01-gn/.\n' +
    'METADADOS fontes (ER-0010, exatamente): ' + JSON.stringify(FONTES) + '\n' +
    'Referência: osis "' + osis + '", livro "Gênesis", capitulo ' + ch.chapter + ', versiculo ' + n + ', pericope "' + (ch.pericope || (ch.book + '.' + ch.chapter + '.' + ch.from + '-' + ch.to)) + '".\n'
  let draft = await agent(ctx +
    'Tarefa (TRADUTOR DRAFT): produza o registro COMPLETO do versículo conforme ' + REPO + '/api/verse-record.schema.json — texto_bv (aplicando o registro editorial), traducao_literal (preservando calques), termos_originais cobrindo TODAS as palavras type=word (palavra, translit, lemma, morfologia, glosa), decisoes das escolhas não-triviais com alternativas_rejeitadas, variantes_textuais relevantes, ambiguidades_preservadas, palavras_supridas, justificativa, confianca (≤0,80), status "DRAFT", ciclos_consenso 1, fontes. Sem campos extras fora do schema.',
    { label: 'draft:' + osis, phase: 'Traduzir', schema: DRAFT })
  if (!draft) return null
  const verdict = await agent(ctx +
    'Tarefa (REFUTADOR DE FIDELIDADE): audite este registro DRAFT contra o hebraico do packet e o registro editorial.\n' + JSON.stringify(draft.registro, null, 1) +
    '\nRefute só o MATERIAL: (1) texto perdeu/alterou conteúdo do hebraico não recuperável pela literal; (2) morfologia/lema errados nos termos_originais; (3) glosa fixada do léxico violada sem justificativa; (4) viés/concordismo (esp. מִין); (5) português agramatical; (6) confianca>0,80 ou status≠DRAFT. Editorial (estilo) não reprova. Se nada material: APROVA.',
    { label: 'refut:' + osis, phase: 'Traduzir', schema: VERDICT })
  if (verdict && verdict.veredito === 'REPROVA' && verdict.objecoes.some(o => o.gravidade === 'MATERIAL')) {
    const rev = await agent(ctx +
      'Tarefa (REVISÃO): seu registro DRAFT recebeu objeções MATERIAIS. Corrija-as e reemita o registro COMPLETO (mesmo schema, status DRAFT, confianca ≤0,80).\nREGISTRO:\n' + JSON.stringify(draft.registro, null, 1) +
      '\nOBJEÇÕES:\n' + JSON.stringify(verdict.objecoes.filter(o => o.gravidade === 'MATERIAL'), null, 1),
      { label: 'rev:' + osis, phase: 'Traduzir', schema: DRAFT })
    if (rev) draft = rev
  }
  return draft.registro
}

async function draftChapter(ch) {
  const verses = []
  for (let n = ch.from; n <= ch.to; n++) verses.push(n)
  const regs = await pipeline(verses, (n) => draftVerse(ch, n))
  return { book: ch.book, chapter: ch.chapter, registros: regs.filter(Boolean) }
}

const results = await parallel(CHAPTERS.map(ch => () => draftChapter(ch)))
return { chapters: results.filter(Boolean) }
