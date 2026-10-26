import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('prepare', Path(__file__).with_name('forge_sol_S09_prepare_source_view_20261026.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class SourceViewTests(unittest.TestCase):
    def test_patch_targets_are_owned_and_large_unchanged_input_is_a_link(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);src=root/'src';src.mkdir();(src/'core.cpp').write_text('old\n');(src/'net.inc').write_text('original net\n')
            dst=root/'private';m.make_source_view(src,dst,{'core.cpp','new.cpp'})
            self.assertFalse((dst/'core.cpp').is_symlink())
            self.assertTrue((dst/'net.inc').is_symlink())
            self.assertFalse((dst/'new.cpp').exists())
            patch='--- a/core.cpp\n+++ b/core.cpp\n@@ -1 +1 @@\n-old\n+new\n'
            r=subprocess.run(['patch','-p1','-F0'],cwd=dst,input=patch,text=True,capture_output=True)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            self.assertEqual((dst/'core.cpp').read_text(),'new\n')
            self.assertEqual((src/'core.cpp').read_text(),'old\n')
            self.assertEqual((src/'net.inc').read_text(),'original net\n')

    def test_existing_output_is_refused(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);src=root/'src';src.mkdir();dst=root/'dst';dst.mkdir()
            with self.assertRaises(FileExistsError):m.make_source_view(src,dst,set())

    def test_traversal_and_absolute_patch_targets_are_refused_before_output(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);src=root/'src';src.mkdir()
            for i,name in enumerate(('../source.cpp','/tmp/source.cpp')):
                dst=root/str(i)
                with self.assertRaises(ValueError):m.make_source_view(src,dst,{name})
                self.assertFalse(dst.exists())

    def test_source_symlink_is_refused_before_output(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);src=root/'src';src.mkdir();(root/'outside').write_text('x');(src/'link').symlink_to(root/'outside')
            with self.assertRaises(ValueError):m.make_source_view(src,root/'dst',set())
            self.assertFalse((root/'dst').exists())

    def test_output_inside_frozen_source_is_refused_before_mutation(self):
        with tempfile.TemporaryDirectory() as t:
            src=Path(t)/'src';src.mkdir();out=src/'new'
            with self.assertRaises(ValueError):m.make_source_view(src,out,set())
            self.assertFalse(out.exists())

    def test_runtime_inventory_detects_bytecode_missing_and_modified_inputs(self):
        with tempfile.TemporaryDirectory() as t:
            src=Path(t);(src/'core.cpp').write_text('original');(src/'remove.txt').write_text('keep')
            expected=m.inventory(src)
            self.assertTrue(m.verify_inventory(src,expected)['unchanged'])
            (src/'__pycache__').mkdir();(src/'__pycache__/module.pyc').write_bytes(b'bytecode')
            (src/'core.cpp').write_text('modified');(src/'remove.txt').unlink()
            result=m.verify_inventory(src,expected)
            self.assertFalse(result['unchanged']);self.assertEqual(result['new'],['__pycache__/module.pyc'])
            self.assertEqual(result['modified'],['core.cpp']);self.assertEqual(result['missing'],['remove.txt'])


if __name__=='__main__':unittest.main(verbosity=2)
