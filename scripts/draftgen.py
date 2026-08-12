"""Shared helpers for main-loop DRAFT chapter translation (ADR-0002/ER-0017).

Import in a chapter build script:
    import sys; sys.path.insert(0, 'scripts')
    from draftgen import verse, decision, anos, dump_chapter

`verse(...)` tolerates a numeric 4th arg as confidence (a common slip);
`decision(...)` tolerates bare-string alternatives. Zero third-party deps.
"""
import json


def anos(x):
    """Portuguese cardinal for a year count 1..999 (EDITORIAL §7)."""
    U = ["", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove",
         "dez", "onze", "doze", "treze", "catorze", "quinze", "dezesseis", "dezessete",
         "dezoito", "dezenove"]
    DZ = ["", "", "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta", "oitenta", "noventa"]
    C = ["", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos",
         "seiscentos", "setecentos", "oitocentos", "novecentos"]

    def ext(n):
        if n < 20:
            return U[n]
        if n < 100:
            d, u = divmod(n, 10)
            return DZ[d] + (" e " + U[u] if u else "")
        if n == 100:
            return "cem"
        c, rr = divmod(n, 100)
        return C[c] + (" e " + ext(rr) if rr else "")

    return ext(x) + " anos"


def decision(questao, escolha, justificativa, alternativas):
    ar = []
    for a in alternativas:
        if isinstance(a, (list, tuple)) and len(a) == 2:
            ar.append({"opcao": a[0], "motivo": a[1]})
        else:
            ar.append({"opcao": str(a), "motivo": ""})
    return {"questao": questao, "escolha": escolha, "justificativa": justificativa,
            "alternativas_rejeitadas": ar}


def variant(descricao, leituras, avaliacao, impacto):
    """Build a schema-valid variantes_textuais entry.

    leituras: list of (leitura, testemunhas) 2-tuples.
    """
    ls = [{"leitura": a, "testemunhas": b} for (a, b) in leituras]
    return {"descricao": descricao, "leituras": ls,
            "avaliacao": avaliacao, "impacto_na_traducao": impacto}


def verse(book, n, bv, lit, just="", conf=0.75, dec=None, sup=None, amb=None, var=None):
    if isinstance(just, (int, float)):  # tolerate verse(...,bv,lit,conf)
        just, conf = "", just
    return {
        "osis": "%s.%d" % (book, n), "versiculo": n,
        "texto_bv": bv, "traducao_literal": lit,
        "decisoes": dec or [], "palavras_supridas": sup or [],
        "ambiguidades_preservadas": amb or [], "variantes_textuais": var or [],
        "justificativa": just or "Tradução DRAFT do capítulo (ADR-0002).",
        "confianca": conf,
    }


def dump_chapter(path, book_osis, chapter, versos):
    payload = {"type": "result", "result": {"book": book_osis, "chapter": chapter, "versos": versos}}
    open(path, "w").write(json.dumps(payload, ensure_ascii=False) + "\n")
    return len(versos)
