from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from seal_pack import seal
from verify_pack import verify
import verify_pack

class PackTests(unittest.TestCase):
    def fixture(self,root):
        (root/'REPORT.md').write_text('Game provenance: UNVERIFIED\n',encoding='utf-8')
        (root/'sub').mkdir()
        (root/'sub'/'receipt.json').write_text('{}',encoding='utf-8')
        seal(root)

    def test_roundtrip_does_not_reclassify_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.fixture(root)
            self.assertEqual(verify(root)['payloads'],2)
            self.assertIn('UNVERIFIED',(root/'REPORT.md').read_text())
            with self.assertRaises(FileExistsError):
                seal(root)

    def test_changed_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.fixture(root)
            (root/'sub'/'receipt.json').write_text('{"changed":true}')
            with self.assertRaisesRegex(ValueError,'checksum'):
                verify(root)

    def test_missing_extra_and_duplicate_manifest(self):
        for mode in ('missing','extra','duplicate'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                self.fixture(root)
                if mode=='missing':
                    (root/'sub'/'receipt.json').unlink()
                elif mode=='extra':
                    (root/'extra.txt').write_text('x')
                else:
                    path=root/'SHA256SUMS'
                    path.write_text(path.read_text()+path.read_text().splitlines()[0]+'\n')
                with self.assertRaises(ValueError):
                    verify(root)

    def test_mutation_during_verification_is_detected(self):
        for mode in ('new_payload','manifest'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                self.fixture(root)
                changed=False
                original=verify_pack.free_guard
                def mutate(*args):
                    nonlocal changed
                    if not changed:
                        changed=True
                        if mode=='new_payload':
                            (root/'late.txt').write_text('late payload')
                        else:
                            path=root/'SHA256SUMS'
                            path.write_text(path.read_text().replace('  REPORT.md','  WRONG.md'))
                    return original(*args)
                with patch.object(verify_pack,'free_guard',side_effect=mutate):
                    with self.assertRaisesRegex(ValueError,'changed|census'):
                        verify(root)

if __name__=='__main__':
    unittest.main()
