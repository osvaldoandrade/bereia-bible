# Morfologia Nestle 1904 — legenda operacional

Fonte pinada: `sources/nestle1904/Nestle1904.csv` (ADR-0003).

Cada palavra grega traz dois códigos no sistema Robinson:

- `func_morph`: análise funcional, que pode distinguir voz média/passiva pelo
  contexto mesmo quando a forma não as distingue;
- `morph`: análise orientada à forma, usada como `morfologia` autoritativa nos
  registros BV;
- `strongs`: número de Strong, às vezes seguido de TVM após `&`;
- `lemma`: lema grego;
- `normalized`: superfície sem pontuação e com normalização limitada de acento.

## Estrutura dos códigos

Os códigos são separados por hífens. O primeiro bloco identifica a classe:

| Prefixo | Classe |
|---|---|
| `N` | substantivo |
| `A` | adjetivo |
| `V` | verbo |
| `T` | artigo |
| `P` | pronome |
| `R` | pronome relativo |
| `D` | demonstrativo |
| `ADV` | advérbio |
| `CONJ` | conjunção |
| `PREP` | preposição |
| `PRT` | partícula |
| `INJ` | interjeição |

Para nominais, os blocos seguintes normalmente codificam caso (`N/G/D/A/V`),
número (`S/P`) e gênero (`M/F/N`). Para verbos, codificam tempo, voz, modo,
pessoa e número; formas nominais acrescentam caso/número/gênero. A legenda
upstream completa e pinada está em `sources/nestle1904/parsing.txt`.

## Regras de uso no pipeline

1. `morph` é copiado mecanicamente para `termos_originais[].morfologia`.
2. `func_morph`, Strong e normalização permanecem no packet como apoio; não são
   reemitidos pelo tradutor.
3. Uma discordância entre `func_morph` e `morph` deve ser documentada, não
   silenciosamente nivelada.
4. A única linha upstream com duas colunas morfológicas extras (Mt 10:28) é
   preservada em `morph_alternatives`.
5. Colchetes, pontuação e marcas de variante são tokens próprios. O final curto
   de Marcos (`Mark.16.99`) entra como aparato de 16:20, nunca como versículo BV.
6. Lacunas tradicionais na numeração não recebem versos inventados nem texto de
   controles; cobertura segue os OSIS presentes na autoridade textual.
