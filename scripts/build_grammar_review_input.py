#!/usr/bin/env python3
"""Build digests for the grammar/cohesion review of the OT (ER-0022).

Difference from the ER-0019 digest: this one carries CONTEXT. A verse read in
isolation cannot be judged for cohesion — pronoun antecedents, tense chains,
connectives and subject continuity all live across verse boundaries, and the
BV was drafted one chapter at a time, so the seams are exactly where the
Portuguese breaks down.

Each verse therefore ships with:

  * `contexto.anteriores` / `contexto.posteriores` — N verses each side, in
    reading order, CROSSING chapter boundaries (the last verse of a chapter is
    read right before the first of the next; a window that stops at the
    chapter edge would be blind at the very seam the drafting created);
  * `controles.kjv` — the King James at the same reference, the English
    formal-equivalence baseline the maintainer chose, plus its own neighbours
    so misalignment is detectable by content;
  * `termos_originais` — surface + Strong lemma + morphology from the pinned
    WLC/OSHB. This is the ceiling: cohesion may never be bought with fidelity.

Versification: WLC/OSHB diverges from the English tradition (Psalm
superscriptions, Joel, Malachi, parts of Exodus), so the KJV slice ships
neighbours and the prompt requires content-checking alignment before use.

Usage:
    python3 scripts/build_grammar_review_input.py [-janela 2] [-livros 1-39]
                                                  [-out DIR]

Zero third-party deps.
"""
import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "qa", "reports", "grammar-input")
KJV = os.path.join(ROOT, "sources", "kjv", "kjv.getbible.json")


def load_kjv():
    with open(KJV, encoding="utf-8") as f:
        data = json.load(f)
    out = {}
    for book in data["books"]:
        out[int(book["nr"])] = {
            int(ch["chapter"]): {int(v["verse"]): v["text"].strip()
                                 for v in ch["verses"]}
            for ch in book["chapters"]}
    return out


def kjv_slice(kjv, book_nr, chapter, verse):
    chap = kjv.get(book_nr, {}).get(chapter, {})
    if not chap:
        return None
    entry = {"texto": chap.get(verse)}
    viz = {str(n): chap[n] for n in (verse - 1, verse + 1) if n in chap}
    if viz:
        entry["vizinhos"] = viz
    return entry


def book_stream(book_path):
    """All verses of a book in reading order: [(chapter, osis, record), ...].

    Flat and ordered so the context window can cross chapter boundaries.
    """
    stream = []
    for cap in sorted(os.listdir(book_path)):
        cap_path = os.path.join(book_path, cap)
        if not os.path.isdir(cap_path):
            continue
        verses = []
        for fn in os.listdir(cap_path):
            if not fn.endswith(".json"):
                continue
            osis = fn[:-5]
            with open(os.path.join(cap_path, fn), encoding="utf-8") as f:
                verses.append((int(osis.rsplit(".", 1)[1]), osis,
                               json.load(f)))
        verses.sort()
        for _n, osis, rec in verses:
            stream.append((int(cap), osis, rec))
    return stream


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-janela", type=int, default=2,
                    help="versos de contexto de cada lado (default 2)")
    ap.add_argument("-livros", default="1-39",
                    help="faixa de book_nr, ex. 1-39 (AT)")
    ap.add_argument("-out", default=OUT_DIR)
    args = ap.parse_args(argv)

    lo, hi = (int(x) for x in args.livros.split("-"))
    kjv = load_kjv()
    os.makedirs(args.out, exist_ok=True)
    trans = os.path.join(ROOT, "translation")

    n_cap = n_vv = 0
    for book_dir in sorted(os.listdir(trans)):
        book_path = os.path.join(trans, book_dir)
        if not os.path.isdir(book_path):
            continue
        book_nr = int(book_dir.split("-", 1)[0])
        if not (lo <= book_nr <= hi):
            continue

        stream = book_stream(book_path)
        by_chapter = {}
        for i, (cap, osis, rec) in enumerate(stream):
            janela = args.janela
            antes = [{"osis": stream[j][1], "texto": stream[j][2]["texto_bv"]}
                     for j in range(max(0, i - janela), i)]
            depois = [{"osis": stream[j][1], "texto": stream[j][2]["texto_bv"]}
                      for j in range(i + 1,
                                     min(len(stream), i + 1 + janela))]
            by_chapter.setdefault(cap, []).append({
                "osis": osis,
                "status": rec.get("status"),
                "texto_bv": rec.get("texto_bv"),
                "traducao_literal": rec.get("traducao_literal"),
                "termos_originais": rec.get("termos_originais") or [],
                "contexto": {"anteriores": antes, "posteriores": depois},
                "controles": {"kjv": kjv_slice(kjv, book_nr, cap,
                                               int(osis.rsplit(".", 1)[1]))},
            })

        for cap, versos in sorted(by_chapter.items()):
            path = os.path.join(args.out, "%s-%03d.json" % (book_dir, cap))
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"book_dir": book_dir, "chapter": cap,
                           "janela": args.janela, "versos": versos},
                          f, ensure_ascii=False, indent=2)
                f.write("\n")
            n_cap += 1
            n_vv += len(versos)

    print("%d capítulos, %d versículos (janela ±%d, KJV como controle) -> %s"
          % (n_cap, n_vv, args.janela, args.out))


if __name__ == "__main__":
    main()
