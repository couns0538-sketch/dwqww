"""Benign replay of an actual captured17 UCI handshake; no engine execution."""
import importlib.util
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('correction_uci_probe',ROOT.parents[1]/'.github/hosted-tt-refresh-strength/run_hosted.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)


class UciExchangeMustComplete(unittest.TestCase):
    def probe(self,mode,success):
        phase=os.environ.get('UCI_TEST_PHASE','red')
        out=ROOT/'uci-fixture-runs'/phase/mode;out.mkdir(parents=True,exist_ok=False)
        error=None
        with patch.dict(os.environ,{'BENCH_FIXTURE_MODE':mode}):
            try:runner._owned_readiness_probe(ROOT/'benign_fixture.py',out,None,10,
                    stdin='uci\nquit\n',prefix='uci',verify_signature=False)
            except ValueError as caught:error=caught
        facts=json.loads((out/'uci-process.json').read_text())
        self.assertEqual(facts['returncode_before_verdict'],0)
        self.assertTrue(facts['owned_group_empty_after_cleanup'])
        self.assertEqual(error is None,success,'Missing/malformed handshakes must not pass readiness')
        self.assertEqual(facts['verdict'],'passed' if success else 'failed')

    def test_actual_captured_handshake_prefix_passes(self):self.probe('uci-good',True)
    def test_missing_standalone_uciok_fails(self):self.probe('uci-noack',False)
    def test_prefixed_option_substring_is_not_an_advertised_record(self):self.probe('uci-option-prefix',False)
    def test_duplicate_uciok_fails(self):self.probe('uci-duplicateack',False)


if __name__=='__main__':unittest.main(verbosity=2)
