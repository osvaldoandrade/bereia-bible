// Chapter-level DRAFT driver (ADR-0002, revised per maintainer): ONE agent per
// chapter, up to 5 chapters in parallel (5 threads). The agent applies the
// ratified editorial register and produces, per verse, only the judgment
// fields (texto_bv, traducao_literal, decisoes, justificativa, confianca).
// It does NOT re-emit per-word morphology — that is assembled mechanically
// from the pinned packet by scripts/persist_chapter_draft.py (F-0015), so the
// audit glyphs are always authoritative and this stays ~50x lighter than the
// per-verse driver.
//
// args = { fontes:{...}, chapters:[ { book, chapter, from, to, packet, pericope } ... up to 5 ] }
export const meta = {
  name: 'bv-draft-chapter-driver',
  description: 'Chapter-level DRAFT translation, 1 agent/chapter, up to 5 chapters in parallel',
  phases: [{ title: 'Traduzir', detail: '5 threads; um agente por capítulo' }],
}
const REPO = '/Users/ova/GolandProjects/bereia-bible'
const RULES = REPO + '/pipeline/rules'
let A = args || {}
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
const FONTES = A.fontes || {
  texto_fonte: 'oshb@3d15126f',
  manifest_sha256: '6479f6dfaaee46f815308ee7ce84fd3277d1e0c730ad3cce50ac70e484b2d790',
  prompts_versao: '1.0.0', regras_versao: '1.1.0', lexico_versao: '0.6.1', modelo: 'claude-fable-5',
}
const CHAPTERS = (A.chapters || []).slice(0, 5)

const S = { type: 'string' }
const arr = (i) => ({ type: 'array', items: i })
const obj = (p, r) => ({ type: 'object', additionalProperties: true, required: r, properties: p })
const VERSE = obj({
  osis: S,
  versiculo: { type: 'integer' },
  texto_bv: S,
  traducao_literal: S,
  decisoes: arr(obj({ questao: S, escolha: S, justificativa: S, alternativas_rejeitadas: arr(obj({ opcao: S, motivo: S }, ['opcao', 'motivo'])) }, ['questao', 'escolha', 'justificativa', 'alternativas_rejeitadas'])),
  palavras_supridas: arr(S),
  ambiguidades_preservadas: arr(S),
  variantes_textuais: arr(obj({ descricao: S, leituras: arr(obj({ leitura: S, testemunhas: S }, ['leitura', 'testemunhas'])), avaliacao: S, impacto_na_traducao: S }, ['descricao', 'leituras', 'avaliacao', 'impacto_na_traducao'])),
  justificativa: S,
  confianca: { type: 'number' },
}, ['osis', 'versiculo', 'texto_bv', 'traducao_literal', 'decisoes', 'justificativa', 'confianca'])
const CHAPTER_OUT = obj({ book: S, chapter: { type: 'integer' }, versos: arr(VERSE) }, ['book', 'chapter', 'versos'])

const preamble = 'Você é o tradutor da Bereia Version (BV), tradução bíblica pt-BR auditável até o hebraico pinado (OSHB). Você traduz um CAPÍTULO inteiro de uma vez, no tier DRAFT (cobertura em massa).\n' +
  'LEIA (uma vez): ' + RULES + '/EDITORIAL.md (v1.1.0); ' + RULES + '/TEOLOGIA.md; ' + RULES + '/NOMES-DIVINOS.md; ' + REPO + '/decisions/DECISOES.md (ER-0011..0016 VINCULANTES); ' + REPO + '/lexicon/lexicon.json.\n' +
  'REGISTRO EDITORIAL RATIFICADO (aplique sempre): S-V uniforme incl. "E Deus disse:" (ER-0011); nomeação minúscula "chamou X de y" (ER-0012); doutrina do calque (ER-0013: traducao_literal preserva TODOS os calques — waw integral, repetição de sujeito, quiasmos, ordem V-S — e o publicado normaliza); fórmula de aprovação "Deus viu que era bom" (כי completivo "que"); refrão de dia com ordinal a partir do 2º; distinção criar(H1254a)/fazer(H6213); nomes divinos ER-0002 (YHWH→SENHOR, Elohim→Deus); מִין por valor lexical sem concordismo (TEOLOGIA §2).\n' +
  'TIER DRAFT (ADR-0002/ER-0016): rascunho auditável — confianca MÁXIMA 0,80 por versículo.\n' +
  'IMPORTANTE — NÃO reemita morfologia palavra a palavra: o lemma, a morfologia e o surface hebraico já vêm do packet pinado e serão anexados mecanicamente. Você produz APENAS o julgamento por versículo: texto_bv, traducao_literal, decisoes (só as não-triviais, com alternativas_rejeitadas), palavras_supridas, ambiguidades_preservadas, variantes_textuais (só as relevantes), justificativa, confianca.\n'

async function draftChapter(ch) {
  const osisBook = ch.book
  const out = await agent(preamble +
    'FONTE: leia o packet do capítulo ' + ch.packet + ' (traz cada versículo com hebraico + morfologia por palavra) e traduza TODOS os versículos de ' + osisBook + '.' + ch.chapter + ' (v.' + ch.from + ' a ' + ch.to + '). As perícopes já traduzidas estão em ' + REPO + '/translation/01-gn/ e ' + REPO + '/translation/02-ex/ (mantenha consistência terminológica com elas — nomes próprios, topônimos, termos rituais — e com o léxico).\n' +
    'Retorne { book:"' + osisBook + '", chapter:' + ch.chapter + ', versos:[ ... um objeto por versículo, na ordem, com osis "' + osisBook + '.' + ch.chapter + '.N" e versiculo N ... ] }. Cubra TODOS os versículos de ' + ch.from + ' a ' + ch.to + '. JSON apenas.',
    { label: 'cap:' + osisBook + '.' + ch.chapter, phase: 'Traduzir', schema: CHAPTER_OUT, model: 'fable' })
  return out || { book: osisBook, chapter: ch.chapter, versos: [] }
}

const results = await parallel(CHAPTERS.map(ch => () => draftChapter(ch)))
return { chapters: results.filter(Boolean) }
