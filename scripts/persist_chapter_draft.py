#!/usr/bin/env python3
"""Persist chapter-level DRAFT output (draft-chapter-driver) into verse records.

The chapter driver's agent returns only judgment fields per verse; this merges
them with per-word morphology assembled MECHANICALLY from the pinned packet
(palavra=surface, lemma, morfologia from OSHB/Nestle 1904 — never re-typed by
an agent, F-0015),
producing full schema-valid DRAFT records (confianca capped at 0.80).

Usage:
  python3 scripts/persist_chapter_draft.py <journal.jsonl> <packet1.json> [packet2.json ...]

Records recovered from the workflow journal (F-0014). Zero third-party deps.
"""
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK_DIR = {"Gen": "01-gn", "Exod": "02-ex", "Lev": "03-lv", "Num": "04-nm", "Deut": "05-dt", "Josh": "06-js", "Judg": "07-jz", "Ruth": "08-rt", "1Sam": "09-1sm", "2Sam": "10-2sm", "1Kgs": "11-1rs", "2Kgs": "12-2rs", "1Chr": "13-1cr", "2Chr": "14-2cr", "Ezra": "15-ed", "Neh": "16-ne", "Esth": "17-et", "Job": "18-jo", "Ps": "19-sl", "Prov": "20-pv", "Eccl": "21-ec", "Song": "22-ct", "Isa": "23-is", "Jer": "24-jr", "Lam": "25-lm", "Ezek": "26-ez", "Dan": "27-dn", "Hos": "28-os", "Joel": "29-jl", "Amos": "30-am", "Obad": "31-ob", "Jonah": "32-jn", "Mic": "33-mq", "Nah": "34-na", "Hab": "35-hc", "Zeph": "36-sf", "Hag": "37-ag", "Zech": "38-zc", "Mal": "39-ml"}
BOOK_NAME = {"Gen": "Gênesis", "Exod": "Êxodo", "Lev": "Levítico", "Num": "Números", "Deut": "Deuteronômio", "Josh": "Josué", "Judg": "Juízes", "Ruth": "Rute", "1Sam": "1 Samuel", "2Sam": "2 Samuel", "1Kgs": "1 Reis", "2Kgs": "2 Reis", "1Chr": "1 Crônicas", "2Chr": "2 Crônicas", "Ezra": "Esdras", "Neh": "Neemias", "Esth": "Ester", "Job": "Jó", "Ps": "Salmos", "Prov": "Provérbios", "Eccl": "Eclesiastes", "Song": "Cântico dos Cânticos", "Isa": "Isaías", "Jer": "Jeremias", "Lam": "Lamentações", "Ezek": "Ezequiel", "Dan": "Daniel", "Hos": "Oseias", "Joel": "Joel", "Amos": "Amós", "Obad": "Obadias", "Jonah": "Jonas", "Mic": "Miqueias", "Nah": "Naum", "Hab": "Habacuque", "Zeph": "Sofonias", "Hag": "Ageu", "Zech": "Zacarias", "Mal": "Malaquias"}
BOOK_DIR.update({
    "Matt": "40-mt", "Mark": "41-mc", "Luke": "42-lc", "John": "43-jo",
    "Acts": "44-at", "Rom": "45-rm", "1Cor": "46-1co", "2Cor": "47-2co",
    "Gal": "48-gl", "Eph": "49-ef", "Phil": "50-fp", "Col": "51-cl",
    "1Thess": "52-1ts", "2Thess": "53-2ts", "1Tim": "54-1tm",
    "2Tim": "55-2tm", "Titus": "56-tt", "Phlm": "57-fm", "Heb": "58-hb",
    "Jas": "59-tg", "1Pet": "60-1pe", "2Pet": "61-2pe", "1John": "62-1jo",
    "2John": "63-2jo", "3John": "64-3jo", "Jude": "65-jd", "Rev": "66-ap",
})
BOOK_NAME.update({
    "Matt": "Mateus", "Mark": "Marcos", "Luke": "Lucas", "John": "João",
    "Acts": "Atos", "Rom": "Romanos", "1Cor": "1 Coríntios",
    "2Cor": "2 Coríntios", "Gal": "Gálatas", "Eph": "Efésios",
    "Phil": "Filipenses", "Col": "Colossenses", "1Thess": "1 Tessalonicenses",
    "2Thess": "2 Tessalonicenses", "1Tim": "1 Timóteo", "2Tim": "2 Timóteo",
    "Titus": "Tito", "Phlm": "Filemom", "Heb": "Hebreus", "Jas": "Tiago",
    "1Pet": "1 Pedro", "2Pet": "2 Pedro", "1John": "1 João",
    "2John": "2 João", "3John": "3 João", "Jude": "Judas", "Rev": "Apocalipse",
})
MANIFEST_PATH = os.path.join(ROOT, "sources", "manifest.json")


def file_sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


FONTES = {
    "manifest_sha256": file_sha256(MANIFEST_PATH),
    "prompts_versao": "1.1.0", "regras_versao": "1.1.0",
    "lexico_versao": "0.6.1",
    "modelo": os.environ.get("BV_MODEL", "claude-sonnet-5"),
}


