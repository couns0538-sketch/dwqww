"""Narrow pure-Python negatives; no network, package download/import or compiler."""
import argparse
from pathlib import Path
import unittest
import tempfile
import zipfile
import collect_wheels as c


class CollectionGuards(unittest.TestCase):
    def test_pip_source_environment_removed(self):
        dirty = {'PIP_EXTRA_INDEX_URL': 'https://untrusted.invalid', 'PIP_FIND_LINKS': 'F:/forbidden',
                 'PIP_TRUSTED_HOST': 'untrusted.invalid', 'pip_proxy': 'bad', 'PIP_CONFIG_FILE': 'C:/bad.ini',
                 'SYSTEMROOT': 'C:/Windows'}
        clean = c.pip_environment(dirty)
        self.assertNotIn('PIP_EXTRA_INDEX_URL', clean)
        self.assertNotIn('PIP_FIND_LINKS', clean)
        self.assertNotIn('PIP_TRUSTED_HOST', clean)
        self.assertNotIn('pip_proxy', clean)
        self.assertEqual(clean['PIP_CONFIG_FILE'], 'NUL')
        self.assertEqual(clean['SYSTEMROOT'], 'C:/Windows')

    def test_torch_changed_hash_refused(self):
        with self.assertRaisesRegex(ValueError, 'identity drift'):
            c.verify_torch_identity(Path(c.TORCH_NAME), {'version': '2.9.1+cpu'}, 'bad', 12,
                                    {'sha256': 'good', 'bytes': 12})

    def test_torch_changed_size_refused(self):
        with self.assertRaisesRegex(ValueError, 'identity drift'):
            c.verify_torch_identity(Path(c.TORCH_NAME), {'version': '2.9.1+cpu'}, 'good', 13,
                                    {'sha256': 'good', 'bytes': 12})

    def test_torch_matching_receipt_accepts(self):
        c.verify_torch_identity(Path(c.TORCH_NAME), {'version': '2.9.1+cpu'}, 'good', 12,
                                {'sha256': 'good', 'bytes': 12})

    def test_vendored_metadata_does_not_replace_root(self):
        with tempfile.TemporaryDirectory(dir=c.RUNTIME / 'tmp') as directory:
            archive = Path(directory) / 'fixture.whl'
            with zipfile.ZipFile(archive, 'w') as stream:
                stream.writestr('fixture-1.dist-info/METADATA', 'Name: fixture\nVersion: 1\n')
                stream.writestr('fixture/vendor/vendor-2.dist-info/METADATA', 'Name: vendor\nVersion: 2\n')
            self.assertEqual(c.metadata(archive)['name'], 'fixture')

    def test_only_vendored_metadata_refused(self):
        with tempfile.TemporaryDirectory(dir=c.RUNTIME / 'tmp') as directory:
            archive = Path(directory) / 'fixture.whl'
            with zipfile.ZipFile(archive, 'w') as stream:
                stream.writestr('fixture/vendor/vendor-2.dist-info/METADATA', 'Name: vendor\nVersion: 2\n')
            with self.assertRaisesRegex(ValueError, 'one root METADATA'):
                c.metadata(archive)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--threads', type=int, choices=[1], required=True)
    parser.parse_args()
    p = c.base.psutil.Process()
    c.need(p.nice() == c.base.psutil.IDLE_PRIORITY_CLASS and p.cpu_affinity() == [3], 'Idle CPU3 required')
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CollectionGuards))
    raise SystemExit(0 if result.wasSuccessful() else 1)
