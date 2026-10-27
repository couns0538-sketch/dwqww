"""S28-1 v3 tests: the AL1 s198 pin proposal matches both observations; planted defects are caught.

Run: python -I -B test_forge_sol_S28_proposal_v3_20261027.py -v   (stdlib only; nothing is applied anywhere)
"""
import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s28chk', HERE / 'forge_sol_S28_check_proposal_v3_20261027.py')
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)
PATCH = (HERE / 'forge_sol_S28_v3_AL1s198_pin_proposal_20261027.patch').read_text(encoding='utf-8')
OBS = json.loads((HERE / 'logs' / 'al1_s198_pin_observation.json').read_text(encoding='utf-8'))
BEFORE = (HERE / 'logs' / 'al1L_forge_tests_before.stderr').read_text(encoding='utf-8', errors='replace')


def once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)


class Proposal(unittest.TestCase):
    def test_observation_values(self):
        o = {c['case']: (c['bestmove'], c['score_kind'], c['score'], c['depth']) for c in OBS['cases']}
        self.assertEqual(o, {'WAC001': ('f6h5', 'cp', 623, 12), 'promotion_white': ('c6d6', 'cp', 569, 1),
                             'promotion_black': ('c3d3', 'cp', 569, 1)})
        self.assertEqual(OBS['engine_sha256'], '5d4df7f1be51b083e0719266e55367577ed580a509a12196d62c0a368826a5b1')

    def test_proposal_passes(self):
        self.assertEqual(C.check(PATCH, OBS, BEFORE), [])

    def test_planted_wrong_wac_score(self):
        bad = once(PATCH, '+    constexpr int documented_wac_score = 623;', '+    constexpr int documented_wac_score = 624;')
        self.assertTrue(any('documented_wac_score' in p for p in C.check(bad, OBS, BEFORE)))

    def test_planted_kings_not_rerecorded(self):
        bad = once(PATCH, '+        const std::string_view documented_king_text = mirrored ? "c3d3" : "c6d6";',
                   '+        const std::string_view documented_king_text = mirrored ? "c3d2" : "c6d7";')
        self.assertTrue(any('king pins' in p for p in C.check(bad, OBS, BEFORE)))

    def test_planted_helper_left_at_661(self):
        bad = once(PATCH, "12,8,'f6h5',623),", "12,8,'f6h5',661),")
        self.assertTrue(any('rerecord_pins.py: WAC001' in p for p in C.check(bad, OBS, BEFORE)))

    def test_planted_engine_change(self):
        bad = PATCH + ('diff --git a/src/search.cpp b/src/search.cpp\n--- a/src/search.cpp\n+++ b/src/search.cpp\n'
                       '@@ -1,1 +1,1 @@\n-int x = 0;\n+int x = 1;\n')
        self.assertTrue(any('outside the pin scope' in p for p in C.check(bad, OBS, BEFORE)))

    def test_planted_known_label_change(self):
        bad = PATCH + ('diff --git a/tests/tests.cpp b/tests/tests.cpp\n--- a/tests/tests.cpp\n+++ b/tests/tests.cpp\n'
                       '@@ -60,1 +60,1 @@\n-              << " (h256_e12 net-evaluation horizon; original 6.4.24 expectation retained)\\n";\n'
                       '+              << " (AL1 net-evaluation horizon; original 6.4.24 expectation retained)\\n";\n')
        self.assertTrue(any('protected text removed' in p for p in C.check(bad, OBS, BEFORE)))

    def test_planted_forge_tests_disagreement(self):
        bad = BEFORE.replace('observed f6h5/623/d12', 'observed f6h5/622/d12')
        self.assertNotEqual(bad, BEFORE)
        self.assertTrue(any('forge_tests observed' in p for p in C.check(PATCH, OBS, bad)))


if __name__ == '__main__':
    unittest.main()
