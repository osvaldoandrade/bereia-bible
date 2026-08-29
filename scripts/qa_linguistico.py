#!/usr/bin/env python3
"""Static linguistic hot-spot triage over DRAFT verse records (ER-0019).

Scans translation/*/*/*.json records with status DRAFT and flags verses whose
texto_bv shows mechanical signs of EDITORIAL.md violations or translationese:

  ARC-1  dead archaisms (EDITORIAL §1.2)                       weight 3
  LEN-1  sentence > 40 words (EDITORIAL §1.3)                  weight 3
  VOS-1  "vós" verb paradigm (EDITORIAL §3/D-0003)             weight 3
  RAT-1  texto_bv diverges in length from traducao_literal     weight 2
  RED-1  repeated content bigram inside one verse (redundancy)  weight 2
  CAL-1  paratactic calques "e aconteceu que"                   weight 2
  CAL-2  deictic calque "eis que"                               weight 1
  PRO-1  third-person pronoun overload (>= 4 in one verse)      weight 1
  PAS-1  passive overload (>= 2 ser+participle in one verse)    weight 1

The detector only FLAGS; adjudication (fix vs. keep as intentional formula)
belongs to the editorial review agent (review-chapter-driver, ER-0019).

Outputs:
  qa/reports/hotspots.json                  machine-readable chapter rollup
  qa/reports/hotspots.md                    human-readable summary
  qa/reports/review-input/<book>-<cap>.json compact digest per hot chapter

Digest schema v2 (with --refs): each verse entry carries an additional
`referencias` field with parallel PT-BR texts from NTLH, ARA, NVIPT so the
review agent can compare the BV against a naturalness baseline.

Usage:
  python3 scripts/qa_linguistico.py [-records translation/] [-threshold 8]
      [-out qa/reports/hotspots.json] [-md qa/reports/hotspots.md]
      [-digest-dir qa/reports/review-input]
      [-refs sources/pt-bolls]

Zero third-party deps.
"""
import argparse
import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- marker definitions -----------------------------------------------------

# Simple (synthetic) pluperfect of high-frequency biblical verbs — literary
# tense that reads archaic in contemporary pt-BR ("fizera", "nascera").
# Ambiguous forms with other live readings are excluded (e.g. "fora").
MAISQUE_SINTETICO = (
    "fizera|dissera|nascera|viera|partira|dera|pusera|soubera|tivera|"
    "quisera|ouvira|saíra|subira|descera|tornara|voltara|chegara|entrara|"
    "falara|mandara|enviara|ordenara|edificara|plantara|gerara|chamara|"
    "morrera|falecera|vivera|reinara|começara|acabara|guardara|quebrara|"
    "achara|deixara|levara|trouxera|bebera|comera|dormira|abrira|fechara|"
    "ofertara|sacrificara|adorara|louvara|tomara|untara|vira"
)
ARC_RE = re.compile(
    r"\b(mui|porventura|deveras|outrossim|destarte|vosso|vossa|vossos|vossas"
    r"|tornou-se em|tornaram-se em|torna-se em|" + MAISQUE_SINTETICO + r")\b",
    re.IGNORECASE,
)
ACONTECEU_RE = re.compile(r"\be?\s*aconteceu que\b", re.IGNORECASE)
EIS_RE = re.compile(r"\beis que\b", re.IGNORECASE)
# "vós" paradigm (EDITORIAL §3/D-0003 requires você/vocês in human<->human
# and God->human discourse). Unambiguous 2pl forms only:
#   - future/conditional/imperfect endings (areis/ereis/ireis/aríeis/...);
#   - -ai imperatives with >= 2 preceding letters (excludes "sai", "cai",
#     "pai"); the bare -ei ending is AMBIGUOUS with 1sg preterite/future
#     ("pensei", "farei"), so those imperatives are an explicit list.
VOS_RE = re.compile(
    r"\b(\w{2,}(?:areis|ereis|ireis|aríeis|eríeis|iríeis|áveis|íeis)"
    r"|\w{2,}ai"
    r"|dai|fazei|trazei|sabei|dizei"
    r"|ponde|tende|vede|vinde|sede|ide"
    r"|sois|estais|tendes|vedes|pondes|dizeis"
    r"|vós)\b")
PASSIVE_RE = re.compile(
    r"\b(?:foi|foram|era|eram|é|são|será|serão|está|estão|estava|estavam|"
    r"tinha|tinham|seja|sejam|fosse|fossem)\s+\w+(?:ado|ada|ados|adas|"
    r"ido|ida|idos|idas)\b")
