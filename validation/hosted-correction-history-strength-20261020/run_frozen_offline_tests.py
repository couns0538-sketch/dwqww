"""Run retained applicable offline tests; preserve their old draft-state checks."""
import hashlib
import json
import os
from pathlib import Path
import time
import unittest

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT.parents[1] / '.github/hosted-correction-history-strength'

def main():
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    os.environ['BENCH_TEST_PHASE'] = 'root-ready-final'
    os.environ['UCI_TEST_PHASE'] = 'root-ready-final'
    hashes = lambda: {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(PACKAGE.glob('*.py'))}
    before = hashes()
    def flatten(suite):
        for item in suite:
            if isinstance(item, unittest.TestSuite):
                yield from flatten(item)
            else:
                yield item
    tests = list(flatten(unittest.defaultTestLoader.discover(str(ROOT), pattern='test_*.py')))
    historical = {'test_actual_draft_keeps_proofs_and_workflow_pending_after_signature_freeze',
                  'test_actual_source18_signature_does_not_waive_other_gates'}
    omitted = [t.id() for t in tests if t.id().rsplit('.',1)[1] in historical]
    assert len(tests) == 96 and len(omitted) == 2
    suite = unittest.TestSuite(t for t in tests if t.id() not in omitted)
    start = time.monotonic()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    after = hashes()
    record = {'status':'PASS' if result.wasSuccessful() and before==after else 'FAIL',
        'tests_run':result.testsRun, 'failures':len(result.failures), 'errors':len(result.errors),
        'elapsed_seconds':time.monotonic()-start, 'package_python_before':before,
        'package_python_after':after, 'historical_draft_only_tests_preserved_not_applied_to_READY':omitted,
        'replacement_checks':'check_frozen_launch.py actual READY plus9 missing-gate controls',
        'scope':'Captured output/schema/inert files/benign Python child processes only; no chess engine/compiler/match/Git/network.'}
    (ROOT/'ROOT-READY-OFFLINE-RESULT.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))
    raise SystemExit(0 if record['status']=='PASS' else 1)

if __name__ == '__main__':
    main()
