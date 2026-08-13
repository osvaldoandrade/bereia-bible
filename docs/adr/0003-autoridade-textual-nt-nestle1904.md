# ADR-0003 — Autoridade textual do NT: Nestle 1904 Morphology

Data: 2026-08-13 · Status: ACEITO · Tier: T3 · Resolve: F-0003

## Contexto

O programa da Bíblia completa precisava de um texto grego crítico cuja licença
fosse compatível com a licença aberta própria da BV. O OpenGNT permanece sob
CC BY-NC-SA 4.0 e, por isso, não pode ser autoridade textual do produto.

O repositório Biblical Humanities publica o texto-base Nestle 1904, declarado
em domínio público por sua fonte, acrescido de morfologia, lematização e números
de Strong sob renúncia CC0 1.0. O snapshot exato é pinado por commit e SHA-256.

## Decisão

1. Adotar `morph/Nestle1904.csv` como autoridade textual do Novo Testamento.
2. Ingerir somente os sete campos documentados: referência OSIS, texto grego,
   morfologia funcional, morfologia formal, Strong, lema e forma normalizada.
   Anotações morfológicas extras presentes em uma linha são preservadas, não
   descartadas. Nenhum gloss ou tradução de terceiro é ingerido.
3. Manter o OpenGNT em `analysis-only-quarantined`; nenhum campo de tradução ou
   packet do NT pode derivar exclusivamente dele.
4. Preservar lacunas de numeração do texto crítico. Controles que misturam dois
   versos-fonte são omitidos ou mapeados explicitamente, nunca divididos por
   inferência.
5. Em Marcos 16, manter o final longo 16:9–20 conforme o CSV e anexar o final
   curto, fornecido como pseudo-verso 16:99, ao aparato de 16:20. O pseudo-verso
   não se torna referência canônica da BV.

## Proveniência pinada

- Upstream: `biblicalhumanities/Nestle1904`
- Commit: `713f28a3b7d4d66132f5aa809fa223fe79762e5d`
- Arquivo: `morph/Nestle1904.csv`
- SHA-256: `3beee6abb6302f691110fe0fc949fc195593b999cf2d0e463c9b573c1bb67150`
- Licença da morfologia: CC0 1.0
- Texto-base: declarado em domínio público no README upstream arquivado em
  `sources/nestle1904/README-BASE-TEXT.md`

## Consequências

- O bloqueio F-0003 deixa de existir; o programa pode avançar pelo NT.
- A extração grega usa `internal/nestle1904`, separada do dialeto OSIS do OSHB.
- Registros do NT pinam `nestle1904@713f28a3` em `fontes.texto_fonte`.
- A numeração crítica pode ter menos registros que a numeração tradicional dos
  controles; cobertura é contada pelos OSIS realmente presentes na fonte.

## Alternativas rejeitadas

- Promover OpenGNT: incompatível com o escopo comercial/aberto pretendido.
- Usar glosses do repositório Nestle1904: licença e autoria diferem do CSV
  morfológico e não são necessários para tradução fonte-primeiro.
- Emitir `Mark.16.99` como versículo canônico: confundiria aparato com cânon.

## Rollback

Reverter o onboarding e os packets do NT antes de qualquer tradução, ou adotar
outra edição crítica por novo ADR com migração explícita dos registros.
