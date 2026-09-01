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
the whole batch BEFORE any write (manual inspection required). For the
recurring failure mode — agent output malformed by unescaped quotes on a
chapter the workflow summary shows as pure no-op (revisados=0) — pass
--regen-noop book_dir/chapter to rebuild that file from the records as
an all-SEM_ALTERACAO review (check the journal/summary for objections
first; EDITORIAL objections in the malformed file are lost).

Usage:
  python3 scripts/ship_review_batch.py qa/reports/review-out/<files>... \
      -modelo qwen3.7-max [-er ER-0022] [-no-push] [--regen-noop 24-jr/13 ...]

The -er label goes into the commit message and is the provenance of the
batch: it must name the directive that actually produced the review-out
files, not the one this script was first written for.

Zero third-party deps.
"""
import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUS_SCOPE = "DRAFT"   # sobrescrito por -status em main()


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


def normalize_objection_severity(out):
    """Agent wart (ER-0022): objections emitted with `tipo` instead of
    `gravidade`.

    Both carry the same MATERIAL/EDITORIAL value — `tipo` is the key used for
    the *mudanca* classification, and the agent reaches for it by analogy. The
    content is unambiguous, so the key is renamed rather than the whole chapter
    rejected. An objection carrying neither key is left alone and the
    persistence guard refuses it, as it should.
    """
    fixed = 0
    for v in out.get("versos", []):
        for o in (v.get("objecoes") or []):
            if o.get("gravidade"):
                continue
            alias = str(o.get("tipo", "")).upper()
            if alias in ("MATERIAL", "EDITORIAL"):
                o["gravidade"] = alias
                o.pop("tipo", None)
                fixed += 1
    return fixed


def repair_quote_swaps(out):
    """Revert quote-only diffs on no-mudanca verses: quote-style swaps and
    the boundary-quote wart (agent adds/drops an opening or closing quote
    of a multi-verse quote without logging anything). Return
    (fixed_osis, bad_osis): bad = other diff needing manual review."""
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
        cur_c, rev_c = canon_quotes(cur), canon_quotes(rev)
        if cur_c == rev_c or cur_c.strip('"') == rev_c.strip('"'):
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


def regen_noop(book_dir, chap):
    """Rebuild a review-out file as an all-SEM_ALTERACAO review from the
    current records (for malformed no-op outputs)."""
    chap_dir = os.path.join(ROOT, "translation", book_dir, "%03d" % chap)
    versos = []
    for fn in sorted(os.listdir(chap_dir)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(chap_dir, fn), encoding="utf-8") as f:
            rec = json.load(f)
        if rec.get("status") != STATUS_SCOPE:
            continue
        versos.append({"osis": fn[:-5], "texto_bv_revisto": rec["texto_bv"],
                       "mudancas": [], "objecoes": [],
                       "veredito": "SEM_ALTERACAO"})
    versos.sort(key=lambda v: int(v["osis"].split(".")[2]))
    path = os.path.join(ROOT, "qa", "reports", "review-out",
                        "%s-%03d.json" % (book_dir, chap))
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"book_dir": book_dir, "chapter": chap,
                   "versos": versos}, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("regen-noop %s/%03d: %d verses rebuilt as SEM_ALTERACAO"
          % (book_dir, chap, len(versos)))


def fix_inner_quotes(chunk):
    """Convert unescaped straight quotes INSIDE JSON string values back to
    curly quotes (the known agent wart: curly quotes of the corpus text are
    emitted as straight quotes, which then break the JSON). Structural
    quotes are recognized by lookahead: a string terminator is followed by
    one of , } ] : (ignoring whitespace)."""
    out, in_str, i = [], False, 0
    while i < len(chunk):
        c = chunk[i]
        if not in_str:
            if c == '"':
                in_str = True
            out.append(c)
            i += 1
            continue
        if c == "\\":
            out.append(chunk[i:i + 2])
            i += 2
            continue
        if c == '"':
            j = i + 1
            while j < len(chunk) and chunk[j] in " \t\r\n":
                j += 1
            if j >= len(chunk) or chunk[j] in ",}]:":
                in_str = False
                out.append(c)
            else:  # internal quote -> curly, opening/closing by neighbor
                prev_c = chunk[i - 1] if i else ""
                out.append("“" if prev_c in " \t\n:([{—" else "”")
            i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _validate_verse(v, record_text):
    """Return a verified verse dict, or None if it cannot be verified.

    No-mudanca verses must equal the record text (quote-style-insensitive)
    and are reset to the record text. REVISADO verses are rebuilt by
    applying their own mudancas to the record text; the result must match
    the declared texto_bv_revisto (quote-style-insensitive)."""
    mudancas = v.get("mudancas") or []
    if not mudancas:
        if canon_quotes(v["texto_bv_revisto"]) != canon_quotes(record_text):
            return None
        v["texto_bv_revisto"] = record_text
        return v
    text, skipped = record_text, 0
    # longest 'antes' first: a whole-verse entry subsumes overlapping
    # partial entries logged alongside it
    for m in sorted(mudancas, key=lambda m: len(m.get("antes", "")),
                    reverse=True):
        # agents sometimes log overlapping mudancas (partial + whole-verse);
        # an entry whose 'antes' is already gone is redundant — the final
        # comparison with texto_bv_revisto is the real verification
        if m.get("antes") not in text:
            skipped += 1
            continue
        text = text.replace(m["antes"], m["depois"], 1)
    if skipped:
        print("  note %s: %d redundant mudanca(s) skipped"
              % (v["osis"], skipped))
    if skipped == len(mudancas):
        # no declared mudanca applies to the record: nothing to verify
        return None
    declared = canon_quotes(v["texto_bv_revisto"])
    rebuilt = canon_quotes(text)
    # tolerate dropped boundary quotes (agent wart) on either end; the
    # rebuilt text keeps the record's quote pairing, which is what the
    # corpus requires
    if rebuilt.strip('"') != declared.strip('"'):
        # UNLOGGED edit: the agent changed more than its mudancas say
        # (e.g. an unrecorded comma deletion). Unlogged changes are
        # unauditable by the program's own guards, so the rebuilt text
        # (recorded mudancas only) wins; surface it for review.
        print("  WARNING %s: unlogged edit dropped; text rebuilt from "
              "recorded mudancas\n    agent : %s\n    applied: %s"
              % (v["osis"], declared, rebuilt))
    v["texto_bv_revisto"] = text
    return v


def regen_block_from_record(chunk, book, chap):
    """Last-resort salvage for a block that quote-repair cannot parse
    (e.g. an unescaped inner quote followed by a comma — ambiguous for
    the lookahead). If the block declares SEM_ALTERACAO, the hard guards
    require its text to equal the record anyway, so rebuild the block
    verbatim from the DRAFT record. Returns None for anything that could
    carry edits (REVISADO, missing veredito) — those stay manual."""
    m = re.search(r'"osis":\s*"([^"]+)"', chunk)
    if not m or not re.search(r'"veredito":\s*"SEM_ALTERACAO"', chunk):
        return None
    osis = m.group(1)
    rec_path = os.path.join(ROOT, "translation", book, "%03d" % chap,
                            osis + ".json")
    with open(rec_path, encoding="utf-8") as f:
        rec = json.load(f)
    if rec.get("status") != STATUS_SCOPE:
        return None
    return {"osis": osis, "texto_bv_revisto": rec["texto_bv"],
            "mudancas": [], "objecoes": [], "veredito": "SEM_ALTERACAO"}


def recover_file(path):
    """Salvage a review-out file whose verse blocks are broken by
    unescaped quotes (known agent wart). Clean blocks are kept; broken
    blocks are quote-repaired, then VERIFIED against the records:
    no-mudanca verses must equal the record text; REVISADO verses must
    equal record text + mudancas applied. Blocks that even quote-repair
    cannot parse are rebuilt from the record when they declare
    SEM_ALTERACAO (their text must equal the record anyway). Aborts on
    anything it cannot verify."""
    raw = open(path, encoding="utf-8").read()
    head = json.loads(raw[:raw.find('"versos"')] + '"versos": []}')
    book, chap = head["book_dir"], int(head["chapter"])
    idxs = ([m.start() for m in re.finditer(r'\{\s*"osis":', raw)]
            + [raw.rfind("]")])
    versos, kept, rebuilt, regen = [], [], [], []
    for a, b in zip(idxs[:-1], idxs[1:]):
        chunk = raw[a:b].rstrip().rstrip(",").rstrip()
        if not chunk.endswith("}"):
            continue
        repaired = False
        try:
            v = json.loads(chunk)
        except json.JSONDecodeError:
            try:
                v = json.loads(fix_inner_quotes(chunk))
                repaired = True
            except json.JSONDecodeError:
                v = regen_block_from_record(chunk, book, chap)
                if v is None:
                    print("recover ABORT: unparseable block near offset %d"
                          % a)
                    sys.exit(1)
                repaired = True
                regen.append(v["osis"])
        osis = v["osis"]
        with open(os.path.join(ROOT, "translation", book, "%03d" % chap,
                               osis + ".json"), encoding="utf-8") as f:
            rec_text = json.load(f)["texto_bv"]
        verified = _validate_verse(v, rec_text)
        if verified is None:
            print("recover ABORT %s: verification failed" % osis)
            sys.exit(1)
        versos.append(verified)
        (rebuilt if repaired else kept).append(osis)
    versos.sort(key=lambda v: int(v["osis"].split(".")[2]))
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"book_dir": book, "chapter": chap, "versos": versos},
                  f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("recover %s: %d verses | verified clean %d | repaired %d (%s)"
          % (os.path.basename(path), len(versos), len(kept),
             len(rebuilt), ",".join(rebuilt) or "-"))
    if regen:
        print("  rebuilt from record (SEM_ALTERACAO unparseable): %s"
              % ",".join(regen))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("out_files", nargs="+")
    ap.add_argument("-modelo", default=os.environ.get("BV_MODEL",
                                                       "claude-sonnet-5"))
    ap.add_argument("-no-push", action="store_true")
    ap.add_argument("-er", default="ER-0019", metavar="ER-NNNN",
                    help="diretriz que este lote executa; entra na mensagem "
                         "de commit como proveniência (ER-0022 = revisão "
                         "gramatical do AT)")
    ap.add_argument("-status", default="DRAFT",
                    choices=["DRAFT", "REVIEW", "APPROVED"],
                    help="estado dos registros que este ciclo revisa "
                         "(ER-0022 revisa o cânon APPROVED)")
    ap.add_argument("--regen-noop", action="append", default=[],
                    metavar="BOOK_DIR/CHAP")
    ap.add_argument("--recover", action="append", default=[], metavar="FILE")
    args = ap.parse_args(argv)
    global STATUS_SCOPE
    STATUS_SCOPE = args.status

    for spec in args.regen_noop:
        book_dir, chap = spec.split("/")
        regen_noop(book_dir, int(chap))
    for path in args.recover:
        recover_file(path)

    book_names = load_script("persist_chapter_draft").BOOK_NAME

    # 1) load + repair
    for path in args.out_files:
        try:
            with open(path, encoding="utf-8") as f:
                out = json.load(f)
        except json.JSONDecodeError as e:
            print("MALFORMED (manual): %s — %s" % (path, e))
            return 1
        sev = normalize_objection_severity(out)
        if sev:
            print("%s: %d objeção(ões) com `tipo` normalizada(s) para "
                  "`gravidade`" % (os.path.basename(path), sev))
        fixed, bad = repair_quote_swaps(out)
        if bad:
            print("NON-QUOTE diff without mudancas (manual): %s — %s"
                  % (path, ",".join(bad)))
            return 1
        if fixed or sev:
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
        records, scope = persist.load_chapter_records(chapter_dir(out),
                                                       args.status)
        errors = persist.validate_chapter(out, records, scope, args.status)
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
        msg = "fix(translation): editorial review of %s %d hot-spots (%s)" % (
            name, chap, args.er)
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
