export const meta = {
  name: 'bv-pilot-gen-1-1-5',
  description: 'Pilot multi-agent translation of Genesis 1:1-5 (Bereia Version)',
  phases: [
    { title: 'Propostas', detail: '4 agentes independentes por versículo' },
    { title: 'Consenso', detail: 'consolidação + refutação adversarial + adjudicação (N<=3)' },
    { title: 'Pericope', detail: 'consistência da perícope + QA qualitativo de contaminação' },
  ],
}
const REPO = '/Users/ova/GolandProjects/bereia-bible'
const RULES = REPO + '/pipeline/rules'
const PROMPTS = REPO + '/pipeline/prompts'
const PACKET = REPO + '/pipeline/packets/gen-001-001-005.json'
const BLIND = REPO + '/pipeline/packets/gen-001-001-005.blind.json'
const FONTES = {
  texto_fonte: 'oshb@3d15126f',
  manifest_sha256: 'a89a122f983e9953398176492f7dcc53debf80ebf072e5f5841113a51a2c824d',
  prompts_versao: '1.0.0',
  regras_versao: '1.0.0',
  lexico_versao: '0.2.0',
  modelo: 'claude-fable-5',
}
const VERSES = ['Gen.1.1', 'Gen.1.2', 'Gen.1.3', 'Gen.1.4', 'Gen.1.5']

const S = { type: 'string' }
const B = { type: 'boolean' }
const arr = (items) => ({ type: 'array', items })
const obj = (props, required) => ({ type: 'object', additionalProperties: true, required, properties: props })

const A1 = obj({ osis: S, analise_morfologica: arr(obj({ surface: S, lemma: S, morph: S, observacao: S }, ['surface', 'lemma', 'morph'])), sintaxe: S, semantica: S, variantes: arr(S), ambiguidades: arr(S), traducao_literal: S, traducao_proposta: S, notas: arr(S) }, ['osis', 'analise_morfologica', 'sintaxe', 'semantica', 'variantes', 'ambiguidades', 'traducao_literal', 'traducao_proposta'])
const A2 = obj({ osis: S, traducao: S, palavras_supridas: arr(S), escolhas: arr(obj({ questao: S, escolha: S, justificativa: S }, ['questao', 'escolha', 'justificativa'])), dificuldades: arr(S) }, ['osis', 'traducao', 'palavras_supridas', 'escolhas'])
const A34 = obj({ osis: S, traducao: S, notas: arr(S), alertas: arr(S) }, ['osis', 'traducao', 'notas'])
const CONS = obj({
  osis: S, texto_consolidado: S, traducao_literal: S,
  divergencias: arr(obj({ questao: S, posicoes: arr(S), resolucao: S, evidencia: S }, ['questao', 'posicoes', 'resolucao', 'evidencia'])),
  decisoes: arr(obj({ questao: S, escolha: S, justificativa: S, alternativas_rejeitadas: arr(obj({ opcao: S, motivo: S }, ['opcao', 'motivo'])) }, ['questao', 'escolha', 'justificativa', 'alternativas_rejeitadas'])),
  palavras_supridas: arr(S), ambiguidades_preservadas: arr(S),
  variantes_textuais: arr(obj({ descricao: S, leituras: arr(obj({ leitura: S, testemunhas: S }, ['leitura', 'testemunhas'])), avaliacao: S, impacto_na_traducao: S }, ['descricao', 'leituras', 'avaliacao', 'impacto_na_traducao'])),
}, ['osis', 'texto_consolidado', 'traducao_literal', 'divergencias', 'decisoes', 'palavras_supridas', 'ambiguidades_preservadas', 'variantes_textuais'])
const REF = obj({ osis: S, objecoes: arr(obj({ alvo: S, gravidade: { enum: ['MATERIAL', 'EDITORIAL'] }, problema: S, proposta: S, evidencia: S }, ['alvo', 'gravidade', 'problema', 'proposta', 'evidencia'])), veredito: { enum: ['APROVA', 'REPROVA'] } }, ['osis', 'objecoes', 'veredito'])
const FIN = obj({
  registro: obj({}, ['schema_version', 'referencia', 'texto_bv', 'traducao_literal', 'termos_originais', 'variantes_textuais', 'decisoes', 'justificativa', 'confianca', 'status', 'ciclos_consenso', 'fontes']),
  precisa_novo_ciclo: B, resumo_adjudicacao: S,
}, ['registro', 'precisa_novo_ciclo', 'resumo_adjudicacao'])
const CONSIST = obj({ aprovado: B, problemas: arr(S), entradas_lexico_propostas: arr(obj({ lemma: S, original: S, translit: S, glosa_bv: S, dominio: S, justificativa: S, primeiras_ocorrencias: arr(S) }, ['lemma', 'original', 'translit', 'glosa_bv', 'dominio', 'justificativa', 'primeiras_ocorrencias'])) }, ['aprovado', 'problemas', 'entradas_lexico_propostas'])
const CONTAM = obj({ alerta: B, avaliacao_geral: S, por_versiculo: arr(obj({ osis: S, coincidencias: S, exigida_pelo_original: B, recomendacao: S }, ['osis', 'coincidencias', 'exigida_pelo_original', 'recomendacao'])) }, ['alerta', 'avaliacao_geral', 'por_versiculo'])

