"""Selected R13/R14 regression receipts; never the inherited full suite."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import time

from run_policy import safe_path

ROOT = Path('D:/a14')
PYTHON = ROOT/'runtime/python/python.exe'
PYTHON_MD5 = '0cfdf7db1b81d067d3dad75f6abb312b'
SELECTED = (
    'test_game_hash.py', 'test_p5_audit.py', 'test_pack.py', 'test_pack_qualification.py',
    'test_qc_core.py', 'test_r14_chain_evidence.py', 'test_r14_group_map.py',
    'test_r14_launcher.py', 'test_r14_overlap.py', 'test_r14_preflight.py',
    'test_r14_qc_fixes.py', 'test_r14_runtime_setup.py', 'test_r14_scan.py',
    'test_r14_segments.py', 'test_r14_suite.py', 'test_runtime_policy.py',
    'r14_native/test_native.py', 'r14_qualification/test_qualification.py',
)
BLOCKED_IMPORTS = ('train', 'train_adapter', 'npt_adapter', 'torch', 'data_loader',
                   'nnue_dataset', 'model', 'trainer')


def vienna():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S Vienna')


def selected_files(fixtures=None):
    paths = [ROOT/'tests'/name for name in SELECTED] if fixtures is None else [Path(p) for p in fixtures]
    if not paths or len(paths) != len(set(paths)):
        raise ValueError('nonempty unique file selection required')
    checked = []
    for path in paths:
        path = safe_path(path, write=True)
        if fixtures is not None and (not path.name.startswith('test_') or path.suffix != '.py' or
                not any(path.is_relative_to(root) for root in (ROOT/'evidence/test_logs', ROOT/'tmp'))):
            raise ValueError('fixture tests require an owned evidence/tmp path')
        if not path.is_file():
            raise ValueError(f'selected test missing: {path}')
        checked.append(path)
    return checked


def identities(paths):
    result = []
    for path in paths:
        path = safe_path(path)
        before = path.stat()
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'md5').hexdigest()
        after = path.stat()
        if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
            raise ValueError(f'identity changed while read: {path}')
        result.append(dict(path=str(path), md5=digest, bytes=after.st_size))
    return result


class ImportGuard:
    def find_spec(self, fullname, path=None, target=None):
        normalized = fullname.casefold()
        if any(normalized == name or normalized.startswith(name+'.') for name in BLOCKED_IMPORTS):
            raise ImportError(f'blocked training import: {fullname}')
        return None


def install_boundary(out):
    """Python import/open/mutation fence for reviewed tests, not an OS sandbox."""
    finder = ImportGuard()
    for name in tuple(sys.modules):
        finder.find_spec(name)
    sys.meta_path.insert(0, finder)
    fixture_roots = (out/'pytest', out/'tmp')

    def check(value, writing=False, unlink=False):
        if isinstance(value, int):
            return
        path = Path(os.fsdecode(value)).absolute()
        if any(part.lower().startswith(('nnue-pytorch', 'nnue_pytorch')) for part in path.parts):
            raise PermissionError('protected training path')
        if unlink and path.name.lower().endswith(('.lock', '.nnue')):
            raise PermissionError('protected removal')
        try:
            # Only fixture marker files may bypass the general lock spelling ban.
            if path.name.lower().endswith('.lock') and any(path.is_relative_to(root) for root in fixture_roots):
                safe_path(path.parent, write=writing)
                if path.exists() and getattr(path.lstat(), 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                    raise ValueError('redirected marker')
                return
            if unlink and os.path.lexists(path):
                info = path.lstat()
                if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                    safe_path(path.parent, write=True)
                    return
            safe_path(path, write=writing)
        except ValueError as exc:
            raise PermissionError(str(exc)) from exc

    def audit(event, args):
        if event == 'open' and args and isinstance(args[0], (str, bytes, os.PathLike)):
            if os.fsdecode(args[0]).casefold() in (os.devnull.casefold(), os.path.abspath(os.devnull).casefold()):
                return  # Exact operating-system sink; no filesystem allocation.
            mode, flags = args[1:3]
            writing = isinstance(mode, str) and any(c in mode for c in 'wax+')
            writing = writing or isinstance(flags, int) and bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
            check(args[0], writing)
        elif event in ('os.remove', 'os.rmdir', 'os.mkdir', 'os.chmod', 'os.utime', 'os.truncate'):
            check(args[0], True, event in ('os.remove', 'os.rmdir'))
        elif event in ('os.rename', 'os.link'):
            check(args[0], True, event == 'os.rename')
            check(args[1], True)
        elif event == 'os.symlink':
            check(args[0])
            check(args[1], True)
        elif event == 'os.chdir':
            check(args[0], True)
    sys.addaudithook(audit)


class Resources:
    def __init__(self, seconds):
        import psutil
        self.psutil = psutil
        self.deadline = time.monotonic()+seconds

    def __call__(self, reserve=0):
        if time.monotonic() >= self.deadline:
            raise TimeoutError('suite deadline reached')
        if self.psutil.disk_usage('D:/').free < 50*1024**3+reserve or self.psutil.disk_usage('C:/').free < 30*1024**3:
            raise OSError('suite disk floor')
        if self.psutil.virtual_memory().available < 8*1024**3 or self.psutil.Process().memory_info().rss > 2*1024**3:
            raise MemoryError('suite memory floor/cap')


class Results:
    def __init__(self, guard=lambda: None):
        self.guard = guard
        self.nodeids = []
        self.reports = []
        self.collection_reports = []

    def pytest_collection_finish(self, session):
        self.guard()
        self.nodeids = [item.nodeid for item in session.items]

    def pytest_collectreport(self, report):
        if report.failed or report.skipped:
            self.collection_reports.append(dict(nodeid=report.nodeid, outcome=report.outcome,
                                                detail=str(report.longrepr)[:4096]))

    def pytest_runtest_setup(self, item):
        self.guard()

    def pytest_runtest_logreport(self, report):
        self.reports.append(dict(nodeid=report.nodeid, when=report.when, outcome=report.outcome,
                                 duration=report.duration, kind='subtest' if hasattr(report, 'context') else 'test'))


def assemble_report(results, exit_code, before, after, *, collect_only):
    counts = dict(passed=0, failed=0, skipped=0, error=0, not_run=0)
    subtests = dict(passed=0, failed=0, skipped=0)
    for report in results.reports:
        if report['kind'] == 'subtest':
            subtests[report['outcome']] += 1
    for nodeid in results.nodeids:
        rows = [r for r in results.reports if r['nodeid'] == nodeid and r['kind'] == 'test']
        if any(r['outcome'] == 'failed' and r['when'] != 'call' for r in rows):
            outcome = 'error'
        elif any(r['outcome'] == 'failed' for r in rows):
            outcome = 'failed'
        elif any(r['outcome'] == 'skipped' for r in rows):
            outcome = 'skipped'
        elif any(r['when'] == 'call' and r['outcome'] == 'passed' for r in rows):
            outcome = 'passed'
        else:
            outcome = 'not_run'
        counts[outcome] += 1
    collection = Counter(r['outcome'] for r in results.collection_reports)
    stable = before == after
    complete = bool(results.nodeids) and stable and not collection and exit_code == 0
    if collect_only:
        status = 'COLLECTED' if complete else 'UNVERIFIED'
    elif not stable:
        status = 'UNVERIFIED'
    elif counts['failed'] or counts['error'] or subtests['failed']:
        status = 'FAIL'
    elif complete and counts['passed'] == len(results.nodeids) and not subtests['skipped']:
        status = 'PASS'
    else:
        status = 'UNVERIFIED'
    return dict(status=status, complete=complete and (collect_only or status == 'PASS'),
                collected=len(results.nodeids), nodeids=results.nodeids, test_counts=counts,
                subtest_counts=subtests, collection_counts=dict(failed=collection['failed'], skipped=collection['skipped']),
                reports=results.reports, collection_reports=results.collection_reports,
                pytest_exit_code=None if exit_code is None else int(exit_code), selected_before=before, selected_after=after,
                files_unchanged=stable, collect_only=collect_only)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seconds', type=int, required=True)
    parser.add_argument('--collect-only', action='store_true')
    parser.add_argument('--fixture-json')
    args = parser.parse_args()
    out = safe_path(args.out, write=True)
    if os.environ.get('R14_SUITE_CHILD') != str(out) or Path(sys.executable).resolve() != PYTHON.resolve():
        raise ValueError('use the owned suite supervisor and runtime')
    if identities([PYTHON])[0]['md5'] != PYTHON_MD5:
        raise ValueError('runtime executable changed')
    fixtures = None if args.fixture_json is None else json.loads(args.fixture_json)
    if fixtures is not None and (not isinstance(fixtures, list) or not all(isinstance(x, str) for x in fixtures)):
        raise ValueError('fixture selection must be a path list')
    selected = selected_files(fixtures)
    guard = Resources(args.seconds)
    guard(1024*1024)
    before = identities(selected)
    started = vienna()
    tempfile.tempdir = str(out/'tmp')
    sys.dont_write_bytecode = True
    install_boundary(out)
    import pytest
    evidence = Results(guard)
    arguments = [*map(str, selected), '-q', '--capture=no', '--noconftest', '-p', 'no:cacheprovider',
                 '--basetemp', str(out/'pytest'), '--rootdir', str(ROOT), '--log-file', os.devnull]
    if args.collect_only:
        arguments.append('--collect-only')
    error = None
    code = None
    try:
        code = int(pytest.main(arguments, plugins=[evidence]))
        after = identities(selected)
    except BaseException as exc:
        after = None
        error = f'{type(exc).__name__}: {exc}'
    result = assemble_report(evidence, code, before, after, collect_only=args.collect_only)
    result.update(schema=1, scope='runner_fixture' if fixtures is not None else 'selected_r13_r14_regression',
                  started=started, finished=vienna(), command=[str(PYTHON), '-m', 'pytest', *arguments],
                  pytest_arguments=arguments, error=error, python=identities([PYTHON])[0],
                  boundary='Python import/open/mutation fence; reviewed native children; not an OS sandbox')
    payload = (json.dumps(result, indent=2)+'\n').encode()
    if len(payload) > 4*1024*1024:
        raise ValueError('suite receipt exceeds bounded size')
    guard(len(payload)+1024*1024)
    with (out/'worker-result.json.part').open('xb') as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return 0 if result['status'] in ('PASS', 'COLLECTED') else 1 if result['status'] == 'FAIL' else 2


if __name__ == '__main__':
    raise SystemExit(main())
