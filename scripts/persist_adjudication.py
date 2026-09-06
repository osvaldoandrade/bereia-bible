#!/usr/bin/env python3
"""Persist adjudication output (adjudicate-objections-driver, ER-0020) into
DRAFT verse records, in place.

This is the ONLY path in the pipeline allowed to change meaning, and only for
a verse that already carries an open MATERIAL objection. It is deliberately
separate from persist_review.py, whose guard (`objeção MATERIAL exige texto
inalterado`) stays untouched — see docs/adr/ADR-0005.

Guards enforced mechanically, all chapters validated BEFORE any write:

  * exact coverage — one output verse per packet verse, no invention;
  * records must be at the expected pre-adjudication status (`-status`,
    default DRAFT), and must still carry an open objection;
  * PROCEDE is the only verdict that may change texto_bv, and the new text
    must be reconstructible from `mudancas` (antes -> depois applied to the
    stored text must yield texto_bv_final) — an unlogged edit is refused,
    never silently accepted;
  * PROCEDE additionally requires `evidencia_original` (the Hebrew/Greek term
    that carries the decision) — no meaning change without original-language
    evidence;
  * words the adjudicator had to supply (Hebrew ellipsis, e.g. the elided
    `sheqel` in weight formulas) are appended to `palavras_supridas`, so a
    supplied word never sits in texto_bv unaudited;
  * PROCEDE must also RECONCILE the entries already in `palavras_supridas`:
    rewriting the text can delete or reinflect a word declared by an earlier
    cycle, leaving the record claiming a suprimento that is no longer there.
    Entries whose head no longer occurs in the new text must be dropped or
    replaced via `palavras_supridas_removidas`, never left dangling;
  * IMPROCEDE / INCONCLUSIVA must leave texto_bv byte-identical;
  * PROCEDE and IMPROCEDE close the objection; INCONCLUSIVA keeps it open;
  * `-final` (maintainer's call, 2026-08-30) refuses INCONCLUSIVA outright:
    every objection must come back decided. A rejected-but-defensible reading
    declared in `leitura_rejeitada` is appended to `ambiguidades_preservadas`
    verbatim AND split (`split_rejeitada`) into the schema's
    `{opcao, motivo}` for `decisoes[].alternativas_rejeitadas` — the original
    ER-0020 code stored it as a bare string there (schema wants an object),
    the root cause of F-0023 (DECISOES.md); forcing a decision narrows the
    text without erasing the crux from the record, and without corrupting
    the schema either;
  * every outcome is logged in `decisoes` with diretriz_ref set to `-er`
    (default ER-0020);
  * `fontes` re-pinned for the cycle (ER-0010).

Usage:
  python3 scripts/persist_adjudication.py <adjudication-out/chapter.json> ... \
      [-modelo claude-fable-5] [-status DRAFT] [-er ER-0020]

`-status` is the precondition gate (default DRAFT, matching ER-0020's
original cycle); pass the record's actual pre-adjudication status when
adjudicating an already-APPROVED canon (e.g. `-status APPROVED` for
ER-0023, which reopens objections left by ER-0022 after ER-0021 promoted
the whole canon). `-er` is the provenance tag stamped into diretriz_ref,
questao, justificativa and the leitura_rejeitada marker (default ER-0020);
pass the adjudicating cycle's own ER number for any cycle after the first.

Zero third-party deps.
"""
import argparse
import importlib.util
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS_VERSAO = "1.4.0"   # + adjudicador-objecoes.md v2.0.0 (ER-0020, modo final)
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


def supplied_head(entry):
    """Head word of a `palavras_supridas` entry.

    The project's convention is `<palavra> — <justificativa>` (also `(nota)`
    and `"palavra", <justificativa>`), not a bare token, so validation must
    look at the head only.
    """
    head = entry
    for sep in (" — ", " (", ", "):
        head = head.split(sep)[0]
    return head.strip().strip("'\u2018\u2019\u201c\u201d\"")


def apply_mudancas(text, mudancas):
    """Replay antes -> depois in order. Returns None if a step does not match."""
    for m in mudancas:
        antes = m.get("antes", "")
        depois = m.get("depois", "")
        if antes == "" or antes not in text:
            return None
        text = text.replace(antes, depois, 1)
    return text


