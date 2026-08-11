export const meta = {
  name: 'bv-pericope-gen-1-6-8',
  description: 'Multi-agent translation of Genesis 1:6-8 (day two) under the ratified editorial register',
  phases: [
    { title: 'Propostas', detail: '4 agentes independentes por versículo' },
    { title: 'Consenso', detail: 'consolidação + refutação adversarial + adjudicação (N<=3)' },
    { title: 'Pericope', detail: 'consistência (interna + com Gen.1.1-5 APPROVED) + QA de contaminação' },
  ],
}
const REPO = '/Users/ova/GolandProjects/bereia-bible'
const RULES = REPO + '/pipeline/rules'
const PROMPTS = REPO + '/pipeline/prompts'
const PACKET = REPO + '/pipeline/packets/gen-001-006-008.json'
const BLIND = REPO + '/pipeline/packets/gen-001-006-008.blind.json'
const FONTES = {
  texto_fonte: 'oshb@3d15126f',
  manifest_sha256: 'a89a122f983e9953398176492f7dcc53debf80ebf072e5f5841113a51a2c824d',
  prompts_versao: '1.0.0',
  regras_versao: '1.1.0',
  lexico_versao: '0.4.1',
  modelo: 'claude-fable-5',
}
const VERSES = ['Gen.1.6', 'Gen.1.7', 'Gen.1.8']

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

const common = (promptFile, packetPath, osis) => 'Você é um agente do pipeline da Bereia Version (BV), tradução bíblica pt-BR auditável até as fontes.\n\n' +
'LEIA PRIMEIRO (obrigatório, nesta ordem):\n' +
'- ' + PROMPTS + '/' + promptFile + '  (seu papel; siga-o à risca; versão 1.0.0)\n' +
'- ' + RULES + '/EDITORIAL.md (v1.1.0)\n' +
'- ' + RULES + '/TEOLOGIA.md\n' +
'- ' + RULES + '/MORFOLOGIA-OSHB.md\n' +
'- ' + RULES + '/NOMES-DIVINOS.md\n' +
'- ' + REPO + '/decisions/DECISOES.md (diretrizes ER-0011, ER-0012, ER-0013 são VINCULANTES)\n' +
'- ' + REPO + '/lexicon/lexicon.json (v0.4.1 — glosas fixadas; desvio exige justificativa)\n\n' +
'REGISTRO EDITORIAL JÁ RATIFICADO (perícope Gen.1.1-5 APPROVED, ER-0014 — aplique desde a primeira proposta):\n' +
'- Ordem S-V uniforme, inclusive fórmula de fala: "E Deus disse:" (ER-0011).\n' +
'- Nomeação em minúscula, sem aspas: "chamou X de y" (ER-0012).\n' +
'- Doutrina do calque (ER-0013): a traducao_literal preserva TODOS os calques (waw integral, repetição de sujeito, quiasmos, ordem V-S); o texto publicado normaliza — waw inicial de versículo vertido "E" só quando a sequência discursiva pedir (precedente: 1:3 mantém "E"; 1:4/1:5 omitem); repetição formular de sujeito condensável; registre cada normalização como decisão.\n' +
'- Precedentes lexicais APPROVED: H2822 escuridão; H4325 águas; H8064 céus; H914 separar (regência "separar X de Y", cf. Gen.1.4); H1961 haja/houve/era; H3117 dia; contagem: "dia um" cardinal no dia 1, ordinais nos demais ("segundo dia").\n' +
'- Distinção vinculante H1254a criar × H6213 fazer (léxico): וַיַּעַשׂ em 1:7 → "fez".\n\n' +
'FONTE: leia o packet ' + packetPath + ' e trabalhe SOMENTE o versículo ' + osis + ' (perícope Gen.1.6-8, dia dois; os demais versos do packet são contexto literário; a perícope anterior APPROVED está em ' + REPO + '/translation/01-gn/001/).\n\n' +
'REGRAS INVIOLÁVEIS:\n' +
'1. A tradução nasce do hebraico do packet (WLC pinado), palavra a palavra, com a morfologia anotada.\n' +
'2. NUNCA copie ou imite a redação de tradução existente. Controles (web/kjv/livre), quando presentes, servem só para detectar divergência ou omissão sua.\n' +
'3. Preserve ambiguidades reais; nenhuma escolha por doutrina sem suporte lexical/sintático (TEOLOGIA.md).\n' +
'4. Sua resposta final é APENAS o JSON estruturado pedido, em pt-BR.\n\n'

