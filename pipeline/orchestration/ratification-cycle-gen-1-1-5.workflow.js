export const meta = {
  name: 'bv-ratification-cycle',
  description: 'Maintainer-ratification cycle for Gen.1.2-5 (apply directives, verify fidelity)',
  phases: [
    { title: 'Aplicar', detail: 'diretrizes do mantenedor por versículo' },
    { title: 'Verificar', detail: 'refutação de fidelidade + consistência da perícope' },
  ],
}
const REPO = '/Users/ova/GolandProjects/bereia-bible'
const PACKET = REPO + '/pipeline/packets/gen-001-001-005.json'
const REC = (osis) => REPO + '/translation/01-gn/001/' + osis + '.json'
const S = { type: 'string' }
const arr = (items) => ({ type: 'array', items })
const obj = (props, required) => ({ type: 'object', additionalProperties: true, required, properties: props })
const FIX = obj({ registro: obj({}, ['schema_version', 'referencia', 'texto_bv', 'traducao_literal', 'termos_originais', 'variantes_textuais', 'decisoes', 'justificativa', 'confianca', 'status', 'ciclos_consenso', 'fontes']), resumo: S }, ['registro', 'resumo'])
const VER = obj({ veredito: { enum: ['APROVA', 'REPROVA'] }, objecoes: arr(obj({ alvo: S, problema: S, evidencia: S }, ['alvo', 'problema', 'evidencia'])) }, ['veredito', 'objecoes'])

const FONTES = 'fontes obrigatórias do ciclo (ER-0010, use exatamente): texto_fonte "oshb@3d15126f", manifest_sha256 "a89a122f983e9953398176492f7dcc53debf80ebf072e5f5841113a51a2c824d", prompts_versao "1.0.0", regras_versao "1.1.0", lexico_versao "0.4.0", modelo "claude-fable-5".'

const ALVOS = {
  'Gen.1.2': {
    texto: 'A terra era desolada e vazia, e havia escuridão sobre a face do abismo, e o Espírito de Deus pairava sobre a face das águas.',
    diretrizes: '1) Waw inicial disjuntivo (וְהָאָרֶץ, circunstancial) NÃO vertido no publicado (ER-0013.1; permanece na literal). 2) תֹהוּ וָבֹהוּ vertido adjetivalmente "desolada e vazia" no publicado — DECISÃO RATIFICADA pelo mantenedor após discussão (alternativa nominal "desolação e vazio" rejeitada por predicativo abstrato duro; substantivos permanecem na literal e no léxico H8414/H922 v0.4.0; eco Jr 4:23 será mantido com os mesmos adjetivos). 3) "Espírito de Deus" com maiúscula — decisão exegética do mantenedor (referente divino pessoal; EDITORIAL §10 permite com documentação): a decisão existente sobre ruach deve ser ATUALIZADA registrando a maiúscula, mantendo documentadas as leituras alternativas "espírito" minúsculo e "vento de Deus".',
  },
  'Gen.1.3': {
    texto: 'E Deus disse: “Haja luz”; e houve luz.',
    diretrizes: '1) Ordem S-V na fórmula de fala: "E Deus disse:" (ER-0011, supersede ER-0008); a ordem V-S hebraica permanece na literal. Aspas curvas e ponto-e-vírgula preservados como estão.',
  },
  'Gen.1.4': {
    texto: 'Deus viu que a luz era boa e separou a luz da escuridão.',
    diretrizes: '1) Waw inicial não vertido (ER-0013.1). 2) Repetição formular do sujeito (אֱלֹהִים 2×) condensada: segundo "Deus" omitido no publicado (ER-0013.2; repetição preservada na literal). 3) Vírgula antes de "e separou" removida (oração coordenada com sujeito comum). A completiva "viu que a luz era boa" e a regência "separou a luz da escuridão" foram explicitamente aprovadas pelo mantenedor — não alterar.',
  },
  'Gen.1.5': {
    texto: 'Deus chamou a luz de dia e chamou a escuridão de noite. E houve tarde e houve manhã: dia um.',
    diretrizes: '1) Waw inicial não vertido (ER-0013.1). 2) Nomeação em minúsculas: "de dia", "de noite" (ER-0012, supersede ER-0009). 3) Quiasmo hebraico (וְלַחֹשֶׁךְ fronteado) normalizado para paralelismo direto "e chamou a escuridão de noite" (ER-0013.3; o quiasmo permanece na literal). 4) "dia um" MANTIDO — DECISÃO RATIFICADA (cardinal אֶחָד só no dia 1; ordinais nos dias 2-6; assimetria do hebraico preservada; alternativa "primeiro dia" rejeitada por nivelar cardinal→ordinal).',
  },
}

