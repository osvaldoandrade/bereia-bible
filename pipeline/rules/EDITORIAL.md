# Regras editoriais — Bereia Version

Versão: **1.1.0** · Status: ATIVA · Mudanças exigem bump SemVer + registro em `decisions/DECISOES.md`.
(1.1.0: §6.2 substituído pela doutrina do calque ER-0013; ordem S-V uniforme ER-0011; nomeação minúscula ER-0012.)

Estas regras governam a *forma* do português da BV. Elas nunca autorizam alterar o
*sentido* do original. Conflito entre regra editorial e fidelidade semântica →
fidelidade vence e a exceção é registrada no registro do versículo.

## 1. Língua e registro

1. Português brasileiro contemporâneo, Acordo Ortográfico de 1990.
2. Registro formal-neutro: nem coloquial, nem arcaizante. Proibidos arcaísmos
   funcionalmente mortos (ex.: "mui", "vosso" fora de vocativo litúrgico, mesóclise).
3. O texto deve ser confortável em leitura em voz alta e TTS: evitar cacofonias,
   ambiguidade de referência pronominal e períodos > 40 palavras quando o original
   permitir divisão sem perda sintática.

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
