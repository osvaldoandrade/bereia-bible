import importlib.util
import json
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


ship = load_script("ship_review_batch")


class FixInnerQuotesTests(unittest.TestCase):
    def test_closing_quote_before_terminator_repaired(self):
        chunk = ('{"osis": "Gen.9.7", '
                 '"antes": "Mas vós, multiplicai-vos nela."",'
                 '"mudancas": []}')
        fixed = ship.fix_inner_quotes(chunk)
        self.assertIn('nela.”"', fixed)

    def test_opening_quote_after_colon_repaired(self):
        chunk = ('{"texto": "disse-lhes: "Frutifiquem e encham a terra.",'
                 '"mudancas": []}')
        fixed = ship.fix_inner_quotes(chunk)
        self.assertIn("disse-lhes: “Frutifiquem", fixed)

    def test_structural_quotes_preserved(self):
        chunk = '{"a": "x", "b": ["y", "z"]}'
        self.assertEqual(ship.fix_inner_quotes(chunk), chunk)

    def test_escaped_quote_untouched(self):
        chunk = '{"a": "x \\" y"}'
        self.assertEqual(ship.fix_inner_quotes(chunk), chunk)


class ValidateVerseTests(unittest.TestCase):
    def _verse(self, revisto, mudancas=None):
        return {"osis": "Gen.9.2", "texto_bv_revisto": revisto,
                "mudancas": mudancas or [], "objecoes": [],
                "veredito": "REVISADO" if mudancas else "SEM_ALTERACAO"}

    def test_sem_mudanca_identico_resetado_para_o_registro(self):
        v = self._verse("texto do registro")
        out = ship._validate_verse(v, "texto do registro")
        self.assertEqual(out["texto_bv_revisto"], "texto do registro")

    def test_sem_mudanca_com_diff_rejeitado(self):
        v = self._verse("texto diferente")
        self.assertIsNone(ship._validate_verse(v, "texto do registro"))

    def test_revisado_reconstruido_do_registro(self):
        rec = "Mas vós, frutificai e multiplicai-vos."
        mud = [{"tipo": "EDITORIAL", "antes": "vós", "depois": "vocês",
                "motivo": "§3"}]
        v = self._verse("Mas vocês, frutificai e multiplicai-vos.", mud)
        out = ship._validate_verse(v, rec)
        self.assertEqual(out["texto_bv_revisto"],
                         "Mas vocês, frutificai e multiplicai-vos.")

    def test_aspa_de_fronteira_ausente_tolerada(self):
        rec = "“Eis que estabeleço a minha aliança convosco;"
        mud = [{"tipo": "EDITORIAL", "antes": "convosco",
                "depois": "com vocês", "motivo": "§3"}]
        # o agente perdeu a aspa de abertura na saída
        v = self._verse("Eis que estabeleço a minha aliança com vocês;", mud)
        out = ship._validate_verse(v, rec)
        self.assertEqual(out["texto_bv_revisto"],
                         "“Eis que estabeleço a minha aliança com vocês;")

    def test_mudancas_sobrepostas_ordem_longest_first(self):
        rec = "Mas vós, frutificai; povoai a terra."
        parcial = [{"tipo": "EDITORIAL", "antes": "vós", "depois": "vocês",
                    "motivo": "§3"}]
        inteiro = [{"tipo": "EDITORIAL",
                    "antes": "Mas vós, frutificai; povoai a terra.",
                    "depois": "Mas vocês, frutifiquem; povoem a terra.",
                    "motivo": "§3"}]
        v = self._verse("Mas vocês, frutifiquem; povoem a terra.",
                        parcial + inteiro)
        out = ship._validate_verse(v, rec)
        self.assertEqual(out["texto_bv_revisto"],
                         "Mas vocês, frutifiquem; povoem a terra.")

    def test_edicao_nao_registrada_descartada(self):
        # o agente trocou o texto além das mudancas declaradas: vence a
        # reconstrução auditável (registro + mudancas registradas)
        rec = "aliança entre mim e vós, e todo ser;"
        mud = [{"tipo": "EDITORIAL", "antes": "entre mim e vós",
                "depois": "entre mim e vocês", "motivo": "§3"}]
        v = self._verse("aliança entre mim e vocês e todo ser;", mud)
        out = ship._validate_verse(v, rec)
        self.assertEqual(out["texto_bv_revisto"],
                         "aliança entre mim e vocês, e todo ser;")

    def test_antes_inexistente_sem_outras_mudancas_rejeitado(self):
        rec = "texto original"
        mud = [{"tipo": "EDITORIAL", "antes": "não existe",
                "depois": "x", "motivo": "m"}]
        v = self._verse("texto alterado", mud)
        self.assertIsNone(ship._validate_verse(v, rec))


class RegenBlockFromRecordTests(unittest.TestCase):
    """Last-resort salvage: a block even quote-repair cannot parse (inner
    quote followed by a comma) is rebuilt from the record when it declares
    SEM_ALTERACAO."""

    def setUp(self):
        self._real_root = ship.ROOT
        self.tmp = tempfile.TemporaryDirectory()
        ship.ROOT = self.tmp.name
        chap = pathlib.Path(self.tmp.name) / "translation" / "05-dt" / "012"
        chap.mkdir(parents=True)
        self.rec_text = 'e você disser: "Quero comer carne", poderá comê-la.'
        (chap / "Deut.12.20.json").write_text(
            json.dumps({"status": "DRAFT", "texto_bv": self.rec_text}),
            encoding="utf-8")

    def tearDown(self):
        ship.ROOT = self._real_root
        self.tmp.cleanup()

    def test_sem_alteracao_reconstruido_do_registro(self):
        chunk = ('"osis": "Deut.12.20",\n'
                 '      "texto_bv_revisto": "e você disser: "Quero comer '
                 'carne", poderá comê-la.",\n'
                 '      "mudancas": [],\n'
                 '      "veredito": "SEM_ALTERACAO"\n    }')
        v = ship.regen_block_from_record(chunk, "05-dt", 12)
        self.assertEqual(v["texto_bv_revisto"], self.rec_text)
        self.assertEqual(v["mudancas"], [])

    def test_revisado_nao_regenerado(self):
        chunk = '"osis": "Deut.12.20", "veredito": "REVISADO"}'
        self.assertIsNone(ship.regen_block_from_record(chunk, "05-dt", 12))

    def test_sem_veredito_nao_regenerado(self):
        chunk = '"osis": "Deut.12.20", "texto_bv_revisto": "x"}'
        self.assertIsNone(ship.regen_block_from_record(chunk, "05-dt", 12))

    def test_sem_osis_nao_regenerado(self):
        chunk = '"texto_bv_revisto": "x", "veredito": "SEM_ALTERACAO"}'
        self.assertIsNone(ship.regen_block_from_record(chunk, "05-dt", 12))


class CanonQuotesTests(unittest.TestCase):
    def test_canoniza_os_dois_estilos(self):
        self.assertEqual(ship.canon_quotes("“x” ‘y’"), '"x" \'y\'')


if __name__ == "__main__":
    unittest.main()
