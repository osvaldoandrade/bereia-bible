#!/usr/bin/env python3
"""Persist editorial-review output (review-chapter-driver, ER-0019) into DRAFT
verse records, in place.

The review agent changes FORM only, never meaning (EDITORIAL.md scope). This
script enforces the hard guards mechanically:

  * exact OSIS coverage — no invented, omitted or renumbered verse;
  * records must be DRAFT (REVIEW/APPROVED are never rewritten);
  * a verse carrying a MATERIAL objection keeps its texto_bv unchanged;
  * a verse without mudancas keeps its texto_bv unchanged;
  * each applied change is logged in `decisoes` (diretriz_ref ER-0019);
  * MATERIAL objections go to `objecoes_nao_resolvidas` (block APPROVED);
  * `fontes` re-pinned for the cycle (ER-0010): prompts/regras/lexico/modelo
    as read this cycle; manifest re-hashed; texto_fonte preserved (the pinned
    original was not re-read).

All chapters are validated BEFORE any record is written. Usage:

  python3 scripts/persist_review.py <review-out/chapter.json> [...] [--modelo NOME]

Review-out files are written by the workflow agents themselves
(qa/reports/review-out/<book_dir>-<cap>.json); there is no dependency on the
workflow journal (robust against F-0014 aggregation hangs). Zero third-party
deps.
"""
import argparse
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST_PATH = os.path.join(ROOT, "sources", "manifest.json")
LEXICON_PATH = os.path.join(ROOT, "lexicon", "lexicon.json")

PROMPTS_VERSAO = "1.2.0"   # review-chapter-driver + revisor-editorial-draft.md
REGRAS_VERSAO = "1.1.0"    # pipeline/rules/EDITORIAL.md et al.


def file_sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def lexicon_version():
    with open(LEXICON_PATH, encoding="utf-8") as f:
        return json.load(f).get("versao", "unknown")


def load_chapter_records(chapter_dir):
    """Return ({osis: (path, record)} all files, {osis: ...} DRAFT-only)."""
    records = {}
    for fn in sorted(os.listdir(chapter_dir)):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(chapter_dir, fn)
        with open(path, encoding="utf-8") as f:
            records[fn[:-5]] = (path, json.load(f))
    scope = {osis: pr for osis, pr in records.items()
             if pr[1].get("status") == "DRAFT"}
    return records, scope


def validate_chapter(out, records, scope):
    """Return list of error strings for one review-out chapter."""
    errors = []
    out_osis = [v.get("osis") for v in out.get("versos", [])]
    missing = sorted(set(scope) - set(out_osis))
    extra = sorted(set(out_osis) - set(records))
    if missing:
        errors.append("versos DRAFT ausentes da saída: %s"
                      % ",".join(missing[:8]))
    if extra:
        errors.append("versos inventados na saída: %s" % ",".join(extra[:8]))
    for osis in sorted(set(out_osis) & (set(records) - set(scope))):
        errors.append("%s: status %s não é DRAFT (recusado)"
                      % (osis, records[osis][1].get("status")))
    if len(out_osis) != len(set(out_osis)):
        errors.append("osis duplicado na saída")
    for v in out.get("versos", []):
        osis = v.get("osis")
        if osis not in scope:
            continue
        rec = scope[osis][1]
        current = rec.get("texto_bv", "")
        revised = v.get("texto_bv_revisto", "")
        mudancas = v.get("mudancas", []) or []
        objecoes = v.get("objecoes", []) or []
        if not isinstance(mudancas, list) or not isinstance(objecoes, list):
            errors.append("%s: mudancas/objecoes devem ser listas" % osis)
            continue
        material = [o for o in objecoes
                    if str(o.get("gravidade", "")).upper() == "MATERIAL"]
        for o in objecoes:
            if str(o.get("gravidade", "")).upper() not in ("MATERIAL",
                                                           "EDITORIAL"):
                errors.append("%s: gravidade inválida %r"
                              % (osis, o.get("gravidade")))
        if material and revised != current:
            errors.append("%s: objeção MATERIAL exige texto inalterado" % osis)
        if material and mudancas:
            errors.append("%s: objeção MATERIAL contradiz mudancas" % osis)
        if not mudancas and revised != current:
            errors.append("%s: texto mudou sem mudancas registradas" % osis)
        for m in mudancas:
            if not all(k in m for k in ("tipo", "antes", "depois", "motivo")):
                errors.append("%s: mudanca sem campos obrigatórios" % osis)
    return errors


