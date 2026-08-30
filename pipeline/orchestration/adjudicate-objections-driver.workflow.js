// Adjudication driver for open MATERIAL objections (ER-0020, ADR-0005).
// ONE agent per chapter carrying `objecoes_nao_resolvidas`, up to 16 in
// parallel. Each agent reads the canonical prompt
// (pipeline/prompts/adjudicador-objecoes.md v2.0.0) and the packet built by
// scripts/build_adjudication_input.py — which carries texto_bv,
// traducao_literal, the PINNED termos_originais (textual authority) and the
// KJV/WEB controls with neighbouring verses — then rules PROCEDE / IMPROCEDE
// / INCONCLUSIVA per objection, writes its output to
// qa/reports/adjudication-out/<book_dir>-<cap>.json and returns a small
// summary. Persistence is mechanical (scripts/persist_adjudication.py) and
// enforces the hard guards (exact coverage, text frozen unless PROCEDE,
// DRAFT-only, every change logged in mudancas).
// Agents write their own output files, so a hung aggregation (F-0014) never
// loses work — recovery = rerun persist on the files already on disk.
//
// args = { chapters: [ { book_dir, chapter } ... up to 16 ], model, modo }
// modo 'final' proíbe INCONCLUSIVA: toda objeção volta decidida (decisão do
// mantenedor, 2026-08-30). A leitura descartada vai em `leitura_rejeitada` e é
// preservada em `ambiguidades_preservadas` pelo persistidor.
export const meta = {
  name: 'bv-adjudicate-objections-driver',
  description: 'Adjudication of open MATERIAL objections against the pinned original, with KJV/WEB as sense controls (ER-0020)',
  phases: [{ title: 'Adjudicar', detail: 'até 16 threads; um agente por capítulo com objeção aberta' }],
}
const REPO = '/Users/ova/GolandProjects/bereia-bible'
let A = args || {}
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
// Model is provenance-bearing: it must equal the -modelo passed to
// scripts/persist_adjudication.py (ER-0010 re-pin of `fontes`).
const MODEL = A.model || 'fable'
const CHAPTERS = (A.chapters || []).slice(0, 16)
const FINAL = String(A.modo || '') === 'final'

const S = { type: 'string' }
const I = { type: 'integer' }
const SUMMARY = {
  type: 'object',
  additionalProperties: true,
  required: ['book_dir', 'chapter', 'procede', 'improcede', 'inconclusiva'],
  properties: { book_dir: S, chapter: I, procede: I, improcede: I, inconclusiva: I },
}

const preamble = 'Você é o adjudicador de objeções MATERIAIS da Bereia Version (BV), etapa ER-0020 (ADR-0005). Diferente da revisão editorial ER-0019, aqui a mudança de SENTIDO é permitida — a objeção foi escalada exatamente por isso.\n' +
  'LEIA, nesta ordem: ' + REPO + '/pipeline/prompts/adjudicador-objecoes.md (v2.0.0 — seu papel, hierarquia de autoridade, detector de divergência textual, vereditos e regras duras de saída); ' + REPO + '/pipeline/rules/EDITORIAL.md (forma do pt-BR); ' + REPO + '/decisions/DECISOES.md (ER-0011..ER-0019, vinculantes); ' + REPO + '/lexicon/lexicon.json (consistência terminológica).\n' +
  'AUTORIDADE: `termos_originais` do pacote é a autoridade textual (hebraico/grego pinado, com lemma Strong e morfologia). A KJV é o BASELINE DE SENTIDO desta etapa; a WEB é o segundo controle. Nenhuma versão supera a morfologia do original.\n' +
  'DETECTOR TEXTUAL: KJV repousa no Textus Receptus, WEB em base crítica, a BV em WLC/OSHB + Nestle 1904. Se KJV e WEB divergem ENTRE SI, a divergência é textual, não semântica — veredito IMPROCEDE ou INCONCLUSIVA, `controles_divergem: true`, e a variante explicada em `nota_textual`. NUNCA importe leitura do TR para o texto_bv (Comma Johanneum, Mc 16:9-20, Jo 5:4, At 8:37, doxologia de Mt 6:13).\n' +
  'VERSIFICAÇÃO: o WLC/OSHB diverge do inglês em sobrescrições de Salmos, Joel, Malaquias e partes de Êxodo. Cada controle traz `vizinhos` — confirme pelo CONTEÚDO que a KJV está no mesmo versículo antes de usá-la; se não bater, registre em `nota_textual` e não a use como evidência.\n' +
  (FINAL
    ? 'MODO FINAL (decisão do mantenedor): INCONCLUSIVA está PROIBIDA. Toda objeção sai como PROCEDE ou IMPROCEDE. Isso não afrouxa a evidência, só retira o direito de não decidir: PROCEDE segue exigindo `evidencia_original`, e se o original não sustenta a correção o veredito é IMPROCEDE — nunca PROCEDE por desencargo. Leitura do Textus Receptus segue barrada: KJV divergindo da WEB resolve-se pela base pinada, com IMPROCEDE e a variante em `nota_textual`.\n' +
      'CRUX DECIDIDO É CRUX DOCUMENTADO: quando sua decisão descartar uma leitura defensável, preencha `leitura_rejeitada` com ela e o motivo de ter perdido — vai para `ambiguidades_preservadas` no registro. O texto passa a dizer uma coisa só; o registro continua sabendo que havia duas.\n' +
      'Objeção que não é reivindicação semântica (trava de governança: tier DRAFT, paradigma de 2ª pessoa, pendência de promoção) é IMPROCEDE — diga em `fundamentacao` que a questão é de processo, não de tradução.\n' +
      'DESEMPATE: vence a leitura com mais apoio na morfologia pinada; empatada a morfologia, vence a que KJV e WEB sustentam juntas; empatado isso, vence o texto atual da BV (o ônus da prova é de quem objeta).\n'
    : 'INCONCLUSIVA é um veredito de primeira classe: use quando a evidência não decide, quando a escolha é teologicamente carregada (cabe ao mantenedor) ou quando os controles estão desalinhados. A objeção permanece aberta. Palpite persistido é pior que objeção aberta.\n') +
  'REGRAS DURAS: (1) `texto_bv_final` sempre presente e, em IMPROCEDE/INCONCLUSIVA, byte a byte idêntico ao `texto_bv` de entrada — preserve as aspas curvas “ ” ‘ ’; (2) em PROCEDE toda alteração vai em `mudancas` {antes, depois, motivo} — mudança não registrada é descartada; (3) `traducao_literal` nunca é reescrita; (4) palavra que a correção insere e o original elide (ex.: o שֶׁקֶל elíptico das fórmulas de peso) vai declarada em `palavras_supridas`, exatamente como aparece no texto final — não declarada, a persistência recusa; (5) um objeto de saída por verso do pacote, na mesma ordem; (6) JSON estritamente VÁLIDO.\n'

