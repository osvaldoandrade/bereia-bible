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


qa = load_script("qa_linguistico")


def ids(findings):
    return sorted(f["id"] for f in findings)


def rec(texto, literal=None, status="DRAFT", osis="Gen.2.2"):
    return {
        "status": status,
        "texto_bv": texto,
        "traducao_literal": literal if literal is not None else texto,
        "referencia": {"osis": osis, "livro": "Gênesis"},
    }


class MarkerTests(unittest.TestCase):
    def test_arcaismo_marcado(self):
        cases = [
            "e o mar tornou-se em seco",
            "e ele fizera toda a obra",
            "Rebeca, que nascera a Betuel",
            "o vosso Deus é grande",
            "mui santo é o seu nome",
        ]
        for t in cases:
            with self.subTest(t=t):
                self.assertIn("ARC-1", ids(qa.verse_findings(rec(t))))

    def test_texto_limpo_sem_marcadores(self):
        t = "Deus viu que era bom."
        self.assertEqual(qa.verse_findings(rec(t)), [])

    def test_sentenca_longa_marcada(self):
        longa = " ".join(["palavra%d" % i for i in range(41)]) + "."
        self.assertIn("LEN-1", ids(qa.verse_findings(rec(longa))))
        limite = " ".join(["palavra%d" % i for i in range(40)]) + "."
        self.assertNotIn("LEN-1", ids(qa.verse_findings(rec(limite))))

    def test_divergencia_de_extensao_marcada(self):
        literal = "palavra outra terceira"
        expandido = "palavra outra terceira e mais quatro palavras extras aqui"
        self.assertIn("RAT-1",
                      ids(qa.verse_findings(rec(expandido, literal))))
        reduzido = "palavra"
        self.assertIn("RAT-1", ids(qa.verse_findings(rec(reduzido, literal))))

    def test_redundancia_interna_marcada(self):
        t = ("Deus terminou a sua obra que fizera e descansou de toda a sua "
             "obra que fizera.")
        f = qa.verse_findings(rec(t))
        self.assertIn("RED-1", ids(f))
        detalhe = [x for x in f if x["id"] == "RED-1"][0]["detalhe"]
        self.assertIn("obra fizera", detalhe)

    def test_paralelismo_sem_redundancia_nao_marcado(self):
        # single occurrence: no repeated bigram
        t = "Deus fez o firmamento e separou as águas."
        self.assertNotIn("RED-1", ids(qa.verse_findings(rec(t))))

    def test_calques_marcados(self):
        t = ("E aconteceu que, antes que ele acabasse de falar, eis que "
             "saía Rebeca com o seu cântaro.")
        self.assertIn("CAL-1", ids(qa.verse_findings(rec(t))))
        self.assertIn("CAL-2", ids(qa.verse_findings(rec(t))))

    def test_pronomes_em_excesso_marcados(self):
        t = "Ele disse a ela que o seu servo lhe daria o seu anel."
        self.assertIn("PRO-1", ids(qa.verse_findings(rec(t))))
        self.assertNotIn("PRO-1",
                         ids(qa.verse_findings(rec("Ele disse uma palavra."))))

    def test_paradigma_vos_marcado(self):
        cases = [
            "comereis o pão com ervas amargas",
            "guardai a páscoa do Senhor",
            "e vós sois o povo do Senhor",
            "fazei isso em memória de mim",
            "amai-vos uns aos outros",
            "vós tendes parte nisso",
        ]
        for t in cases:
            with self.subTest(t=t):
                self.assertIn("VOS-1", ids(qa.verse_findings(rec(t))))

    def test_primeira_pessoa_nao_confundida_com_vos(self):
        # -ei is ambiguous: 1sg preterite/future must NOT flag VOS-1;
        # "sai"/"cai"/"pai" are not 2pl imperatives either
        cases = [
            "Amanhã farei o que mandei.",
            "Eu falei com ele e pensei no assunto.",
            "O pai dele sai de casa e cai no chão.",
        ]
        for t in cases:
            with self.subTest(t=t):
                self.assertNotIn("VOS-1", ids(qa.verse_findings(rec(t))))

    def test_passivas_em_excesso_marcadas(self):
        t = "as águas foram partidas e o muro foi levantado."
        self.assertIn("PAS-1", ids(qa.verse_findings(rec(t))))
        self.assertNotIn("PAS-1",
                         ids(qa.verse_findings(rec("as águas foram partidas."))))


