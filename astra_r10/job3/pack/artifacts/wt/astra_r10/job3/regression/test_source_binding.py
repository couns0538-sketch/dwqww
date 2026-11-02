"""Local identity fixtures only: no external NPT import or training. UNPROVEN."""
import importlib.util
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('r10_regression', HERE/'run_regression.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class SourceBindingTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='binding-', dir=os.environ['TEMP']))
        for name in (*runner.NPT_SOURCE_TREES, 'build'):
            (self.root/name).mkdir()
        self.source = self.root/'model/example.py'
        self.source.write_text('value = 1\n', encoding='utf8')
        self.dll = self.root/'build/libtraining_data_loader.dll'
        self.dll.write_bytes(b'identity fixture only; never loaded')
        self.old_root, self.old_dll = runner.NPT, runner.DLL
        runner.NPT, runner.DLL = self.root, self.dll
        self.name = '_r10_bound_fixture'

    def tearDown(self):
        sys.modules.pop(self.name, None)
        runner.NPT, runner.DLL = self.old_root, self.old_dll
        # Fixtures remain as evidence; no recursive removal.

    def imported(self, path):
        sys.modules[self.name] = types.SimpleNamespace(__file__=str(path))

    def test_late_import_of_prebound_source_is_covered(self):
        bound = runner.prebind_npt_sources()
        self.imported(self.source)
        self.assertIn(str(self.source.resolve()), runner.verify_npt_binding(bound))

    def test_late_unbound_import_refused(self):
        bound = runner.prebind_npt_sources()
        extra = self.root/'unbound.bin'
        extra.write_bytes(b'not a declared Python source')
        self.imported(extra)
        with self.assertRaisesRegex(ValueError, 'not bound before import'):
            runner.verify_npt_binding(bound)

    def test_changed_imported_source_refused(self):
        bound = runner.prebind_npt_sources()
        self.source.write_text('value = 2\n', encoding='utf8')
        self.imported(self.source)
        with self.assertRaisesRegex(ValueError, 'differs from pre-import'):
            runner.verify_npt_binding(bound)

    def test_changed_unimported_source_refused(self):
        bound = runner.prebind_npt_sources()
        self.source.write_text('value = 2\n', encoding='utf8')
        with self.assertRaisesRegex(ValueError, 'source set or bytes changed'):
            runner.verify_npt_binding(bound)

    def test_changed_dll_refused(self):
        bound = runner.prebind_npt_sources()
        self.dll.write_bytes(b'changed library bytes')
        with self.assertRaisesRegex(ValueError, 'differs from pre-import'):
            runner.verify_npt_binding(bound)

    def test_new_source_set_refused(self):
        bound = runner.prebind_npt_sources()
        (self.root/'trainer/added.py').write_text('new = True\n', encoding='utf8')
        with self.assertRaisesRegex(ValueError, 'source set or bytes changed'):
            runner.verify_npt_binding(bound)

    def test_unbound_cached_bytecode_refused(self):
        bound = runner.prebind_npt_sources()
        cache = self.root/'model/existing.pyc'
        cache.write_bytes(b'preexisting cached code')
        self.imported(cache)
        with self.assertRaisesRegex(ValueError, 'not bound before import'):
            runner.verify_npt_binding(bound)


class PrivateRuntimeBindingTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(tempfile.mkdtemp(prefix='runtime-binding-',dir=os.environ['TEMP']))
        for name in runner.runtime_binding.TREES:
            (self.root/name).mkdir()
            (self.root/name/'fixture.bin').write_bytes(name.encode())
        self.record={'schema':1,'status':'RUNTIME_ASSEMBLED','root':str(self.root),
            'files':[{'path':path.relative_to(self.root).as_posix(),'bytes':path.stat().st_size,
                      'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
                     for path in self.root.glob('*/*.bin')]}
        self.publish()

    def publish(self):
        self.manifest=self.root/'RUNTIME_FILES.json'
        self.manifest.write_text(json.dumps(self.record),encoding='utf8')
        self.sha=hashlib.sha256(self.manifest.read_bytes()).hexdigest()

    def test_exact_assembled_runtime_accepted(self):
        self.assertEqual(runner.runtime_binding.verify(self.root,self.sha)['files'],3)

    def test_changed_runtime_file_refused(self):
        (self.root/'packages/fixture.bin').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'differs from assembled manifest'):
            runner.runtime_binding.verify(self.root,self.sha)

    def test_extra_runtime_file_refused(self):
        (self.root/'python/new.py').write_text('value=1',encoding='utf8')
        with self.assertRaisesRegex(ValueError,'file set differs'):
            runner.runtime_binding.verify(self.root,self.sha)

    def test_manifest_identity_mismatch_refused(self):
        with self.assertRaisesRegex(ValueError,'SHA256 differs'):
            runner.runtime_binding.verify(self.root,'0'*64)

    def test_runtime_path_escape_refused(self):
        self.record['files'][0]['path']='python/../escape.bin'
        self.publish()
        with self.assertRaisesRegex(ValueError,'escaped explicit input trees'):
            runner.runtime_binding.verify(self.root,self.sha)

    def test_duplicate_runtime_identity_refused(self):
        self.record['files'].append(dict(self.record['files'][0]))
        self.publish()
        with self.assertRaisesRegex(ValueError,'duplicate runtime'):
            runner.runtime_binding.verify(self.root,self.sha)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--threads', type=int, choices=[1], required=True)
    parser.add_argument('--out',type=Path,required=True)
    arguments=parser.parse_args()
    evidence=arguments.out.resolve()
    if not evidence.is_relative_to(Path('D:/a10/job3/regression-runs')):
        raise ValueError('fresh owned output outside Git required')
    evidence.mkdir(parents=True,exist_ok=False)
    os.environ['TEMP']=str(evidence)
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(case)
                            for case in (SourceBindingTests,PrivateRuntimeBindingTests)])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    receipt = {'tests':result.testsRun, 'failures':len(result.failures), 'errors':len(result.errors),
        'skipped':len(result.skipped), 'scope':'local original identity fixtures; external NPT never imported',
        'runner':runner.identity(HERE/'run_regression.py')}
    target = Path(os.environ['TEMP'])/'RESULT.json'
    with target.open('x', encoding='utf8') as stream:
        json.dump(receipt, stream, indent=2)
    raise SystemExit(0 if result.wasSuccessful() else 1)
