#!/usr/bin/env python3
"""Publish a read-only JSON API of the Bereia Version (BV) into site/,
ready to be served as-is by GitHub Pages.

Walks translation/<NN-xx>/<chapter>/*.json verse records (schema:
api/verse-record.schema.json) and emits, per chapter:

  site/api/v1/bv/<bookId>/<chapter>.json
      [{"verse": 1, "text": "..."}, {"verse": 2, "text": "..."}, ...]

and a manifest listing which book ids have at least one published chapter:

  site/api/v1/bv/manifest.json
      {"books": [1, 2, ..., 39]}

Field whitelist is deliberate and load-bearing: only `referencia.versiculo`
and `texto_bv` cross into the public payload. Everything else in a verse
record — decisoes, justificativa, confianca, termos_originais, fontes — is
the private editorial audit trail and must never leak into site/ (ADR-0004).

Book id = the numeric prefix of the translation/ directory (01-gn -> 1,
39-ml -> 39), already 1:1 with the Protestant-canon numbering the reader
(bereia-www) uses. Idempotent: safe to rerun, always regenerates from disk.

Usage: python3 scripts/publish_api.py [--out site]
Zero third-party deps (ADR-0001 §10).
"""
import argparse
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSLATION_DIR = os.path.join(ROOT, "translation")

BOOK_DIR_RE = re.compile(r"^(\d{2})-")


def iter_book_dirs():
    for name in sorted(os.listdir(TRANSLATION_DIR)):
        path = os.path.join(TRANSLATION_DIR, name)
        if not os.path.isdir(path):
            continue
        m = BOOK_DIR_RE.match(name)
        if not m:
            continue
        yield int(m.group(1)), name, path


def iter_chapter_dirs(book_path):
    for name in sorted(os.listdir(book_path)):
        path = os.path.join(book_path, name)
        if not os.path.isdir(path) or not name.isdigit():
            continue
        yield int(name), path


def load_chapter_verses(chapter_path):
    verses = []
    for f in sorted(glob.glob(os.path.join(chapter_path, "*.json"))):
        with open(f, encoding="utf-8") as fh:
            record = json.load(fh)
        verses.append({
            "verse": record["referencia"]["versiculo"],
            "text": record["texto_bv"],
        })
    verses.sort(key=lambda v: v["verse"])
    return verses


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=os.path.join(ROOT, "site"))
    args = parser.parse_args()

    bv_dir = os.path.join(args.out, "api", "v1", "bv")
    os.makedirs(bv_dir, exist_ok=True)

    books_published = []
    chapters_written = verses_written = 0

    for book_id, dir_name, book_path in iter_book_dirs():
        book_out = os.path.join(bv_dir, str(book_id))
        chapter_count = 0
        for chapter_num, chapter_path in iter_chapter_dirs(book_path):
            verses = load_chapter_verses(chapter_path)
            if not verses:
                continue
            os.makedirs(book_out, exist_ok=True)
            out_file = os.path.join(book_out, f"{chapter_num}.json")
            with open(out_file, "w", encoding="utf-8") as fh:
                json.dump(verses, fh, ensure_ascii=False, separators=(",", ":"))
            chapter_count += 1
            chapters_written += 1
            verses_written += len(verses)
        if chapter_count:
            books_published.append(book_id)
            print(f"{dir_name}: {chapter_count} capítulos publicados")

    books_published.sort()
    manifest_path = os.path.join(bv_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump({"books": books_published}, fh, separators=(",", ":"))

    # GitHub Pages must not run this through Jekyll (would drop dotfiles /
    # mishandle the plain JSON tree).
    open(os.path.join(args.out, ".nojekyll"), "w").close()

    print(
        f"publish_api: {len(books_published)} livros, "
        f"{chapters_written} capítulos, {verses_written} versículos -> {args.out}"
    )


if __name__ == "__main__":
    main()
