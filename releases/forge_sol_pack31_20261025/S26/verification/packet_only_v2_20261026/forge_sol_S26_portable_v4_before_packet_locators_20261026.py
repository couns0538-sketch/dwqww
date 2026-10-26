"""Relocated packet setup and SYNTHETIC process integration; no genuine build."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SETUP = HERE / 'forge_sol_S26_setup_local_dependencies_20261026.py'
LAUNCHER = HERE / 'forge_sol_S26_run_v4_20261026.sh'
FIXTURE = HERE / 'successor_ctest_v4/test_forge_sol_S26_netbatch_v4_20261026.py'
FIXTURE_SHA = '39d9a2ce759c2e9be2c98c7ea53910f21b5e6526db0862ddbb06b3c03dbf0e2c'
V4_SHA = '4dbf73e63032d7512c6beff12fdca03b7d29e1489b6d0ae3cab26b09753ac36f'
DEPS_SHA = '8a719c05c2e94b918c3e9b70fdc8b03036ffa23488748b848d5baa0541472744'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class PortableKitTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SETUP.is_file(), 'portable setup missing: initial RED')
        self.assertTrue(LAUNCHER.is_file(), 'v4 launcher missing: initial RED')
        temp = tempfile.TemporaryDirectory(prefix='SYNTHETIC relocated packet ', dir=HERE)
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.packet = self.root / 'packet with spaces'
        self.s26 = self.packet / 'S26'
        self.s26.mkdir(parents=True)
        source_deps = HERE / 'forge_sol_S26_dependencies_20261026.json'
        self.assertEqual(sha(source_deps), DEPS_SHA)
        self.declarations = json.loads(source_deps.read_text())
        shutil.copy2(source_deps, self.s26 / source_deps.name)
        for key, record in self.declarations.items():
            self.assertEqual(sha(record['path']), record['sha256'])
            target = self.packet / 'provided_tools' / key / Path(record['path']).name
            target.parent.mkdir(parents=True)
            shutil.copy2(record['path'], target)
        v4 = HERE / 'successor_ctest_v4/forge_sol_S26_netbatch_v4_20261026.py'
        self.assertEqual(sha(v4), V4_SHA)
        self.v4 = self.s26 / 'successor_ctest_v4' / v4.name
        self.v4.parent.mkdir()
        shutil.copy2(v4, self.v4)
        shutil.copy2(SETUP, self.s26 / SETUP.name)
        shutil.copy2(LAUNCHER, self.s26 / LAUNCHER.name)
        self.out = self.s26 / 'owner local dependencies.json'
        self.lock = self.s26 / 'owner local resource.lock'

    def setup_command(self, out=None, lock=None):
        return [sys.executable, '-B', str(self.s26 / SETUP.name), '--packet-root', str(self.packet),
                '--out', str(out or self.out), '--lock-file', str(lock or self.lock)]

    def run_setup(self, **kwargs):
        return subprocess.run(self.setup_command(**kwargs), cwd='/', capture_output=True, text=True, timeout=10)

    def before(self):
        return {str(p.relative_to(self.packet)): sha(p) for p in self.packet.rglob('*') if p.is_file()}

    def test_relocated_setup_maps_exact_helpers_and_preserves_all_originals(self):
        before = self.before()
        run = self.run_setup()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        local = json.loads(self.out.read_text())
        self.assertEqual(set(local), {'screen', 'fma', 'pins', 'recipe'})
        for key, record in local.items():
            path = self.packet / 'provided_tools' / key / Path(self.declarations[key]['path']).name
            self.assertEqual(record, {'path': str(path), 'sha256': self.declarations[key]['sha256']})
            self.assertEqual(sha(path), record['sha256'])
        self.assertEqual(self.lock.read_bytes(), b'')
        after = self.before()
        for path, digest in before.items():
            self.assertEqual(after[path], digest)
        self.assertEqual(set(after) - set(before), {str(self.out.relative_to(self.packet)), str(self.lock.relative_to(self.packet))})

    def test_wrong_helper_hash_fails_before_either_output_is_created(self):
        item = self.declarations['screen']
        (self.packet / 'provided_tools/screen' / Path(item['path']).name).write_text('SYNTHETIC wrong helper')
        run = self.run_setup()
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('SHA256', run.stderr)
        self.assertFalse(self.out.exists())
        self.assertFalse(self.lock.exists())

    def test_wrong_delivered_v4_and_original_declarations_fail_before_writes(self):
        for path in [self.v4, self.s26 / 'forge_sol_S26_dependencies_20261026.json']:
            with self.subTest(path=path.name):
                original = path.read_bytes()
                path.write_bytes(original + b'\n')
                run = self.run_setup()
                self.assertNotEqual(run.returncode, 0)
                self.assertFalse(self.out.exists())
                self.assertFalse(self.lock.exists())
                path.write_bytes(original)

    def test_existing_output_or_lock_is_never_changed_and_no_peer_created(self):
        for existing, peer in [(self.out, self.lock), (self.lock, self.out)]:
            with self.subTest(existing=existing.name):
                existing.write_text('OWNER ORIGINAL')
                run = self.run_setup()
                self.assertNotEqual(run.returncode, 0)
                self.assertEqual(existing.read_text(), 'OWNER ORIGINAL')
                self.assertFalse(peer.exists())
                existing.unlink()

    def test_output_escape_and_symlink_parent_fail_before_writes(self):
        escape = self.root / 'outside.json'
        run = self.run_setup(out=escape)
        self.assertNotEqual(run.returncode, 0)
        self.assertFalse(escape.exists())
        self.assertFalse(self.lock.exists())
        link = self.s26 / 'symlink parent'
        link.symlink_to(self.s26, target_is_directory=True)
        run = self.run_setup(out=link / 'deps.json')
        self.assertNotEqual(run.returncode, 0)
        self.assertFalse(self.lock.exists())

    def test_new_shell_launcher_runs_reused_actual_fake_process_fixture(self):
        # Changing path mapping, dropping argv, or launching old v3 must fail.
        self.assertEqual(sha(FIXTURE), FIXTURE_SHA)
        copied_fixture = self.v4.parent / FIXTURE.name
        shutil.copy2(FIXTURE, copied_fixture)
        spec = importlib.util.spec_from_file_location('original_s26_fixture', copied_fixture)
        fixture_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fixture_module)
        suite = self.packet / 'provided_inputs/WAC300_original.epd'
        suite.parent.mkdir()
        shutil.copy2('/workspace/forge-sol-next-20261024/int16-review/wac300.epd', suite)
        setup = self.run_setup()
        self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)
        fixture_module.TOOL = self.v4
        fixture_module.DEPS = self.out
        fixture_module.WAC = suite
        fixture = fixture_module.NetBatchTests(methodName='runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        base, candidate_a, candidate_b, _ = fixture.fixture()
        args = list(fixture.args)
        args[args.index('--lock-file') + 1] = str(self.lock)
        # This is a path/argv integration case, not the original timeout test.
        # Allow scheduling headroom at nice19 while preserving the fixture bytes.
        args[args.index('--timeout') + 1] = '15'
        before = {str(p): sha(p) for p in base.rglob('*') if p.is_file()}
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH='/workspace/.cloud-setup/venv/lib/python3.12/site-packages')
        run = subprocess.run(['/bin/sh', str(self.s26 / LAUNCHER.name), *args, '--compare-lock', str(base)],
                             cwd='/', env=env, capture_output=True, text=True, timeout=120)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        result = json.loads((fixture.root / 'output/result.json').read_text())
        self.assertEqual(result['tool_sha256'], V4_SHA)
        self.assertEqual(result['evidence_kind'], 'SYNTHETIC')
        self.assertEqual(len(result['nets']), 2)
        self.assertEqual(result['compare_lock']['bench']['22'], 122)
        self.assertEqual([row['bench']['11'] for row in result['nets']], [111, 211])
        for row, net in zip(result['nets'], [candidate_a, candidate_b]):
            self.assertEqual(row['wac']['evaluated'], 300)
            self.assertEqual(row['ctest']['status'], 'PASS')
            self.assertEqual(row['fma']['fma_count'], 0)
            self.assertEqual((Path(row['private_source']) / 'src/nnue_weights.inc').read_bytes(), net.read_bytes())
        self.assertEqual(before, {str(p): sha(p) for p in base.rglob('*') if p.is_file()})
        self.assertEqual(self.lock.read_bytes(), b'')
        self.assertEqual(sha(self.v4), V4_SHA)
        self.assertLess(sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file()), 1024 * 1024,
                        'relocated SYNTHETIC fixture exceeded1MiB')


if __name__ == '__main__':
    unittest.main()
