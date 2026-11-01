"""Packaging tests use source fixtures, never builds or engine processes."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch as mock_patch

sys.path.insert(0, str(Path(__file__).parent))
try:
    import package_lock_candidate as package
except ModuleNotFoundError:
    package = None


class AvailabilityTest(unittest.TestCase):
    def test_actual_lock_packager_exists(self):
        self.assertIsNotNone(package, 'actual-lock source packager is not implemented')


@unittest.skipIf(package is None, 'packager not implemented')
class SourcePackagingTests(unittest.TestCase):
    def fixture(self, root):
        blobs = {'src/main.cpp': b'old\n', 'README.md': b'base\n'}
        expected = {'src/main.cpp': b'new\n', 'README.md': b'base\n', 'src/tm.hpp': b'model\n'}
        stage = root / 'stage'
        for name, data in expected.items():
            path = stage / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        (stage / 'build.exe').write_bytes(b'not source')
        (stage / 'receipt.json').write_text('{}')
        patch = root / 'change.patch'
        patch.write_bytes(b'diff --git a/src/main.cpp b/src/main.cpp\n'
                          b'--- a/src/main.cpp\n+++ b/src/main.cpp\n@@ -1 +1 @@\n-old\n+new\n'
                          b'diff --git a/src/tm.hpp b/src/tm.hpp\nnew file mode 100644\n'
                          b'--- /dev/null\n+++ b/src/tm.hpp\n@@ -0,0 +1 @@\n+model\n')
        return blobs, expected, stage, patch

    def full_fixture(self, root):
        blobs, expected, stage, patch = self.fixture(root)
        for i in range(73):
            name = f'fixture/{i}.txt'
            blobs[name] = expected[name] = b'source\n'
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b'source\n')
        extra = 'tests/tmfit_tests.cpp'
        expected[extra] = b'test\n'
        (stage / 'tests').mkdir()
        (stage / extra).write_bytes(b'test\n')
        patch.write_bytes(patch.read_bytes() + b'diff --git a/tests/tmfit_tests.cpp b/tests/tmfit_tests.cpp\n'
            b'new file mode 100644\n--- /dev/null\n+++ b/tests/tmfit_tests.cpp\n@@ -0,0 +1 @@\n+test\n')
        return blobs, expected, stage, patch

    def test_archive_is_deterministic_and_preserves_exact_blob_bytes(self):
        files = {'z.cpp': b'line\n', 'a.hpp': b'unchanged\r\n'}
        first = package.source_tar(files)
        self.assertEqual(first, package.source_tar(dict(reversed(list(files.items())))))
        with tarfile.open(fileobj=io.BytesIO(first)) as archive:
            self.assertEqual(archive.getnames(), ['a.hpp', 'z.cpp'])
            for member in archive:
                self.assertEqual(member.mtime, 0)
                self.assertEqual(member.uid, 0)
                self.assertEqual(member.gid, 0)
                self.assertEqual(archive.extractfile(member).read(), files[member.name])

    def test_patch_is_checked_applied_and_compared_to_stage_ignoring_extras(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blobs, expected, stage, patch = self.fixture(root)
            actual, receipt = package.apply_verify(blobs, patch, root / 'new-scratch', stage, set(expected))
            self.assertEqual(actual, expected)
            self.assertEqual([r['exit_code'] for r in receipt['commands']], [0, 0])
            self.assertEqual(receipt['stage_match_files'], 3)
            self.assertNotIn('build.exe', actual)
            self.assertNotIn('receipt.json', actual)

    def test_changed_stage_and_unexpected_patch_source_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blobs, expected, stage, patch = self.fixture(root)
            (stage / 'src/tm.hpp').write_bytes(b'other model\n')
            with self.assertRaisesRegex(ValueError, 'stage source mismatch'):
                package.apply_verify(blobs, patch, root / 'changed-stage', stage, set(expected))
            with self.assertRaisesRegex(ValueError, 'unexpected source paths'):
                package.apply_verify(blobs, patch, root / 'unexpected-source', stage, set(blobs))

    def test_preexisting_scratch_and_unsafe_archive_path_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blobs, expected, stage, patch = self.fixture(root)
            scratch = root / 'exists'
            scratch.mkdir()
            witness = scratch / 'keep.log'
            witness.write_bytes(b'original')
            with self.assertRaises(FileExistsError):
                package.apply_verify(blobs, patch, scratch, stage, set(expected))
            self.assertEqual(witness.read_bytes(), b'original')
            for name in ('../escape', '/absolute', 'C:/drive', 'src\\backslash'):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    package.source_tar({name: b'x'})

    def test_candidate_identity_binds_base_patch_and_all_source_files(self):
        first = package.candidate_identity('a' * 40, 'b' * 64, {'a.cpp': b'a\n'})
        self.assertEqual(first, package.candidate_identity('a' * 40, 'b' * 64, {'a.cpp': b'a\n'}))
        changed = package.candidate_identity('a' * 40, 'b' * 64, {'a.cpp': b'b\n'})
        self.assertNotEqual(first['candidate_id'], changed['candidate_id'])
        self.assertEqual(first['base_commit'], 'a' * 40)
        self.assertNotIn('head', json.dumps(first).lower())

    def test_missing_checks_stay_unverified_and_native_pass_needs_exact_identity(self):
        identity = package.candidate_identity('a' * 40, 'b' * 64, {'a': b'x'})
        checks = package.validate_declarations({}, identity)
        self.assertTrue(checks)
        self.assertTrue(all(c['status'] == 'UNVERIFIED' for c in checks))
        evidence = {'path': 'native.json', 'sha256': 'c' * 64}
        bad = {'candidate_id': 'wrong', 'checks': [
            {'name': '1_off_on_bench_and_perft', 'status': 'PASS', 'evidence': evidence}]}
        with self.assertRaisesRegex(ValueError, 'candidate_id'):
            package.validate_declarations(bad, identity)
        bad['candidate_id'] = identity['candidate_id']
        good = package.validate_declarations(bad, identity)
        self.assertEqual(good[0]['status'], 'PASS')
        self.assertTrue(any(c['status'] == 'UNVERIFIED' for c in good))

    def test_sealing_checks_expected_hash_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'native.log'
            source.write_bytes(b'actual bytes\n')
            output = root / 'out'
            output.mkdir()
            bad = {'path': 'native.log', 'sha256': '0' * 64}
            with self.assertRaisesRegex(ValueError, 'producer SHA256 mismatch'):
                package.copy_evidence(bad, root, output, 0)
            good = {'path': 'native.log', 'sha256': package.sha(source.read_bytes())}
            sealed = package.copy_evidence(good, root, output, 0)
            self.assertEqual((output / sealed['path']).read_bytes(), source.read_bytes())
            with self.assertRaises(FileExistsError):
                package.copy_evidence(good, root, output, 0)

    @unittest.skipUnless(package and package.DEFAULT_CHECKER.is_file(), 'installed evidence checker unavailable')
    def test_complete_draft_packages_only_sources_and_checker_reports_unverified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Production candidate adds two paths; the tiny fixture exercises
            # the same75->77 cardinality contract without a real engine source.
            blobs, expected, stage, patch = self.full_fixture(root)
            output = root / 'package'
            args = ['--repo', str(root), '--stage', str(stage), '--patch', str(patch),
                    '--scratch', str(root / 'fresh'), '--output', str(output)]
            with mock_patch.object(package, 'git_source', return_value=blobs), \
                 mock_patch.object(package, 'CR_PATCH_SHA256', package.sha(patch.read_bytes())), \
                 mock_patch.object(package, 'NEW_FILES', {'src/tm.hpp', 'tests/tmfit_tests.cpp'}), \
                 mock_patch('sys.stdout', new_callable=io.StringIO):
                result = package.main(args)
                self.assertEqual(result, 1)
                with self.assertRaises(FileExistsError):
                    package.main(args)
            record = json.loads((output / 'record.json').read_text())
            self.assertEqual(record['candidate']['commit'], package.BASE)
            self.assertIn('Base anchor only', record['candidate']['commit_semantics'])
            report = json.loads((output / 'checker.stdout.json').read_text())
            self.assertEqual(report['status'], 'FAIL')
            self.assertTrue(all(item['status'] == 'PASS' for item in report['artifacts']))
            self.assertEqual(sum(check['status'] == 'UNVERIFIED' for check in record['checks']), 8)
            execution = json.loads((output / 'execution.json').read_text())
            self.assertEqual(execution['qualification_status'], 'UNVERIFIED')
            with tarfile.open(output / 'candidate-source.tar') as archive:
                self.assertEqual(set(archive.getnames()), set(expected))
                self.assertEqual(len(archive.getnames()), 77)

    @unittest.skipUnless(package and package.DEFAULT_CHECKER.is_file(), 'installed evidence checker unavailable')
    def test_declarations_are_read_once_and_exact_bytes_survive_input_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blobs, expected, stage, patch = self.full_fixture(root)
            declaration = root / 'declaration.json'
            original = b'\xef\xbb\xbf{ "checks": [] }\r\n'
            mutated = b'{"checks":[{"name":"later", "status":"FAIL"}]}\n'
            declaration.write_bytes(original)
            output = root / 'package'
            args = ['--repo', str(root), '--stage', str(stage), '--patch', str(patch),
                    '--scratch', str(root / 'fresh'), '--output', str(output), '--input', str(declaration)]
            real_run = subprocess.run

            def mutate_during_checker(command, **kwargs):
                if len(command) > 1 and command[1] == str(package.DEFAULT_CHECKER.resolve()):
                    declaration.write_bytes(mutated)
                return real_run(command, **kwargs)

            with mock_patch.object(package, 'git_source', return_value=blobs), \
                 mock_patch.object(package, 'CR_PATCH_SHA256', package.sha(patch.read_bytes())), \
                 mock_patch.object(package, 'NEW_FILES', {'src/tm.hpp', 'tests/tmfit_tests.cpp'}), \
                 mock_patch.object(package, 'stable_read', wraps=package.stable_read) as reads, \
                 mock_patch.object(package.subprocess, 'run', side_effect=mutate_during_checker), \
                 mock_patch('sys.stdout', new_callable=io.StringIO):
                self.assertEqual(package.main(args), 1)
            execution = json.loads((output / 'execution.json').read_text())
            self.assertEqual(declaration.read_bytes(), mutated)
            self.assertEqual(execution['input_sha256'], package.sha(original))
            self.assertEqual((output / 'declarations.json').read_bytes(), original)
            self.assertEqual(sum(call.args[0] == declaration for call in reads.call_args_list), 1)
            record = json.loads((output / 'record.json').read_text())
            refs = [ref for ref in record['candidate']['artifacts'] if ref['path'] == 'declarations.json']
            self.assertEqual(refs, [{'path': 'declarations.json', 'sha256': package.sha(original)}])
            self.assertFalse(record['producer_identity_audit']['automatic_verification'])
            self.assertIn('Main agent and Code Review', record['producer_identity_audit']['required_review'])
            self.assertFalse(execution['producer_identity_audit']['automatic_verification'])


@unittest.skipUnless(package and os.environ.get('FORGE_TMFIT_REAL_PATCH') == '1',
                     'set FORGE_TMFIT_REAL_PATCH=1 for exact75-blob/CR applicability check')
class ActualLockSourceTests(unittest.TestCase):
    def test_actual_lock_and_supplied_cr_patch_match_frozen_stage(self):
        repo = Path(__file__).resolve().parents[2]
        stage = Path(os.environ['FORGE_TMFIT_CR_STAGE'])
        patch = Path(os.environ.get('FORGE_TMFIT_CR_PATCH', str(repo / 'astra_r8/tmfit/cr_fixes/tmfit_lockport.patch')))
        self.assertEqual(package.sha(patch.read_bytes()), package.CR_PATCH_SHA256)
        blobs = package.git_source(repo, package.BASE)
        self.assertEqual(len(blobs), 75)
        self.assertFalse(any(b'\r\n' in blob for blob in blobs.values()))
        with tempfile.TemporaryDirectory() as tmp:
            actual, receipt = package.apply_verify(blobs, patch, Path(tmp) / 'fresh', stage,
                                                   set(blobs) | package.NEW_FILES)
        self.assertEqual(len(actual), 77)
        self.assertEqual(receipt['stage_match_files'], 77)


if __name__ == '__main__':
    unittest.main()
