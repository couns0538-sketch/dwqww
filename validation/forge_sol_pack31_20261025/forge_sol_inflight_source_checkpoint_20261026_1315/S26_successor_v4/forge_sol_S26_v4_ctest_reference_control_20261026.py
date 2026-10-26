#!/usr/bin/env python3
"""Parser-only configuration regression; launches no engine or CTest process."""
import inspect
import sys
import tempfile
from pathlib import Path
from types import ModuleType
import unittest

CORE = ['forge_tests','forge_correction_history_tests','forge_runtime_psqt_tests',
        'forge_pawn_span_tests','forge_nearest_pawn_tests','forge_pv_metadata_tests',
        'forge_tt_tests','forge_rule50_tests','forge_legal_witness_tests',
        'match_tool_tests','windows_validation_tests','uci_regression',
        'ponder_regression','ownbook_regression']

class CompletenessRegression(unittest.TestCase):
    def test_one_case_cannot_claim_configured_suite_complete(self):
        path=Path(sys.argv[1]); module=ModuleType('ctest_subject');module.__file__=str(path)
        exec(compile(path.read_bytes(),str(path),'exec'),module.__dict__)
        with tempfile.TemporaryDirectory(prefix='ctest_reference_',dir=Path(__file__).parent) as d:
            xml=Path(d)/'one_case.xml';xml.write_text('<testsuite><testcase name="forge_tests"/></testsuite>')
            kwargs={'expected_names':CORE} if 'expected_names' in inspect.signature(module.check_ctest).parameters else {}
            with self.assertRaises(ValueError):
                module.check_ctest(xml,0,{'allowed_test_failure':'forge_tests','rules':[]},**kwargs)

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(CompletenessRegression)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