async function adjudicateChapter(ch) {
  const pad = String(ch.chapter).padStart(3, '0')
  const packet = REPO + '/qa/reports/adjudication-input/' + ch.book_dir + '-' + pad + '.json'
  const out = REPO + '/qa/reports/adjudication-out/' + ch.book_dir + '-' + pad + '.json'
  const summary = await agent(preamble +
    'CAPÍTULO: ' + ch.book_dir + '/' + pad + '. Leia o pacote ' + packet + ': traz SOMENTE os versos com objeção MATERIAL aberta, cada um com osis, texto_bv, traducao_literal, termos_originais (autoridade), as objeções abertas e os controles KJV/WEB com vizinhos.\n' +
    'Para cada verso: (1) leia a objeção e identifique o que ela afirma; (2) confronte com `termos_originais` — a morfologia decide; (3) use a KJV como baseline de sentido e a WEB como segundo controle, checando antes o alinhamento pelo conteúdo; (4) se KJV e WEB divergem entre si, trate como variante textual, não como erro de sentido; (5) emita PROCEDE (corrija o texto, com `evidencia_original` citando o termo e o Strong) ou IMPROCEDE (texto idêntico, com `fundamentacao` de por que a BV está correta)' + (FINAL ? ' — INCONCLUSIVA está proibida neste lote.' : ' ou INCONCLUSIVA (texto idêntico, objeção segue aberta).') + '\n' +
    'Escreva o JSON de saída COMPLETO no arquivo ' + out + ' usando a ferramenta Write, no formato do prompt canônico: { "book_dir": "' + ch.book_dir + '", "chapter": ' + ch.chapter + ', "versos": [ { osis, veredito, texto_bv_final, mudancas, evidencia_original, fundamentacao, controles_divergem, nota_textual, palavras_supridas, leitura_rejeitada } ... ] } com TODOS os versos do pacote, na mesma ordem.\n' +
    'Depois de escrever o arquivo, retorne APENAS o resumo: { book_dir: "' + ch.book_dir + '", chapter: ' + ch.chapter + ', procede: <nº>, improcede: <nº>, inconclusiva: <nº> }.',
    { label: 'adj:' + ch.book_dir + '/' + pad, phase: 'Adjudicar', schema: SUMMARY, model: MODEL })
  return summary || { book_dir: ch.book_dir, chapter: ch.chapter, procede: 0, improcede: 0, inconclusiva: 0 }
}

const results = await parallel(CHAPTERS.map(ch => () => adjudicateChapter(ch)))
return { chapters: results.filter(Boolean) }
