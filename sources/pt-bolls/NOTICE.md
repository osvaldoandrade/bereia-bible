# bolls.life PT-BR reference texts — NOTICE

**Acesso:** 2026-08-29
**Fonte:** <https://bolls.life/static/translations/{NTLH,ARA,NVIPT}.json>

## Propriedade intelectual

Os textos contidos em `NTLH.json`, `ARA.json` e `NVIPT.json` são propriedade
das respectivas editoras:

- **NTLH** — Nova Tradução na Linguagem de Hoje © Sociedade Bíblica do Brasil (SBB).
- **ARA** — Almeida Revista e Atualizada © SBB.
- **NVIPT** — Nova Versão Internacional © Biblica International.

## Finalidade e restrições

Estes arquivos existem **exclusivamente** para uso como referência editorial
interna no pipeline de revisão da Bereia Version (ER-0019). Eles **não
devem**:

- ser versionados no git (o diretório `sources/pt-bolls/*.json` está no
  `.gitignore`);
- ser redistribuídos, publicados ou incorporados em output publicado;
- ser enviados a APIs, repositórios públicos ou terceiros.

O uso transformativo local (comparação paralela para revisão de forma) é
considerado fair use / uso justo para fins editoriais não comerciais. A
publicação do texto das referências exigiria licença direta das editoras.

## Arquivos

| Versão | Versículos | Acesso |
|---|---|---|
| NTLH | 30321 | 2026-08-29 |
| ARA | 31097 | 2026-08-29 |
| NVIPT | 31100 | 2026-08-29 |


## Como regenerar

```
python3 scripts/fetch_bolls_references.py
```

A data de acesso acima deve ser atualizada a cada regeneração.