def validate_chapter(out, packet, records, status="DRAFT", final=False):
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
        if rec.get("status") != status:
            errors.append("%s: status %s não é %s (recusado)"
                          % (osis, rec.get("status"), status))
            continue
        if not (rec.get("objecoes_nao_resolvidas") or []):
            errors.append("%s: registro não tem objeção aberta" % osis)
            continue

        verdict = str(v.get("veredito", "")).upper()
        if verdict not in VERDICTS:
            errors.append("%s: veredito inválido %r" % (osis, v.get("veredito")))
            continue
        if final and verdict == "INCONCLUSIVA":
            errors.append("%s: modo final não aceita INCONCLUSIVA — a objeção "
                          "tem de sair decidida" % osis)
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
        supridas = v.get("palavras_supridas") or []
        if not isinstance(supridas, list) or any(
                not isinstance(w, str) for w in supridas):
            errors.append("%s: palavras_supridas deve ser lista de strings"
                          % osis)
        else:
            for w in supridas:
                if supplied_head(w).lower() not in final.lower():
                    errors.append("%s: palavra suprida %r não aparece no "
                                  "texto final" % (osis, w))
        # Reconciliação: entrada declarada num ciclo anterior pode ter sido
        # apagada ou reflexionada pela correção. Deixá-la é afirmar um
        # suprimento que não está mais no texto.
        removidas = v.get("palavras_supridas_removidas") or []
        for e in (rec.get("palavras_supridas") or []):
            if supplied_head(e).lower() in final.lower():
                continue
            if e in removidas:
                continue
            errors.append("%s: entrada de palavras_supridas %r ficou órfã "
                          "após a correção — declare-a em "
                          "palavras_supridas_removidas ou substitua-a"
                          % (osis, supplied_head(e)))
        rebuilt = apply_mudancas(current, mudancas)
        if rebuilt is None:
            errors.append("%s: mudanca não casa com o texto armazenado" % osis)
        elif rebuilt != final:
            errors.append("%s: texto_bv_final não reconstrói a partir de "
                          "mudancas (edição não registrada)" % osis)
    return errors


def _close_objections(rec):
    rec.pop("objecoes_nao_resolvidas", None)


# `leitura_rejeitada` is one free-text paragraph (option + why it lost, per
# the adjudicador-objecoes.md instruction); the schema's
# `alternativas_rejeitadas` wants `{opcao, motivo}`. Split on the marker the
# agent's own prose almost always uses to pivot from describing the option
# to arguing why it lost — same convention as the F-0023 manual repairs
# (DECISOES.md) of the ER-0020-era records this exact gap first surfaced in.
# A `rejeitada` string with no marker degrades to opcao=texto
# integral/motivo=aviso explícito — never silently drops content, and the
# full paragraph is always ALSO preserved verbatim in
# `ambiguidades_preservadas`.
_REJEITADA_MARKERS = re.compile(
    "(" + "|".join([
        r"perde porque", r"perde pel[oa]s?", r"perdeu porque",
        r"foi preterid[oa]:?\s*porque", r"preterid[oa]:?\s*porque",
        r"foi preterid[oa]:", r"preterid[oa]:",
        r"descartad[oa]:?\s*porque", r"rejeitad[oa]:?\s*porque",
        r"considerad[oa] e (?:descartad[oa]|rejeitad[oa]):",
        r"considerad[oa] e (?:descartad[oa]|rejeitad[oa]) porque",
    ]) + ")", re.IGNORECASE)
_REJEITADA_FALLBACK = re.compile(r"\bporque\b", re.IGNORECASE)


def split_rejeitada(texto):
    """`leitura_rejeitada` free text -> {opcao, motivo}, content-preserving."""
    m = _REJEITADA_MARKERS.search(texto) or _REJEITADA_FALLBACK.search(texto)
    if m:
        return texto[:m.start()].strip(" .;—-"), texto[m.start():].strip()
    return texto, ("Leitura descartada — motivo não isolável automaticamente "
                   "do texto acima; ver o parágrafo completo em "
                   "ambiguidades_preservadas.")


