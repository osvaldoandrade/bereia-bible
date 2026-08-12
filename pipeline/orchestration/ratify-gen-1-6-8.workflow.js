export const meta = {
  name: 'bv-ratify-gen-1-6-8',
  description: 'Ratification cycle for Gen.1.6-8: apply maintainer decisions, verify fidelity',
  phases: [
    { title: 'Aplicar', detail: 'normalização de 1:6 + registro da ratificação de raqia' },
    { title: 'Verificar', detail: 'refutação de fidelidade + consistência da perícope' },
  ],
}
const REPO = '/Users/ova/GolandProjects/bereia-bible'
const PACKET = REPO + '/pipeline/packets/gen-001-006-008.json'
const REC = (o) => REPO + '/translation/01-gn/001/' + o + '.json'
const S = { type: 'string' }
const arr = (i) => ({ type: 'array', items: i })
const obj = (p, r) => ({ type: 'object', additionalProperties: true, required: r, properties: p })
const FIX = obj({ registro: obj({}, ['schema_version', 'referencia', 'texto_bv', 'traducao_literal', 'termos_originais', 'variantes_textuais', 'decisoes', 'justificativa', 'confianca', 'status', 'ciclos_consenso', 'fontes']), resumo: S }, ['registro', 'resumo'])
const VER = obj({ veredito: { enum: ['APROVA', 'REPROVA'] }, objecoes: arr(obj({ alvo: S, problema: S, evidencia: S }, ['alvo', 'problema', 'evidencia'])) }, ['veredito', 'objecoes'])

const FONTES = 'fontes obrigatórias (ER-0010, use exatamente): texto_fonte "oshb@3d15126f", manifest_sha256 "a89a122f983e9953398176492f7dcc53debf80ebf072e5f5841113a51a2c824d", prompts_versao "1.0.0", regras_versao "1.1.0", lexico_versao "0.5.1", modelo "claude-fable-5".'

phase('Aplicar')
const fix = await agent('Você é o finalizador do pipeline da Bereia Version executando o CICLO DE RATIFICAÇÃO DO MANTENEDOR de Gen.1.6.\n\nLeia: ' + REPO + '/pipeline/prompts/finalizador.md, ' + REPO + '/pipeline/rules/EDITORIAL.md (v1.1.0), ' + REPO + '/decisions/DECISOES.md (ER-0011, ER-0013, ER-0015), o packet ' + PACKET + ' e o registro atual ' + REC('Gen.1.6') + '.\n\nDECISÕES DO MANTENEDOR (ER-0015):\n1) רָקִיעַ = "firmamento" RATIFICADO (já no texto; H7549 APPROVED no léxico v0.5.1) — nenhuma mudança de texto por isso, apenas registre a ratificação (adicione decisão citando ER-0015 e uma divergencia "ratificação do mantenedor").\n2) CORREÇÃO MECÂNICA: uniformizar os dois volitivos de 1:6. Hoje: "Haja um firmamento no meio das águas, e que separe águas de águas." O primeiro volitivo (יְהִי→"Haja") não tem complementizador; o segundo (וִיהִי מַבְדִּיל) foi vertido "e que separe" (com "que"). Remova o "que" para paralelismo: texto_bv = "E Deus disse: “Haja um firmamento no meio das águas, e separe águas de águas.”". A traducao_literal PERMANECE inalterada (preserva a perífrase durativa היה+particípio "esteja separando", ER-0013). Registre a mudança em decisoes + divergencias.\n3) Garanta que "um" (firmamento anartro) conste em palavras_supridas (ER-0006).\n\n' + FONTES + '\n\nReferência: osis "Gen.1.6", livro "Gênesis", capitulo 1, versiculo 6, pericope "Gen.1.6-8".\nTarefa: emita o registro COMPLETO atualizado conforme ' + REPO + '/api/verse-record.schema.json — status "APPROVED", ciclos_consenso = (valor atual)+1, re-pin fontes conforme acima. Todos os demais campos preservados. Sem campos extras fora do schema.', { label: 'ratificar:Gen.1.6', phase: 'Aplicar', schema: FIX })
if (!fix) throw new Error('aplicação de 1:6 falhou')

phase('Verificar')
const ver = await agent('Refutador adversarial de FIDELIDADE da Bereia Version. Leia o packet ' + PACKET + ' (Gen.1.6), ' + REPO + '/pipeline/rules/TEOLOGIA.md e ' + REPO + '/decisions/DECISOES.md (ER-0013, ER-0015).\n\nREGISTRO PÓS-RATIFICAÇÃO:\n' + JSON.stringify(fix.registro, null, 1) + '\n\nEscopo estrito (estilo é prerrogativa do mantenedor sob ER-0013 — não objete estilo). Refute só se: (1) o texto publicado perdeu/alterou conteúdo semântico do hebraico não recuperável pela literal+registro; (2) a queda do "que" mudou a força volitiva/sintática de forma que o publicado agora afirme algo que o hebraico não diz; (3) documentação nova inexata; (4) campo corrompido vs. ' + REC('Gen.1.6') + '; (5) português agramatical. Senão APROVA.', { label: 'verificar:Gen.1.6', phase: 'Verificar', schema: VER })

const textos = [
  { osis: 'Gen.1.6', texto: fix.registro.texto_bv },
  { osis: 'Gen.1.7', texto: 'Deus fez o firmamento e separou as águas que estavam debaixo do firmamento das águas que estavam acima do firmamento; e assim foi.' },
  { osis: 'Gen.1.8', texto: 'Deus chamou o firmamento de céus. E houve tarde e houve manhã: segundo dia.' },
]
const consist = await agent('Verificador de consistência da perícope Gen.1.6-8 da BV pós-ratificação. Leia ' + REPO + '/pipeline/rules/EDITORIAL.md (v1.1.0), ' + REPO + '/decisions/DECISOES.md (ER-0011..0015), ' + REPO + '/lexicon/lexicon.json (v0.5.1) e os registros APPROVED de Gen.1.1-5 em ' + REPO + '/translation/01-gn/001/.\n\nTEXTOS FINAIS:\n' + JSON.stringify(textos, null, 1) + '\n\nCheque: firmamento uniforme (H7549 APPROVED); águas/céus/separar coerentes com Gen.1.1-5; "E Deus disse:" idêntico a 1:3; "e assim foi" (וַיְהִי־כֵן) coerente; "segundo dia" ordinal apoiando "dia um"; a queda do "que" em 1:6 deixou o paralelismo dos volitivos limpo; pontuação. Liste só problemas REAIS.', { label: 'consistencia:final', phase: 'Verificar', schema: obj({ aprovado: { type: 'boolean' }, problemas: arr(S) }, ['aprovado', 'problemas']) })
return { fix, ver, consist }