const common = (promptFile, packetPath, osis) => 'Você é um agente do pipeline da Bereia Version (BV), tradução bíblica pt-BR auditável até as fontes.\n\n' +
'LEIA PRIMEIRO (obrigatório, nesta ordem):\n' +
'- ' + PROMPTS + '/' + promptFile + '  (seu papel; siga-o à risca; versão 1.0.0)\n' +
'- ' + RULES + '/EDITORIAL.md\n' +
'- ' + RULES + '/TEOLOGIA.md\n' +
'- ' + RULES + '/MORFOLOGIA-OSHB.md\n' +
'- ' + RULES + '/NOMES-DIVINOS.md\n' +
'- ' + REPO + '/lexicon/lexicon.json\n\n' +
'FONTE: leia o packet ' + packetPath + ' e trabalhe SOMENTE o versículo ' + osis + ' (perícope Gen.1.1-5; os demais versos do packet são apenas contexto literário).\n\n' +
'REGRAS INVIOLÁVEIS:\n' +
'1. A tradução nasce do hebraico do packet (WLC pinado), palavra a palavra, com a morfologia anotada.\n' +
'2. NUNCA copie ou imite a redação de tradução existente. Se o packet trouxer controles (web/kjv/livre), eles servem exclusivamente para detectar divergência ou omissão sua — jamais como fonte de redação.\n' +
'3. Preserve ambiguidades reais do original; nenhuma escolha por doutrina sem suporte lexical/sintático (TEOLOGIA.md).\n' +
'4. Sua resposta final é APENAS o JSON estruturado pedido, em pt-BR.\n\n'

async function propor(osis) {
  const res = await parallel([
    () => agent(common('agente1-linguas-originais.md', PACKET, osis) + 'Tarefa: análise morfológica/sintática/semântica completa, variantes textuais relevantes (LXX, Pentateuco Samaritano, Qumran, ketiv/qere), tradução literal e tradução proposta.', { label: 'a1:' + osis, phase: 'Propostas', schema: A1 }),
    () => agent(common('agente2-tradutor.md', BLIND, osis) + 'Tarefa: tradução direta e independente do hebraico. Seu packet não contém controles, de propósito: você é o tradutor cego.', { label: 'a2:' + osis, phase: 'Propostas', schema: A2 }),
    () => agent(common('agente3-revisor-linguistico.md', PACKET, osis) + 'Tarefa (fase proposta): sua própria tradução do versículo com máxima qualidade de português brasileiro (gramática normativa, fluidez, TTS), sem sacrificar conteúdo. Registre notas linguísticas.', { label: 'a3:' + osis, phase: 'Propostas', schema: A34 }),
    () => agent(common('agente4-revisor-exegetico.md', PACKET, osis) + 'Tarefa (fase proposta): sua tradução informada pelo contexto canônico (uso do lexema no corpus, paralelos reais), mais alertas de possível viés (inclusive reformado) em qualquer escolha comum. Notas exegéticas em notas; alertas em alertas.', { label: 'a4:' + osis, phase: 'Propostas', schema: A34 }),
  ])
  if (res.some(r => !r)) throw new Error('propostas incompletas para ' + osis)
  return { a1: res[0], a2: res[1], a3: res[2], a4: res[3] }
}

