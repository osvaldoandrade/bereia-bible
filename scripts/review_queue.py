#!/usr/bin/env python3
"""Fila de revisão humana do ciclo de adjudicação (ER-0020).

Três seções, em ordem decrescente do que exige o mantenedor:

  ABERTAS      objeções que seguem bloqueando APPROVED — o adjudicador as
               marcou INCONCLUSIVA (crux, escolha confessional, controles
               desalinhados) ou nunca foram adjudicadas. É aqui que a decisão
               é sua.
  PROCEDE      versos cujo SENTIDO mudou por adjudicação. Risco alto: revise
               a evidência do original citada em cada um.
  IMPROCEDE    objeções fechadas sem tocar no texto. Risco baixo, listadas
               para auditoria.

Usage:
    python3 scripts/review_queue.py [-secao abertas|procede|improcede|todas]
                                    [-livro 01-gn] [-full]

Zero third-party deps.
"""
import argparse
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def er0020_decisions(rec):
    return [d for d in (rec.get("decisoes") or [])
            if d.get("diretriz_ref") == "ER-0020"]


def collect(livro=None):
    abertas, procede, improcede = [], [], []
    pattern = os.path.join(ROOT, "translation", livro or "*", "*", "*.json")
    for path in sorted(glob.glob(pattern)):
        with open(path, encoding="utf-8") as f:
            rec = json.load(f)
        osis = rec.get("referencia", {}).get("osis", os.path.basename(path))
        rel = os.path.relpath(path, ROOT)
        decs = er0020_decisions(rec)
        open_objs = rec.get("objecoes_nao_resolvidas") or []
        if open_objs:
            motivo = ""
            for d in decs:
                if "inconclusiva" in d.get("escolha", ""):
                    motivo = d.get("justificativa", "")
            abertas.append((osis, rel, rec.get("texto_bv", ""), open_objs,
                            motivo))
        for d in decs:
            if d.get("questao", "").startswith("Adjudicação") and \
                    "improcedente" in d.get("escolha", ""):
                improcede.append((osis, rel, d.get("justificativa", "")))
            elif d.get("questao", "").startswith("Adjudicação") and \
                    "→" in d.get("escolha", ""):
                procede.append((osis, rel, d.get("escolha", ""),
                                d.get("justificativa", "")))
    return abertas, procede, improcede


def show(title, rows, render, full):
    print("\n" + "=" * 72)
    print("%s — %d" % (title, len(rows)))
    print("=" * 72)
    for row in rows:
        render(row, full)


def cut(s, n, full):
    s = " ".join(str(s).split())
    return s if full else (s[:n] + ("…" if len(s) > n else ""))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-secao", default="todas",
                    choices=["abertas", "procede", "improcede", "todas"])
    ap.add_argument("-livro", default=None)
    ap.add_argument("-full", action="store_true",
                    help="não trunca justificativas")
    args = ap.parse_args(argv)

    abertas, procede, improcede = collect(args.livro)

    if args.secao in ("abertas", "todas"):
        def r(row, full):
            osis, rel, texto, objs, motivo = row
            print("\n--- %s   %s" % (osis, rel))
            print("    TEXTO : %s" % cut(texto, 160, full))
            for o in objs:
                print("    OBJ   : %s" % cut(o, 220, full))
            if motivo:
                print("    MOTIVO: %s" % cut(motivo, 260, full))
        show("ABERTAS — decisão do mantenedor", abertas, r, args.full)

    if args.secao in ("procede", "todas"):
        def r(row, full):
            osis, rel, escolha, just = row
            print("\n--- %s   %s" % (osis, rel))
            print("    MUDOU : %s" % cut(escolha, 200, full))
            print("    EVID  : %s" % cut(just, 300, full))
        show("PROCEDE — sentido alterado, revisar evidência", procede, r,
             args.full)

    if args.secao in ("improcede", "todas"):
        def r(row, full):
            osis, rel, just = row
            print("--- %-18s %s" % (osis, cut(just, 150, full)))
        show("IMPROCEDE — fechadas sem mudar texto", improcede, r, args.full)

    print("\nresumo: %d abertas | %d procede | %d improcede"
          % (len(abertas), len(procede), len(improcede)))


if __name__ == "__main__":
    main()