def apply_chapter(out, records, modelo, er="ER-0020"):
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
        rejeitada = (v.get("leitura_rejeitada") or "").strip()
        sufixo = (" Nota textual: " + nota) if nota else ""
        if rejeitada:
            ambig = rec.setdefault("ambiguidades_preservadas", [])
            marcada = "Leitura descartada na adjudicação " + er + ": " + rejeitada
            if marcada not in ambig:
                ambig.append(marcada)

        if verdict == "PROCEDE":
            rec["texto_bv"] = v["texto_bv_final"]
            for e in (v.get("palavras_supridas_removidas") or []):
                atuais = rec.get("palavras_supridas") or []
                if e in atuais:
                    atuais.remove(e)
            for w in (v.get("palavras_supridas") or []):
                supridas = rec.setdefault("palavras_supridas", [])
                if w not in supridas:
                    supridas.append(w)
            escolha = " | ".join("%s → %s" % (m.get("antes", ""),
                                              m.get("depois", ""))
                                 for m in v["mudancas"])
            rec.setdefault("decisoes", []).append({
                "questao": "Adjudicação de objeção MATERIAL (%s)" % er,
                "escolha": escolha,
                "justificativa": "Objeção procedente. Evidência do original: "
                                 + evid + (" " + fund if fund else "")
                                 + " Objeções fechadas: "
                                 + " || ".join(abertas) + sufixo
                                 + " (%s, controles KJV/WEB)." % er,
                "alternativas_rejeitadas": ([{"opcao": o, "motivo": m}
                                            for o, m in
                                            [split_rejeitada(rejeitada)]]
                                           if rejeitada else []),
                "diretriz_ref": er,
            })
            _close_objections(rec)
            procede += 1
        elif verdict == "IMPROCEDE":
            rec.setdefault("decisoes", []).append({
                "questao": "Adjudicação de objeção MATERIAL (%s)" % er,
                "escolha": "texto mantido — objeção improcedente",
                "justificativa": fund + (" Evidência do original: " + evid
                                         if evid else "")
                                 + " Objeções fechadas: "
                                 + " || ".join(abertas) + sufixo
                                 + " (%s, controles KJV/WEB)." % er,
                "alternativas_rejeitadas": ([{"opcao": o, "motivo": m}
                                            for o, m in
                                            [split_rejeitada(rejeitada)]]
                                           if rejeitada else []),
                "diretriz_ref": er,
            })
            _close_objections(rec)
            improcede += 1
        else:  # INCONCLUSIVA — objeção segue bloqueando APPROVED
            rec.setdefault("decisoes", []).append({
                "questao": "Adjudicação de objeção MATERIAL (%s)" % er,
                "escolha": "inconclusiva — escalada ao mantenedor",
                "justificativa": (fund or "Evidência disponível não decide.")
                                 + (" Evidência do original: " + evid
                                    if evid else "") + sufixo
                                 + " Objeção mantida aberta (%s)." % er,
                "alternativas_rejeitadas": ([{"opcao": o, "motivo": m}
                                            for o, m in
                                            [split_rejeitada(rejeitada)]]
                                           if rejeitada else []),
                "diretriz_ref": er,
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
    ap.add_argument("-status", default="DRAFT",
                    help="status exigido dos registros antes da adjudicação "
                         "(default DRAFT; use APPROVED quando o cânone já "
                         "foi promovido antes do ciclo de adjudicação)")
    ap.add_argument("-er", default="ER-0020",
                    help="diretriz de proveniência gravada em decisoes[] "
                         "(default ER-0020)")
    ap.add_argument("-final", action="store_true",
                    help="recusa INCONCLUSIVA: toda objeção sai decidida")
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
        errors = validate_chapter(out, packet, records, status=args.status,
                                  final=args.final)
        if errors:
            print("ERROS em %s:" % path)
            for e in errors:
                print("  - " + e)
            sys.exit(1)
        staged.append((out, records))

    tp = ti = tn = 0
    for out, records in staged:
        p, i, n = apply_chapter(out, records, args.modelo, er=args.er)
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
