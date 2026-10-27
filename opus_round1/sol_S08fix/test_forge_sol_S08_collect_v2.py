"""Standard-library checks of the S08 v2 collector: Sol's six delivery checks (ported to the v2 file) plus the
S08-4 table rules (disabled-by-default rows dropped from the rare-event rows, corpus limit stated) and the AL1 pins.
usage: python -B test_forge_sol_S08_collect_v2.py -v"""
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s08_collector_v2', ROOT / 'forge_sol_S08_collect_profiles_v2.py')
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)
REFERENCE = ROOT / 'forge_sol_S08_profile_packet_reference_20261026.stdout'
MANIFEST = ROOT / 'corpus' / 'forge_sol_S08_authorized_corpus_manifest_20261026.json'


@contextlib.contextmanager
def corpus_directory():
    old = Path.cwd()
    os.chdir(ROOT / 'corpus')
    try:
        yield
    finally:
        os.chdir(old)


class SolDeliveryChecks(unittest.TestCase):
    def corpus(self, manifest=None, repeat=False):
        with corpus_directory():
            manifest = manifest if manifest is not None else json.loads(MANIFEST.read_text())
            suites = [Path(row['path']) for row in manifest['corpora']]
            if repeat:
                suites.append(suites[0])
            return collector.corpus_metadata(suites, manifest=manifest)

    def test_exact_authorized_distinct_corpus(self):
        result = self.corpus()
        self.assertEqual((result['unique_positions'], result['coverage_status']), (2000, 'COMPLETE_AUTHORIZED_SUBSTITUTE'))
        self.assertEqual((result['wac_sts_only_positions'], result['wac_sts_only_coverage_gap']), (300, 1700))
        self.assertEqual({k: sum(row['kind'] == k for row in result['positions']) for k in ('WAC', 'BENCH', 'OPENING')},
                         {'WAC': 300, 'BENCH': 7, 'OPENING': 1693})

    def test_duplicate_input_does_not_pad_positions(self):
        self.assertEqual(self.corpus(repeat=True)['unique_positions'], 2000)

    def test_absent_substitution_authority_rejected(self):
        manifest = json.loads(MANIFEST.read_text())
        manifest.pop('authorization')
        with self.assertRaises(ValueError):
            self.corpus(manifest)

    def test_wrong_corpus_digest_rejected(self):
        manifest = json.loads(MANIFEST.read_text())
        manifest['corpora'][-1]['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            self.corpus(manifest)

    def test_original_native_packet_validates(self):
        packet = collector.parse_packet(REFERENCE.read_text().splitlines(), terminal='bench')
        self.assertEqual(len(packet['counters']), 55)
        self.assertFalse(packet['overflow'])
        self.assertEqual(packet['counters']['nodes']['count'], 308972)

    def test_late_or_missing_counter_rejected(self):
        lines = REFERENCE.read_text().splitlines()
        with self.assertRaises(ValueError):
            collector.parse_packet(lines + [lines[1]], terminal='bench')
        with self.assertRaises(ValueError):
            collector.parse_packet(lines[:1] + lines[2:], terminal='bench')


class S08_4_Table(unittest.TestCase):
    def setUp(self):
        packet = collector.parse_packet(REFERENCE.read_text().splitlines(), terminal='bench')
        self.rows = collector.firing_table([packet])
        self.text = collector._table_text([('Reference packet', self.rows)])

    def test_capture_futility_prunes_is_not_a_rare_row(self):
        row = next(r for r in self.rows if r['event'] == 'capture_futility_prunes')
        self.assertEqual(row['count'], 0)
        self.assertIsNone(row['rare_below_0_1_pct'])
        self.assertIn('CaptureFutilityBase = 0', row['disabled_by_default'])
        table_rows = [line for line in self.text.splitlines() if line.startswith('| capture_futility_prunes ')]
        self.assertEqual(table_rows, [])
        self.assertIn('Not a dead-feature row (disabled by default', self.text)
        self.assertIn('- capture_futility_prunes: count 0 of', self.text)

    def test_other_rows_and_checks_stay(self):
        self.assertIn('| capture_futility_checks |', self.text)
        self.assertIn('| nnue_refresh | 8 | nnue_forward |', self.text)
        self.assertEqual(sum(line.startswith('| ') and not line.startswith('| Event') for line in self.text.splitlines()), 54)

    def test_corpus_limit_is_stated(self):
        self.assertIn('the specified 2,000 WAC/STS set is not available', self.text)
        self.assertIn('It is not a WAC/STS corpus.', self.text)


class Pins(unittest.TestCase):
    def test_al1_pins_are_the_defaults(self):
        self.assertEqual((collector.DEFAULT_BENCH11_NODES, collector.DEFAULT_BENCH20_NODES), (312866, 12389307))
        import inspect
        sig = inspect.signature(collector.collect)
        self.assertEqual(sig.parameters['bench11_nodes'].default, 312866)
        self.assertEqual(sig.parameters['bench20_nodes'].default, 12389307)


if __name__ == '__main__':
    unittest.main()