PRONOUNS = {"ele", "ela", "eles", "elas", "lhe", "lhes", "seu", "sua",
            "seus", "suas", "dele", "dela", "deles", "delas", "consigo"}

MARKER_WEIGHT = {"ARC-1": 3, "LEN-1": 3, "VOS-1": 3, "RAT-1": 2, "RED-1": 2,
                 "CAL-1": 2, "CAL-2": 1, "PRO-1": 1, "PAS-1": 1}

MAX_SENTENCE_WORDS = 40          # EDITORIAL §1.3
PRONOUN_LIMIT = 4                # PRO-1 fires at >= 4
PASSIVE_LIMIT = 2                # PAS-1 fires at >= 2
RATIO_HIGH, RATIO_LOW = 1.6, 0.65
CONTENT_MIN_LEN = 4              # content-token length for RED-1
# function words that break content runs for RED-1 (otherwise "a sua obra que
# fizera" x2 never collapses into a repeated unit)
RED_STOPWORDS = {"que", "não", "mas", "com", "por", "para", "como", "quando",
                 "seu", "sua", "seus", "suas", "dele", "dela", "deste",
                 "desta", "aquele", "aquela", "todo", "toda", "todos",
                 "todas", "outro", "outra", "cada", "muito", "muita"}

# sentence break: [.!?…] (+ closing quote) followed by space + uppercase/quote
SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?…])["”’»]?\s+(?=["“«A-ZÀ-Þ0-9])')
TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def sentence_lengths(text):
    return [len(TOKEN_RE.findall(s))
            for s in SENTENCE_SPLIT_RE.split(text) if s.strip()]


def content_tokens(text):
    return [strip_accents(t.lower()) for t in TOKEN_RE.findall(text)
            if len(t) >= CONTENT_MIN_LEN
            and strip_accents(t.lower()) not in RED_STOPWORDS]


def repeated_bigrams(text):
    """Return sorted set of content bigrams occurring >= 2 times in text."""
    toks = content_tokens(text)
    counts = {}
    for i in range(len(toks) - 1):
        bi = " ".join(toks[i:i + 2])
        counts[bi] = counts.get(bi, 0) + 1
    return sorted(bi for bi, n in counts.items() if n >= 2)


def verse_findings(rec):
    """Return list of {id, peso, detalhe} for one record's texto_bv."""
    text = rec.get("texto_bv", "")
    literal = rec.get("traducao_literal", "")
    findings = []

    hits = sorted({m.group(0).lower() for m in ARC_RE.finditer(text)})
    if hits:
        findings.append({"id": "ARC-1", "peso": MARKER_WEIGHT["ARC-1"],
                         "detalhe": ", ".join(hits)})

    long_sents = [n for n in sentence_lengths(text) if n > MAX_SENTENCE_WORDS]
    if long_sents:
        findings.append({"id": "LEN-1", "peso": MARKER_WEIGHT["LEN-1"],
                         "detalhe": "sentença de %d palavras" % max(long_sents)})

    vos_hits = sorted({m.group(0).lower() for m in VOS_RE.finditer(text)})
    if vos_hits:
        findings.append({"id": "VOS-1", "peso": MARKER_WEIGHT["VOS-1"],
                         "detalhe": ", ".join(vos_hits[:5])})

    if literal:
        n_bv, n_lit = len(text.split()), len(literal.split())
        if n_lit:
            ratio = n_bv / n_lit
            if ratio > RATIO_HIGH or ratio < RATIO_LOW:
                findings.append({
                    "id": "RAT-1", "peso": MARKER_WEIGHT["RAT-1"],
                    "detalhe": "ratio %.2f (%d/%d palavras vs literal)"
                               % (ratio, n_bv, n_lit)})

    bis = repeated_bigrams(text)
    if bis:
        findings.append({"id": "RED-1", "peso": MARKER_WEIGHT["RED-1"],
                         "detalhe": "; ".join(bis[:3])})

    n_ac = len(ACONTECEU_RE.findall(text))
    if n_ac:
        findings.append({"id": "CAL-1", "peso": MARKER_WEIGHT["CAL-1"],
                         "detalhe": "%d× 'aconteceu que'" % n_ac})
    n_eis = len(EIS_RE.findall(text))
    if n_eis:
        findings.append({"id": "CAL-2", "peso": MARKER_WEIGHT["CAL-2"],
                         "detalhe": "%d× 'eis que'" % n_eis})

    low = strip_accents(text.lower())
    n_pron = len([t for t in TOKEN_RE.findall(low) if t in PRONOUNS])
    if n_pron >= PRONOUN_LIMIT:
        findings.append({"id": "PRO-1", "peso": MARKER_WEIGHT["PRO-1"],
                         "detalhe": "%d pronomes de 3ª pessoa" % n_pron})

    n_pas = len(PASSIVE_RE.findall(text))
    if n_pas >= PASSIVE_LIMIT:
        findings.append({"id": "PAS-1", "peso": MARKER_WEIGHT["PAS-1"],
                         "detalhe": "%d construções passivas" % n_pas})

    return findings


