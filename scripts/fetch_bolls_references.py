#!/usr/bin/env python3
"""Fetch PT-BR reference translations from bolls.life (ER-0019 v2).

Downloads NTLH, ARA, NVIPT bulk JSON, reorganizes into per-version files
keyed by OSIS book abbreviation (for fast lookup by qa_linguistico.py).

Output layout (gitignored, never redistributed):

  sources/pt-bolls/
    NOTICE.md          provenance, access date, fair-use rationale
    NTLH.json          { "<osis_book>": { "1": { "1": "verse text" ... } ... } ... }
    ARA.json           (same shape)
    NVIPT.json         (same shape)

The texts are property of their respective publishers (SBB for NTLH/ARA,
Biblica for NVIPT) and are used ONLY as editorial-reference input for the
local review pipeline. They must never be committed, redistributed, or
included in published output.

Usage:
  python3 scripts/fetch_bolls_references.py [--out sources/pt-bolls]

Zero third-party deps (stdlib only: urllib, json, pathlib).
"""
import argparse
import datetime
import json
import os
import re
import sys
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.path.join(ROOT, "sources", "pt-bolls")

BOLLS_BASE = "https://bolls.life/static/translations"
VERSIONS = ("NTLH", "ARA", "NVIPT")

# bolls.life numeric book id -> OSIS book abbreviation (Bereia convention).
# IDs 1..66 map 1:1 to the Protestant canon; 67+ (deuterocanonical) ignored.
BOLLS_TO_OSIS = {
    1: "Gen", 2: "Exod", 3: "Lev", 4: "Num", 5: "Deut",
    6: "Josh", 7: "Judg", 8: "Ruth",
    9: "1Sam", 10: "2Sam", 11: "1Kgs", 12: "2Kgs",
    13: "1Chr", 14: "2Chr", 15: "Ezra", 16: "Neh", 17: "Esth",
    18: "Job", 19: "Ps", 20: "Prov", 21: "Eccl", 22: "Song",
    23: "Isa", 24: "Jer", 25: "Lam", 26: "Ezek",
    27: "Dan", 28: "Hos", 29: "Joel", 30: "Amos", 31: "Obad",
    32: "Jonah", 33: "Mic", 34: "Nah", 35: "Hab", 36: "Zeph",
    37: "Hag", 38: "Zech", 39: "Mal",
    40: "Matt", 41: "Mark", 42: "Luke", 43: "John", 44: "Acts",
    45: "Rom", 46: "1Cor", 47: "2Cor", 48: "Gal", 49: "Eph",
    50: "Phil", 51: "Col", 52: "1Thess", 53: "2Thess",
    54: "1Tim", 55: "2Tim", 56: "Titus", 57: "Phlm", 58: "Heb",
    59: "Jas", 60: "1Pet", 61: "2Pet", 62: "1John", 63: "2John",
    64: "3John", 65: "Jude", 66: "Rev",
}

STRONG_RE = re.compile(r"<S>[^<]*</S>")
FOOTNOTE_RE = re.compile(r"<f>[^<]*</f>")


def clean_verse(text: str) -> str:
    """Strip Strong's numbers and footnote markers (matches bereia-www cleanVerse)."""
    return FOOTNOTE_RE.sub("", STRONG_RE.sub("", text)).strip()


def download(version: str, timeout: int = 120) -> list:
    url = f"{BOLLS_BASE}/{version}.json"
    print(f"  baixando {url} ...")
    req = urllib.request.Request(url, headers={"User-Agent": "bereia-bible/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def reorganize(flat: list) -> dict:
    """flat list of {book, chapter, verse, text} -> nested dict by OSIS book."""
    nested = {}
    skipped = 0
    for entry in flat:
        book_id = entry.get("book")
        osis = BOLLS_TO_OSIS.get(book_id)
        if osis is None:
            skipped += 1
            continue
        chapter = str(entry.get("chapter", ""))
        verse = str(entry.get("verse", ""))
        text = clean_verse(entry.get("text", ""))
        nested.setdefault(osis, {}).setdefault(chapter, {})[verse] = text
    return nested, skipped


def write_notice(out_dir: str, access_date: str, counts: dict) -> None:
    notice = f"""# bolls.life PT-BR reference texts — NOTICE

**Acesso:** {access_date}
**Fonte:** <https://bolls.life/static/translations/{{NTLH,ARA,NVIPT}}.json>

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
{"".join(f"| {v} | {counts.get(v, '?')} | {access_date} |\n" for v in VERSIONS)}

## Como regenerar

```
python3 scripts/fetch_bolls_references.py
```

A data de acesso acima deve ser atualizada a cada regeneração.
"""
    with open(os.path.join(out_dir, "NOTICE.md"), "w", encoding="utf-8") as f:
        f.write(notice)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=DEFAULT_OUT,
                    help="output directory (default: sources/pt-bolls)")
    ap.add_argument("--timeout", type=int, default=120)
    args = ap.parse_args(argv)

    os.makedirs(args.out, exist_ok=True)
    access_date = datetime.date.today().isoformat()
    counts = {}

    for version in VERSIONS:
        flat = download(version, timeout=args.timeout)
        nested, skipped = reorganize(flat)
        out_path = os.path.join(args.out, f"{version}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(nested, f, ensure_ascii=False, indent=1)
            f.write("\n")
        n_verses = sum(len(vv) for ch in nested.values() for vv in ch.values())
        counts[version] = n_verses
        print(f"  {version}: {n_verses} versos, {skipped} fora do cânone 66")

    write_notice(args.out, access_date, counts)
    print(f"\nOK — {len(VERSIONS)} versões salvas em {args.out}")
    print(f"NOTICE.md gerado. Lembre-se de não commitar {args.out}/*.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
