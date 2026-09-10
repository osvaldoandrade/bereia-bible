#!/usr/bin/env python3
"""Valida um arquivo review-out contra o digest de entrada (ER-0031/ER-0032).

Uso: python3 scripts/validate_review_out.py DIGEST.json OUT.json

Checagens (todas obrigatórias):
  1. JSON válido nos dois arquivos; book_dir/chapter coerentes.
  2. Cobertura exata: um objeto por verso do digest, na mesma ordem de osis.
  3. Conteúdo por verso:
     - veredito REVISADO  => mudancas não vazias; cada 'antes' é substring
       ÚNICA da entrada; texto_bv_revisto == entrada + mudancas (aplicadas
       uma vez cada, da mais longa para a mais curta).
     - qualquer outro veredito => texto_bv_revisto IDÊNTICO à entrada e
       mudancas vazias (previne a classe "revisado-fantasma": veredito/
       justificativa que alegam edição que o texto não materializa).
     - objeção MATERIAL => texto_bv_revisto IDÊNTICO à entrada.
     - gravidade de objeção ∈ {MATERIAL, EDITORIAL}.
     - mudancas com tipo ∈ {calque, regencia, concordancia, colocacao,
       coesao, pontuacao, extensao, naturalidade} e campos
       {tipo, antes, depois, motivo} presentes e não vazios.

Saída: linhas "FAIL ..." por problema; exit 0 se limpo, 1 caso contrário.
"""
import json
import sys

TIPOS = {
    "calque", "regencia", "concordancia", "colocacao",
    "coesao", "pontuacao", "extensao", "naturalidade",
}
GRAVIDADES = {"MATERIAL", "EDITORIAL"}


def apply_muds(entrada, muds):
    """Aplica mudancas longest-antes-first, uma ocorrência cada."""
    r = entrada
    for m in sorted(muds, key=lambda m: -len(m["antes"])):
        r = r.replace(m["antes"], m["depois"], 1)
    return r


def main():
    if len(sys.argv) != 3:
        print("uso: validate_review_out.py DIGEST.json OUT.json")
        return 2
    digest_path, out_path = sys.argv[1], sys.argv[2]
    fails = []

    try:
        digest = json.load(open(digest_path))
    except Exception as e:  # noqa: BLE001
        print(f"FAIL digest: JSON inválido: {e}")
        return 1
    try:
        out = json.load(open(out_path))
    except Exception as e:  # noqa: BLE001
        print(f"FAIL out: JSON inválido: {e}")
        return 1

    ent_list = [v["osis"] for v in digest["versos"]]
    ent = {v["osis"]: v["texto_bv"] for v in digest["versos"]}

    if out.get("book_dir") != digest.get("book_dir"):
        fails.append(f"FAIL book_dir: out={out.get('book_dir')!r} digest={digest.get('book_dir')!r}")
    if out.get("chapter") != digest.get("chapter"):
        fails.append(f"FAIL chapter: out={out.get('chapter')!r} digest={digest.get('chapter')!r}")

    out_list = [v.get("osis") for v in out.get("versos", [])]
    if out_list != ent_list:
        missing = [o for o in ent_list if o not in set(out_list)]
        extra = [o for o in out_list if o not in set(ent_list)]
        order = "ordem divergente" if not missing and not extra else ""
        fails.append(f"FAIL cobertura: {len(out_list)} versos vs {len(ent_list)} no digest; "
                     f"faltando={missing[:5]} extras={extra[:5]} {order}")

    for v in out.get("versos", []):
        osis = v.get("osis")
        if osis not in ent:
            continue  # já reportado na cobertura
        e = ent[osis]
        rev = v.get("texto_bv_revisto")
        muds = v.get("mudancas") or []
        veredito = v.get("veredito")

        for i, m in enumerate(muds):
            for campo in ("tipo", "antes", "depois", "motivo"):
                if not m.get(campo):
                    fails.append(f"FAIL {osis} mudancas[{i}]: campo {campo!r} ausente/vazio")
            if m.get("tipo") and m["tipo"] not in TIPOS:
                fails.append(f"FAIL {osis} mudancas[{i}]: tipo inválido {m['tipo']!r}")
            antes = m.get("antes", "")
            if antes:
                n = e.count(antes)
                if n == 0:
                    fails.append(f"FAIL {osis} mudancas[{i}]: 'antes' NÃO é substring da entrada (fantasma)")
                elif n > 1:
                    fails.append(f"FAIL {osis} mudancas[{i}]: 'antes' ocorre {n}× na entrada (deve ser única)")
                if antes == m.get("depois"):
                    fails.append(f"FAIL {osis} mudancas[{i}]: antes == depois (no-op)")

        if veredito == "REVISADO":
            if not muds:
                fails.append(f"FAIL {osis}: REVISADO sem mudancas")
            elif rev != apply_muds(e, muds):
                fails.append(f"FAIL {osis}: texto_bv_revisto != entrada + mudancas")
        else:
            if muds:
                fails.append(f"FAIL {osis}: veredito {veredito!r} com mudancas não vazias")
            if rev != e:
                fails.append(f"FAIL {osis}: veredito {veredito!r} mas texto_bv_revisto difere da entrada")

        for i, ob in enumerate(v.get("objecoes") or []):
            g = ob.get("gravidade")
            if g not in GRAVIDADES:
                fails.append(f"FAIL {osis} objecoes[{i}]: gravidade inválida {g!r}")
            if g == "MATERIAL" and rev != e:
                fails.append(f"FAIL {osis}: objeção MATERIAL com texto alterado")
            for campo in ("problema", "evidencia"):
                if not ob.get(campo):
                    fails.append(f"FAIL {osis} objecoes[{i}]: campo {campo!r} ausente/vazio")

    if fails:
        for f in fails:
            print(f)
        print(f"FAIL total: {len(fails)}")
        return 1
    print("OK: JSON válido, cobertura exata, conteúdo consistente")
    return 0


if __name__ == "__main__":
    sys.exit(main())
