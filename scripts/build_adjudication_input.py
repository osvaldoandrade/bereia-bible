#!/usr/bin/env python3
"""Build adjudication packets for open MATERIAL objections (ER-0020).

One packet per chapter that still carries `objecoes_nao_resolvidas`. Each
objecting verse gets everything the adjudicator needs to decide WITHOUT
re-reading the pinned XML:

  * texto_bv and traducao_literal (the BV's own two layers);
  * termos_originais (surface + Strong lemma + morphology, already pinned in
    the record by persist_chapter_draft.py — this is the textual AUTHORITY);
  * the open objection strings;
  * KJV and WEB at the same reference, plus the two neighbouring verses.

Why two English controls: KJV rests on the Textus Receptus / Ben Chayyim,
WEB on a modern critical base. When the two disagree, the divergence is
TEXTUAL (a variant), not semantic, and must never be followed into texto_bv
— the adjudicator reports it instead. Both are `qa-control-only` in
sources/manifest.json; neither outranks the Hebrew/Greek.

Versification: WLC/OSHB (which the BV follows) diverges from the English
tradition in Psalms superscriptions, Joel, Malachi and parts of Exodus, so
the same chapter:verse is NOT guaranteed to align. Neighbours are shipped
precisely so the adjudicator can detect misalignment by content instead of
assuming it away.

Usage:
    python3 scripts/build_adjudication_input.py [-out DIR]

Zero third-party deps.
"""
import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "qa", "reports", "adjudication-input")
CONTROLS = {
    "kjv": os.path.join(ROOT, "sources", "kjv", "kjv.getbible.json"),
    "web": os.path.join(ROOT, "sources", "web", "web.getbible.json"),
}


def load_control(path):
    """{book_nr: {chapter: {verse: text}}} from a getBible dump."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    out = {}
    for book in data["books"]:
        chapters = {}
        for ch in book["chapters"]:
            chapters[int(ch["chapter"])] = {
                int(v["verse"]): v["text"].strip() for v in ch["verses"]}
        out[int(book["nr"])] = chapters
    return out


def control_slice(control, book_nr, chapter, verse):
    """The verse plus its two neighbours, so misalignment is detectable."""
    chap = control.get(book_nr, {}).get(chapter, {})
    if not chap:
        return None
    entry = {"texto": chap.get(verse)}
    viz = {}
    for n in (verse - 1, verse + 1):
        if n in chap:
            viz[str(n)] = chap[n]
    if viz:
        entry["vizinhos"] = viz
    return entry


def collect():
    """[(book_dir, chapter, [verse-packet, ...]), ...] sorted canonically."""
    controls = {k: load_control(p) for k, p in CONTROLS.items()}
    trans = os.path.join(ROOT, "translation")
    chapters = []
    for book_dir in sorted(os.listdir(trans)):
        book_path = os.path.join(trans, book_dir)
        if not os.path.isdir(book_path):
            continue
        book_nr = int(book_dir.split("-", 1)[0])
        for cap in sorted(os.listdir(book_path)):
            cap_path = os.path.join(book_path, cap)
            if not os.path.isdir(cap_path):
                continue
            versos = []
            for fn in sorted(os.listdir(cap_path)):
                if not fn.endswith(".json"):
                    continue
                with open(os.path.join(cap_path, fn), encoding="utf-8") as f:
                    rec = json.load(f)
                objs = rec.get("objecoes_nao_resolvidas") or []
                if not objs:
                    continue
                osis = fn[:-5]
                verse_nr = int(osis.rsplit(".", 1)[1])
                versos.append({
                    "osis": osis,
                    "status": rec.get("status"),
                    "texto_bv": rec.get("texto_bv"),
                    "traducao_literal": rec.get("traducao_literal"),
                    "termos_originais": rec.get("termos_originais") or [],
                    "objecoes": objs,
                    "controles": {
                        name: control_slice(ctl, book_nr, int(cap), verse_nr)
                        for name, ctl in controls.items()},
                })
            if versos:
                chapters.append((book_dir, int(cap), versos))
    return chapters


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-out", default=OUT_DIR)
    args = ap.parse_args(argv)

    os.makedirs(args.out, exist_ok=True)
    chapters = collect()
    total = 0
    for book_dir, cap, versos in chapters:
        total += sum(len(v["objecoes"]) for v in versos)
        path = os.path.join(args.out, "%s-%03d.json" % (book_dir, cap))
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"book_dir": book_dir, "chapter": cap,
                       "versos": versos}, f, ensure_ascii=False, indent=2)
            f.write("\n")
    print("%d capítulos, %d versos, %d objeções -> %s"
          % (len(chapters), sum(len(v) for _, _, v in chapters), total,
             args.out))


if __name__ == "__main__":
    main()
