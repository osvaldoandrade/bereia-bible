# Licenciamento — fontes e produto

> Este documento é análise de engenharia, **não aconselhamento jurídico**.
> Decisões finais de licenciamento do produto: mantenedor (F-0002).

## Fontes (tabela normativa)

| Fonte | SPDX | Escopo permitido | Implicação para a BV | Atribuição |
|---|---|---|---|---|
| OSHB (WLC + morfologia) | CC-BY-4.0 | **textual-authority** (AT) | BV deve atribuir (NOTICE.md); sem restrição de licença resultante | "Open Scriptures Hebrew Bible, CC BY 4.0" |
| Nestle 1904 Morphology | CC0-1.0; texto-base PD | **textual-authority** (NT) | Sem restrição de licença resultante; atribuição mantida por transparência | "Nestle 1904 Morphology, Biblical Humanities; texto-base PD, morfologia CC0" |
| OpenGNT | CC-BY-NC-SA-4.0 | analysis-only-**quarantined** | NC+SA são incompatíveis com a cadeia produtiva; permanece fora do NT (ADR-0001/0003) | "OpenGNT (Eliran Wong), CC BY-NC-SA 4.0" |
| WEB | Domínio público | qa-control-only | nenhuma | cortesia |
| KJV 1769 | PD fora do UK | qa-control-only | nenhuma (não distribuímos no UK a partir do texto KJV) | cortesia |
| Bíblia Livre | CC-BY-3.0 (BR)* | qa-control-only | atribuição em NOTICE.md por prudência | "Bíblia Livre (BLIVRE), CC BY 3.0 BR" |

\* Licença declarada pelo transporte getBible; verificação na página eBible pendente (F-0006).

## Traduções protegidas (ARA, NVI, NAA, NTLH)

- **Nunca armazenadas** no repositório; **nunca fonte de redação**.
- Uso: comparação qualitativa de divergência (conhecimento de modelo), com
  citação mínima apenas quando uma divergência precisar ser descrita.

## Produto (BV)

- Objetivo: licença aberta própria do Bereia.org. Candidatas: **CC BY-SA 4.0**
  (protege abertura derivada) ou **CC BY 4.0** (máxima adoção). Decisão: F-0002.
- A cadeia AT (OSHB CC-BY) e a cadeia NT (Nestle 1904 PD/CC0) são compatíveis
  com ambas.
- F-0003 foi resolvido pelo ADR-0003. O OpenGNT continua em quarentena e não é
  necessário para traduzir o NT.

## Risco residual de contaminação (bastion)

O QA qualitativo contra traduções protegidas depende de memória de modelo e não
prova mecanicamente a ausência de reprodução verbatim. Controles compensatórios:

1. Processo fonte-primeiro: agentes redigem a partir do hebraico/grego pinado;
   controles entram só para detecção de divergência (Agente 2 nem os recebe).
2. Prompts proíbem reprodução de redação de qualquer tradução existente.
3. QA mecânico (n-gram/LCS) contra os controles pt armazenados (PD/CC-BY).
4. Gate humano de ratificação (REVIEW → APPROVED) com registro em DECISOES.md.
5. Coincidência inevitável (tradução natural do original) é documentada, não
   reescrita artificialmente — a independência vem do processo, não de paráfrase evasiva.
