# ADR-0001 — Bootstrap da Bereia Version: fontes, pipeline, contratos

Data: 2026-08-11 · Status: ACEITO · Tier: T3 (sinais de tamanho) · Autor: pipeline BV, ratificação pendente do mantenedor

## Contexto

O Bereia.org quer uma tradução bíblica pt-BR auditável até os textos-fonte
(WLC/OSHB para AT; grego crítico para NT), publicável sob licença aberta própria,
produzida por pipeline multiagente determinístico-por-artefatos, sem derivar
redação de traduções protegidas (ARA/NVI/NAA/NTLH).

## Decisões

1. **Fontes pinadas como dependências de dados.** `sources/manifest.json`
   (contrato `api/manifest.schema.json`, 17 campos) com URL https, commit git,
   SHA-256, SPDX, atribuição, `usage_scope` e condição de retirada. Allowlist de
   licenças por escopo em `docs/licenses/allowlist.txt`.
2. **Quarentena OpenGNT (carve-out imediato, não adiado).** OpenGNT é
   CC BY-NC-SA 4.0 → `usage_scope=analysis-only-quarantined`. Nenhum campo de
   registro BV deriva exclusivamente dele. Autoridade textual do NT será edição
   de domínio público (candidata: Nestle 1904), salvo ADR futuro (F-0003).
3. **Controle pt-BR.** Almeida 1911 não existe digitalizada em fonte aberta
   confiável (verificado em getBible e eBible.org em 2026-08-11) → Bíblia Livre
   (linhagem Almeida 1819/TR) como controle histórico pt (ER-0005; F-0001/F-0006).
4. **Perícope = agregado; versículo = entidade.** ID do agregado = faixa OSIS
   (`Gen.1.1-5`); versículo tem ID OSIS. A consistência editorial é transacional
   dentro da perícope e **eventual** entre perícopes, propagada exclusivamente
   por `lexicon/lexicon.json` (LexiconEntry) e `decisions/DECISOES.md` (ER).
5. **Hexagonal não aplicado (intencional).** Não há serviço em runtime: `cmd/` é
   a porta de condução, arquivos são o lado conduzido; `internal/` plano.
   Reavaliar somente se surgir superfície de rede (site/API do bereia.org).
6. **`internal/oshb`, não `internal/osis`.** O parser implementa o dialeto OSIS
   específico do OSHB (códigos morfológicos WLC, lemmas Strong estendidos). O NT
   (OpenGNT) é CSV — não haverá parser OSIS genérico reutilizado.
7. **Contratos versionados file-per-major.** `api/verse-record.schema.json` e
   `api/manifest.schema.json`: `$id` estável por major (`…/verse-record/1`),
   minor aditivo atualiza anotação `version`; breaking → novo `$id` major.
   Horizonte de compatibilidade: leitores aceitam N e N-1; N-2 migra antes da
   retirada. Exemplos executáveis em `api/examples/` validados em `go test`.
8. **Mapeamento nominal vs. especificação do projeto** (herald B6):
   `variantes` → `variantes_textuais`; `confidence` → `confianca`;
   `alternativas_rejeitadas` aninhado em `decisoes[]`; adicionados
   `palavras_supridas`, `ambiguidades_preservadas`, `divergencias`,
   `objecoes_nao_resolvidas` (ASCII), `ciclos_consenso`, `referencia.pericope`.
9. **Resolução da colisão do termo "decisão"** (curator): por-versículo =
   **Adjudicação** (`decisoes[]` no registro, nome mantido por fidelidade à
   especificação, semântica definida no glossário editorial); transversal =
   **Diretriz Editorial (ER-NNNN)** em DECISOES.md; terminológica =
   **LexiconEntry** em lexicon.json.
10. **Zero dependências Go.** Stdlib apenas; guardas: `test ! -f go.sum` +
    depguard. Ferramentas: `bvsrc` (extração), `bvqa` (similaridade),
    `bvcheck` (conformidade de schema + invariantes do léxico).
11. **Determinismo por artefatos persistidos.** Sampler não é determinístico na
    infraestrutura atual; a camada determinística são os artefatos versionados
    (fontes, prompts, regras, léxico, adjudicações). Registro grava modelo e
    versões. Regeneração não pode contrariar artefato persistido sem diff +
    novo ciclo (PIPELINE.md §FSM). Pipeline programático com temperatura 0: F-0004.
12. **Licença do produto BV**: aberta, decisão entre CC BY-SA 4.0 e CC BY 4.0
    pendente do mantenedor (F-0002). Cadeia AT (CC-BY) compatível com ambas.

## Consequências

- Auditoria: registro → packet → manifest → fonte upstream por SHA-256/commit.
- A fase NT tem pré-condição explícita (resolver F-0003) em vez de risco tácito.
- Custo: ferramentas de validação próprias (schemavalidate) por causa do zero-dep;
  subset de JSON Schema documentado no código.

## Alternativas rejeitadas

- OpenGNT como autoridade NT imediata (risco NC-SA inaceitável para licença aberta própria).
- Versículo como agregado (perde consistência intra-perícope); capítulo (transação longa demais).
- Parser OSIS genérico agora (YAGNI; NT é CSV).
- Dependências Go de terceiros para JSON Schema (viola zero-dep sem necessidade).

## Rollback

Repositório local; `git revert`/reset. Nenhum efeito externo até publicação.