def repin_fontes(rec, modelo):
    fontes = dict(rec.get("fontes", {}))
    fontes["prompts_versao"] = PROMPTS_VERSAO
    fontes["regras_versao"] = REGRAS_VERSAO
    fontes["lexico_versao"] = lexicon_version()
    fontes["modelo"] = modelo
    fontes["manifest_sha256"] = file_sha256(MANIFEST_PATH)
    rec["fontes"] = fontes


def apply_chapter(out, records, modelo):
    """Mutate + rewrite changed records. Return (revised, objections)."""
    revised = objections = 0
    for v in out.get("versos", []):
        osis = v["osis"]
        path, rec = records[osis]
        mudancas = v.get("mudancas", []) or []
        objecoes = v.get("objecoes", []) or []
        if not mudancas and not objecoes:
            continue
        if mudancas:
            rec["texto_bv"] = v["texto_bv_revisto"]
            escolha = " | ".join(
                "%s → %s" % (m.get("antes", ""), m.get("depois", ""))
                for m in mudancas)
            motivo = " | ".join(str(m.get("motivo", "")) for m in mudancas)
            rec.setdefault("decisoes", []).append({
                "questao": "Revisão editorial do texto_bv",
                "escolha": escolha,
                "justificativa": motivo + " — revisão de forma sem alteração "
                                 "de sentido (ER-0019).",
                "alternativas_rejeitadas": [],
                "diretriz_ref": "ER-0019",
            })
            revised += 1
        for o in objecoes:
            grav = str(o.get("gravidade", "")).upper()
            problema = str(o.get("problema", ""))
            evid = str(o.get("evidencia", ""))
            if grav == "MATERIAL":
                rec.setdefault("objecoes_nao_resolvidas", []).append(
                    "Objeção MATERIAL (revisão ER-0019): %s — evidência: %s"
                    % (problema, evid))
                objections += 1
            else:  # EDITORIAL: registrada, não bloqueia
                rec.setdefault("decisoes", []).append({
                    "questao": "Objeção editorial não aplicada",
                    "escolha": "texto mantido",
                    "justificativa": problema + " — evidência: " + evid
                                     + " (ER-0019).",
                    "alternativas_rejeitadas": [],
                    "diretriz_ref": "ER-0019",
                })
        repin_fontes(rec, modelo)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)
            f.write("\n")
    return revised, objections


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("out_files", nargs="+")
    ap.add_argument("-modelo", default=os.environ.get("BV_MODEL",
                                                       "claude-sonnet-5"))
    args = ap.parse_args(argv)

    outs = []
    for path in args.out_files:
        with open(path, encoding="utf-8") as f:
            out = json.load(f)
        book_dir = out["book_dir"]
        chap_dir = os.path.join(ROOT, "translation", book_dir,
                                "%03d" % int(out["chapter"]))
        records, scope = load_chapter_records(chap_dir)
        errors = validate_chapter(out, records, scope)
        if errors:
            print("ERROS em %s:" % path)
            for e in errors:
                print("  - " + e)
            sys.exit(1)
        outs.append((path, out, scope))

    total_revised = total_objections = 0
    for path, out, scope in outs:
        revised, objections = apply_chapter(out, scope, args.modelo)
        total_revised += revised
        total_objections += objections
        print("%s: %d versos revisados, %d objeções MATERIAIS"
              % (os.path.basename(path), revised, objections))
    print("total: %d versos revisados, %d objeções MATERIAIS"
          % (total_revised, total_objections))
    return 0


if __name__ == "__main__":
    sys.exit(main())