async function aplicar(osis) {
  const a = ALVOS[osis]
  return agent('Você é o finalizador do pipeline da Bereia Version executando o CICLO DE RATIFICAÇÃO DO MANTENEDOR da perícope Gen.1.1-5.\n\nLeia primeiro: ' + REPO + '/pipeline/prompts/finalizador.md, ' + REPO + '/pipeline/rules/EDITORIAL.md (v1.1.0), ' + REPO + '/decisions/DECISOES.md (ER-0011, ER-0012, ER-0013), o packet ' + PACKET + ' e o registro atual ' + REC(osis) + '.\n\nTEXTO RATIFICADO PELO MANTENEDOR para ' + osis + ':\n"' + a.texto + '"\n\nDIRETRIZES (autoridade: revisão do mantenedor, 2026-08-11):\n' + a.diretrizes + '\n\n' + FONTES + '\n\nTarefa: emita o registro COMPLETO atualizado conforme ' + REPO + '/api/verse-record.schema.json:\n- texto_bv = exatamente o texto ratificado acima;\n- traducao_literal INALTERADA (ela é a camada que preserva os calques, ER-0013);\n- para CADA mudança vs. o registro atual, adicione uma decisão (questao/escolha/justificativa/alternativas_rejeitadas) citando a diretriz (diretriz_ref ER-00NN quando aplicável) e uma entrada em divergencias marcando este ciclo como "ratificação do mantenedor";\n- glosas de termos_originais ajustadas onde a rendição publicada mudou (com observacao apontando a glosa lexical);\n- ciclos_consenso = (valor atual do registro) + 1;\n- status "REVIEW" (a promoção a APPROVED é ato de governança posterior);\n- todos os demais campos preservados.', { label: 'ratificar:' + osis, phase: 'Aplicar', schema: FIX })
}

async function verificar(fix, osis) {
  if (!fix) throw new Error('aplicação falhou para ' + osis)
  const v = await agent('Você é refutador adversarial de FIDELIDADE da Bereia Version. Leia o packet ' + PACKET + ' (versículo ' + osis + '), ' + REPO + '/pipeline/rules/TEOLOGIA.md e ' + REPO + '/decisions/DECISOES.md (ER-0011..0013).\n\nREGISTRO PÓS-RATIFICAÇÃO:\n' + JSON.stringify(fix.registro, null, 1) + '\n\nEscopo estrito: estilo é prerrogativa do mantenedor sob ER-0013 — NÃO objete estilo. Refute APENAS se: (1) o texto publicado perdeu ou alterou CONTEÚDO SEMÂNTICO do hebraico do packet (não recuperável pela traducao_literal + registro); (2) uma diretriz foi aplicada errado ou o texto difere do ratificado; (3) a documentação nova é inexata; (4) algum campo foi corrompido vs. ' + REC(osis) + '; (5) português agramatical. Senão, APROVA.', { label: 'verificar:' + osis, phase: 'Verificar', schema: VER })
  return { fix, ver: v }
}

phase('Aplicar')
const done = await pipeline(['Gen.1.2', 'Gen.1.3', 'Gen.1.4', 'Gen.1.5'], aplicar, verificar)
const ok = done.filter(Boolean)
log('versículos processados: ' + ok.length + '/4')

phase('Verificar')
const textos = ok.map(d => ({ osis: d.fix.registro.referencia.osis, texto: d.fix.registro.texto_bv }))
textos.unshift({ osis: 'Gen.1.1', texto: 'No princípio, Deus criou os céus e a terra.' })
const consist = await agent('Verificador de consistência da perícope Gen.1.1-5 da BV pós-ratificação. Leia ' + REPO + '/pipeline/rules/EDITORIAL.md (v1.1.0), ' + REPO + '/decisions/DECISOES.md (ER-0011..0013) e ' + REPO + '/lexicon/lexicon.json (v0.4.0).\n\nTEXTOS FINAIS:\n' + JSON.stringify(textos, null, 1) + '\n\nCheque: glosa única por lexema (escuridão em 2/4/5; luz; dia/noite minúsculos); ordem S-V uniforme inclusive na fórmula de fala; padrão de waw inicial coerente com ER-0013 (por que 1.3 mantém "E" e 1.4/1.5 não — a sequência discursiva justifica?); pontuação uniforme. Liste problemas REAIS apenas.', { label: 'consistencia:final', phase: 'Verificar', schema: obj({ aprovado: { type: 'boolean' }, problemas: arr(S) }, ['aprovado', 'problemas']) })
return { done: ok, consist }
