#!/usr/bin/env python3
"""Generate every remaining OT chapter packet from the pinned OSHB XML.

Mirrors generate_nt_packets.py but sources from sources/oshb/<Osis>.xml
instead of the Nestle 1904 CSV. Writes a full packet (with WEB/KJV/Livre
controls) and an otherwise identical `.blind.json` packet with no
`controles` keys, for every book not yet present in pipeline/packets/.

Usage: python3 scripts/generate_ot_packets.py [--books Esth,Job,...]
"""
import argparse
import glob
import json
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OSHB_DIR = os.path.join(ROOT, "sources", "oshb")
BVSRC = os.path.join(ROOT, "bin", "bvsrc")
CONTROLS = {
    "web": os.path.join(ROOT, "sources", "web", "web.getbible.json"),
    "kjv": os.path.join(ROOT, "sources", "kjv", "kjv.getbible.json"),
    "livre": os.path.join(ROOT, "sources", "pt-pd", "livre.getbible.json"),
}
OSHB_COMMIT = "3d15126fb1ef74867fc1434be1942e837932691f"

# (booknr, osis, dir-prefix) — remaining OT books per translation/PROGRESS.md order
BOOKS = [
    (17, "Esth", "17-et"), (18, "Job", "18-jo"), (19, "Ps", "19-sl"),
    (20, "Prov", "20-pv"), (21, "Eccl", "21-ec"), (22, "Song", "22-ct"),
    (23, "Isa", "23-is"), (24, "Jer", "24-jr"), (25, "Lam", "25-lm"),
    (26, "Ezek", "26-ez"), (27, "Dan", "27-dn"), (28, "Hos", "28-os"),
    (29, "Joel", "29-jl"), (30, "Amos", "30-am"), (31, "Obad", "31-ob"),
    (32, "Jonah", "32-jn"), (33, "Mic", "33-mq"), (34, "Nah", "34-na"),
    (35, "Hab", "35-hc"), (36, "Zeph", "36-sf"), (37, "Hag", "37-ag"),
    (38, "Zech", "38-zc"), (39, "Mal", "39-ml"),
]


def oshb_verse_sets(osis_book):
    path = os.path.join(OSHB_DIR, osis_book + ".xml")
    text = open(path, encoding="utf-8").read()
    verses = {}
    for m in re.finditer(r'osisID="%s\.(\d+)\.(\d+)"' % re.escape(osis_book), text):
        chapter, verse = int(m.group(1)), int(m.group(2))
        verses.setdefault(chapter, set()).add(verse)
    return verses


def command(book_nr, osis, chapter, first, last, out, blind):
    cmd = [
        BVSRC, "-oshb", os.path.join("sources", "oshb", osis + ".xml"),
        "-osis", osis, "-booknr", str(book_nr),
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
    parser.add_argument("--books", default="", help="comma-separated OSIS ids to limit to")
    args = parser.parse_args()
    os.makedirs(args.out, exist_ok=True)
    if not os.path.exists(BVSRC):
        raise SystemExit("bin/bvsrc ausente; execute `make build`")

    wanted = set(args.books.split(",")) if args.books else None
    generated = verses_total = 0
    for book_nr, osis, prefix in BOOKS:
        if wanted and osis not in wanted:
            continue
        stem_prefix = prefix.split("-", 1)[1]
        existing = glob.glob(os.path.join(args.out, f"{stem_prefix}-*.json"))
        if existing:
            print(f"skip {osis}: {len(existing)} packet(s) já existem")
            continue
        verses = oshb_verse_sets(osis)
        chapters = sorted(verses)
        if not chapters or chapters != list(range(1, max(chapters) + 1)):
            raise SystemExit(f"capítulos não contíguos para {osis}: {chapters}")
        for chapter in chapters:
            vv = verses[chapter]
            first, last, count = min(vv), max(vv), len(vv)
            stem = f"{stem_prefix}-{chapter:03d}-{first:03d}-{last:03d}"
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
                "id": "oshb", "arquivo": f"sources/oshb/{osis}.xml",
                "git_commit": OSHB_COMMIT,
            }
            if full.get("fonte") != expected_source or blind.get("fonte") != expected_source:
                raise SystemExit(f"pin/caminho da fonte divergente em {osis}.{chapter}: {full.get('fonte')}")
            if without_controls(full) != blind:
                raise SystemExit(f"blind diverge além de controles em {osis}.{chapter}")
            if any("controles" in verse for verse in blind["versos"]):
                raise SystemExit(f"controle vazou no blind em {osis}.{chapter}")
            generated += 1
            verses_total += count
        print(f"{osis}: {len(chapters)} capítulos, {sum(len(v) for v in verses.values())} versos")

    print(f"packets gerados: {generated} capítulos, {verses_total} versículos")


if __name__ == "__main__":
    main()
