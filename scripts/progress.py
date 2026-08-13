#!/usr/bin/env python3
"""Regenerate translation/PROGRESS.md from disk state vs. pinned authorities.

Scans translation/<book>/<chapter>/*.json records and cross-references the
verse counts in OSHB/Nestle 1904, reporting per-chapter coverage and
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
    ("04-nm", "Num", "Números"),
    ("05-dt", "Deut", "Deuteronômio"),
    ("06-js", "Josh", "Josué"),
    ("07-jz", "Judg", "Juízes"),
    ("08-rt", "Ruth", "Rute"),
    ("09-1sm", "1Sam", "1 Samuel"),
    ("10-2sm", "2Sam", "2 Samuel"),
    ("11-1rs", "1Kgs", "1 Reis"),
    ("12-2rs", "2Kgs", "2 Reis"),
    ("13-1cr", "1Chr", "1 Crônicas"),
    ("14-2cr", "2Chr", "2 Crônicas"),
    ("15-ed", "Ezra", "Esdras"),
    ("16-ne", "Neh", "Neemias"),
    ("17-et", "Esth", "Ester"),
    ("18-jo", "Job", "Jó"),
    ("19-sl", "Ps", "Salmos"),
    ("20-pv", "Prov", "Provérbios"),
    ("21-ec", "Eccl", "Eclesiastes"),
    ("22-ct", "Song", "Cântico dos Cânticos"),
    ("23-is", "Isa", "Isaías"),
    ("24-jr", "Jer", "Jeremias"),
    ("25-lm", "Lam", "Lamentações"),
    ("26-ez", "Ezek", "Ezequiel"),
    ("27-dn", "Dan", "Daniel"),
    ("28-os", "Hos", "Oseias"),
    ("29-jl", "Joel", "Joel"),
    ("30-am", "Amos", "Amós"),
    ("31-ob", "Obad", "Obadias"),
    ("32-jn", "Jonah", "Jonas"),
    ("33-mq", "Mic", "Miqueias"),
    ("34-na", "Nah", "Naum"),
    ("35-hc", "Hab", "Habacuque"),
    ("36-sf", "Zeph", "Sofonias"),
    ("37-ag", "Hag", "Ageu"),
    ("38-zc", "Zech", "Zacarias"),
    ("39-ml", "Mal", "Malaquias"),
    ("40-mt", "Matt", "Mateus"),
    ("41-mc", "Mark", "Marcos"),
    ("42-lc", "Luke", "Lucas"),
    ("43-jo", "John", "João"),
    ("44-at", "Acts", "Atos"),
    ("45-rm", "Rom", "Romanos"),
    ("46-1co", "1Cor", "1 Coríntios"),
    ("47-2co", "2Cor", "2 Coríntios"),
    ("48-gl", "Gal", "Gálatas"),
    ("49-ef", "Eph", "Efésios"),
    ("50-fp", "Phil", "Filipenses"),
    ("51-cl", "Col", "Colossenses"),
    ("52-1ts", "1Thess", "1 Tessalonicenses"),
    ("53-2ts", "2Thess", "2 Tessalonicenses"),
    ("54-1tm", "1Tim", "1 Timóteo"),
    ("55-2tm", "2Tim", "2 Timóteo"),
    ("56-tt", "Titus", "Tito"),
    ("57-fm", "Phlm", "Filemom"),
    ("58-hb", "Heb", "Hebreus"),
    ("59-tg", "Jas", "Tiago"),
    ("60-1pe", "1Pet", "1 Pedro"),
    ("61-2pe", "2Pet", "2 Pedro"),
    ("62-1jo", "1John", "1 João"),
    ("63-2jo", "2John", "2 João"),
    ("64-3jo", "3John", "3 João"),
    ("65-jd", "Jude", "Judas"),
    ("66-ap", "Rev", "Apocalipse"),
]


def oshb_verse_sets(osis_book):
    path = os.path.join(ROOT, "sources", "oshb", osis_book + ".xml")
    if not os.path.exists(path):
        return {}
    text = open(path, encoding="utf-8").read()
    verses = {}
    for m in re.finditer(r'osisID="%s\.(\d+)\.(\d+)"' % osis_book, text):
        chapter, verse = int(m.group(1)), int(m.group(2))
        verses.setdefault(chapter, set()).add(verse)
    return verses


def nestle_verse_sets(osis_book):
    path = os.path.join(ROOT, "sources", "nestle1904", "Nestle1904.csv")
    if not os.path.exists(path):
        return {}
    verses = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        next(f, None)
        for line in f:
            cols = line.rstrip("\r\n").split("\t")
            if not cols:
                continue
            ref = cols[0].split()
            if len(ref) != 2 or ref[0] != osis_book:
                continue
            chapter, verse = map(int, ref[1].split(":"))
            if osis_book == "Mark" and chapter == 16 and verse == 99:
                continue
            verses.setdefault(chapter, set()).add(verse)
    return verses


def source_verse_sets(osis_book):
    verses = oshb_verse_sets(osis_book)
    return verses if verses else nestle_verse_sets(osis_book)


def chapter_status(book_dir, osis_book, chapter):
    d = os.path.join(ROOT, "translation", book_dir, "%03d" % chapter)
    recs = sorted(glob.glob(os.path.join(d, "%s.%d.*.json" % (osis_book, chapter))))
    statuses, broken = {}, []
    for path in recs:
        try:
            record = json.load(open(path))
            ref = record["referencia"]
            parts = ref["osis"].split(".")
            if (len(parts) != 3 or parts[0] != osis_book or
                    int(parts[1]) != chapter or
                    int(ref["capitulo"]) != chapter or
                    int(ref["versiculo"]) != int(parts[2])):
                raise ValueError("referência divergente")
            verse = int(parts[2])
            if verse in statuses:
                raise ValueError("OSIS duplicado")
            statuses[verse] = record["status"]
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            broken.append(os.path.basename(path))
    return statuses, broken


def chapter_progress(expected, statuses, broken):
    """Return (covered_count, rendered_status) for one source chapter."""
    valid = {verse for verse, status in statuses.items()
             if status in ("REVIEW", "APPROVED", "DRAFT")}
    actual = set(statuses)
    covered = expected & valid
    missing = expected - valid
    extra = actual - expected
    invalid = {verse for verse, status in statuses.items()
               if status not in ("REVIEW", "APPROVED", "DRAFT")}
    expect = len(expected)
    shown_statuses = ",".join(sorted(set(statuses.values())))
    if not actual and not broken:
        mark = "· pendente"
    elif not missing and not extra and not invalid and not broken:
        mark = "● %d/%d [%s]" % (len(covered), expect, shown_statuses)
    else:
        details = []
        if extra:
            details.append("extras=" + ",".join(map(str, sorted(extra))))
        if invalid:
            details.append("status-inválido=" + ",".join(map(str, sorted(invalid))))
        if broken:
            details.append("broken=" + ",".join(broken))
        suffix = ("; " + "; ".join(details)) if details else ""
        mark = "◐ parcial %d/%d [%s]%s" % (
            len(covered), expect, shown_statuses or "—", suffix)
    return len(covered), mark


def main():
    lines = ["# PROGRESS — Bereia Version (programa Bíblia completa)", ""]
    lines.append("Rastreador por capítulo (ADR-0002/0003).")
    lines.append("Regenerar: `python3 scripts/progress.py`. Fontes de contagem: OSHB e Nestle 1904 pinados.")
    lines.append("")
    grand_done = grand_total = 0
    for book_dir, osis_book, name in BOOKS:
        verse_sets = source_verse_sets(osis_book)
        if not verse_sets:
            lines.append("## %s — fonte não baixada" % name)
            continue
        nch = max(verse_sets)
        total = sum(len(verses) for verses in verse_sets.values())
        done = 0
        rows = []
        for c in range(1, nch + 1):
            expected = verse_sets.get(c, set())
            statuses, broken = chapter_status(book_dir, osis_book, c)
            expect = len(expected)
            covered, mark = chapter_progress(expected, statuses, broken)
            done += covered
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
    lines.insert(4, "**Total Bíblia sourced: %d/%d versículos.**" % (grand_done, grand_total))
    lines.insert(5, "")
    open(os.path.join(ROOT, "translation", "PROGRESS.md"), "w").write("\n".join(lines) + "\n")
    print("PROGRESS.md: %d/%d versículos" % (grand_done, grand_total))


if __name__ == "__main__":
    main()
