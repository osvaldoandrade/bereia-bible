#!/usr/bin/env python3
"""Persist adjudication output (adjudicate-objections-driver, ER-0020) into
DRAFT verse records, in place.

This is the ONLY path in the pipeline allowed to change meaning, and only for
a verse that already carries an open MATERIAL objection. It is deliberately
separate from persist_review.py, whose guard (`objeção MATERIAL exige texto
inalterado`) stays untouched — see docs/adr/ADR-0005.

Guards enforced mechanically, all chapters validated BEFORE any write:

  * exact coverage — one output verse per packet verse, no invention;
  * records must be DRAFT, and must still carry an open objection;
  * PROCEDE is the only verdict that may change texto_bv, and the new text
    must be reconstructible from `mudancas` (antes -> depois applied to the
    stored text must yield texto_bv_final) — an unlogged edit is refused,
    never silently accepted;
  * PROCEDE additionally requires `evidencia_original` (the Hebrew/Greek term
    that carries the decision) — no meaning change without original-language
    evidence;
  * IMPROCEDE / INCONCLUSIVA must leave texto_bv byte-identical;
  * PROCEDE and IMPROCEDE close the objection; INCONCLUSIVA keeps it open;
  * every outcome is logged in `decisoes` with diretriz_ref ER-0020;
  * `fontes` re-pinned for the cycle (ER-0010).

Usage:
  python3 scripts/persist_adjudication.py <adjudication-out/chapter.json> ... \
      [-modelo claude-fable-5]

Zero third-party deps.
"""
import argparse
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS_VERSAO = "1.3.0"   # + adjudicador-objecoes.md v1.0.0 (ER-0020)
VERDICTS = ("PROCEDE", "IMPROCEDE", "INCONCLUSIVA")


