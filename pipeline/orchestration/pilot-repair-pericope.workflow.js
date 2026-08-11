export const meta = {
  name: 'bv-pilot-repair-pericope',
  description: 'Pericope-consistency adjudication cycle for Gen.1.2 and Gen.1.4 (pilot)',
  phases: [
    { title: 'Reparo', detail: 'adjudicação de consistência por versículo' },
    { title: 'Verificacao', detail: 'refutação adversarial dos reparos + recheque de contaminação' },
  ],
}
const REPO = '/Users/ova/GolandProjects/bereia-bible'
const PACKET = REPO + '/pipeline/packets/gen-001-001-005.json'
const REC = (osis) => REPO + '/translation/01-gn/001/' + osis + '.json'
const S = { type: 'string' }
const B = { type: 'boolean' }
const arr = (items) => ({ type: 'array', items })
const obj = (props, required) => ({ type: 'object', additionalProperties: true, required, properties: props })
const FIX = obj({ registro: obj({}, ['schema_version', 'referencia', 'texto_bv', 'traducao_literal', 'termos_originais', 'variantes_textuais', 'decisoes', 'justificativa', 'confianca', 'status', 'ciclos_consenso', 'fontes']), resumo: S }, ['registro', 'resumo'])
const VER = obj({ veredito: { enum: ['APROVA', 'REPROVA'] }, objecoes: arr(obj({ alvo: S, problema: S, evidencia: S }, ['alvo', 'problema', 'evidencia'])) }, ['veredito', 'objecoes'])

const base = (osis) => 'Você é o finalizador do pipeline da Bereia Version executando um CICLO DE ADJUDICAÇÃO DE CONSISTÊNCIA DA PERÍCOPE Gen.1.1-5 (ciclo 2 deste versículo).\n\nLeia primeiro: ' + REPO + '/pipeline/prompts/finalizador.md, ' + REPO + '/pipeline/rules/EDITORIAL.md, ' + REPO + '/pipeline/rules/TEOLOGIA.md, o packet ' + PACKET + ' e o registro atual ' + REC(osis) + '.\n\n'

phase('Reparo')
const fixes = await parallel([
  () => agent(base('Gen.1.4') +
    'ADJUDICAÇÃO REQUERIDA (P1 do verificador de perícope, BLOQUEANTE): o lexema חֹשֶׁךְ (H2822) recebeu a glosa "escuridão" em Gen.1.2 e Gen.1.5, mas "trevas" em Gen.1.4 — violação de EDITORIAL.md §11 (mesmo lexema recorrente → mesma glosa na perícope, salvo adjudicação registrada). O QA de contaminação também recomendou rederivar Gen.1.4 pelo léxico próprio da BV. A base da mudança é a CONSISTÊNCIA LEXICAL COM EVIDÊNCIA (mesmo lexema, mesmo referente físico na perícope), nunca "reduzir similaridade" (isso é proibido; a redução é efeito colateral legítimo).\n\nTarefa: emita o registro COMPLETO e atualizado de Gen.1.4 conforme ' + REPO + '/api/verse-record.schema.json — texto_bv e traducao_literal com "escuridão" no lugar de "trevas"; glosa correspondente em termos_originais corrigida; ADICIONE uma decisão (questao/escolha/justificativa/alternativas_rejeitadas com "trevas" e o motivo, lexico_ref "H2822") e uma entrada em divergencias documentando este ciclo de consistência da perícope; ciclos_consenso passa a 2; recalcule a confiança pela régua do finalizador; status REVIEW; demais campos preservados exatamente como estão no registro atual.',
    { label: 'reparo:Gen.1.4', phase: 'Reparo', schema: FIX }),
  () => agent(base('Gen.1.2') +
    'REGISTROS REQUERIDOS (P3 e P4 do verificador de perícope, sem mudança de texto):\n(P3) "havia" na cláusula "e havia escuridão sobre a face do abismo" traduz oração nominal hebraica sem verbo expresso — precisa constar em palavras_supridas (ER-0006, EDITORIAL.md §4).\n(P4) TEOLOGIA.md §4 exige que a decisão רוּחַ אֱלֹהִים → "espírito de Deus" documente explicitamente a leitura alternativa "vento de Deus" e o porquê da minúscula em "espírito" (EDITORIAL.md §10): se já houver decisão/ambiguidade no registro, complete-a; se não houver, adicione-a (com alternativas_rejeitadas e evidência lexical de רוּחַ).\n\nTarefa: emita o registro COMPLETO e atualizado de Gen.1.2 — texto_bv e traducao_literal INALTERADOS; palavras_supridas incluindo "havia"; decisões/ambiguidades completadas conforme acima; adicione em divergencias a entrada deste ciclo de consistência; ciclos_consenso 2; confiança recalculada pela régua; status REVIEW; todo o resto preservado.',
    { label: 'reparo:Gen.1.2', phase: 'Reparo', schema: FIX }),
])
if (fixes.some(f => !f)) throw new Error('reparo incompleto')

phase('Verificacao')
const checks = await parallel(fixes.map((f, i) => () => {
  const osis = ['Gen.1.4', 'Gen.1.2'][i]
  return agent('Você é refutador adversarial da Bereia Version. Leia o packet ' + PACKET + ' (versículo ' + osis + '), ' + REPO + '/pipeline/rules/EDITORIAL.md e ' + REPO + '/pipeline/rules/TEOLOGIA.md.\n\nREGISTRO REPARADO (ciclo de consistência da perícope):\n' + JSON.stringify(f.registro, null, 1) + '\n\nTente refutar: (1) o texto ainda é tradução fiel do hebraico do packet, palavra a palavra? (2) o reparo introduziu erro de português ou de morfologia? (3) a documentação nova (decisões/supridas/ambiguidades) é exata e com evidência? (4) algum campo do registro anterior foi perdido ou corrompido (compare com ' + REC(osis) + ')? Objeções só com evidência; senão APROVA.', { label: 'verificar:' + osis, phase: 'Verificacao', schema: VER })
}))
const contamRecheck = await agent('Auditor de contaminação da BV: o texto reparado de Gen.1.4 é: ' + JSON.stringify(fixes[0].registro.texto_bv) + '. Compare DE MEMÓRIA com ARA, NVI, NAA, NTLH (não reproduza versículos; fragmentos de no máximo 5 palavras). A coincidência residual com alguma delas ainda é extensa e evitável, ou o texto agora reflete o léxico próprio da BV com coincidências apenas inevitáveis? Responda JSON.', { label: 'contaminacao:Gen.1.4', phase: 'Verificacao', schema: obj({ alerta: B, avaliacao: S }, ['alerta', 'avaliacao']) })
return { fixes, checks, contamRecheck }
