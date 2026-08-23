#!/usr/bin/env python3
"""Ship one editorial-review batch end-to-end (ER-0019):

  1. load review-out files; repair the known agent wart — incidental
     straight-quote swaps on verses WITHOUT mudancas (EDITORIAL mandates
     curly double quotes; the swap is reverted, never "logged");
  2. validate ALL chapters with persist_review guards BEFORE writing any;
  3. per chapter: apply changes, bvcheck, Conventional Commit (one commit
     per chapter: translation/<book>/<cap> + the review-out audit file);
  4. single push to origin/main at the end.

Any malformed review-out file or non-quote diff without mudancas aborts
the whole batch BEFORE any write (manual inspection required).

Usage:
  python3 scripts/ship_review_batch.py qa/reports/review-out/<files>... \
      -modelo qwen3.7-max [-no-push]

Zero third-party deps.
"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_script(name):
    path = os.path.join(ROOT, "scripts", name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


persist = load_script("persist_review")


def canon_quotes(s):
    return (s.replace("“", '"').replace("”", '"')
             .replace("‘", "'").replace("’", "'"))


def chapter_dir(out):
    return os.path.join(ROOT, "translation", out["book_dir"],
                        "%03d" % int(out["chapter"]))


def repair_quote_swaps(out):
    """Revert quote-style-only diffs on no-mudanca verses. Return
    (fixed_osis, bad_osis): bad = non-quote diff needing manual review."""
    fixed, bad = [], []
    for v in out["versos"]:
        if v.get("mudancas"):
            continue
        rec_path = os.path.join(chapter_dir(out), v["osis"] + ".json")
        with open(rec_path, encoding="utf-8") as f:
            cur = json.load(f)["texto_bv"]
        rev = v["texto_bv_revisto"]
        if rev == cur:
            continue
        if canon_quotes(cur) == canon_quotes(rev):
            v["texto_bv_revisto"] = cur
            fixed.append(v["osis"])
        else:
            bad.append(v["osis"])
    return fixed, bad


def osis_book_code(chap_dir):
    for fn in sorted(os.listdir(chap_dir)):
        if fn.endswith(".json"):
            with open(os.path.join(chap_dir, fn), encoding="utf-8") as f:
                return json.load(f)["referencia"]["osis"].split(".")[0]
    return None


def run(cmd, **kw):
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, **kw)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("out_files", nargs="+")
    ap.add_argument("-modelo", default=os.environ.get("BV_MODEL",
                                                       "claude-sonnet-5"))
    ap.add_argument("-no-push", action="store_true")
    args = ap.parse_args(argv)

    book_names = load_script("persist_chapter_draft").BOOK_NAME

    # 1) load + repair
    for path in args.out_files:
        try:
            with open(path, encoding="utf-8") as f:
                out = json.load(f)
        except json.JSONDecodeError as e:
            print("MALFORMED (manual): %s — %s" % (path, e))
            return 1
        fixed, bad = repair_quote_swaps(out)
        if bad:
            print("NON-QUOTE diff without mudancas (manual): %s — %s"
                  % (path, ",".join(bad)))
            return 1
        if fixed:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=1)
                f.write("\n")
            print("%s: reverted incidental quote-swap on %d verse(s)"
                  % (os.path.basename(path), len(fixed)))

    # 2) validate ALL before writing any
    outs = []
    for path in args.out_files:
        with open(path, encoding="utf-8") as f:
            out = json.load(f)
        records, scope = persist.load_chapter_records(chapter_dir(out))
        errors = persist.validate_chapter(out, records, scope)
        if errors:
            print("ERROS em %s:" % path)
            for e in errors:
                print("  - " + e)
            return 1
        outs.append((path, out, scope))

    # 3) apply + bvcheck + commit per chapter
    total_revised = total_obj = 0
    for path, out, scope in outs:
        revised, objections = persist.apply_chapter(out, scope, args.modelo)
        total_revised += revised
        total_obj += objections
        book_dir, chap = out["book_dir"], int(out["chapter"])
        rel_chap = "translation/%s/%03d" % (book_dir, chap)
        bv = run([os.path.join("bin", "bvcheck"), "-records", rel_chap,
                  "-lexicon", os.path.join("lexicon", "lexicon.json")])
        if bv.returncode != 0:
            print("BVCHECK FAIL %s:\n%s%s"
                  % (rel_chap, bv.stdout, bv.stderr))
            return 1
        run(["git", "add", rel_chap, os.path.relpath(path, ROOT)])
        if run(["git", "diff", "--cached", "--quiet"]).returncode == 0:
            print("%s/%03d: no changes, no commit" % (book_dir, chap))
            continue
        code = osis_book_code(chapter_dir(out))
        name = book_names.get(code, code or book_dir)
        msg = "fix(translation): editorial review of %s %d hot-spots (ER-0019)" % (
            name, chap)
        commit = run(["git", "commit", "-q", "-m", msg])
        if commit.returncode != 0:
            print("COMMIT FAIL %s:\n%s%s"
                  % (rel_chap, commit.stdout, commit.stderr))
            return 1
        print("%s/%03d: %d revisados, %d objecoes — committed (%s)"
              % (book_dir, chap, revised, objections, name))

    # 4) single push
    if not args.no_push:
        push = run(["git", "push", "-q", "origin", "main"])
        if push.returncode != 0:
            print("PUSH FAIL:\n%s%s" % (push.stdout, push.stderr))
            return 1
        print("pushed to origin/main")
    print("batch total: %d versos revisados, %d objeções MATERIAIS"
          % (total_revised, total_obj))
    return 0


if __name__ == "__main__":
    sys.exit(main())
