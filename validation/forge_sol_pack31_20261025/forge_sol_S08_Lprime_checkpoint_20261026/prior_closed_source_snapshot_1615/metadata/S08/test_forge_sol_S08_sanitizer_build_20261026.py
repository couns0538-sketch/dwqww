"""Pure sanitizer configuration/guard fixtures; no compiler or engine."""
import importlib.util
import json
from pathlib import Path
import tempfile
import time
import types
import unittest

MODULE=Path(__file__).with_name('forge_sol_S08_sanitizer_build_20261026.py')


class SanitizerTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(MODULE.is_file(),'sanitizer parameter adapter missing')
        spec=importlib.util.spec_from_file_location('asanadapter',MODULE)
        self.api=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.api)

    def test_configure_uses_separate_debug_sanitizer_recipe(self):
        args=self.api.configure_args(Path('/source'),Path('/new-build'))
        for flag in ('-DCMAKE_BUILD_TYPE=RelWithDebInfo','-DFORGE_ENABLE_SANITIZERS=ON','-DFORGE_PROF=ON','-DFORGE_NATIVE=OFF','-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF'):
            self.assertIn(flag,args)
        self.assertIn('-DCMAKE_CXX_FLAGS='+self.api.shared.FLAGS,args)

    def test_disk_floor_and_explicit_stop_block_child_launch(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);stop=root/'STOP'
            guard=self.api.ActiveGuard(root,stop,disk_usage=lambda _:types.SimpleNamespace(free=8*1048576))
            self.assertIsNone(guard.check(None,time.monotonic()+10))
            guard.disk_usage=lambda _:types.SimpleNamespace(free=8*1048576-1)
            self.assertEqual(guard.check(None,time.monotonic()+10),'DISK_FREE_BELOW_8MIB')
            guard.disk_usage=lambda _:types.SimpleNamespace(free=20*1048576);stop.touch()
            self.assertEqual(guard.check(None,time.monotonic()+10),'ROOT_STOP_FILE')

    def recipe(self,root):
        source=root/'source';source.mkdir();build=root/'build';build.mkdir()
        cache={'CMAKE_BUILD_TYPE':'RelWithDebInfo','CMAKE_CXX_COMPILER':str(self.api.shared.CXX),'CMAKE_CXX_FLAGS':self.api.shared.FLAGS,
               'CMAKE_HOME_DIRECTORY':str(source),'FORGE_NATIVE':'OFF','FORGE_ENABLE_SANITIZERS':'ON','FORGE_PROF':'ON','CMAKE_INTERPROCEDURAL_OPTIMIZATION':'OFF'}
        (build/'CMakeCache.txt').write_text(''.join(k+':STRING='+v+'\n' for k,v in cache.items()))
        tokens=[str(self.api.shared.CXX),*self.api.shared.FLAGS.split(),'-O2','-g','-DNDEBUG','-DFORGE_PROF=1','-std=c++20','-fsanitize=address,undefined','-fno-omit-frame-pointer']
        (build/'compile_commands.json').write_text(json.dumps([{'file':str(source/'src/nnue.cpp'),'arguments':tokens}]))
        link=build/'CMakeFiles/forge.dir';link.mkdir(parents=True);(link/'link.txt').write_text(str(self.api.shared.CXX)+' -O2 -g -fsanitize=address,undefined a.o -o forge\n')
        return source,build,tokens

    def test_audit_accepts_o2_debug_and_rejects_release_or_missing_sanitizer(self):
        with tempfile.TemporaryDirectory() as root:
            source,build,tokens=self.recipe(Path(root))
            self.assertEqual(self.api.audit_recipe(source,build,{'src/nnue.cpp'})['status'],'PASS_ASAN_UBSAN_RECIPE')
            for bad in ([x for x in tokens if x!='-g'],[x for x in tokens if not x.startswith('-fsanitize=')],[x if x!='-O2' else '-O3' for x in tokens],tokens+['-ffast-math']):
                (build/'compile_commands.json').write_text(json.dumps([{'file':str(source/'src/nnue.cpp'),'arguments':bad}]))
                with self.assertRaises(ValueError):self.api.audit_recipe(source,build,{'src/nnue.cpp'})

    def test_release_receipt_cannot_resume_as_sanitizer_build(self):
        with self.assertRaises(ValueError):
            self.api.resume_pending({'build_dir':'/tmp/build','profile':'Release','completed_targets':['forge']},Path('/tmp/build'),'freeze')

    def test_full_stage_contains_all_registered_cpp_targets(self):
        self.assertEqual(self.api.TARGETS,self.api.shared.TARGETS)


if __name__=='__main__':unittest.main(verbosity=2)
