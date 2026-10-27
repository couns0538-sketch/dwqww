"""S27 v2 tests (fix-ups S27-1, S27-2, S27-3). Fixture files are written as LF bytes so the tests also run on
Windows; the real-tree tests export the AL1 source of this checkout with `git archive HEAD` into scratch.

Run: python -I -B test_forge_sol_S27_v2_20261027.py -v
Env: S27_HYGIENE / S27_BUILDCOMPARE (mutant copies), S27_V1 (Sol's v1 hygiene, for contrast tests),
     S27_SCRATCH (scratch dir outside git).
"""
import difflib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRATCH = Path(os.environ.get('S27_SCRATCH', tempfile.gettempdir()))
FIX = HERE / 'tests_fixtures'
V1 = Path(os.environ.get('S27_V1', r'F:/opus_scratch/sol_S27fix/sol_orig/S27/forge_sol_S27_hygiene_20261026.py'))


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = load(Path(os.environ.get('S27_HYGIENE', HERE / 'forge_sol_S27_hygiene_v2_20261027.py')), 's27_hygiene_v2')
B = load(Path(os.environ.get('S27_BUILDCOMPARE', HERE / 'forge_sol_S27_buildcompare_v2_20261027.py')), 's27_buildcompare_v2')
AL1 = {11: 312866, 13: 862329, 16: 3024920, 20: 12389307, 22: 34048354}
LPRIME = {11: 308972, 13: 745494, 16: 2460422, 20: 11901452, 22: 31111774}


def new_dir(tag):
    return Path(tempfile.mkdtemp(prefix='s27v2_%s_' % tag, dir=SCRATCH))


def write(root, files):
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode())


def udiff(path, before, after):
    return ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), 'a/' + path, 'b/' + path)).encode()


_AL1_EXPORT = None


def al1_export():
    """AL1 lock source of this checkout (git archive HEAD), exported once per run into scratch."""
    global _AL1_EXPORT
    if _AL1_EXPORT is None:
        root = new_dir('al1') / 'al1_src'
        top = subprocess.run(['git', '-C', str(HERE), 'rev-parse', '--show-toplevel'], capture_output=True, text=True,
                             check=True).stdout.strip()
        data = subprocess.run(['git', '-C', top, 'archive', '--format=tar', 'HEAD', 'CMakeLists.txt', 'IDEA_SOURCE.md',
                               'README.md', 'bench', 'include', 'src', 'tests', 'tools'], capture_output=True, check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(data)) as t:
            t.extractall(root)
        _AL1_EXPORT = root
    return _AL1_EXPORT


