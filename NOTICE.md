# NOTICE — Atribuições obrigatórias

Qualquer distribuição de artefatos da Bereia Version (BV) deve incluir este arquivo.

A BV é derivada de/auditada contra as seguintes obras:

- **Open Scriptures Hebrew Bible (OSHB)** — Westminster Leningrad Codex com
  anotação morfológica. Licença: CC BY 4.0. https://github.com/openscriptures/morphhb
  (autoridade textual do Antigo Testamento; commit pinado em `sources/manifest.json`).
- **World English Bible (WEB)** — domínio público. https://worldenglish.bible/
  (controle de QA; nenhuma redação da BV deriva dela).
- **King James Version (1769)** — domínio público fora do Reino Unido
  (controle histórico de QA).
- **Bíblia Livre (BLIVRE)** — CC BY 3.0 BR. https://ebible.org/find/details.php?id=porbr2018
  (controle histórico de QA em português; nenhuma redação da BV deriva dela).
- **OpenGNT** — CC BY-NC-SA 4.0. https://github.com/eliranwong/OpenGNT
  (EM QUARENTENA: apoio analítico apenas; não é autoridade textual da BV;
  ver `sources/opengnt/README-QUARENTENA.md` e ADR-0001).

Traduções protegidas (ARA, NVI, NAA, NTLH) NÃO são armazenadas neste repositório
e NÃO são fonte de redação da BV; são consultadas apenas qualitativamente para
detecção de divergência, conforme `pipeline/PIPELINE.md` §QA.