def chapter_key(path):
    """Return (book_dir, chapter_int) from .../translation/<book>/<cap>/<f>."""
    cap_dir = os.path.basename(os.path.dirname(path))
    book_dir = os.path.basename(os.path.dirname(os.path.dirname(path)))
    return book_dir, int(cap_dir)


def scan(records_dir, threshold):
    """Scan records; return (chapters, totals) where chapters maps
    (book_dir, chapter) -> row dict; totals has corpus-wide marker counts."""
    chapters = {}
    totals = {"versos": 0, "versos_com_achados": 0,
              "por_marcador": {m: 0 for m in MARKER_WEIGHT}}
    for dirpath, _dirnames, filenames in os.walk(records_dir):
        for fn in sorted(filenames):
            if not fn.endswith(".json"):
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, encoding="utf-8") as f:
                    rec = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue
            if rec.get("status") != "DRAFT":
                continue
            totals["versos"] += 1
            text = rec.get("texto_bv", "")
            literal = rec.get("traducao_literal", "")
            findings = verse_findings(rec)
            book_dir, chap = chapter_key(path)
            row = chapters.setdefault(
                (book_dir, chap),
                {"livro": rec.get("referencia", {}).get("livro", book_dir),
                 "versos": 0, "versos_com_achados": 0, "score": 0,
                 "todos": []})
            row["versos"] += 1
            if findings:
                totals["versos_com_achados"] += 1
                row["versos_com_achados"] += 1
                row["score"] += sum(fi["peso"] for fi in findings)
                for fi in findings:
                    totals["por_marcador"][fi["id"]] += 1
            # the digest carries EVERY DRAFT verse of the chapter so the
            # review agent's output can satisfy ER-0019's exact OSIS coverage
            row["todos"].append({
                "osis": rec.get("referencia", {}).get("osis", fn[:-5]),
                "texto_bv": text,
                "traducao_literal": literal,
                "achados": findings})
    for row in chapters.values():
        row["todos"].sort(key=lambda v: int(v["osis"].split(".")[2]))
        row["hot"] = row["score"] >= threshold
    return chapters, totals


def load_references(refs_dir):
    """Load NTLH/ARA/NVIPT reference texts from refs_dir.

    Returns dict {version: {osis_book: {chapter: {verse: text}}}} or None if
    refs_dir is None/empty. Missing files are skipped silently (the digest
    will have an empty "referencias" for verses without a match).
    """
    if not refs_dir:
        return None
    refs = {}
    for version in ("NTLH", "ARA", "NVIPT"):
        path = os.path.join(refs_dir, f"{version}.json")
        if not os.path.isfile(path):
            print(f"aviso: referência não encontrada: {path}", file=sys.stderr)
            continue
        with open(path, encoding="utf-8") as f:
            refs[version] = json.load(f)
    return refs or None


def _lookup_refs(refs, osis_book, chapter, verse):
    """Return {version: text} for one verse. Empty dict if no match."""
    if not refs:
        return {}
    out = {}
    for version, data in refs.items():
        try:
            text = data[osis_book][chapter][verse]
            if text:
                out[version] = text
        except (KeyError, TypeError):
            pass
    return out


