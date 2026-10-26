"""Portable, standard-library-only checks of the delivered S08 data and parser."""
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('s08_delivered_collector',ROOT/'forge_sol_S08_collect_profiles_substitute_20261026.py')
collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)

@contextlib.contextmanager
def corpus_directory():
    old=Path.cwd()
    os.chdir(ROOT/'corpus')
    try:yield
    finally:os.chdir(old)

class Delivery(unittest.TestCase):
    def corpus(self,manifest=None,repeat=False):
        with corpus_directory():
            manifest=manifest if manifest is not None else json.loads(Path('forge_sol_S08_authorized_corpus_manifest_20261026.json').read_text())
            suites=[Path(row['path']) for row in manifest['corpora']]
            if repeat:suites.append(suites[0])
            return collector.corpus_metadata(suites,manifest=manifest)

    def test_exact_authorized_distinct_corpus(self):
        result=self.corpus()
        self.assertEqual((result['unique_positions'],result['coverage_status']),(2000,'COMPLETE_AUTHORIZED_SUBSTITUTE'))
        self.assertEqual((result['wac_sts_only_positions'],result['wac_sts_only_coverage_gap']),(300,1700))
        self.assertEqual({k:sum(row['kind']==k for row in result['positions']) for k in ('WAC','BENCH','OPENING')},{'WAC':300,'BENCH':7,'OPENING':1693})

    def test_duplicate_input_does_not_pad_positions(self):
        self.assertEqual(self.corpus(repeat=True)['unique_positions'],2000)

    def test_absent_substitution_authority_rejected(self):
        manifest=json.loads((ROOT/'corpus/forge_sol_S08_authorized_corpus_manifest_20261026.json').read_text())
        manifest.pop('authorization')
        with self.assertRaises(ValueError):self.corpus(manifest)

    def test_wrong_corpus_digest_rejected(self):
        manifest=json.loads((ROOT/'corpus/forge_sol_S08_authorized_corpus_manifest_20261026.json').read_text())
        manifest['corpora'][-1]['sha256']='0'*64
        with self.assertRaises(ValueError):self.corpus(manifest)

    def test_original_native_packet_validates(self):
        lines=(ROOT/'forge_sol_S08_profile_packet_reference_20261026.stdout').read_text().splitlines()
        packet=collector.parse_packet(lines,terminal='bench')
        self.assertEqual(len(packet['counters']),55)
        self.assertFalse(packet['overflow'])
        self.assertEqual(packet['counters']['nodes']['count'],308972)

    def test_late_or_missing_counter_rejected(self):
        lines=(ROOT/'forge_sol_S08_profile_packet_reference_20261026.stdout').read_text().splitlines()
        with self.assertRaises(ValueError):collector.parse_packet(lines+[lines[1]],terminal='bench')
        with self.assertRaises(ValueError):collector.parse_packet(lines[:1]+lines[2:],terminal='bench')

if __name__=='__main__':unittest.main()