class ScanRollupTests(unittest.TestCase):
    def _tree(self, tmp, rows):
        for (cap, osis, texto, status) in rows:
            d = os.path.join(tmp, "01-gn", "%03d" % cap)
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, osis + ".json"), "w",
                      encoding="utf-8") as f:
                json.dump(rec(texto, status=status, osis=osis), f)

    def test_hot_flag_e_score_acumulado(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._tree(tmp, [
                (2, "Gen.2.2", "e o mar tornou-se em seco", "DRAFT"),
                (2, "Gen.2.3", "texto limpo aqui", "DRAFT"),
                (3, "Gen.3.1", "E aconteceu que algo houve", "DRAFT"),
                (4, "Gen.4.1", "e o mar tornou-se em seco", "APPROVED"),
            ])
            # default: varre todo estado — a triagem é sobre o texto
            chapters, totals = qa.scan(tmp, threshold=3)
            self.assertEqual(totals["versos"], 4)
            self.assertIn(("01-gn", 4), chapters)
            self.assertIn(("01-gn", 2), chapters)
            self.assertEqual(chapters[("01-gn", 2)]["score"], 3)
            self.assertTrue(chapters[("01-gn", 2)]["hot"])
            self.assertFalse(chapters[("01-gn", 3)]["hot"])
            # com filtro explícito, o estado é respeitado
            chapters_d, totals_d = qa.scan(tmp, threshold=3, status="DRAFT")
            self.assertEqual(totals_d["versos"], 3)
            self.assertNotIn(("01-gn", 4), chapters_d)

    def test_digest_traz_todos_os_versos_do_capitulo(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "hot.json")
            md = os.path.join(tmp, "hot.md")
            dig = os.path.join(tmp, "digest")
            records = os.path.join(tmp, "translation")
            self._tree(records, [
                (2, "Gen.2.2", "e o mar tornou-se em seco", "DRAFT"),
                (2, "Gen.2.3", "texto limpo aqui", "DRAFT"),
                (2, "Gen.2.10", "outro texto limpo", "DRAFT"),
            ])
            chapters, totals = qa.scan(records, threshold=1)
            qa.write_reports(out, md, dig, chapters, totals, 1)
            with open(os.path.join(dig, "01-gn-002.json"),
                      encoding="utf-8") as f:
                digest = json.load(f)
            osis = [v["osis"] for v in digest["versos"]]
            self.assertEqual(osis, ["Gen.2.2", "Gen.2.3", "Gen.2.10"])
            verso2 = digest["versos"][0]
            self.assertEqual(verso2["texto_bv"], "e o mar tornou-se em seco")
            self.assertEqual(verso2["achados"][0]["id"], "ARC-1")
            self.assertEqual(digest["versos"][1]["achados"], [])

    def test_corpus_real_smoke(self):
        # structural assertions only: marker content of specific verses
        # changes as editorial review cycles land (ER-0019)
        # sem filtro de status: a triagem é sobre o TEXTO, e o corpus inteiro
        # foi promovido a APPROVED em 2026-08-31 (ER-0021)
        chapters, totals = qa.scan(str(ROOT / "translation"), threshold=8)
        self.assertGreater(totals["versos"], 31000)
        # o filtro por estado continua funcionando quando pedido
        _, so_draft = qa.scan(str(ROOT / "translation"), threshold=8,
                              status="DRAFT")
        self.assertEqual(0, so_draft["versos"])
        gen24 = chapters.get(("01-gn", 24))
        self.assertIsNotNone(gen24)
        verso_15 = [v for v in gen24["todos"] if v["osis"] == "Gen.24.15"]
        self.assertEqual(len(verso_15), 1)
        for fi in verso_15[0]["achados"]:
            self.assertIn(fi["id"], qa.MARKER_WEIGHT)


if __name__ == "__main__":
    unittest.main()