def write_reports(out_path, md_path, digest_dir, chapters, totals, threshold,
                  refs=None):
    hot = sorted(((k, r) for k, r in chapters.items() if r["hot"]),
                 key=lambda kr: (-kr[1]["score"], kr[0]))
    com_achados = [r for r in chapters.values() if r["versos_com_achados"]]
    report = {
        "data": __import__("datetime").date.today().isoformat(),
        "threshold": threshold,
        "capitulos_total": len(chapters),
        "capitulos_com_achados": len(com_achados),
        "capitulos_hot": len(hot),
        "totais": totals,
        "capitulos": [
            {"livro_dir": k[0], "capitulo": k[1], "livro": r["livro"],
             "versos": r["versos"],
             "versos_com_achados": r["versos_com_achados"],
             "score": r["score"]}
            for k, r in sorted(chapters.items(),
                               key=lambda kr: (-kr[1]["score"], kr[0]))],
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
        f.write("\n")

    if digest_dir:
        os.makedirs(digest_dir, exist_ok=True)
        for (book_dir, chap), r in hot:
            versos = r["todos"]
            if refs:
                # Derive the OSIS book abbreviation from the first verse's
                # osis (e.g. "Gen.1.14" -> "Gen").
                versos = []
                for v in r["todos"]:
                    osis = v["osis"]
                    osis_book = osis.split(".")[0] if "." in osis else ""
                    entry = dict(v)
                    entry["referencias"] = _lookup_refs(refs, osis_book,
                                                        str(chap),
                                                        osis.split(".")[-1])
                    versos.append(entry)
            digest = {"livro_dir": book_dir, "capitulo": chap,
                      "livro": r["livro"], "score": r["score"],
                      "versos": versos}
            name = "%s-%03d.json" % (book_dir, chap)
            with open(os.path.join(digest_dir, name), "w",
                      encoding="utf-8") as f:
                json.dump(digest, f, ensure_ascii=False, indent=1)
                f.write("\n")

    if md_path:
        lines = [
            "# Hot-spots linguísticos — triagem estática (ER-0019)",
            "",
            "- Threshold: score ≥ %d por capítulo" % threshold,
            "- Versos DRAFT varridos: %d; com achados: %d (%.1f%%)" % (
                totals["versos"], totals["versos_com_achados"],
                100 * totals["versos_com_achados"] / max(totals["versos"], 1)),
            "- Capítulos varridos: %d; com achados: %d; hot: %d" % (
                len(chapters), len(com_achados), len(hot)),
            "",
            "## Achados por marcador (versos)",
            "",
        ]
        for m in sorted(MARKER_WEIGHT, key=lambda x: -totals["por_marcador"][x]):
            lines.append("- %s (peso %d): %d versos" % (
                m, MARKER_WEIGHT[m], totals["por_marcador"][m]))
        lines += ["", "## Top 50 capítulos hot", "",
                  "| Capítulo | Livro | Versos c/ achado | Score |", "|---|---|---|---|"]
        for (book_dir, chap), r in hot[:50]:
            lines.append("| %s/%03d | %s | %d/%d | %d |" % (
                book_dir, chap, r["livro"], r["versos_com_achados"],
                r["versos"], r["score"]))
        lines += ["", "## Distribuição de scores (capítulos com achados)", ""]
        dist = {}
        for r in com_achados:
            bucket = (r["score"] // 5) * 5
            dist[bucket] = dist.get(bucket, 0) + 1
        for bucket in sorted(dist):
            lines.append("- score %d–%d: %d capítulos" % (
                bucket, bucket + 4, dist[bucket]))
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    return hot


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-records", default=os.path.join(ROOT, "translation"))
    ap.add_argument("-threshold", type=int, default=8)
    ap.add_argument("-out", default=os.path.join(ROOT, "qa", "reports",
                                                  "hotspots.json"))
    ap.add_argument("-md", default=os.path.join(ROOT, "qa", "reports",
                                                 "hotspots.md"))
    ap.add_argument("-digest-dir", default=os.path.join(
        ROOT, "qa", "reports", "review-input"))
    ap.add_argument("-refs", default=None, metavar="REFS_DIR",
                    help="directory with NTLH/ARA/NVIPT.json (e.g. "
                         "sources/pt-bolls). Enables digest schema v2 "
                         "(parallel PT-BR references per verse).")
    args = ap.parse_args(argv)
    refs = load_references(args.refs)
    if refs:
        print("referências PT-BR carregadas: %s" % ", ".join(sorted(refs)))
    chapters, totals = scan(args.records, args.threshold)
    hot = write_reports(args.out, args.md, args.digest_dir, chapters,
                        totals, args.threshold, refs=refs)
    print("versos DRAFT varridos: %d (com achados: %d)" % (
        totals["versos"], totals["versos_com_achados"]))
    print("capítulos com achados: %d; hot (score >= %d): %d" % (
        sum(1 for r in chapters.values() if r["versos_com_achados"]),
        args.threshold, len(hot)))
    for (book_dir, chap), r in hot[:10]:
        print("  hot: %s/%03d %s score=%d" % (book_dir, chap, r["livro"],
                                               r["score"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
