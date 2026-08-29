# Regras editoriais — Bereia Version

Versão: **1.2.0** · Status: ATIVA · Mudanças exigem bump SemVer + registro em `decisions/DECISOES.md`.
(1.2.0: §1.2 expandido com tabela de arcaísmos; §1.4 novo — consistência lexical
intra-capítulo; piso de naturalidade NTLH/ARA/NVIPT; revisão editorial v2 com
comparação guiada. 1.1.0: §6.2 doutrina do calque ER-0013; S-V uniforme ER-0011;
nomeação minúscula ER-0012.)

Estas regras governam a *forma* do português da BV. Elas nunca autorizam alterar o
*sentido* do original. Conflito entre regra editorial e fidelidade semântica →
fidelidade vence e a exceção é registrada no registro do versículo.

## 1. Língua e registro

1. Português brasileiro contemporâneo, Acordo Ortográfico de 1990.
2. Registro formal-neutro: nem coloquial, nem arcaizante. Proibidos arcaísmos
   funcionalmente mortos — itens abaixo e os listados em §1.2-tabela.
3. O texto deve ser confortável em leitura em voz alta e TTS: evitar cacofonias,
   ambiguidade de referência pronominal e períodos > 40 palavras quando o original
   permitir divisão sem perda sintática.
4. **Piso de naturalidade**: o texto publicado da BV deve soar pelo menos tão
   natural quanto NTLH, ARA e NVIPT para o mesmo trecho. Quando as três
   referências convergem contra a BV, presumir que a BV está com problema de
   forma (arcaísmo, inconsistência lexical, calque) — a menos que haja razão
   estilística documentada em contrário.

### 1.2-tabela — Arcaísmos e substitutos (não exaustiva; cresce com o review)

| Arcaísmo / forma morta | Substituto contemporâneo | Observação |
|---|---|---|
| mui | muito | |
| porventura | acaso / talvez | |
| deveras | de fato / realmente | |
| outrossim | também / ademais | |
| destarte | dessa forma / assim | |
| vosso / vossa / vossos / vossas | seu / sua / seus / suas | exceto vocativo litúrgico (§3) |
| luzeiros | luminares / luzes | Gn 1.14-16 (mesmo heb. `maor`) |
| tornou-se em / tornaram-se em | virou / tornou-se / fez-se | calque de devir; escolher conforme contexto |
| mais-que-perfeito sintético (fizera, nascera, viera, …) | pretérito composto (tinha feito, havia nascido) | exceto em fórmula litúrgica consolidada |
| mesóclise (dar-te-ei, far-se-á) | próclise ou ênclise (te darei, se fará) | mesóclise soa artificial em pt-BR contemporâneo |

A tabela é viva: cada review que descobre novo arcaísmo deve propor adição
via PR com evidência (3+ ocorrências no corpus + atestação em dicionário
histórico como Houaiss/Michaelis marcando o termo como "antigo" ou "desusado").

### 1.4 — Consistência lexical intra-capítulo (ER-0019 v2)

1. O mesmo termo original (hebraico/grego) deve ser traduzido pelo mesmo
   lexema português dentro do capítulo, exceto quando:
   - (a) o contexto imediato exigir registro distinto (ex: jogo de palavras
     intencional do autor);
   - (b) houver variação estilística documentada (paralelismo sinonímico,
     ênfase progressiva);
   - (c) o léxico oficial (`lexicon/lexicon.json`) prever sinônimos
     intercambiáveis para o termo.
2. Quando a BV varia sem razão (ex: "luzeiros" em Gn 1.14 e "luminares" em
   Gn 1.15 para o mesmo `maor`), normalizar para o lexema majoritário no
   capítulo. Conferir com NTLH/ARA/NVIPT: se as três referências mantêm
   coerência onde a BV varia, a variação é provavelmente defeito.
3. A decisão de normalizar (ou manter variação) deve aparecer em `mudancas`
   (com motivo referenciando §1.4) ou em `justificativa` (quando mantida).

## 2. Nomes divinos

Política própria versionada: **`pipeline/rules/NOMES-DIVINOS.md`** (v1.0.0, ER-0002).
Resumo: YHWH → SENHOR; Elohim (ref. Deus de Israel) → Deus; Adonai → Senhor;
Adonai YHWH → Senhor DEUS. Desvio exige adjudicação registrada.

## 3. Segunda pessoa (decisão provisória D-0003)

- Discurso entre humanos e de Deus para humanos: **você/vocês**.
- Oração/salmo dirigido a Deus: **tu** (uso litúrgico vivo no Brasil).
- A distinção singular/plural do original é sempre preservada (você × vocês).

## 4. Palavras supridas e elipses

- Palavras exigidas pelo português sem correspondente formal no original **não**
  recebem itálico; são listadas no campo `palavras_supridas` do registro.
- Elipses do original são supridas apenas quando o português for agramatical sem isso.

## 5. Discurso direto

- Introduzido por dois-pontos e **aspas duplas curvas** ("…"). Travessão rejeitado
  (diálogos bíblicos intercalados com oração narrativa quebram mal com travessão).
- Citação dentro de citação: aspas simples.

## 6. Pontuação e estrutura

1. Pontuação segue a sintaxe do português, não os acentos massoréticos; o atnach
   informa, mas não obriga vírgula.
2. Doutrina do calque (ER-0013): a `traducao_literal` preserva todos os calques
   estruturais (waw paratático integral, repetição formular de sujeito, quiasmos);
   o texto publicado os normaliza quando soarem artificiais, com adjudicação por
   versículo. Waw disjuntivo circunstancial não é vertido; wayyiqtol inicial vira
   "E" só quando a sequência discursiva pedir. Ordem S-V uniforme (ER-0011);
   nomeação em minúscula (ER-0012).
3. Poesia recebe quebras de linha (layout futuro); narrativa é prosa corrida.

## 7. Números e medidas

- Numerais por extenso em texto corrido, inclusive idades e contagens.
- Medidas antigas mantidas (côvado, efa) — conversões vão em nota, nunca no texto.

## 8. Nomes próprios

- Grafia consolidada em português (Adão, Eva, Abraão, Jerusalém), não transliteração
  erudita. Base: uso corrente + tradição Almeida (domínio público).
- Nomes sem tradição consolidada: transliteração simplificada do original.

## 9. Transliteração (campo `translit`)

- Sistema simplificado legível: bereshit, ruach, tohu vabohu. Sem diacríticos
  acadêmicos no registro; א = ' e ע = ' apenas quando a distinção for relevante à
  justificativa.

## 10. Maiúsculas

- Pronomes referentes a Deus: minúscula (ele, seu), prática contemporânea.
- "Espírito" com maiúscula somente quando o registro do versículo documentar a
  decisão exegética (ver TEOLOGIA.md §4); caso contrário, minúscula.

## 11. Consistência terminológica

- Termo técnico-teológico recorrente (aliança, propiciação, justificar) tem entrada
  no `lexicon/lexicon.json`; desvio da glosa padrão exige justificativa no registro
  do versículo e referência `lexico_ref`.
