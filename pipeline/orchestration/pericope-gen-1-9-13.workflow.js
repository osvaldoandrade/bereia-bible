export const meta = {
  name: 'bv-pericope-gen-1-9-13',
  description: 'Multi-agent translation of Genesis 1:9-13 (day three) under the ratified editorial register',
  phases: [
    { title: 'Propostas', detail: '4 agentes independentes por versículo' },
    { title: 'Consenso', detail: 'consolidação + refutação adversarial + adjudicação (N<=3)' },
    { title: 'Pericope', detail: 'consistência (interna + com Gen.1.1-8 APPROVED) + QA de contaminação' },
  ],
}
const REPO = '/Users/ova/GolandProjects/bereia-bible'
const RULES = REPO + '/pipeline/rules'
const PROMPTS = REPO + '/pipeline/prompts'
const PACKET = REPO + '/pipeline/packets/gen-001-009-013.json'
const BLIND = REPO + '/pipeline/packets/gen-001-009-013.blind.json'
const FONTES = {
  texto_fonte: 'oshb@3d15126f',
  manifest_sha256: 'a89a122f983e9953398176492f7dcc53debf80ebf072e5f5841113a51a2c824d',
  prompts_versao: '1.0.0', regras_versao: '1.1.0', lexico_versao: '0.5.1', modelo: 'claude-fable-5',
}
const VERSES = ['Gen.1.9', 'Gen.1.10', 'Gen.1.11', 'Gen.1.12', 'Gen.1.13']
const HINT = {
  'Gen.1.9': 'יִקָּווּ (nifal jussivo "ajuntem-se/reúnam-se"), הַיַּבָּשָׁה (a terra seca/o seco), fecho וַיְהִי־כֵן ("e assim foi", precedente 1:7).',
  'Gen.1.10': 'Ato de nomeação DUPLO (minúscula, ER-0012): לַיַּבָּשָׁה→"terra" (יַבָּשָׁה), לְמִקְוֵה הַמַּיִם→"mares" (יַמִּים). PRIMEIRA fórmula de aprovação da série de aprovações: וַיַּרְא אֱלֹהִים כִּי־טוֹב — precedente APPROVED de 1:4 ("Deus viu que a luz era boa"): aqui sem objeto explícito (refrão curto), "Deus viu que era bom".',
  'Gen.1.11': 'Taxonomia botânica: דֶּשֶׁא (relva/vegetação), עֵשֶׂב מַזְרִיעַ זֶרַע (erva que produz semente), עֵץ פְּרִי עֹשֶׂה פְּרִי (árvore frutífera que dá fruto). לְמִינוֹ = "segundo a sua espécie" — traduzir pelo VALOR LEXICAL de מִין; NÃO importar fixismo/antievolucionismo (guarda anti-concordismo, TEOLOGIA). אֲשֶׁר זַרְעוֹ־בוֹ ("cuja semente está nela").',
  'Gen.1.12': 'Execução da vegetação (espelha 1:11 com wayyiqtol); SEGUNDA fórmula de aprovação וַיַּרְא אֱלֹהִים כִּי־טוֹב. Manter glosa botânica idêntica à de 1:11 (consistência intra-perícope).',
  'Gen.1.13': 'Refrão do terceiro dia idêntico a 1:5/1:8, só muda o rótulo: יוֹם שְׁלִישִׁי (ordinal, "terceiro dia" — apoia dia um cardinal / segundo dia ordinal).',
}

