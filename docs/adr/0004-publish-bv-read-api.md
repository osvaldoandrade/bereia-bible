# ADR-0004 — Publicar a BV como API de leitura via GitHub Pages próprio

Data: 2026-08-18 · Status: ACEITO · Tier: T3 (workflow de CI novo)

## Contexto

O Antigo Testamento da Bereia Version fechou 100% em tier DRAFT (23.213
versículos, Gênesis→Malaquias; ADR-0002/ER-0017). O leitor de produção
(`bereia-www`, bereia.org) é uma SPA estática publicada no GitHub Pages; toda
versão bíblica hoje nela (ARA, NVI, NTLH, KJV, WLC, TISCH, VULG) é buscada ao
vivo, em tempo de execução, de `bolls.life`. A BV não está nesse provedor —
não existe outro lugar de onde o leitor possa buscá-la.

Este repositório (`bereia-bible`) é privado — contém o rastro editorial
completo por versículo (decisões, justificativas, confiança, termos
originais, fontes pinadas). Esse rastro é o que torna a tradução auditável,
mas não é o que um leitor final deve receber.

## Decisão

1. **Publicar via GitHub Pages do próprio `bereia-bible`**, não vendorizar
   cópia dentro do `bereia-www`. O leitor busca a BV com o mesmo padrão de
   fetch externo já usado para as outras seis versões — nenhuma arquitetura
   nova no lado do leitor, só mais uma origem.
2. **Whitelist de campos, não serialização do registro.** O script
   (`scripts/publish_api.py`) lê cada registro de versículo e emite **apenas**
   `referencia.versiculo` e `texto_bv`. `decisoes`, `justificativa`,
   `confianca`, `termos_originais`, `variantes_textuais`, `fontes` e
   `ambiguidades_preservadas` nunca cruzam para `site/`. O rastro auditável
   continua existindo — em `translation/`, neste repositório privado — só não
   é publicado.
3. **Contrato versionado por path: `/api/v1/bv/...`.** Uma mudança
   incompatível de formato cria `/api/v2/`; o leitor aponta para o major que
   suporta. Sem isso, qualquer ajuste de forma quebraria o leitor em produção
   sem aviso.
4. **Publicar como DRAFT, sem esperar promoção.** Nenhum registro do AT
   passou pelo ciclo de consenso completo (F-0016: "DRAFT não é publicável;
   consenso pleno + revisão ocorrem na promoção"). Decisão consciente do
   mantenedor: publicar mesmo assim, com indicação visível de "rascunho
   auditável" no leitor — não uma revogação de F-0016, uma exceção registrada
   para este lançamento.
5. **Manifesto, não contagem fixa.** `manifest.json` lista os `bookId` com
   pelo menos um capítulo publicado. O leitor consulta o manifesto em vez de
   assumir "livros 1–39"; conforme o NT for fechando, novos livros aparecem
   sem exigir mudança de código no `bereia-www`.

## Consequências

- O conteúdo de `site/api/v1/` fica **publicamente alcançável por URL**
  (`osvaldoandrade.github.io/bereia-bible/...`) mesmo com o repositório-fonte
  privado — GitHub Pages não herda a visibilidade do repo. Aceito
  explicitamente pelo mantenedor; é o texto final que se pretende publicar,
  não o rastro editorial.
- Todo push em `main` que toque `translation/**` republica automaticamente
  (`.github/workflows/publish-api.yml`); nenhum passo manual de deploy.
- `site/` é gerado, não versionado — reconstrução determinística a partir de
  `translation/` a cada execução do workflow.

## Alternativas rejeitadas

- **Vendorizar cópia dentro do `bereia-www`:** exigiria sincronização manual
  a cada atualização de tradução; o padrão de fetch externo já existe e
  funciona para as outras seis versões.
- **Servir o registro completo e filtrar no cliente:** vazaria o rastro
  editorial (decisões, confiança) para qualquer requisição de rede
  inspecionável no navegador, mesmo que a UI não o exibisse.

## Rollback

Remover `.github/workflows/publish-api.yml` (para de republicar) e apagar o
site do GitHub Pages nas configurações do repositório; o leitor volta a não
listar "BV" assim que `bereia-www` reverter a mudança correspondente.
