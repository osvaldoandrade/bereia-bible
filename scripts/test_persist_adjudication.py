import importlib.util
import json
import os
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


adj = load_script("persist_adjudication")


def make_record(osis, texto, objecoes=("Objeção MATERIAL (ER-0019): x",),
                status="DRAFT"):
    return {
        "schema_version": "1.1.0",
        "referencia": {"osis": osis},
        "texto_bv": texto,
        "traducao_literal": texto,
        "termos_originais": [],
        "decisoes": [],
        "objecoes_nao_resolvidas": list(objecoes),
        "status": status,
        "fontes": {"texto_fonte": "oshb@3d15126f", "manifest_sha256": "x",
                   "prompts_versao": "1.2.3", "regras_versao": "1.2.0",
                   "lexico_versao": "0.6.1", "modelo": "claude-sonnet-5"},
    }


def packet(osis, texto):
    return {"book_dir": "99-tt", "chapter": 1,
            "versos": [{"osis": osis, "texto_bv": texto, "objecoes": ["x"]}]}


def out_verse(osis, veredito, final, mudancas=(), evidencia="", fund=""):
    return {"osis": osis, "veredito": veredito, "texto_bv_final": final,
            "mudancas": list(mudancas), "evidencia_original": evidencia,
            "fundamentacao": fund, "controles_divergem": False,
            "nota_textual": ""}


class PersistAdjudicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.chap_dir = os.path.join(self.tmp.name, "translation", "99-tt",
                                     "001")
        os.makedirs(self.chap_dir)

    def write(self, osis, rec):
        path = os.path.join(self.chap_dir, osis + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False)
        return path

    def records(self, osis, rec):
        return {osis: (self.write(osis, rec), rec)}

    # ---- coverage -----------------------------------------------------
    def test_coverage_mismatch_is_refused(self):
        osis = "Tst.1.1"
        recs = self.records(osis, make_record(osis, "a"))
        out = {"versos": [out_verse("Tst.1.2", "IMPROCEDE", "a", fund="f")]}
        errs = adj.validate_chapter(out, packet(osis, "a"), recs)
        self.assertTrue(any("cobertura divergente" in e for e in errs))

    # ---- IMPROCEDE / INCONCLUSIVA freeze the text ---------------------
    def test_improcede_must_not_change_text(self):
        osis = "Tst.1.1"
        recs = self.records(osis, make_record(osis, "a"))
        out = {"versos": [out_verse(osis, "IMPROCEDE", "b", fund="f")]}
        errs = adj.validate_chapter(out, packet(osis, "a"), recs)
        self.assertTrue(any("exige texto inalterado" in e for e in errs))

    def test_improcede_requires_fundamentacao(self):
        osis = "Tst.1.1"
        recs = self.records(osis, make_record(osis, "a"))
        out = {"versos": [out_verse(osis, "IMPROCEDE", "a")]}
        errs = adj.validate_chapter(out, packet(osis, "a"), recs)
        self.assertTrue(any("exige fundamentacao" in e for e in errs))

    def test_inconclusiva_keeps_objection_open(self):
        osis = "Tst.1.1"
        rec = make_record(osis, "a")
        recs = self.records(osis, rec)
        out = {"book_dir": "99-tt", "chapter": 1,
               "versos": [out_verse(osis, "INCONCLUSIVA", "a", fund="dúvida")]}
        self.assertEqual([], adj.validate_chapter(out, packet(osis, "a"), recs))
        p, i, n = adj.apply_chapter(out, recs, "claude-fable-5")
        self.assertEqual((0, 0, 1), (p, i, n))
        with open(recs[osis][0], encoding="utf-8") as f:
            saved = json.load(f)
        self.assertTrue(saved["objecoes_nao_resolvidas"])

    # ---- PROCEDE ------------------------------------------------------
    def test_procede_requires_evidencia_original(self):
        osis = "Tst.1.1"
        recs = self.records(osis, make_record(osis, "o justo"))
        out = {"versos": [out_verse(
            osis, "PROCEDE", "o reto",
            mudancas=[{"antes": "justo", "depois": "reto", "motivo": "m"}])]}
        errs = adj.validate_chapter(out, packet(osis, "o justo"), recs)
        self.assertTrue(any("evidencia_original" in e for e in errs))

    def test_procede_rejects_unlogged_edit(self):
        osis = "Tst.1.1"
        recs = self.records(osis, make_record(osis, "o justo vive"))
        out = {"versos": [out_verse(
            osis, "PROCEDE", "o reto anda",
            mudancas=[{"antes": "justo", "depois": "reto", "motivo": "m"}],
            evidencia="H6662")]}
        errs = adj.validate_chapter(out, packet(osis, "o justo vive"), recs)
        self.assertTrue(any("não reconstrói" in e for e in errs))

    def test_procede_applies_and_closes_objection(self):
        osis = "Tst.1.1"
        rec = make_record(osis, "o justo vive")
        recs = self.records(osis, rec)
        out = {"book_dir": "99-tt", "chapter": 1, "versos": [out_verse(
            osis, "PROCEDE", "o reto vive",
            mudancas=[{"antes": "justo", "depois": "reto", "motivo": "m"}],
            evidencia="H6662 tsaddiq")]}
        self.assertEqual([], adj.validate_chapter(
            out, packet(osis, "o justo vive"), recs))
        p, i, n = adj.apply_chapter(out, recs, "claude-fable-5")
        self.assertEqual((1, 0, 0), (p, i, n))
        with open(recs[osis][0], encoding="utf-8") as f:
            saved = json.load(f)
        self.assertEqual("o reto vive", saved["texto_bv"])
        self.assertNotIn("objecoes_nao_resolvidas", saved)
        self.assertEqual("ER-0020", saved["decisoes"][-1]["diretriz_ref"])
        self.assertEqual("claude-fable-5", saved["fontes"]["modelo"])

    def test_supplied_word_must_appear_in_final_text(self):
        osis = "Tst.1.1"
        recs = self.records(osis, make_record(osis, "seiscentos de ouro"))
        v = out_verse(
            osis, "PROCEDE", "seiscentos siclos de ouro",
            mudancas=[{"antes": "seiscentos de", "depois":
                       "seiscentos siclos de", "motivo": "elipse"}],
            evidencia="H8255 sheqel elíptico")
        v["palavras_supridas"] = ["dracmas"]
        errs = adj.validate_chapter(
            {"versos": [v]}, packet(osis, "seiscentos de ouro"), recs)
        self.assertTrue(any("não aparece no texto final" in e for e in errs))

    def test_supplied_word_is_recorded(self):
        osis = "Tst.1.1"
        recs = self.records(osis, make_record(osis, "seiscentos de ouro"))
        v = out_verse(
            osis, "PROCEDE", "seiscentos siclos de ouro",
            mudancas=[{"antes": "seiscentos de", "depois":
                       "seiscentos siclos de", "motivo": "elipse"}],
            evidencia="H8255 sheqel elíptico")
        v["palavras_supridas"] = ["siclos"]
        out = {"book_dir": "99-tt", "chapter": 1, "versos": [v]}
        self.assertEqual([], adj.validate_chapter(
            out, packet(osis, "seiscentos de ouro"), recs))
        adj.apply_chapter(out, recs, "claude-fable-5")
        with open(recs[osis][0], encoding="utf-8") as f:
            saved = json.load(f)
        self.assertIn("siclos", saved["palavras_supridas"])

    # ---- reconciliação de palavras_supridas ---------------------------
    def test_orphaned_supplied_entry_is_refused(self):
        osis = "Tst.1.1"
        rec = make_record(osis, "seiscentas unidades de ouro")
        rec["palavras_supridas"] = ["unidades"]
        recs = self.records(osis, rec)
        v = out_verse(
            osis, "PROCEDE", "seiscentos siclos de ouro",
            mudancas=[{"antes": "seiscentas unidades", "depois":
                       "seiscentos siclos", "motivo": "elipse de sheqel"}],
            evidencia="H8255")
        errs = adj.validate_chapter(
            {"versos": [v]}, packet(osis, "seiscentas unidades de ouro"), recs)
        self.assertTrue(any("ficou órfã" in e for e in errs))

    def test_orphaned_entry_can_be_declared_removed(self):
        osis = "Tst.1.1"
        rec = make_record(osis, "seiscentas unidades de ouro")
        rec["palavras_supridas"] = ["unidades"]
        recs = self.records(osis, rec)
        v = out_verse(
            osis, "PROCEDE", "seiscentos siclos de ouro",
            mudancas=[{"antes": "seiscentas unidades", "depois":
                       "seiscentos siclos", "motivo": "elipse de sheqel"}],
            evidencia="H8255")
        v["palavras_supridas"] = ["siclos"]
        v["palavras_supridas_removidas"] = ["unidades"]
        out = {"book_dir": "99-tt", "chapter": 1, "versos": [v]}
        self.assertEqual([], adj.validate_chapter(
            out, packet(osis, "seiscentas unidades de ouro"), recs))
        adj.apply_chapter(out, recs, "claude-fable-5")
        with open(recs[osis][0], encoding="utf-8") as f:
            saved = json.load(f)
        self.assertEqual(["siclos"], saved["palavras_supridas"])

    def test_annotated_entry_head_is_matched(self):
        # convenção do projeto: "<palavra> — <justificativa>"
        self.assertEqual("o", adj.supplied_head("o — artigo definido em 'No'"))
        self.assertEqual("de", adj.supplied_head("de (2×)"))
        self.assertEqual("está", adj.supplied_head("'está' (cópula)"))
        self.assertEqual("mulher", adj.supplied_head(
            "\u201cmulher\u201d, núcleo nominal suprido da forma feminina"))

    # ---- modo final ---------------------------------------------------
    def test_final_mode_refuses_inconclusiva(self):
        osis = "Tst.1.1"
        recs = self.records(osis, make_record(osis, "a"))
        out = {"versos": [out_verse(osis, "INCONCLUSIVA", "a", fund="dúvida")]}
        errs = adj.validate_chapter(out, packet(osis, "a"), recs, final=True)
        self.assertTrue(any("não aceita INCONCLUSIVA" in e for e in errs))
        # o mesmo veredito segue válido no modo normal
        self.assertEqual([], adj.validate_chapter(
            out, packet(osis, "a"), recs, final=False))

    def test_rejected_reading_is_preserved(self):
        osis = "Tst.1.1"
        recs = self.records(osis, make_record(osis, "nas gorduras"))
        v = out_verse(
            osis, "PROCEDE", "das gorduras",
            mudancas=[{"antes": "nas", "depois": "das", "motivo": "partitivo"}],
            evidencia="min- partitivo em H4924")
        v["leitura_rejeitada"] = "leitura privativa 'longe das gorduras'"
        out = {"book_dir": "99-tt", "chapter": 1, "versos": [v]}
        self.assertEqual([], adj.validate_chapter(
            out, packet(osis, "nas gorduras"), recs, final=True))
        adj.apply_chapter(out, recs, "claude-fable-5")
        with open(recs[osis][0], encoding="utf-8") as f:
            saved = json.load(f)
        self.assertTrue(any("privativa" in a for a in
                            saved["ambiguidades_preservadas"]))
        self.assertEqual(["leitura privativa 'longe das gorduras'"],
                         saved["decisoes"][-1]["alternativas_rejeitadas"])

    # ---- status / precondition guards ---------------------------------
    def test_non_draft_is_refused(self):
        osis = "Tst.1.1"
        recs = self.records(osis, make_record(osis, "a", status="APPROVED"))
        out = {"versos": [out_verse(osis, "IMPROCEDE", "a", fund="f")]}
        errs = adj.validate_chapter(out, packet(osis, "a"), recs)
        self.assertTrue(any("não é DRAFT" in e for e in errs))

    def test_verse_without_open_objection_is_refused(self):
        osis = "Tst.1.1"
        recs = self.records(osis, make_record(osis, "a", objecoes=()))
        out = {"versos": [out_verse(osis, "IMPROCEDE", "a", fund="f")]}
        errs = adj.validate_chapter(out, packet(osis, "a"), recs)
        self.assertTrue(any("não tem objeção aberta" in e for e in errs))

    def test_invalid_verdict_is_refused(self):
        osis = "Tst.1.1"
        recs = self.records(osis, make_record(osis, "a"))
        out = {"versos": [out_verse(osis, "TALVEZ", "a")]}
        errs = adj.validate_chapter(out, packet(osis, "a"), recs)
        self.assertTrue(any("veredito inválido" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