const S = { type: 'string' }, B = { type: 'boolean' }
const arr = (i) => ({ type: 'array', items: i })
const obj = (p, r) => ({ type: 'object', additionalProperties: true, required: r, properties: p })
const A1 = obj({ osis: S, analise_morfologica: arr(obj({ surface: S, lemma: S, morph: S, observacao: S }, ['surface', 'lemma', 'morph'])), sintaxe: S, semantica: S, variantes: arr(S), ambiguidades: arr(S), traducao_literal: S, traducao_proposta: S, notas: arr(S) }, ['osis', 'analise_morfologica', 'sintaxe', 'semantica', 'variantes', 'ambiguidades', 'traducao_literal', 'traducao_proposta'])
const A2 = obj({ osis: S, traducao: S, palavras_supridas: arr(S), escolhas: arr(obj({ questao: S, escolha: S, justificativa: S }, ['questao', 'escolha', 'justificativa'])), dificuldades: arr(S) }, ['osis', 'traducao', 'palavras_supridas', 'escolhas'])
const A34 = obj({ osis: S, traducao: S, notas: arr(S), alertas: arr(S) }, ['osis', 'traducao', 'notas'])
const CONS = obj({ osis: S, texto_consolidado: S, traducao_literal: S, divergencias: arr(obj({ questao: S, posicoes: arr(S), resolucao: S, evidencia: S }, ['questao', 'posicoes', 'resolucao', 'evidencia'])), decisoes: arr(obj({ questao: S, escolha: S, justificativa: S, alternativas_rejeitadas: arr(obj({ opcao: S, motivo: S }, ['opcao', 'motivo'])) }, ['questao', 'escolha', 'justificativa', 'alternativas_rejeitadas'])), palavras_supridas: arr(S), ambiguidades_preservadas: arr(S), variantes_textuais: arr(obj({ descricao: S, leituras: arr(obj({ leitura: S, testemunhas: S }, ['leitura', 'testemunhas'])), avaliacao: S, impacto_na_traducao: S }, ['descricao', 'leituras', 'avaliacao', 'impacto_na_traducao'])) }, ['osis', 'texto_consolidado', 'traducao_literal', 'divergencias', 'decisoes', 'palavras_supridas', 'ambiguidades_preservadas', 'variantes_textuais'])
const REF = obj({ osis: S, objecoes: arr(obj({ alvo: S, gravidade: { enum: ['MATERIAL', 'EDITORIAL'] }, problema: S, proposta: S, evidencia: S }, ['alvo', 'gravidade', 'problema', 'proposta', 'evidencia'])), veredito: { enum: ['APROVA', 'REPROVA'] } }, ['osis', 'objecoes', 'veredito'])
const FIN = obj({ registro: obj({}, ['schema_version', 'referencia', 'texto_bv', 'traducao_literal', 'termos_originais', 'variantes_textuais', 'decisoes', 'justificativa', 'confianca', 'status', 'ciclos_consenso', 'fontes']), precisa_novo_ciclo: B, resumo_adjudicacao: S }, ['registro', 'precisa_novo_ciclo', 'resumo_adjudicacao'])

const common = (promptFile, packetPath, osis) => 'Você é um agente do pipeline da Bereia Version (BV), tradução bíblica pt-BR auditável até as fontes.\n\n' +
'LEIA PRIMEIRO (obrigatório): ' + PROMPTS + '/' + promptFile + ' (seu papel, v1.0.0); ' + RULES + '/EDITORIAL.md (v1.1.0); ' + RULES + '/TEOLOGIA.md; ' + RULES + '/MORFOLOGIA-OSHB.md; ' + RULES + '/NOMES-DIVINOS.md; ' + REPO + '/decisions/DECISOES.md (ER-0011..0015 VINCULANTES); ' + REPO + '/lexicon/lexicon.json (v0.5.1).\n\n' +
'REGISTRO EDITORIAL RATIFICADO (perícopes Gen.1.1-8 APPROVED — aplique desde a primeira proposta):\n' +
'- Ordem S-V uniforme, inclusive fórmula de fala "E Deus disse:" (ER-0011).\n' +
'- Nomeação em minúscula, sem aspas: "chamou X de y" (ER-0012) — vale para "terra"/"mares" em 1:10.\n' +
'- Doutrina do calque (ER-0013): traducao_literal preserva TODOS os calques (waw integral, repetição de sujeito, quiasmos, ordem V-S); o publicado normaliza — waw inicial vertido "E" só quando a sequência discursiva pedir; registre cada normalização como decisão.\n' +
'- Fórmula de aprovação: precedente APPROVED de 1:4 "Deus viu que a luz era boa" (וירא אלהים כי־טוב) — em 1:10/1:12 é o refrão curto sem objeto: "Deus viu que era bom" (verter כי completivo "que", não "porque"; cf. registro 1:4).\n' +
'- Refrão de dia: "E houve tarde e houve manhã: N dia" — ordinal ("terceiro dia") apoiando "dia um" cardinal / "segundo dia" ordinal (série ratificada; NÃO mudar para "dia terceiro").\n' +
'- Glosas fixadas (léxico v0.5.1): H4325 águas, H8064 céus, H776 terra, H914 separar, H1961 haver/ser (haja/houve/era/foi), H7549 firmamento, H6213 fazer, H3651 assim, H8478 debaixo de. H1254a criar × H6213 fazer distintos.\n' +
'- מִין (kind/espécie) em 1:11-12: traduzir pelo valor lexical ("segundo a sua espécie"); NUNCA importar fixismo de espécies nem antievolucionismo (guarda anti-concordismo, TEOLOGIA §2).\n\n' +
'DICA DO VERSÍCULO ' + osis + ': ' + HINT[osis] + '\n\n' +
'FONTE: leia o packet ' + packetPath + ' e trabalhe SOMENTE o versículo ' + osis + ' (perícope Gen.1.9-13, dia três; os demais versos do packet são contexto; as perícopes anteriores APPROVED estão em ' + REPO + '/translation/01-gn/001/).\n\n' +
'REGRAS INVIOLÁVEIS: (1) tradução nasce do hebraico do packet palavra a palavra com a morfologia anotada; (2) NUNCA copie/imite redação de tradução existente — controles servem só p/ detectar divergência; (3) preserve ambiguidades reais, nenhuma escolha por doutrina sem suporte lexical (TEOLOGIA); (4) resposta final APENAS o JSON pedido, em pt-BR.\n\n'