def _load_persist_review():
    path = os.path.join(ROOT, "scripts", "persist_review.py")
    spec = importlib.util.spec_from_file_location("persist_review", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


review = _load_persist_review()


def packet_path(book_dir, chapter):
    return os.path.join(ROOT, "qa", "reports", "adjudication-input",
                        "%s-%03d.json" % (book_dir, int(chapter)))


def apply_mudancas(text, mudancas):
    """Replay antes -> depois in order. Returns None if a step does not match."""
    for m in mudancas:
        antes = m.get("antes", "")
        depois = m.get("depois", "")
        if antes == "" or antes not in text:
            return None
        text = text.replace(antes, depois, 1)
    return text


def validate_chapter(out, packet, records):
    """Return list of error strings for one adjudication-out chapter."""
    errors = []
    want = [v["osis"] for v in packet["versos"]]
    got = [v.get("osis") for v in out.get("versos", [])]
    if got != want:
        errors.append("cobertura divergente do pacote: esperado %s, obtido %s"
                      % (",".join(want[:6]), ",".join(str(g) for g in got[:6])))
        return errors

    for v in out["versos"]:
        osis = v["osis"]
        if osis not in records:
            errors.append("%s: registro inexistente" % osis)
            continue
        rec = records[osis][1]
        if rec.get("status") != "DRAFT":
            errors.append("%s: status %s não é DRAFT (recusado)"
                          % (osis, rec.get("status")))
            continue
        if not (rec.get("objecoes_nao_resolvidas") or []):
            errors.append("%s: registro não tem objeção aberta" % osis)
            continue

        verdict = str(v.get("veredito", "")).upper()
        if verdict not in VERDICTS:
            errors.append("%s: veredito inválido %r" % (osis, v.get("veredito")))
            continue

        current = rec.get("texto_bv", "")
        final = v.get("texto_bv_final")
        if final is None:
            errors.append("%s: texto_bv_final ausente" % osis)
            continue
        mudancas = v.get("mudancas") or []
        if not isinstance(mudancas, list):
            errors.append("%s: mudancas deve ser lista" % osis)
            continue

        if verdict in ("IMPROCEDE", "INCONCLUSIVA"):
            if final != current:
                errors.append("%s: %s exige texto inalterado" % (osis, verdict))
            if mudancas:
                errors.append("%s: %s não pode registrar mudancas"
                              % (osis, verdict))
            if verdict == "IMPROCEDE" and not (v.get("fundamentacao") or "").strip():
                errors.append("%s: IMPROCEDE exige fundamentacao" % osis)
            continue

        # PROCEDE
        if final == current:
            errors.append("%s: PROCEDE sem alteração de texto" % osis)
            continue
        if not mudancas:
            errors.append("%s: PROCEDE exige mudancas registradas" % osis)
            continue
        for m in mudancas:
            if not all(k in m for k in ("antes", "depois", "motivo")):
                errors.append("%s: mudanca sem campos obrigatórios" % osis)
        if not (v.get("evidencia_original") or "").strip():
            errors.append("%s: PROCEDE exige evidencia_original (termo do "
                          "hebraico/grego)" % osis)
        rebuilt = apply_mudancas(current, mudancas)
        if rebuilt is None:
            errors.append("%s: mudanca não casa com o texto armazenado" % osis)
        elif rebuilt != final:
            errors.append("%s: texto_bv_final não reconstrói a partir de "
                          "mudancas (edição não registrada)" % osis)
    return errors


def _close_objections(rec):
    rec.pop("objecoes_nao_resolvidas", None)


def apply_chapter(out, records, modelo):
    """Mutate + rewrite records. Return (procede, improcede, inconclusiva)."""
    procede = improcede = inconclusiva = 0
    for v in out["versos"]:
        osis = v["osis"]
        path, rec = records[osis]
        verdict = str(v["veredito"]).upper()
        abertas = list(rec.get("objecoes_nao_resolvidas") or [])
        evid = (v.get("evidencia_original") or "").strip()
        fund = (v.get("fundamentacao") or "").strip()
        nota = (v.get("nota_textual") or "").strip()
        sufixo = (" Nota textual: " + nota) if nota else ""

        if verdict == "PROCEDE":
            rec["texto_bv"] = v["texto_bv_final"]
            escolha = " | ".join("%s → %s" % (m.get("antes", ""),
                                              m.get("depois", ""))
                                 for m in v["mudancas"])
            rec.setdefault("decisoes", []).append({
                "questao": "Adjudicação de objeção MATERIAL (ER-0020)",
                "escolha": escolha,
                "justificativa": "Objeção procedente. Evidência do original: "
                                 + evid + (" " + fund if fund else "")
                                 + " Objeções fechadas: "
                                 + " || ".join(abertas) + sufixo
                                 + " (ER-0020, controles KJV/WEB).",
                "alternativas_rejeitadas": [],
                "diretriz_ref": "ER-0020",
            })
            _close_objections(rec)
            procede += 1
        elif verdict == "IMPROCEDE":
            rec.setdefault("decisoes", []).append({
                "questao": "Adjudicação de objeção MATERIAL (ER-0020)",
                "escolha": "texto mantido — objeção improcedente",
                "justificativa": fund + (" Evidência do original: " + evid
                                         if evid else "")
                                 + " Objeções fechadas: "
                                 + " || ".join(abertas) + sufixo
                                 + " (ER-0020, controles KJV/WEB).",
                "alternativas_rejeitadas": [],
                "diretriz_ref": "ER-0020",
            })
            _close_objections(rec)
            improcede += 1
        else:  # INCONCLUSIVA — objeção segue bloqueando APPROVED
            rec.setdefault("decisoes", []).append({
                "questao": "Adjudicação de objeção MATERIAL (ER-0020)",
                "escolha": "inconclusiva — escalada ao mantenedor",
                "justificativa": (fund or "Evidência disponível não decide.")
                                 + (" Evidência do original: " + evid
                                    if evid else "") + sufixo
                                 + " Objeção mantida aberta (ER-0020).",
                "alternativas_rejeitadas": [],
                "diretriz_ref": "ER-0020",
            })
            inconclusiva += 1

        review.PROMPTS_VERSAO = PROMPTS_VERSAO
        review.repin_fontes(rec, modelo)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)
            f.write("\n")
    return procede, improcede, inconclusiva


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("out_files", nargs="+")
    ap.add_argument("-modelo", default=os.environ.get("BV_MODEL",
                                                      "claude-fable-5"))
    args = ap.parse_args(argv)

    staged = []
    for path in args.out_files:
        with open(path, encoding="utf-8") as f:
            out = json.load(f)
        with open(packet_path(out["book_dir"], out["chapter"]),
                  encoding="utf-8") as f:
            packet = json.load(f)
        chap_dir = os.path.join(ROOT, "translation", out["book_dir"],
                                "%03d" % int(out["chapter"]))
        records, _ = review.load_chapter_records(chap_dir)
        errors = validate_chapter(out, packet, records)
        if errors:
            print("ERROS em %s:" % path)
            for e in errors:
                print("  - " + e)
            sys.exit(1)
        staged.append((out, records))

    tp = ti = tn = 0
    for out, records in staged:
        p, i, n = apply_chapter(out, records, args.modelo)
        tp += p
        ti += i
        tn += n
        print("%s/%03d: %d procede, %d improcede, %d inconclusiva"
              % (out["book_dir"], int(out["chapter"]), p, i, n))
    print("total: %d procede, %d improcede, %d inconclusiva (abertas)"
          % (tp, ti, tn))
    return 0


if __name__ == "__main__":
    sys.exit(main())