class S27_1_NoBackupAndPerBase(unittest.TestCase):
    def offset_case(self):
        base = new_dir('offset') / 'tree'
        body = ''.join('line %d\n' % i for i in range(1, 21))
        write(base, {'tests/sample.txt': ''.join('extra %d\n' % i for i in range(5)) + body})
        patch = udiff('tests/sample.txt', body, body.replace('line 10\n', 'line ten\n'))  # applies at offset +5
        return base, patch

    def run_check(self, mod, base, patch, **kw):
        root = new_dir('run')
        (root / 'in.patch').write_bytes(patch)
        return mod.check_submission(root / 'in.patch', {'fixture': base}, root / 'out', [], **kw), root / 'out'

    def test_offset_hunk_passes_without_orig(self):
        base, patch = self.offset_case()
        r, out = self.run_check(H, base, patch)
        self.assertEqual(r['status'], 'PASS', r['findings'])
        self.assertEqual(list((out / 'fixture' / 'candidate').rglob('*.orig')), [])
        self.assertIn('--no-backup-if-mismatch', json.loads((out / r['raw_records'][-1]).read_text())['argv'])

    @unittest.skipUnless(V1.is_file(), 'Sol v1 not available')
    def test_v1_aborted_on_the_same_offset_hunk(self):
        v1 = load(V1, 's27_hygiene_v1')
        base, patch = self.offset_case()
        r, out = self.run_check(v1, base, patch)
        self.assertEqual(r['status'], 'FAIL')
        self.assertIn('applied_path_mismatch', {f['code'] for f in r['findings']})
        self.assertTrue(list((out / 'fixture' / 'candidate').rglob('*.orig')))

    def bases_with_bad_middle(self):
        root = new_dir('bases')
        files = {'tests/sample.txt': 'x = 1\n'}
        for name in ('A_good', 'C_good'):
            write(root / name, files)
        write(root / 'B_toolarge', dict(files, **{'tests/f%04d.txt' % i: '.' for i in range(2050)}))
        patch = udiff('tests/sample.txt', 'x = 1\n', 'x = 2\n')
        return root, patch

    def test_per_base_error_recorded_and_next_base_checked(self):
        root, patch = self.bases_with_bad_middle()
        (root / 'in.patch').write_bytes(patch)
        r = H.check_submission(root / 'in.patch', {n: root / n for n in ('A_good', 'B_toolarge', 'C_good')}, root / 'out', [])
        rows = {b['name']: b for b in r['bases']}
        self.assertEqual(set(rows), {'A_good', 'B_toolarge', 'C_good'})
        self.assertEqual(rows['B_toolarge']['status'], 'ERROR')
        self.assertEqual(rows['C_good']['status'], 'CHECKED')
        self.assertIn({'code': 'base_limit', 'message': 'Source-tree resource limit exceeded', 'base': 'B_toolarge'},
                      [{k: f[k] for k in ('code', 'message', 'base') if k in f} for f in r['findings']])

    @unittest.skipUnless(V1.is_file(), 'Sol v1 not available')
    def test_v1_stopped_at_the_bad_base(self):
        v1 = load(V1, 's27_hygiene_v1b')
        root, patch = self.bases_with_bad_middle()
        (root / 'in.patch').write_bytes(patch)
        r = v1.check_submission(root / 'in.patch', {n: root / n for n in ('A_good', 'B_toolarge', 'C_good')}, root / 'out', [])
        self.assertNotIn('C_good', [b['name'] for b in r['bases']])


class S27_2_Refs(unittest.TestCase):
    def test_default_is_AL1(self):
        self.assertEqual(B.REFS, AL1)
        self.assertEqual(B.resolve_ref(), AL1)
        self.assertEqual(B.resolve_ref('AL1'), AL1)

    def test_named_json_and_explicit(self):
        self.assertEqual(B.resolve_ref('Lprime'), LPRIME)
        self.assertEqual(B.resolve_ref('B'), LPRIME)
        p = new_dir('ref') / 'pins.json'
        p.write_text(json.dumps({'11': 1, '13': 2}))
        self.assertEqual(B.resolve_ref(str(p)), {11: 1, 13: 2})
        self.assertEqual(B.resolve_ref('AL1', {11: 5}), {11: 5})
        for bad in ('nope', None):
            with self.assertRaises(ValueError):
                B.resolve_ref(bad)
        with self.assertRaises(ValueError):
            B.resolve_ref('AL1', {13: 5})

    def probe(self, d11, nodes):
        exe = new_dir('probe') / 'fixture_engine'
        exe.write_bytes(b'x')

        class Cap:
            def run(self, label, argv, stdin=None):
                if label.endswith('_first_d11') or label.endswith('_bench_11'):
                    return 0, b'info string bench depth 11 nodes %d time 1 nps 1\r\n' % d11, b''
                if label.endswith('_uci'):
                    return 0, b'id name F\r\nid author A\r\noption name Clear Hash type button\r\nuciok\r\n', b''
                return 0, b'00001 T main\n', b''
        return B._probe(exe, 'fixture', Cap(), nodes, [11])

    def test_probe_default_AL1_and_named_Lprime(self):
        self.assertEqual(self.probe(312866, B.resolve_ref())['status'], 'PASS')
        self.assertEqual(self.probe(308972, B.resolve_ref())['first_d11']['errors'], ['reference'])
        self.assertEqual(self.probe(308972, B.resolve_ref('Lprime'))['status'], 'PASS')

    def test_hygiene_defaults(self):
        import inspect
        sig = inspect.signature(H.check_submission)
        self.assertEqual(sig.parameters['ref'].default, 'AL1')
        self.assertEqual(sig.parameters['parallel'].default, 1)


