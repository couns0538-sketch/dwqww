"""Synthetic restoration safety tests; never read/copy real engine evidence."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('restore20', ROOT / 'restore_new_scratch.py')
restore20 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(restore20)
SHA = lambda data: hashlib.sha256(data).hexdigest()


class RecoverySafety(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='forge20-archive-prep-')
        self.base = Path(self.temp.name)
        self.parts = self.base / 'parts'; self.parts.mkdir()
        self.destination = self.base / 'recovered-new'

    def tearDown(self):
        self.temp.cleanup()

    def fixture(self, name='payload/test-source/engine', mode=0o700, extra=None):
        raw = b'not an executable; synthetic byte fixture\n'
        row = {'group': 'fixture', 'original': '/must-not-write-here/engine', 'payload_path': name,
               'size': len(raw), 'sha256': SHA(raw), 'mode': mode, 'mtime_ns': 1600000000123456789}
        directories = [{'group': 'fixture', 'original': '/must-not-write-here',
                        'payload_path': 'payload/test-source', 'mode': 0o750}]
        modes = json.dumps({'files': [row], 'directories': directories}).encode()
        payload = {name: raw, 'archive-provenance/LIVE-FILES-AND-MODES.json': modes}
        if extra: payload.update(extra)
        files = [{'path': n, 'size': len(b), 'sha256': SHA(b)} for n, b in sorted(payload.items())]
        target = io.BytesIO()
        with zipfile.ZipFile(target, 'w') as z:
            for n, b in payload.items(): z.writestr('files/' + n, b)
            z.writestr('manifest.json', json.dumps({'schema_version': 1, 'files': files}))
        combined = target.getvalue()
        (self.parts / 'fixture.zip').write_bytes(combined)
        manifest = {'schema_version': 1, 'format': 'raw-split-zip', 'split_size': 67108864,
                    'manifest_member': 'manifest.json', 'archive': {'file': 'fixture.zip', 'size': len(combined), 'sha256': SHA(combined)},
                    'parts': [{'file': 'fixture.zip', 'size': len(combined), 'sha256': SHA(combined)}], 'files': files}
        data = json.dumps(manifest).encode(); (self.parts / restore20.NAME).write_bytes(data)
        return SHA(data), raw, row

    def test_new_scratch_restores_exact_bytes_and_permissions(self):
        digest, raw, row = self.fixture()
        result = restore20.restore(self.parts, self.destination, digest)
        target = self.destination / 'files' / row['payload_path']
        self.assertEqual(target.read_bytes(), raw)
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o700)
        self.assertEqual(target.stat().st_mtime_ns, row['mtime_ns'])
        self.assertEqual(stat.S_IMODE(target.parent.stat().st_mode), 0o750)
        self.assertEqual(result['original_file_modes_restored'], 1)
        self.assertFalse(result['original_absolute_paths_written'])

    def test_existing_destination_rejected_and_kept(self):
        digest, _, _ = self.fixture(); self.destination.mkdir()
        marker = self.destination / 'keep'; marker.write_bytes(b'keep')
        with self.assertRaisesRegex(ValueError, 'NEW'): restore20.restore(self.parts, self.destination, digest)
        self.assertEqual(marker.read_bytes(), b'keep')

    def test_symlink_destination_rejected(self):
        digest, _, _ = self.fixture(); self.destination.symlink_to(self.base / 'nonexistent')
        with self.assertRaisesRegex(ValueError, 'NEW'): restore20.restore(self.parts, self.destination, digest)
        self.assertTrue(self.destination.is_symlink())

    def test_bad_external_manifest_rejected_before_creation(self):
        self.fixture()
        with self.assertRaisesRegex(ValueError, 'manifest SHA256'): restore20.restore(self.parts, self.destination, '0' * 64)
        self.assertFalse(self.destination.exists())

    def test_bad_part_rejected_before_creation(self):
        digest, _, _ = self.fixture(); p = self.parts / 'fixture.zip'; p.write_bytes(p.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, 'Part integrity'): restore20.restore(self.parts, self.destination, digest)
        self.assertFalse(self.destination.exists())

    def test_traversal_rejected_before_creation(self):
        digest, _, _ = self.fixture(name='../escape')
        with self.assertRaisesRegex(ValueError, 'Unsafe payload'): restore20.restore(self.parts, self.destination, digest)
        self.assertFalse(self.destination.exists())

    def test_setuid_mode_rejected_before_creation(self):
        digest, _, _ = self.fixture(mode=0o4700)
        with self.assertRaisesRegex(ValueError, 'Unsafe file mode'): restore20.restore(self.parts, self.destination, digest)
        self.assertFalse(self.destination.exists())

    def test_relative_destination_rejected(self):
        digest, _, _ = self.fixture()
        with self.assertRaisesRegex(ValueError, 'absolute'): restore20.restore(self.parts, Path('unsafe-relative'), digest)


if __name__ == '__main__':
    unittest.main(verbosity=2)