async function consenso(p, osis) {
  const n = Number(osis.split('.')[2])
  const cons = await agent(common('consolidador.md', PACKET, osis) +
    'AS QUATRO PROPOSTAS INDEPENDENTES:\n\n[Agente 1 — línguas originais]\n' + JSON.stringify(p.a1, null, 1) +
    '\n\n[Agente 2 — tradutor cego]\n' + JSON.stringify(p.a2, null, 1) +
    '\n\n[Agente 3 — revisor linguístico]\n' + JSON.stringify(p.a3, null, 1) +
    '\n\n[Agente 4 — revisor exegético]\n' + JSON.stringify(p.a4, null, 1) +
    '\n\nTarefa: alinhe as quatro propostas palavra a palavra contra o hebraico do packet; liste TODAS as divergências não-triviais; decida cada uma por evidência lexical/morfológica/sintática (nunca por maioria); aplique EDITORIAL.md, NOMES-DIVINOS.md e o léxico; produza a consolidação completa.',
    { label: 'consolidar:' + osis, phase: 'Consenso', schema: CONS })
  if (!cons) throw new Error('consolidação falhou para ' + osis)

  let alvo = cons
  let registro = null
  let ciclos = 0
  while (ciclos < 3) {
    ciclos++
    const lentes = [
      ['1', 'línguas originais: morfologia mal lida, sintaxe distorcida, lexema fora do campo semântico, variante ignorada'],
      ['2', 'tradução: informação do original perdida, expansão interpretativa, equivalência formal quebrada sem necessidade'],
      ['3', 'linguística: erro de português, pontuação que muda sentido, ambiguidade não-intencional, prejuízo de TTS/voz alta'],
      ['4', 'exegética: viés doutrinário sem suporte, quebra de consistência canônica, harmonização artificial, ambiguidade do original resolvida indevidamente'],
    ]
    const refs = await parallel(lentes.map(l => () => agent(common('refutador.md', PACKET, osis) +
      'SUA LENTE: ' + l[0] + ' (' + l[1] + ').\n\nPROPOSTA CONSOLIDADA A ATACAR (ciclo ' + ciclos + '):\n' +
      JSON.stringify({ texto: alvo.texto_consolidado, traducao_literal: alvo.traducao_literal, decisoes: alvo.decisoes, ambiguidades_preservadas: alvo.ambiguidades_preservadas }, null, 1) +
      '\n\nTarefa: tente DERRUBAR esta proposta pela sua lente, contra o hebraico do packet. Cada objeção: alvo exato, gravidade MATERIAL ou EDITORIAL, problema, proposta de correção, evidência. Se nada material: veredito APROVA.',
      { label: 'refutar' + l[0] + ':' + osis + '(c' + ciclos + ')', phase: 'Consenso', schema: REF })))
    const fin = await agent(common('finalizador.md', PACKET, osis) +
      'CONSOLIDAÇÃO SOB JULGAMENTO (ciclo ' + ciclos + ' de no máximo 3):\n' + JSON.stringify(alvo, null, 1) +
      '\n\nREFUTAÇÕES DAS QUATRO LENTES:\n' + JSON.stringify(refs.filter(Boolean), null, 1) +
      '\n\nMETADADOS OBRIGATÓRIOS do campo fontes (use exatamente):\n' + JSON.stringify(FONTES) +
      '\n\nReferência obrigatória: osis "' + osis + '", livro "Gênesis", capitulo 1, versiculo ' + n + ', pericope "Gen.1.1-5".\n' +
      'Tarefa: adjudique cada objeção por evidência (régua de confiança do seu prompt aplicada mecanicamente) e emita o registro COMPLETO conforme ' + REPO + '/api/verse-record.schema.json — schema_version "1.0.0", status "REVIEW", ciclos_consenso ' + ciclos + ', termos_originais cobrindo TODAS as palavras type=word do versículo (palavra, translit simplificada, lemma, morfologia, glosa adotada). Campos em pt-BR ASCII nos nomes; sem campos extras fora do schema.',
      { label: 'finalizar:' + osis + '(c' + ciclos + ')', phase: 'Consenso', schema: FIN })
    if (!fin) throw new Error('finalização falhou para ' + osis)
    registro = fin.registro
    registro.ciclos_consenso = ciclos
    if (!fin.precisa_novo_ciclo) break
    alvo = Object.assign({}, alvo, { texto_consolidado: registro.texto_bv, traducao_literal: registro.traducao_literal, decisoes: registro.decisoes })
    log(osis + ': mudança material no ciclo ' + ciclos + ', reabrindo refutação')
  }
  return registro
}