class S27_3_ReviewedAndRelative(unittest.TestCase):
    PATCH = FIX / 'fc_sol_buffix_h256e12_vs_lock.patch'
    REVIEW = FIX / 'CR_PASS_sol_buffix_h256e12_samediff.txt'

    def run_buffix(self, **kw):
        out = new_dir('buffix') / 'out'
        return H.check_submission(self.PATCH, {'AL1': al1_export()}, out, [], **kw)

    def test_allowlist_loads_and_validates(self):
        entries = H.load_reviewed()
        self.assertEqual([e['patch_sha256'] for e in entries], [H.BUFFIX_SHA])
        self.assertEqual(entries[0]['review_record_sha256'], H.BUFFIX_REVIEW_SHA)
        bad = new_dir('allow') / 'bad.json'
        for doc in ({'schema': 'x', 'entries': []},
                    {'schema': 'forge_sol_S27_reviewed_bugfixes_v2', 'entries': [{'patch_sha256': 'a' * 64, 'review_record_sha256': 'b' * 64,
                                                                                   'scope': ['a'], 'default_code_allowed': ['b']}]}):
            bad.write_text(json.dumps(doc))
            with self.subTest(doc=doc), self.assertRaises(ValueError):
                H.load_reviewed(bad)

    def test_reviewed_buffix_passes_on_al1(self):
        r = self.run_buffix(control_role='reviewed_bugfix', review_record=self.REVIEW)
        self.assertEqual(r['status'], 'PASS', r['findings'])
        self.assertEqual(r['bases'][0]['control_role'], 'reviewed_bugfix:buffix_h256e12_node_identical')

    def test_alias_still_works(self):
        r = self.run_buffix(control_role='approved_buffix_control', review_record=self.REVIEW)
        self.assertEqual(r['status'], 'PASS', r['findings'])

    def test_unreviewed_buffix_is_flagged(self):
        r = self.run_buffix()
        self.assertEqual(r['status'], 'FAIL')
        self.assertIn('unguarded_default_code', {f['code'] for f in r['findings']})

    def test_wrong_review_record_rejected(self):
        r = self.run_buffix(control_role='reviewed_bugfix', review_record=FIX / 'fc_sol_buffix_h256e12_vs_lock.patch')
        self.assertIn('control_authority', {f['code'] for f in r['findings']})

    def test_relative_base_accepted(self):
        src = al1_export()
        cwd = os.getcwd()
        try:
            os.chdir(src.parent.parent)
            rel = os.path.join('.', src.parent.name, '..', src.parent.name, src.name)
            out = new_dir('rel') / 'out'
            r = H.check_submission(self.PATCH, {'AL1': rel}, out, [], control_role='reviewed_bugfix', review_record=self.REVIEW)
        finally:
            os.chdir(cwd)
        self.assertEqual(r['status'], 'PASS', r['findings'])

    @unittest.skipUnless(V1.is_file(), 'Sol v1 not available')
    def test_v1_rejected_the_relative_base(self):
        v1 = load(V1, 's27_hygiene_v1c')
        src = al1_export()
        cwd = os.getcwd()
        try:
            os.chdir(src.parent.parent)
            rel = os.path.join('.', src.parent.name, '..', src.parent.name, src.name)
            with self.assertRaises(ValueError):
                v1.check_submission(self.PATCH, {'AL1': rel}, new_dir('relv1') / 'out', [])
        finally:
            os.chdir(cwd)


if __name__ == '__main__':
    unittest.main()