async function propor(osis) {
  const res = await parallel([
    () => agent(common('agente1-linguas-originais.md', PACKET, osis) + 'Tarefa: análise morfológica/sintática/semântica completa, variantes textuais relevantes (atenção do dia dois: posição de וַיְהִי־כֵן no TM vs LXX; ausência da fórmula de aprovação no TM do dia 2 que a LXX acrescenta; רָקִיעַ e sua história tradutória LXX στερέωμα/Vulgata firmamentum), tradução literal e tradução proposta.', { label: 'a1:' + osis, phase: 'Propostas', schema: A1 }),
    () => agent(common('agente2-tradutor.md', BLIND, osis) + 'Tarefa: tradução direta e independente do hebraico. Seu packet não contém controles, de propósito: você é o tradutor cego.', { label: 'a2:' + osis, phase: 'Propostas', schema: A2 }),
    () => agent(common('agente3-revisor-linguistico.md', PACKET, osis) + 'Tarefa (fase proposta): sua própria tradução com máxima qualidade de português brasileiro (gramática normativa, fluidez, TTS), sem sacrificar conteúdo. Registre notas linguísticas.', { label: 'a3:' + osis, phase: 'Propostas', schema: A34 }),
    () => agent(common('agente4-revisor-exegetico.md', PACKET, osis) + 'Tarefa (fase proposta): tradução informada pelo contexto canônico (uso de רָקִיעַ no corpus: Ez 1; Sl 19:2; Dn 12:3; a cosmologia do texto sem modernizar nem mitologizar além do que o hebraico codifica) + alertas de viés, inclusive concordismo científico. Notas exegéticas em notas; alertas em alertas.', { label: 'a4:' + osis, phase: 'Propostas', schema: A34 }),
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
    '\n\nTarefa: alinhe as quatro propostas palavra a palavra contra o hebraico do packet; liste TODAS as divergências não-triviais; decida cada uma por evidência lexical/morfológica/sintática (nunca por maioria); aplique EDITORIAL.md v1.1.0, as diretrizes ER-0011..0013 e o léxico v0.4.1; produza a consolidação completa.',
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
      ['4', 'exegética: viés doutrinário sem suporte, concordismo, quebra de consistência canônica, harmonização artificial, ambiguidade resolvida indevidamente'],
    ]
    const refs = await parallel(lentes.map(l => () => agent(common('refutador.md', PACKET, osis) +
      'SUA LENTE: ' + l[0] + ' (' + l[1] + ').\n\nPROPOSTA CONSOLIDADA A ATACAR (ciclo ' + ciclos + '):\n' +
      JSON.stringify({ texto: alvo.texto_consolidado, traducao_literal: alvo.traducao_literal, decisoes: alvo.decisoes, ambiguidades_preservadas: alvo.ambiguidades_preservadas }, null, 1) +
      '\n\nTarefa: tente DERRUBAR esta proposta pela sua lente, contra o hebraico do packet e as diretrizes vinculantes. Cada objeção: alvo exato, gravidade MATERIAL ou EDITORIAL, problema, proposta, evidência. Se nada material: APROVA.',
      { label: 'refutar' + l[0] + ':' + osis + '(c' + ciclos + ')', phase: 'Consenso', schema: REF })))
    const fin = await agent(common('finalizador.md', PACKET, osis) +
      'CONSOLIDAÇÃO SOB JULGAMENTO (ciclo ' + ciclos + ' de no máximo 3):\n' + JSON.stringify(alvo, null, 1) +
      '\n\nREFUTAÇÕES DAS QUATRO LENTES:\n' + JSON.stringify(refs.filter(Boolean), null, 1) +
      '\n\nMETADADOS OBRIGATÓRIOS do campo fontes (ER-0010, use exatamente):\n' + JSON.stringify(FONTES) +
      '\n\nReferência obrigatória: osis "' + osis + '", livro "Gênesis", capitulo 1, versiculo ' + n + ', pericope "Gen.1.6-8".\n' +
      'Tarefa: adjudique cada objeção por evidência (régua de confiança aplicada mecanicamente) e emita o registro COMPLETO conforme ' + REPO + '/api/verse-record.schema.json — schema_version "1.0.0", status "REVIEW", ciclos_consenso ' + ciclos + ', termos_originais cobrindo TODAS as palavras type=word (palavra, translit simplificada, lemma, morfologia, glosa adotada). A traducao_literal preserva os calques (ER-0013). Sem campos extras fora do schema.',
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
log('registros finalizados: ' + ok.length + '/3')

phase('Pericope')
const textos = ok.map(r => ({ osis: r.referencia.osis, texto_bv: r.texto_bv, traducao_literal: r.traducao_literal }))
const perRes = await parallel([
  () => agent('Você é o verificador de consistência da perícope Gen.1.6-8 da Bereia Version.\nLeia: ' + RULES + '/EDITORIAL.md (v1.1.0), ' + REPO + '/decisions/DECISOES.md (ER-0011..0014), ' + REPO + '/lexicon/lexicon.json (v0.4.1), o packet ' + PACKET + ' e os 5 registros APPROVED da perícope anterior em ' + REPO + '/translation/01-gn/001/ (Gen.1.1..Gen.1.5).\n\nTEXTOS FINAIS DE Gen.1.6-8:\n' + JSON.stringify(textos, null, 1) + '\n\nTarefas: (1) consistência interna da perícope (glosa única por lexema; S-V; minúsculas em nomeação; padrão de waw coerente com o precedente 1:3/1:4-5; pontuação); (2) consistência ENTRE perícopes com Gen.1.1-5 APPROVED (mesmos lexemas → mesmas glosas: águas, céus, separar, haja/houve, dia; "segundo dia" ordinal coerente com "dia um" cardinal; fórmula "E Deus disse:" idêntica à de 1:3); (3) proponha entradas de léxico para lexemas novos fixados (ex.: H7549 raqia, H6213 asah, H8478 tachat, H8145 sheni, H3605? apenas se recorrente), formato: lemma H+número, original, translit, glosa_bv, dominio, justificativa, primeiras_ocorrencias OSIS. Liste problemas REAIS apenas. Retorne só o JSON.', { label: 'consistencia:pericope', phase: 'Pericope', schema: obj({ aprovado: B, problemas: arr(S), entradas_lexico_propostas: arr(obj({ lemma: S, original: S, translit: S, glosa_bv: S, dominio: S, justificativa: S, primeiras_ocorrencias: arr(S) }, ['lemma', 'original', 'translit', 'glosa_bv', 'dominio', 'justificativa', 'primeiras_ocorrencias'])) }, ['aprovado', 'problemas', 'entradas_lexico_propostas']) }),
  () => agent('Você é o auditor de contaminação de copyright da Bereia Version (QA qualitativo, PIPELINE.md §QA).\n\nTEXTOS BV DE Gen.1.6-8:\n' + JSON.stringify(textos.map(t => ({ osis: t.osis, texto: t.texto_bv })), null, 1) + '\n\nCompare DE MEMÓRIA com ARA, NVI, NAA e NTLH (não leia nem escreva arquivo nenhum dessas versões; NUNCA reproduza um versículo delas; cite no máximo fragmentos de até 5 palavras quando indispensável). Para cada versículo: coincidência extensa? exigida pelo original (inevitável) ou imitação evitável? Recomendação: manter ou reavaliar a partir da fonte. alerta=true só para coincidência extensa evitável. Retorne só o JSON.', { label: 'contaminacao:qualitativa', phase: 'Pericope', schema: obj({ alerta: B, avaliacao_geral: S, por_versiculo: arr(obj({ osis: S, coincidencias: S, exigida_pelo_original: B, recomendacao: S }, ['osis', 'coincidencias', 'exigida_pelo_original', 'recomendacao'])) }, ['alerta', 'avaliacao_geral', 'por_versiculo']) }),
])
return { registros: ok, consistencia: perRes[0], contaminacao: perRes[1] }
