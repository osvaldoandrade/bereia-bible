#!/usr/bin/env python3
"""Generate every NT chapter packet from the pinned Nestle 1904 CSV.

Writes a full packet (with WEB/KJV/Livre controls where cleanly alignable) and
an otherwise identical `.blind.json` packet with no `controles` keys. The
canonical chapter ranges come from source OSIS references; Mark 16:99 is kept
as apparatus by bvsrc and is never counted as a canonical verse.
"""

import argparse
import csv
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "sources", "nestle1904", "Nestle1904.csv")
SOURCE_REL = os.path.relpath(SOURCE, ROOT)
BVSRC = os.path.join(ROOT, "bin", "bvsrc")
CONTROLS = {
    "web": os.path.join(ROOT, "sources", "web", "web.getbible.json"),
    "kjv": os.path.join(ROOT, "sources", "kjv", "kjv.getbible.json"),
    "livre": os.path.join(ROOT, "sources", "pt-pd", "livre.getbible.json"),
}

BOOKS = [
    (40, "Matt", "matt"), (41, "Mark", "mark"), (42, "Luke", "luke"),
    (43, "John", "john"), (44, "Acts", "acts"), (45, "Rom", "rom"),
    (46, "1Cor", "1cor"), (47, "2Cor", "2cor"), (48, "Gal", "gal"),
    (49, "Eph", "eph"), (50, "Phil", "phil"), (51, "Col", "col"),
    (52, "1Thess", "1thess"), (53, "2Thess", "2thess"),
    (54, "1Tim", "1tim"), (55, "2Tim", "2tim"), (56, "Titus", "titus"),
    (57, "Phlm", "phlm"), (58, "Heb", "heb"), (59, "Jas", "jas"),
    (60, "1Pet", "1pet"), (61, "2Pet", "2pet"),
    (62, "1John", "1john"), (63, "2John", "2john"),
    (64, "3John", "3john"), (65, "Jude", "jude"), (66, "Rev", "rev"),
]


def source_ranges():
    verses = {}
    with open(SOURCE, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            book, cv = row["BCV"].split()
            chapter, verse = map(int, cv.split(":"))
            if book == "Mark" and chapter == 16 and verse == 99:
                continue
            verses.setdefault((book, chapter), set()).add(verse)
    return {key: (min(vv), max(vv), len(vv)) for key, vv in verses.items()}


def command(book_nr, osis, chapter, first, last, out, blind):
    cmd = [
        BVSRC, "-nestle1904", SOURCE_REL, "-osis", osis, "-booknr", str(book_nr),
        "-chapter", str(chapter), "-from", str(first), "-to", str(last),
        "-pericope", f"{osis}.{chapter}.{first}-{last}", "-out", out,
    ]
    if not blind:
        for flag, path in CONTROLS.items():
            cmd.extend(["-" + flag, path])
    return cmd


def without_controls(packet):
    packet = json.loads(json.dumps(packet, ensure_ascii=False))
    for verse in packet["versos"]:
        verse.pop("controles", None)
    return packet


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=os.path.join(ROOT, "pipeline", "packets"))
    args = parser.parse_args()
    os.makedirs(args.out, exist_ok=True)
    if not os.path.exists(BVSRC):
        raise SystemExit("bin/bvsrc ausente; execute `make build`")

    ranges = source_ranges()
    generated = verses_total = 0
    control_coverage = {"web": 0, "kjv": 0, "livre": 0}
    variant_osis = []
    for book_nr, osis, prefix in BOOKS:
        chapters = sorted(ch for book, ch in ranges if book == osis)
        if not chapters or chapters != list(range(1, max(chapters) + 1)):
            raise SystemExit(f"capítulos não contíguos para {osis}: {chapters}")
        for chapter in chapters:
            first, last, count = ranges[(osis, chapter)]
            stem = f"{prefix}-{chapter:03d}-{first:03d}-{last:03d}"
            full_path = os.path.join(args.out, stem + ".json")
            blind_path = os.path.join(args.out, stem + ".blind.json")
            subprocess.run(command(book_nr, osis, chapter, first, last, full_path, False), check=True, cwd=ROOT)
            subprocess.run(command(book_nr, osis, chapter, first, last, blind_path, True), check=True, cwd=ROOT)

            with open(full_path) as f:
                full = json.load(f)
            with open(blind_path) as f:
                blind = json.load(f)
            if len(full["versos"]) != count or len(blind["versos"]) != count:
                raise SystemExit(f"cobertura divergente em {osis}.{chapter}")
            expected_source = {
                "id": "nestle1904", "arquivo": SOURCE_REL,
                "git_commit": "713f28a3b7d4d66132f5aa809fa223fe79762e5d",
            }
            if full.get("fonte") != expected_source or blind.get("fonte") != expected_source:
                raise SystemExit(f"pin/caminho da fonte divergente em {osis}.{chapter}")
            if without_controls(full) != blind:
                raise SystemExit(f"blind diverge além de controles em {osis}.{chapter}")
            if any("controles" in verse for verse in blind["versos"]):
                raise SystemExit(f"controle vazou no blind em {osis}.{chapter}")
            for verse in full["versos"]:
                for control in control_coverage:
                    if verse.get("controles", {}).get(control, "").strip():
                        control_coverage[control] += 1
                if verse.get("variantes_fonte"):
                    variant_osis.append(verse["osis"])
            generated += 1
            verses_total += count

    if (generated, verses_total) != (260, 7942):
        raise SystemExit(f"cobertura canônica inesperada: {generated} capítulos/{verses_total} versículos")
    if control_coverage != {"web": 7935, "kjv": 7938, "livre": 7940}:
        raise SystemExit(f"cobertura de controles inesperada: {control_coverage}")
    if variant_osis != ["Mark.16.20"]:
        raise SystemExit(f"aparato-fonte inesperado: {variant_osis}")
    print(
        f"NT packets: {generated} capítulos, {verses_total} versículos; "
        f"controles {control_coverage}; full+blind OK"
    )


if __name__ == "__main__":
    main()
