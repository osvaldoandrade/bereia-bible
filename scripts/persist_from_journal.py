#!/usr/bin/env python3
"""Recover verse records from a workflow journal and persist them.

Long batch workflows tend to hang at final aggregation (F-0014); the per-agent
results are durable in journal.jsonl regardless. This recovers the latest
record per verse, re-injects the authoritative Hebrew surface from the pinned
packet (F-0015), validates word alignment, and writes to translation/<book>/<chap>/.

Usage:
  python3 scripts/persist_from_journal.py <journal.jsonl> <packet1.json> [packet2.json ...]

Records are matched to packets by osisID. Zero third-party deps.
"""
import json
import os
import sys
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK_DIR = {"Gen": "01-gn"}  # extend as books are added


def latest_records(journal_path):
    """Return {osis: record}, keeping the highest ciclos_consenso / last seen."""
    by_osis = {}
    with open(journal_path) as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("type") != "result":
                continue
            r = d.get("result")
            if not isinstance(r, dict):
                continue
            reg = r.get("registro") if isinstance(r.get("registro"), dict) else None
            if reg is None:
                continue
            osis = reg.get("referencia", {}).get("osis")
            if not osis:
                continue
            prev = by_osis.get(osis)
            if not prev or reg.get("ciclos_consenso", 1) >= prev.get("ciclos_consenso", 1):
                by_osis[osis] = reg
    return by_osis


def packet_surfaces(packet_paths):
    """Return {osis: [surface,...]} of type=word tokens, in order."""
    out = {}
    for p in packet_paths:
        pk = json.load(open(p))
        for v in pk["versos"]:
            out[v["osis"]] = [w["surface"] for w in v["palavras"] if w["type"] == "word"]
    return out


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    journal, packets = sys.argv[1], sys.argv[2:]
    recs = latest_records(journal)
    surf = packet_surfaces(packets)
    written, reinjected, flagged = 0, 0, []
    for osis, reg in sorted(recs.items()):
        book = osis.split(".")[0]
        chap = int(osis.split(".")[1])
        d = os.path.join(ROOT, "translation", BOOK_DIR.get(book, book), "%03d" % chap)
        os.makedirs(d, exist_ok=True)
        src = surf.get(osis)
        to = reg.get("termos_originais", [])
        if src is not None and len(src) == len(to):
            for i, t in enumerate(to):
                if t.get("palavra") != src[i]:
                    reinjected += 1
                t["palavra"] = src[i]
        elif src is not None:
            flagged.append("%s (termos=%d packet=%d)" % (osis, len(to), len(src)))
        path = os.path.join(d, osis + ".json")
        json.dump(reg, open(path, "w"), ensure_ascii=False, indent=2)
        open(path, "a").write("\n")
        written += 1
    print("persistidos: %d | surfaces re-injetadas: %d" % (written, reinjected))
    if flagged:
        print("DESALINHADOS (checar):", ", ".join(flagged))


if __name__ == "__main__":
    main()
