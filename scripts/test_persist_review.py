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


persist = load_script("persist_review")


def make_record(osis, texto, status="DRAFT"):
    return {
        "schema_version": "1.1.0",
        "referencia": {"osis": osis},
        "texto_bv": texto,
        "traducao_literal": texto,
        "decisoes": [],
        "objecoes_nao_resolvidas": [],
        "status": status,
        "fontes": {"texto_fonte": "oshb@3d15126f", "manifest_sha256": "x",
                   "prompts_versao": "1.1.0", "regras_versao": "1.1.0",
                   "lexico_versao": "0.6.1", "modelo": "claude-sonnet-5"},
    }


class PersistReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name
        self.chap_dir = os.path.join(self.root, "translation", "99-tt", "001")
        os.makedirs(self.chap_dir)
        # patch module paths to the sandbox
        self._orig = (persist.ROOT, persist.MANIFEST_PATH,
                      persist.LEXICON_PATH)
        persist.ROOT = self.root
        persist.MANIFEST_PATH = os.path.join(self.root, "manifest.json")
        persist.LEXICON_PATH = os.path.join(self.root, "lexicon.json")
        with open(persist.MANIFEST_PATH, "w") as f:
            f.write("{}")
        with open(persist.LEXICON_PATH, "w") as f:
            json.dump({"versao": "9.9.9"}, f)

    def tearDown(self):
        persist.ROOT, persist.MANIFEST_PATH, persist.LEXICON_PATH = \
            self._orig

    def write_records(self, rows):
        for osis, texto, status in rows:
            with open(os.path.join(self.chap_dir, osis + ".json"), "w",
                      encoding="utf-8") as f:
                json.dump(make_record(osis, texto, status), f)

    def chapter_out(self, versos):
        return {"book_dir": "99-tt", "chapter": 1, "versos": versos}

    def records_and_scope(self):
        return persist.load_chapter_records(self.chap_dir)

    def test_revisao_aplicada_com_decisao_e_repin(self):
        self.write_records([("Tt.1.1", "texto antigo com arcaismo", "DRAFT"),
                            ("Tt.1.2", "verso limpo", "DRAFT")])
        out = self.chapter_out([
            {"osis": "Tt.1.1", "texto_bv_revisto": "texto novo",
             "mudancas": [{"tipo": "EDITORIAL", "antes": "arcaismo",
                           "depois": "novo", "motivo": "arcaísmo §1.2"}],
             "objecoes": [], "veredito": "REVISADO"},
            {"osis": "Tt.1.2", "texto_bv_revisto": "verso limpo",
             "mudancas": [], "objecoes": [],
             "veredito": "SEM_ALTERACAO"},
        ])
        records, scope = self.records_and_scope()
        self.assertEqual(persist.validate_chapter(out, records, scope), [])
        revised, objections = persist.apply_chapter(out, scope, "modelo-x")
        self.assertEqual((revised, objections), (1, 0))
        with open(os.path.join(self.chap_dir, "Tt.1.1.json")) as f:
            rec = json.load(f)
        self.assertEqual(rec["texto_bv"], "texto novo")
        self.assertEqual(rec["decisoes"][-1]["diretriz_ref"], "ER-0019")
        self.assertEqual(rec["fontes"]["prompts_versao"],
                         persist.PROMPTS_VERSAO)
        self.assertEqual(rec["fontes"]["lexico_versao"], "9.9.9")
        self.assertEqual(rec["fontes"]["modelo"], "modelo-x")
        # verso sem mudança não é reescrito
        with open(os.path.join(self.chap_dir, "Tt.1.2.json")) as f:
            self.assertEqual(json.load(f)["fontes"]["prompts_versao"],
                             "1.1.0")

    def test_verse_drafted_missing_rejected(self):
        self.write_records([("Tt.1.1", "a", "DRAFT"), ("Tt.1.2", "b",
                                                          "DRAFT")])
        out = self.chapter_out([
            {"osis": "Tt.1.1", "texto_bv_revisto": "a", "mudancas": [],
             "objecoes": [], "veredito": "SEM_ALTERACAO"},
        ])
        records, scope = self.records_and_scope()
        errors = persist.validate_chapter(out, records, scope)
        self.assertTrue(any("ausentes" in e for e in errors))

    def test_invented_verse_rejected(self):
        self.write_records([("Tt.1.1", "a", "DRAFT")])
        out = self.chapter_out([
            {"osis": "Tt.1.1", "texto_bv_revisto": "a", "mudancas": [],
             "objecoes": [], "veredito": "SEM_ALTERACAO"},
            {"osis": "Tt.1.99", "texto_bv_revisto": "x", "mudancas": [],
             "objecoes": [], "veredito": "SEM_ALTERACAO"},
        ])
        records, scope = self.records_and_scope()
        errors = persist.validate_chapter(out, records, scope)
        self.assertTrue(any("inventados" in e for e in errors))

    def test_material_objection_requires_unchanged_text(self):
        self.write_records([("Tt.1.1", "a", "DRAFT")])
        out = self.chapter_out([
            {"osis": "Tt.1.1", "texto_bv_revisto": "b",
             "mudancas": [{"tipo": "EDITORIAL", "antes": "a", "depois": "b",
                           "motivo": "m"}],
             "objecoes": [{"gravidade": "MATERIAL", "problema": "p",
                           "evidencia": "e"}],
             "veredito": "REVISADO"},
        ])
        records, scope = self.records_and_scope()
        errors = persist.validate_chapter(out, records, scope)
        self.assertTrue(any("MATERIAL" in e for e in errors))

    def test_text_changed_without_mudancas_rejected(self):
        self.write_records([("Tt.1.1", "a", "DRAFT")])
        out = self.chapter_out([
            {"osis": "Tt.1.1", "texto_bv_revisto": "b", "mudancas": [],
             "objecoes": [], "veredito": "SEM_ALTERACAO"},
        ])
        records, scope = self.records_and_scope()
        errors = persist.validate_chapter(out, records, scope)
        self.assertTrue(any("sem mudancas" in e for e in errors))

    def test_approved_record_out_of_scope(self):
        self.write_records([("Tt.1.1", "a", "APPROVED"),
                            ("Tt.1.2", "b", "DRAFT")])
        out = self.chapter_out([
            {"osis": "Tt.1.2", "texto_bv_revisto": "b", "mudancas": [],
             "objecoes": [], "veredito": "SEM_ALTERACAO"},
        ])
        records, scope = self.records_and_scope()
        self.assertEqual(persist.validate_chapter(out, records, scope), [])
        # saída que tenta tocar o APPROVED é recusada
        out_bad = self.chapter_out([
            {"osis": "Tt.1.1", "texto_bv_revisto": "a", "mudancas": [],
             "objecoes": [], "veredito": "SEM_ALTERACAO"},
            {"osis": "Tt.1.2", "texto_bv_revisto": "b", "mudancas": [],
             "objecoes": [], "veredito": "SEM_ALTERACAO"},
        ])
        errors = persist.validate_chapter(out_bad, records, scope)
        self.assertTrue(any("fora do escopo DRAFT" in e for e in errors))

    def test_material_objection_lands_in_objecoes_nao_resolvidas(self):
        self.write_records([("Tt.1.1", "a", "DRAFT")])
        out = self.chapter_out([
            {"osis": "Tt.1.1", "texto_bv_revisto": "a", "mudancas": [],
             "objecoes": [{"gravidade": "MATERIAL", "problema": "sentido",
                           "evidencia": "hebraico"}],
             "veredito": "SEM_ALTERACAO"},
        ])
        records, scope = self.records_and_scope()
        self.assertEqual(persist.validate_chapter(out, records, scope), [])
        revised, objections = persist.apply_chapter(out, scope, "m")
        self.assertEqual((revised, objections), (0, 1))
        with open(os.path.join(self.chap_dir, "Tt.1.1.json")) as f:
            rec = json.load(f)
        self.assertEqual(rec["texto_bv"], "a")
        self.assertEqual(len(rec["objecoes_nao_resolvidas"]), 1)
        self.assertIn("MATERIAL", rec["objecoes_nao_resolvidas"][0])


class StatusScopeTests(unittest.TestCase):
    """ER-0022 revisa o cânon APPROVED; o escopo tem de ser parâmetro."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.chap = os.path.join(self.tmp.name, "translation", "99-tt", "001")
        os.makedirs(self.chap)

    def _write(self, osis, status):
        path = os.path.join(self.chap, osis + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(make_record(osis, "texto", status=status), f,
                      ensure_ascii=False)
        return path

    def test_approved_scope_admits_approved_record(self):
        self._write("Tst.1.1", "APPROVED")
        records, scope = persist.load_chapter_records(self.chap, "APPROVED")
        self.assertIn("Tst.1.1", scope)
        out = {"versos": [{"osis": "Tst.1.1", "texto_bv_revisto": "texto",
                           "mudancas": [], "objecoes": [],
                           "veredito": "SEM_ALTERACAO"}]}
        self.assertEqual([], persist.validate_chapter(out, records, scope,
                                                      "APPROVED"))

    def test_draft_record_is_out_of_approved_scope(self):
        self._write("Tst.1.1", "DRAFT")
        records, scope = persist.load_chapter_records(self.chap, "APPROVED")
        self.assertEqual({}, scope)


if __name__ == "__main__":
    unittest.main()