async function propor(osis) {
  const res = await parallel([
    () => agent(common('agente1-linguas-originais.md', PACKET, osis) + 'Tarefa: análise morfológica/sintática/semântica completa, variantes textuais relevantes (LXX/Sam/Qumran; em 1:9 a LXX tem o plus da execução "e a água se ajuntou..."; ketiv/qere), tradução literal e proposta.', { label: 'a1:' + osis, phase: 'Propostas', schema: A1 }),
    () => agent(common('agente2-tradutor.md', BLIND, osis) + 'Tarefa: tradução direta e independente do hebraico. Packet sem controles (tradutor cego).', { label: 'a2:' + osis, phase: 'Propostas', schema: A2 }),
    () => agent(common('agente3-revisor-linguistico.md', PACKET, osis) + 'Tarefa (fase proposta): sua tradução com máxima qualidade de pt-BR (gramática, fluidez, TTS), sem sacrificar conteúdo. A taxonomia botânica de 1:11-12 é um teste de fluidez — não deixe emperrar. Notas linguísticas.', { label: 'a3:' + osis, phase: 'Propostas', schema: A34 }),
    () => agent(common('agente4-revisor-exegetico.md', PACKET, osis) + 'Tarefa (fase proposta): tradução informada pelo contexto canônico + alertas de viés. ATENÇÃO especial em 1:11-12: מִין/"espécie" NÃO pode carregar fixismo nem antievolucionismo; a fórmula de aprovação não deve ser inflada ("aprovou"→ NÃO; "viu que era bom"→ sim). Notas exegéticas + alertas.', { label: 'a4:' + osis, phase: 'Propostas', schema: A34 }),
  ])
  if (res.some(r => !r)) throw new Error('propostas incompletas para ' + osis)
  return { a1: res[0], a2: res[1], a3: res[2], a4: res[3] }
}

