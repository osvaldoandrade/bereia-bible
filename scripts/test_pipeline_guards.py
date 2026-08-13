import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PipelineGuardTests(unittest.TestCase):
    def test_mark_short_ending_requires_explicit_adjudication(self):
        persist = load_script("persist_chapter_draft")
        packet = ROOT / "pipeline" / "packets" / "mark-016-001-020.blind.json"
        index = persist.packet_index([str(packet)])
        self.assertEqual(
            persist.unadjudicated_source_variants({}, index),
            ["Mark.16.20(Mark.16.99)"],
        )
        chapters = {
            ("Mark", 16): {
                "Mark.16.20": {"variantes_textuais": []},
            }
        }
        self.assertEqual(
            persist.unadjudicated_source_variants(chapters, index),
            ["Mark.16.20(Mark.16.99)"],
        )
        chapters[("Mark", 16)]["Mark.16.20"]["variantes_textuais"] = [
            {"descricao": "Mark.16.99 — final curto"}
        ]
        self.assertEqual(
            persist.unadjudicated_source_variants(chapters, index), []
        )

    def test_progress_requires_exact_source_set_and_valid_status(self):
        progress = load_script("progress")
        expected = progress.source_verse_sets("Matt")[17]
        self.assertEqual(len(expected), 26)
        self.assertNotIn(21, expected)

        complete = {verse: "DRAFT" for verse in expected}
        covered, mark = progress.chapter_progress(expected, complete, [])
        self.assertEqual(covered, 26)
        self.assertTrue(mark.startswith("● 26/26"))

        swapped = dict(complete)
        swapped.pop(20)
        swapped[21] = "DRAFT"
        covered, mark = progress.chapter_progress(expected, swapped, [])
        self.assertEqual(covered, 25)
        self.assertTrue(mark.startswith("◐ parcial 25/26"))
        self.assertIn("extras=21", mark)

        broken = dict(complete)
        broken[20] = "BROKEN"
        covered, mark = progress.chapter_progress(
            expected, broken, ["Matt.17.20.json"]
        )
        self.assertEqual(covered, 25)
        self.assertTrue(mark.startswith("◐ parcial 25/26"))
        self.assertIn("status-inválido=20", mark)
        self.assertIn("broken=Matt.17.20.json", mark)


if __name__ == "__main__":
    unittest.main()
