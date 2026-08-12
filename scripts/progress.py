#!/usr/bin/env python3
"""Regenerate translation/PROGRESS.md from disk state vs. the pinned OSHB.

Scans translation/<book>/<chapter>/*.json records and cross-references the
verse counts in the pinned OSHB source, reporting per-chapter coverage and
record status. Zero third-party deps (ADR-0001 §10). Run: python3 scripts/progress.py
"""
import json
import os
import re
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = [  # AT expands here as books are sourced
    ("01-gn", "Gen", "Gênesis"),
    ("02-ex", "Exod", "Êxodo"),
    ("03-lv", "Lev", "Levítico"),
]


def oshb_verse_counts(osis_book):
    path = os.path.join(ROOT, "sources", "oshb", osis_book + ".xml")
    if not os.path.exists(path):
        return {}
    text = open(path, encoding="utf-8").read()
    counts = {}
    for m in re.finditer(r'osisID="%s\.(\d+)\.(\d+)"' % osis_book, text):
        c, v = int(m.group(1)), int(m.group(2))
        counts[c] = max(counts.get(c, 0), v)
    return counts


def chapter_status(book_dir, osis_book, chapter):
    d = os.path.join(ROOT, "translation", book_dir, "%03d" % chapter)
    recs = sorted(glob.glob(os.path.join(d, "%s.%d.*.json" % (osis_book, chapter))))
    statuses = []
    for p in recs:
        try:
            statuses.append(json.load(open(p))["status"])
        except (json.JSONDecodeError, KeyError):
            statuses.append("BROKEN")
    return statuses


def main():
    lines = ["# PROGRESS — Bereia Version (programa Bíblia completa)", ""]
    lines.append("Rastreador por capítulo (ADR-0002). NT bloqueado por F-0003 (quarentena OpenGNT).")
    lines.append("Regenerar: `python3 scripts/progress.py`. Fonte de contagem: OSHB pinado.")
    lines.append("")
    grand_done = grand_total = 0
    for book_dir, osis_book, name in BOOKS:
        counts = oshb_verse_counts(osis_book)
        if not counts:
            lines.append("## %s — fonte não baixada" % name)
            continue
        nch = max(counts)
        total = sum(counts.values())
        done = 0
        rows = []
        for c in range(1, nch + 1):
            st = chapter_status(book_dir, osis_book, c)
            expect = counts.get(c, 0)
            have = len(st)
            done += sum(1 for s in st if s in ("REVIEW", "APPROVED", "DRAFT"))
            if have == 0:
                mark = "· pendente"
            elif have < expect:
                mark = "◐ parcial %d/%d [%s]" % (have, expect, ",".join(sorted(set(st))))
            else:
                mark = "● %d/%d [%s]" % (have, expect, ",".join(sorted(set(st))))
            rows.append((c, expect, mark))
        grand_done += done
        grand_total += total
        pct = 100.0 * done / total if total else 0
        lines.append("## %s — %d/%d versículos (%.1f%%), %d capítulos" % (name, done, total, pct, nch))
        lines.append("")
        lines.append("| Cap | Vers | Estado |")
        lines.append("|---|---|---|")
        for c, expect, mark in rows:
            lines.append("| %d | %d | %s |" % (c, expect, mark))
        lines.append("")
    lines.insert(4, "**Total AT sourced: %d/%d versículos.**" % (grand_done, grand_total))
    lines.insert(5, "")
    open(os.path.join(ROOT, "translation", "PROGRESS.md"), "w").write("\n".join(lines) + "\n")
    print("PROGRESS.md: %d/%d versículos" % (grand_done, grand_total))


if __name__ == "__main__":
    main()
