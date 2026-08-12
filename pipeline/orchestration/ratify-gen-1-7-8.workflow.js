export const meta = {
  name: 'bv-ratify-gen-1-7-8',
  description: 'Proper ratification of Gen.1.7 and Gen.1.8 (clear stale raqia-provisional metadata, resolve objection, promote)',
  phases: [
    { title: 'Aplicar', detail: 'finalizador em 1:7 e 1:8' },
    { title: 'Verificar', detail: 'consistência da perícope pós-ratificação' },
  ],
}
const REPO = '/Users/ova/GolandProjects/bereia-bible'
const PACKET = REPO + '/pipeline/packets/gen-001-006-008.json'
const REC = (o) => REPO + '/translation/01-gn/001/' + o + '.json'
const S = { type: 'string' }
const arr = (i) => ({ type: 'array', items: i })
const obj = (p, r) => ({ type: 'object', additionalProperties: true, required: r, properties: p })
const FIX = obj({ registro: obj({}, ['schema_version', 'referencia', 'texto_bv', 'traducao_literal', 'termos_originais', 'variantes_textuais', 'decisoes', 'justificativa', 'confianca', 'status', 'ciclos_consenso', 'fontes']), resumo: S }, ['registro', 'resumo'])
const FONTES = 'fontes obrigatórias (ER-0010): texto_fonte "oshb@3d15126f", manifest_sha256 "a89a122f983e9953398176492f7dcc53debf80ebf072e5f5841113a51a2c824d", prompts_versao "1.0.0", regras_versao "1.1.0", lexico_versao "0.5.1", modelo "claude-fable-5".'

const alvo = {
  'Gen.1.7': 'Deus fez o firmamento e separou as águas que estavam debaixo do firmamento das águas que estavam acima do firmamento; e assim foi.',
  'Gen.1.8': 'Deus chamou o firmamento de céus. E houve tarde e houve manhã: segundo dia.',
}

async function ratificar(osis) {
  const n = Number(osis.split('.')[2])
  const fix = await agent('Você é o finalizador do pipeline da Bereia Version executando o CICLO DE RATIFICAÇÃO DO MANTENEDOR de ' + osis + ' (perícope Gen.1.6-8).\n\nLeia: ' + REPO + '/pipeline/prompts/finalizador.md, ' + REPO + '/pipeline/rules/EDITORIAL.md (v1.1.0), ' + REPO + '/decisions/DECISOES.md (ER-0013, ER-0015), ' + REPO + '/lexicon/lexicon.json (v0.5.1, onde H7549 firmamento é APPROVED) e o registro atual ' + REC(osis) + '.\n\nCONTEXTO: o mantenedor RATIFICOU רָקִיעַ = "firmamento" (ER-0015); H7549 agora é APPROVED no léxico v0.5.1. O TEXTO deste versículo NÃO muda:\n"' + alvo[osis] + '"\n\nTarefa: emita o registro COMPLETO atualizado conforme ' + REPO + '/api/verse-record.schema.json, corrigindo os metadados obsoletos do ciclo 1:\n1) TODA menção a "firmamento PROVISÓRIA" / "a ratificar" / "sem entrada em lexicon.json" / "LexiconEntry em adjudicação do mantenedor" nas observações de termos_originais e nas decisoes DEVE ser atualizada: H7549 "firmamento" é APPROVED no léxico v0.5.1, ratificado pelo mantenedor (ER-0015); a materialidade permanece ambiguidade preservada, não afirmada.\n2) Se houver objecoes_nao_resolvidas relativa à glosa de raqia diferida ao mantenedor, ela está RESOLVIDA por ER-0015 — remova-a de objecoes_nao_resolvidas e registre a resolução em divergencias (guarda F-0011: objecoes_nao_resolvidas não-vazio ⇒ nunca APPROVED).\n3) Adicione uma decisão/divergencia citando ER-0015 (ratificação do mantenedor: firmamento).\n4) status "APPROVED"; ciclos_consenso = (valor atual)+1; recalcule confianca pela régua do finalizador (a resolução da objeção pendente eleva a confiança).\n5) ' + FONTES + '\n6) Referência: osis "' + osis + '", livro "Gênesis", capitulo 1, versiculo ' + n + ', pericope "Gen.1.6-8". texto_bv e traducao_literal preservados; sem campos extras fora do schema.',
    { label: 'ratificar:' + osis, phase: 'Aplicar', schema: FIX })
  if (!fix) throw new Error('ratificação falhou para ' + osis)
  return fix.registro
}

phase('Aplicar')
const regs = await parallel([() => ratificar('Gen.1.7'), () => ratificar('Gen.1.8')])
if (regs.some(r => !r)) throw new Error('ratificação incompleta')

phase('Verificar')
const textos = [
  { osis: 'Gen.1.6', texto: 'E Deus disse: “Haja um firmamento no meio das águas, e separe águas de águas.”' },
  { osis: 'Gen.1.7', texto: regs[0].texto_bv },
  { osis: 'Gen.1.8', texto: regs[1].texto_bv },
]
const metaChecks = regs.map(r => ({ osis: r.referencia.osis, status: r.status, lexico: r.fontes.lexico_versao, obj_abertas: (r.objecoes_nao_resolvidas || []).length, cita_er0015: JSON.stringify(r).includes('ER-0015') }))
const consist = await agent('Verificador de consistência FINAL da perícope Gen.1.6-8 da BV pós-ratificação completa. Leia ' + REPO + '/decisions/DECISOES.md (ER-0011..0015), ' + REPO + '/lexicon/lexicon.json (v0.5.1) e os registros APPROVED de Gen.1.1-5.\n\nMETADADOS DOS REGISTROS 1:7/1:8 APÓS RATIFICAÇÃO:\n' + JSON.stringify(metaChecks, null, 1) + '\n\nTEXTOS FINAIS:\n' + JSON.stringify(textos, null, 1) + '\n\nConfirme que os defeitos de metadados do ciclo anterior estão sanados: (a) status APPROVED nos dois; (b) lexico_versao 0.5.1 (ER-0010); (c) objecoes_nao_resolvidas vazio (F-0011); (d) nenhuma linguagem "firmamento provisória/a ratificar" remanescente; (e) ER-0015 citado. E que o texto publicado dos 3 segue consistente com Gen.1.1-5. Liste só problemas REAIS restantes.', { label: 'consistencia:final2', phase: 'Verificar', schema: obj({ aprovado: { type: 'boolean' }, problemas: arr(S) }, ['aprovado', 'problemas']) })
return { regs, consist }
