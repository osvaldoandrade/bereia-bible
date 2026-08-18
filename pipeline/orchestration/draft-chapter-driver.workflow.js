// Chapter-level DRAFT driver (ADR-0002, revised per maintainer): ONE agent per
// chapter, up to 16 chapters in parallel (matches Workflow's own concurrency
// ceiling, min(16, cores-2) — raised from 5 once the driver moved to
// chapter-level agents; the old cap dated from the per-verse driver's spend
// incidents, which chapter-level ~50x lighter cost no longer risks). The
// agent applies the ratified editorial register and produces, per verse,
// only the judgment fields (texto_bv, traducao_literal, decisoes,
// justificativa, confianca).
// It does NOT re-emit per-word morphology — that is assembled mechanically
// from the pinned packet by scripts/persist_chapter_draft.py (F-0015), so the
// audit glyphs are always authoritative and this stays ~50x lighter than the
// per-verse driver.
//
// args = { chapters:[ { book, chapter, from, to, packet, pericope } ... up to 16 ] }
export const meta = {
  name: 'bv-draft-chapter-driver',
  description: 'Chapter-level DRAFT translation, 1 agent/chapter, up to 16 chapters in parallel',
  phases: [{ title: 'Traduzir', detail: 'até 16 threads; um agente por capítulo' }],
}
const REPO = '/Users/ova/GolandProjects/bereia-bible'
const RULES = REPO + '/pipeline/rules'
let A = args || {}
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
const CHAPTERS = (A.chapters || []).slice(0, 16)

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

const preamble = 'Você é o tradutor da Bereia Version (BV), tradução bíblica pt-BR auditável até o texto original pinado (OSHB no AT; Nestle 1904 no NT). Você traduz um CAPÍTULO inteiro de uma vez, no tier DRAFT (cobertura em massa).\n' +
  'LEIA (uma vez): ' + RULES + '/EDITORIAL.md (v1.1.0); ' + RULES + '/TEOLOGIA.md; ' + RULES + '/NOMES-DIVINOS.md; a legenda morfológica da fonte (' + RULES + '/MORFOLOGIA-OSHB.md ou ' + RULES + '/MORFOLOGIA-NESTLE1904.md); ' + REPO + '/decisions/DECISOES.md (ER-0011..0018 VINCULANTES); ' + REPO + '/lexicon/lexicon.json.\n' +
  'REGISTRO EDITORIAL RATIFICADO (aplique sempre): S-V uniforme incl. "E Deus disse:" (ER-0011); nomeação minúscula "chamou X de y" (ER-0012); doutrina do calque (ER-0013: traducao_literal preserva TODOS os calques — waw integral, repetição de sujeito, quiasmos, ordem V-S — e o publicado normaliza); fórmula de aprovação "Deus viu que era bom" (כי completivo "que"); refrão de dia com ordinal a partir do 2º; distinção criar(H1254a)/fazer(H6213); nomes divinos ER-0002 (YHWH→SENHOR, Elohim→Deus); מִין por valor lexical sem concordismo (TEOLOGIA §2).\n' +
  'TIER DRAFT (ADR-0002/ER-0016): rascunho auditável — confianca MÁXIMA 0,80 por versículo.\n' +
  'IMPORTANTE — NÃO reemita morfologia palavra a palavra: o lema, a morfologia e a superfície original já vêm do packet pinado e serão anexados mecanicamente. Você produz APENAS o julgamento por versículo: texto_bv, traducao_literal, decisoes (só as não-triviais, com alternativas_rejeitadas), palavras_supridas, ambiguidades_preservadas, variantes_textuais (só as relevantes), justificativa, confianca.\n' +
  'APARATO: se um verso contiver variantes_fonte, adjudique CADA item em variantes_textuais; mencione literalmente referencia_fonte em descricao. Nunca deixe esse campo vazio quando o packet trouxer aparato.\n'

async function draftChapter(ch) {
  const osisBook = ch.book
  const out = await agent(preamble +
    'FONTE: leia SOMENTE o packet CEGO do capítulo ' + ch.packet + ' (traz cada versículo com o texto original + morfologia por palavra, sem controles) e traduza EXATAMENTE todos os versículos presentes nele para ' + osisBook + '.' + ch.chapter + '. Mantenha consistência terminológica pelo léxico e pelas diretrizes, sem consultar traduções existentes. Lacunas internas da numeração crítica são deliberadas: não invente, renumere nem preencha um OSIS ausente do packet.\n' +
    'Retorne { book:"' + osisBook + '", chapter:' + ch.chapter + ', versos:[ ... um objeto por versículo presente no packet, na mesma ordem, com osis "' + osisBook + '.' + ch.chapter + '.N" e versiculo N ... ] }. A cobertura deve ser idêntica ao conjunto de OSIS do packet, ainda que haja lacunas entre ' + ch.from + ' e ' + ch.to + '. JSON apenas.',
    { label: 'cap:' + osisBook + '.' + ch.chapter, phase: 'Traduzir', schema: CHAPTER_OUT, model: 'sonnet' })
  return out || { book: osisBook, chapter: ch.chapter, versos: [] }
}

const results = await parallel(CHAPTERS.map(ch => () => draftChapter(ch)))
return { chapters: results.filter(Boolean) }