async function consenso(p, osis) {
  const n = Number(osis.split('.')[2])
  const cons = await agent(common('consolidador.md', PACKET, osis) +
    'AS QUATRO PROPOSTAS:\n[A1 línguas]\n' + JSON.stringify(p.a1, null, 1) + '\n[A2 tradutor cego]\n' + JSON.stringify(p.a2, null, 1) + '\n[A3 linguístico]\n' + JSON.stringify(p.a3, null, 1) + '\n[A4 exegético]\n' + JSON.stringify(p.a4, null, 1) +
    '\n\nTarefa: alinhe palavra a palavra contra o hebraico; liste TODAS as divergências não-triviais; decida cada uma por evidência (nunca maioria); aplique EDITORIAL v1.1.0, ER-0011..0015 e léxico v0.5.1; consolidação completa.', { label: 'consolidar:' + osis, phase: 'Consenso', schema: CONS })
  if (!cons) throw new Error('consolidação falhou para ' + osis)
  let alvo = cons, registro = null, ciclos = 0
  while (ciclos < 3) {
    ciclos++
    const lentes = [['1', 'línguas: morfologia/sintaxe/lexema/variante'], ['2', 'tradução: informação perdida, expansão, equivalência formal'], ['3', 'linguística: pt-BR, pontuação, ambiguidade, TTS'], ['4', 'exegética: viés/concordismo, fixismo em מִין, harmonização, ambiguidade resolvida indevidamente']]
    const refs = await parallel(lentes.map(l => () => agent(common('refutador.md', PACKET, osis) +
      'SUA LENTE: ' + l[0] + ' (' + l[1] + ').\n\nCONSOLIDAÇÃO A ATACAR (ciclo ' + ciclos + '):\n' + JSON.stringify({ texto: alvo.texto_consolidado, traducao_literal: alvo.traducao_literal, decisoes: alvo.decisoes, ambiguidades_preservadas: alvo.ambiguidades_preservadas }, null, 1) +
      '\n\nTente DERRUBAR pela sua lente, contra o hebraico e as diretrizes. Cada objeção: alvo, gravidade MATERIAL/EDITORIAL, problema, proposta, evidência. Nada material: APROVA.', { label: 'refutar' + l[0] + ':' + osis + '(c' + ciclos + ')', phase: 'Consenso', schema: REF })))
    const fin = await agent(common('finalizador.md', PACKET, osis) +
      'CONSOLIDAÇÃO (ciclo ' + ciclos + '/3):\n' + JSON.stringify(alvo, null, 1) + '\n\nREFUTAÇÕES:\n' + JSON.stringify(refs.filter(Boolean), null, 1) +
      '\n\nMETADADOS fontes (ER-0010, exatamente):\n' + JSON.stringify(FONTES) + '\nReferência: osis "' + osis + '", livro "Gênesis", capitulo 1, versiculo ' + n + ', pericope "Gen.1.9-13".\n' +
      'Adjudique por evidência (régua de confiança) e emita o registro COMPLETO conforme ' + REPO + '/api/verse-record.schema.json — schema_version "1.0.0", status "REVIEW", ciclos_consenso ' + ciclos + ', termos_originais cobrindo TODAS as palavras type=word. traducao_literal preserva calques (ER-0013). Sem campos extras.', { label: 'finalizar:' + osis + '(c' + ciclos + ')', phase: 'Consenso', schema: FIN })
    if (!fin) throw new Error('finalização falhou para ' + osis)
    registro = fin.registro; registro.ciclos_consenso = ciclos
    if (!fin.precisa_novo_ciclo) break
    alvo = Object.assign({}, alvo, { texto_consolidado: registro.texto_bv, traducao_literal: registro.traducao_literal, decisoes: registro.decisoes })
    log(osis + ': mudança material no ciclo ' + ciclos)
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
  () => agent('Verificador de consistência da perícope Gen.1.9-13 da BV. Leia ' + RULES + '/EDITORIAL.md (v1.1.0), ' + REPO + '/decisions/DECISOES.md (ER-0011..0015), ' + REPO + '/lexicon/lexicon.json (v0.5.1), o packet ' + PACKET + ' e os registros APPROVED de Gen.1.1-8 em ' + REPO + '/translation/01-gn/001/.\n\nTEXTOS FINAIS:\n' + JSON.stringify(textos, null, 1) + '\n\n(1) Consistência interna: taxonomia botânica idêntica entre 1:11 e 1:12; fórmula de aprovação idêntica em 1:10 e 1:12; nomeação minúscula (terra/mares); waw coerente. (2) Consistência com Gen.1.1-8 APPROVED: águas/céus/terra/fazer/haver glosas idênticas; fórmula de aprovação coerente com 1:4; "E Deus disse:" idêntica; refrão "terceiro dia" ordinal coerente com dia um/segundo dia; "e assim foi" (1:9) coerente com 1:7. (3) Proponha entradas de léxico p/ lexemas novos fixados (ex.: H3004 yabbashah terra-seca, H3220 yam mar, H4725 maqom lugar, H1877 deshe, H6212 esev, H6086 etz, H6529 peri, H4327 min espécie, H2232 zara semear, H2233 zera semente, H8027 shelishi terceiro), formato: lemma H+número, original, translit, glosa_bv, dominio, justificativa, primeiras_ocorrencias OSIS. Só problemas REAIS. JSON.', { label: 'consistencia:pericope', phase: 'Pericope', schema: obj({ aprovado: B, problemas: arr(S), entradas_lexico_propostas: arr(obj({ lemma: S, original: S, translit: S, glosa_bv: S, dominio: S, justificativa: S, primeiras_ocorrencias: arr(S) }, ['lemma', 'original', 'translit', 'glosa_bv', 'dominio', 'justificativa', 'primeiras_ocorrencias'])) }, ['aprovado', 'problemas', 'entradas_lexico_propostas']) }),
  () => agent('Auditor de contaminação de copyright da BV (QA qualitativo, PIPELINE.md §QA).\n\nTEXTOS BV DE Gen.1.9-13:\n' + JSON.stringify(textos.map(t => ({ osis: t.osis, texto: t.texto_bv })), null, 1) + '\n\nCompare DE MEMÓRIA com ARA, NVI, NAA, NTLH (não leia/escreva arquivo dessas versões; NUNCA reproduza um versículo; fragmentos ≤5 palavras). Por versículo: coincidência extensa? exigida pelo original (inevitável) ou evitável? Recomendação manter/reavaliar. alerta=true só p/ coincidência extensa evitável. JSON.', { label: 'contaminacao:qualitativa', phase: 'Pericope', schema: obj({ alerta: B, avaliacao_geral: S, por_versiculo: arr(obj({ osis: S, coincidencias: S, exigida_pelo_original: B, recomendacao: S }, ['osis', 'coincidencias', 'exigida_pelo_original', 'recomendacao'])) }, ['alerta', 'avaliacao_geral', 'por_versiculo']) }),
])
return { registros: ok, consistencia: perRes[0], contaminacao: perRes[1] }
