#!/usr/bin/env python3
"""Promote verse records along the status FSM, in bulk.

The FSM (PIPELINE.md) is DRAFT -> REVIEW -> APPROVED. Until now there was no
tool to move it: status was only ever written by the drafting persister, so a
promotion meant hand-editing 31155 files. This is that tool.

The transition itself is the maintainer's call and is recorded as such — the
`-autoridade` string goes into every promoted record, so any reader can see who
authorised the move and under which directive. What the script still refuses is
an INCOHERENT record, not an unpopular decision:

  * unknown source/target status (typo protection);
  * a record whose `objecoes_nao_resolvidas` is non-empty being promoted to
    APPROVED — that is F-0011, and it is a claim of fact: "this verse has an
    unresolved objection" and "this verse is publishable" cannot both be true.
    Use -force to override, which records the override in the file itself.

Usage:
  python3 scripts/promote_status.py -de DRAFT -para REVIEW \
      -autoridade "ER-0021, determinação do mantenedor 2026-08-31" [-livro 01-gn]
      [-dry-run] [-force]

Zero third-party deps.
"""
import argparse
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUSES = ("DRAFT", "REVIEW", "APPROVED")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-de", required=True, choices=STATUSES)
    ap.add_argument("-para", required=True, choices=STATUSES)
    ap.add_argument("-autoridade", required=True,
                    help="quem autorizou e sob qual diretriz; gravado no registro")
    ap.add_argument("-livro", default=None, help="restringe a um book_dir")
    ap.add_argument("-dry-run", action="store_true")
    ap.add_argument("-force", action="store_true",
                    help="promove a APPROVED mesmo com objeção aberta (F-0011)")
    args = ap.parse_args(argv)

    if args.de == args.para:
        print("origem e destino iguais — nada a fazer")
        return 0

    pattern = os.path.join(ROOT, "translation", args.livro or "*", "*", "*.json")
    promoted = skipped = blocked = 0
    for path in sorted(glob.glob(pattern)):
        with open(path, encoding="utf-8") as f:
            rec = json.load(f)
        if rec.get("status") != args.de:
            skipped += 1
            continue
        objs = rec.get("objecoes_nao_resolvidas") or []
        if args.para == "APPROVED" and objs and not args.force:
            print("BLOQUEADO %s: objeção aberta (F-0011)"
                  % rec.get("referencia", {}).get("osis", path))
            blocked += 1
            continue

        if not args.dry_run:
            rec["status"] = args.para
            entrada = {
                "questao": "Transição de status %s → %s" % (args.de, args.para),
                "escolha": args.para,
                "justificativa": "Autoridade: " + args.autoridade
                                 + (" — promovido com objeção aberta via -force "
                                    "(F-0011 sobreposta)" if objs else ""),
                "alternativas_rejeitadas": [],
                "diretriz_ref": "ER-0021",
            }
            rec.setdefault("decisoes", []).append(entrada)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rec, f, ensure_ascii=False, indent=2)
                f.write("\n")
        promoted += 1

    verbo = "promoveria" if args.dry_run else "promovidos"
    print("%s: %d %s | %d fora do estado de origem | %d bloqueados"
          % (verbo, promoted, args.de + "→" + args.para, skipped, blocked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
