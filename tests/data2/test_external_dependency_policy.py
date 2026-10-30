"""Original regression for explicit external GPL tool opt-in and isolation."""
import json, pathlib, subprocess, sys, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
FETCH=ROOT/'tools/data2/fetch_binpack_dependency.py'

class ExternalPolicy(unittest.TestCase):
    def test_manifest_discloses_gpl_transitive_code(self):
        m=json.loads((ROOT/'tools/data2/binpack_dependency_manifest.json').read_text())
        self.assertEqual(m.get('effective_tool_license'), 'GPL-3.0')
        self.assertIn('GPL', m['files']['nodchip.h']['license'])
        self.assertFalse(m.get('enabled_by_default', True))
    def test_fetch_requires_explicit_license_opt_in_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=pathlib.Path(tmp)/'external'
            p=subprocess.run([sys.executable,str(FETCH),'--out',str(dest)],capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0)
            self.assertIn('--accept-gpl3',p.stderr)
            self.assertFalse(dest.exists())
    def test_fetch_rejects_repository_directory_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=pathlib.Path(tmp); (repo/'.git').write_text('gitdir: /somewhere')
            dest=repo/'external'
            p=subprocess.run([sys.executable,str(FETCH),'--accept-gpl3','--out',str(dest)],capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0)
            self.assertIn('outside',p.stderr)
            self.assertFalse(dest.exists())
    def test_fetch_rejects_symlink_into_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=pathlib.Path(tmp); repo=base/'repo'; repo.mkdir();(repo/'.git').mkdir()
            (base/'alias').symlink_to(repo,target_is_directory=True)
            p=subprocess.run([sys.executable,str(FETCH),'--accept-gpl3','--out',str(base/'alias'/'deps')],capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0); self.assertIn('outside',p.stderr)
            self.assertFalse((repo/'deps').exists())

if __name__=='__main__': unittest.main()
