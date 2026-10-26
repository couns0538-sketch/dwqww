#!/usr/bin/env python3
"""Audit old-path independence and preserve failed synthetic roots before cleanup."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
import types
import unittest

sys.dont_write_bytecode = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--operative-test-path', type=Path, required=True)
    parser.add_argument('--proof-root', type=Path, required=True)
    args = parser.parse_args()
    source = args.source.read_bytes()
    actual = hashlib.sha256(source).hexdigest()
    if actual != args.expected_sha256:
        raise ValueError('test source SHA mismatch')
    if not args.proof_root.is_absolute() or args.proof_root.exists():
        raise ValueError('NEW absolute proof root required')
    args.proof_root.mkdir()
    packet_root = args.operative_test_path.parent.parent
    original = json.loads((packet_root / 'S26/forge_sol_S26_dependencies_20261026.json').read_text())
    denied = {item['path'] for item in original.values()}
    denied.add('/workspace/forge-sol-next-20261024/int16-review/wac300.epd')
    denials = []
    phase = ['guard_selfcheck']

    def hook(event, values):
        if event == 'open' and values and isinstance(values[0], (str, bytes, os.PathLike)):
            path = os.path.abspath(os.fsdecode(values[0]))
            if path in denied:
                denials.append({'path': path, 'phase': phase[0]})
                raise AssertionError('AUDIT_DENIED_ORIGINAL_PATH: ' + path)

    sys.addaudithook(hook)
    for path in sorted(denied):
        try:
            open(path, 'rb')
        except AssertionError:
            pass
        else:
            raise AssertionError('audit guard failed: ' + path)
    phase[0] = 'test_execution'
    module = types.ModuleType('s26_portable_guard_subject')
    module.__file__ = str(args.operative_test_path)
    exec(compile(source, str(args.operative_test_path), 'exec'), module.__dict__)
    captures = []

    class PreservingResult(unittest.TextTestResult):
        def preserve(self, test, kind):
            root = getattr(test, 'root', None)
            row = {'test': test.id(), 'kind': kind, 'captured_before_unittest_cleanup': True,
                   'source_root': str(root) if root else None}
            if root is not None and Path(root).is_dir():
                target = args.proof_root / ('failure_%02d_%s' % (len(captures), test._testMethodName))
                try:
                    shutil.copytree(root, target)
                    row.update(captured_root=str(target), files=sum(p.is_file() for p in target.rglob('*')))
                except Exception as exc:
                    row['capture_error'] = type(exc).__name__ + ': ' + str(exc)
            captures.append(row)

        def addFailure(self, test, error):
            self.preserve(test, 'FAILURE')
            super().addFailure(test, error)

        def addError(self, test, error):
            self.preserve(test, 'ERROR')
            super().addError(test, error)

    started = time.monotonic()
    result = unittest.TextTestRunner(verbosity=2, resultclass=PreservingResult).run(
        unittest.defaultTestLoader.loadTestsFromModule(module))
    receipt = {'test_source': str(args.source), 'test_source_sha256': actual,
               'operative_test_path': str(args.operative_test_path), 'packet_root': str(packet_root),
               'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
               'status': 'PASS' if result.wasSuccessful() else 'FAIL', 'seconds': time.monotonic() - started,
               'denied_original_paths': sorted(denied), 'open_denials': denials,
               'test_execution_original_path_denials': sum(x['phase'] == 'test_execution' for x in denials),
               'failure_captures': captures, 'caller_PYTHONPATH': os.environ.get('PYTHONPATH'),
               'scope': 'SYNTHETIC process suite only; audit hook rejects original helper/WAC opens. Failure roots copied before cleanup. No C++ compilation, genuine engine, Git or network.'}
    (args.proof_root / 'forge_sol_S26_guarded_test_receipt_20261026.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