phase('Propostas')
const registros = await pipeline(VERSES, propor, consenso)
const ok = registros.filter(Boolean)
log('registros finalizados: ' + ok.length + '/5')

phase('Pericope')
const textos = ok.map(r => ({ osis: r.referencia.osis, texto_bv: r.texto_bv, traducao_literal: r.traducao_literal }))
const perRes = await parallel([
  () => agent('Você é o verificador de consistência da perícope Gen.1.1-5 da Bereia Version.\nLeia: ' + RULES + '/EDITORIAL.md, ' + RULES + '/NOMES-DIVINOS.md, ' + REPO + '/lexicon/lexicon.json e o packet ' + PACKET + '.\n\nTEXTOS FINAIS DA PERÍCOPE:\n' + JSON.stringify(textos, null, 1) + '\n\nTarefas: (1) verifique consistência terminológica e estilística entre os 5 versículos (mesmo lexema hebraico → mesma glosa, salvo adjudicação; parataxe uniforme; pontuação de discurso direto uniforme); (2) proponha entradas de léxico (LexiconEntry) para lexemas recorrentes fixados nesta perícope (ex.: H1254 criar, H216 luz, H2822, H3117, H8064, H776, H7307, H930x), com lemma no formato H+número, translit, glosa adotada, domínio, justificativa e primeiras_ocorrencias OSIS. Retorne só o JSON.', { label: 'consistencia:pericope', phase: 'Pericope', schema: CONSIST }),
  () => agent('Você é o auditor de contaminação de copyright da Bereia Version (QA qualitativo, PIPELINE.md §QA).\n\nTEXTOS BV DE Gen.1.1-5:\n' + JSON.stringify(textos.map(t => ({ osis: t.osis, texto: t.texto_bv })), null, 1) + '\n\nCompare DE MEMÓRIA com ARA, NVI, NAA e NTLH (não leia nem escreva arquivo nenhum dessas versões; NUNCA reproduza um versículo delas — cite no máximo fragmentos de até 5 palavras quando indispensável para descrever uma coincidência).\nPara cada versículo: há coincidência de redação extensa com alguma delas? Ela é exigida pelo original hebraico (tradução natural inevitável) ou é imitação evitável? Recomendação: manter (coincidência inevitável) ou reavaliar a partir da fonte. alerta=true somente se houver coincidência extensa evitável. Retorne só o JSON.', { label: 'contaminacao:qualitativa', phase: 'Pericope', schema: CONTAM }),
])
return { registros: ok, consistencia: perRes[0], contaminacao: perRes[1] }
