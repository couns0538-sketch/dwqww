"""Pure B configuration, exact-TU and closed-cache resume guards; no native work."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
MODULE=Path(__file__).with_name('forge_sol_S08_B_release_build_20261026.py')
class BBuildTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(MODULE.is_file(),'B parameter adapter missing')
        spec=importlib.util.spec_from_file_location('bbuild',MODULE);self.api=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.api)
    def test_config_is_canonical_ON_and_all_B_targets_are_declared(self):
        args=self.api.original.configure_args(Path('/source'),Path('/fresh'),True)
        for flag in ('-DCMAKE_BUILD_TYPE=Release','-DFORGE_PROF=ON','-DFORGE_NATIVE=OFF','-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF'):self.assertIn(flag,args)
        self.assertEqual(self.api.TARGETS,self.api.shared.TARGETS+('forge_bad_capture_tests',))
        self.assertEqual(len(self.api.EXPECTED_TUS),21);self.assertIn('tests/bad_capture_tests.cpp',self.api.EXPECTED_TUS)
    def make_recipe(self,root):
        source=root/'source';source.mkdir();build=root/'build';build.mkdir()
        cache={'FORGE_PROF':'ON','FORGE_NATIVE':'OFF','FORGE_ENABLE_SANITIZERS':'OFF','FORGE_EXPOSE_TUNABLES':'OFF','FORGE_BUILD_VALIDATION_TOOLS':'OFF','FORGE_BUILD_TUNING_TOOLS':'OFF','CMAKE_BUILD_TYPE':'Release','CMAKE_CXX_FLAGS':self.api.shared.FLAGS,'CMAKE_INTERPROCEDURAL_OPTIMIZATION':'OFF','CMAKE_EXPORT_COMPILE_COMMANDS':'ON','CMAKE_HOME_DIRECTORY':str(source),'CMAKE_CXX_COMPILER':str(self.api.shared.CXX)}
        (build/'CMakeCache.txt').write_text(''.join(k+':STRING='+v+'\n' for k,v in cache.items()))
        flags=[str(self.api.shared.CXX),*self.api.shared.FLAGS.split(),'-O3','-DNDEBUG','-DFORGE_PROF=1','-std=c++20']
        rows=[{'file':str(source/name),'arguments':flags} for name in sorted(self.api.EXPECTED_TUS)]
        (build/'compile_commands.json').write_text(json.dumps(rows))
        for name in self.api.TARGETS:
            p=build/f'CMakeFiles/{name}.dir/link.txt';p.parent.mkdir(parents=True);p.write_text(' '.join([str(self.api.shared.CXX),self.api.shared.FLAGS,'-O3 -DNDEBUG input.o -o '+name]))
        return source,build,rows,{'source_sha256':{name:'unused' for name in self.api.EXPECTED_TUS}}
    def test_audit_accepts21_B_TUs_and_rejects_missing_foreign_or_override(self):
        with tempfile.TemporaryDirectory() as folder:
            source,build,rows,freeze=self.make_recipe(Path(folder));self.assertEqual(len(self.api.audit_recipe(source,build,freeze)['translation_units']),21)
            variants=[rows[:-1],rows+[{'file':str(source/'tests/foreign.cpp'),'arguments':rows[0]['arguments']}],rows+[rows[0]]]
            for bad in variants:
                (build/'compile_commands.json').write_text(json.dumps(bad))
                with self.assertRaises(ValueError):self.api.audit_recipe(source,build,freeze)
            rows[0]['arguments']=rows[0]['arguments']+['-march=x86-64']
            (build/'compile_commands.json').write_text(json.dumps(rows))
            with self.assertRaises(ValueError):self.api.audit_recipe(source,build,freeze)
    def test_resume_rejects_wrong_binding_unreaped_children_and_changed_artifact(self):
        with tempfile.TemporaryDirectory() as folder:
            build=Path(folder);(build/'forge').write_bytes(b'ELF')
            old={'status':'PAUSED_BUILD_ONLY','profile':'B_RELEASE_ON','source_freeze_sha256':'freeze','build_dir':str(build),'source_unchanged':True,'configured':True,'completed_targets':['forge'],'target_artifacts':{'forge':{'sha256':self.api.shared.sha(build/'forge')}},'commands':[{'leader_reaped':True,'all_group_members_after_reap':[]}]}
            self.assertEqual(self.api.resume_state(old,build,'freeze')['completed_targets'],['forge'])
            for patch in ({'source_freeze_sha256':'wrong'},{'profile':'ON'},{'completed_targets':['forge_bad_capture_tests']},{'commands':[{'leader_reaped':True,'all_group_members_after_reap':[{'state':'Z'}]}]}):
                with self.subTest(patch=patch),self.assertRaises(ValueError):self.api.resume_state(dict(old,**patch),build,'freeze')
            (build/'forge').write_bytes(b'changed')
            with self.assertRaises(ValueError):self.api.resume_state(old,build,'freeze')
if __name__=='__main__':unittest.main(verbosity=2)