def chapter_results(journal_path):
    """Return {(book,chapter): {osis: verse_judgment}} from journal, latest wins."""
    out = {}
    with open(journal_path) as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("type") != "result":
                continue
            r = d.get("result")
            if not isinstance(r, dict) or "versos" not in r or "chapter" not in r:
                continue
            key = (r.get("book", "Gen"), r["chapter"])
            bucket = out.setdefault(key, {})
            for v in r["versos"]:
                if v.get("osis"):
                    bucket[v["osis"]] = v
    return out


def packet_index(packet_paths):
    """Return {osis: (pericope, words, source_pin, source_variants)}."""
    idx = {}
    for p in packet_paths:
        with open(p, encoding="utf-8") as f:
            pk = json.load(f)
        peri = pk.get("unidade")
        source = pk.get("fonte", {})
        commit = source.get("git_commit", "")
        source_pin = "%s@%s" % (source.get("id", "unknown"), commit[:8])
        for v in pk["versos"]:
            words = [(w["surface"], w.get("lemma", ""), w.get("morph", ""))
                     for w in v["palavras"] if w["type"] == "word"]
            idx[v["osis"]] = (peri, words, source_pin,
                               v.get("variantes_fonte", []))
    return idx


def unadjudicated_source_variants(chapters, idx):
    judgments = {osis: judgment
                 for verses in chapters.values()
                 for osis, judgment in verses.items()}
    errors = []
    for osis, (_pericope, _words, _source_pin, variants) in idx.items():
        refs = [v.get("referencia_fonte", "") for v in variants]
        if not refs:
            continue
        rendered = json.dumps(
            judgments.get(osis, {}).get("variantes_textuais", []),
            ensure_ascii=False,
        )
        missing = [ref for ref in refs if ref and ref not in rendered]
        if missing:
            errors.append("%s(%s)" % (osis, ",".join(missing)))
    return errors


def build_record(osis, vj, pericope, words, source_pin="oshb@3d15126f"):
    book, chap, num = osis.split(".")
    termos = [{"palavra": s, "lemma": lem, "morfologia": mor} for (s, lem, mor) in words]
    conf = vj.get("confianca", 0.75)
    just = vj.get("justificativa", "")
    # Guard against a driver/helper slip that puts the confidence number into
    # justificativa (must be a string per schema); recover it as confidence.
    if isinstance(just, (int, float)) and not isinstance(conf, (int, float)):
        conf, just = just, ""
    conf = min(conf if isinstance(conf, (int, float)) else 0.75, 0.80)
    if not isinstance(just, str) or not just:
        just = "Tradução DRAFT do capítulo (ADR-0002)."
    # palavras_supridas must be an array of strings (schema); tolerate a richer
    # {palavra, motivo} object form by flattening it to "palavra — motivo".
    supridas = []
    for s in vj.get("palavras_supridas", []):
        if isinstance(s, dict):
            pal, mot = s.get("palavra", ""), s.get("motivo", "")
            supridas.append((pal + " — " + mot) if mot else pal)
        else:
            supridas.append(str(s))
    fontes = dict(FONTES)
    fontes["texto_fonte"] = source_pin
    return {
        "schema_version": "1.1.0",
        "referencia": {
            "osis": osis, "livro": BOOK_NAME.get(book, book),
            "capitulo": int(chap), "versiculo": int(num), "pericope": pericope,
        },
        "texto_bv": vj["texto_bv"],
        "traducao_literal": vj["traducao_literal"],
        "termos_originais": termos,
        "variantes_textuais": vj.get("variantes_textuais", []),
        "decisoes": vj.get("decisoes", []),
        "palavras_supridas": supridas,
        "ambiguidades_preservadas": vj.get("ambiguidades_preservadas", []),
        "justificativa": just,
        "confianca": round(conf, 2),
        "status": "DRAFT",
        "ciclos_consenso": 1,
        "objecoes_nao_resolvidas": [],
        "fontes": fontes,
    }


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    journal, packets = sys.argv[1], sys.argv[2:]
    chapters = chapter_results(journal)
    idx = packet_index(packets)
    unadjudicated = unadjudicated_source_variants(chapters, idx)
    if unadjudicated:
        print("VARIANTE-FONTE SEM ADJUDICAÇÃO:", ", ".join(unadjudicated))
        sys.exit(1)
    written, missing = 0, []
    for (book, chap), verses in sorted(chapters.items()):
        d = os.path.join(ROOT, "translation", BOOK_DIR.get(book, book), "%03d" % chap)
        os.makedirs(d, exist_ok=True)
        for osis, vj in sorted(verses.items(), key=lambda kv: int(kv[0].split(".")[2])):
            if osis not in idx:
                missing.append(osis)
                continue
            pericope, words, source_pin, _source_variants = idx[osis]
            if not words:
                missing.append(osis + "(no-words)")
                continue
            rec = build_record(osis, vj, pericope, words, source_pin)
            path = os.path.join(d, osis + ".json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rec, f, ensure_ascii=False, indent=2)
                f.write("\n")
            written += 1
    print("registros DRAFT persistidos: %d" % written)
    if missing:
        print("SEM packet/words (checar):", ", ".join(missing[:20]))


if __name__ == "__main__":
    main()
