"""Pure fixed-source resume validation; no compiler/engine execution."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
MODULE=Path(__file__).with_name('forge_sol_S08_release_resume_after_timing_20261026.py')
class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(MODULE.is_file(),'Release resume adapter missing')
        spec=importlib.util.spec_from_file_location('release_resume',MODULE)
        self.api=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.api)
    def test_resume_requires_same_source_build_profile_and_closed_children(self):
        with tempfile.TemporaryDirectory() as folder:
            build=Path(folder)/'build';build.mkdir();(build/'forge').write_bytes(b'ELF')
            old={'status':'PAUSED_BUILD_ONLY','profile':'ON','build_dir':str(build),'source_freeze_sha256':'freeze',
                 'source_unchanged':True,'completed_targets':['forge'],'target_artifacts':{'forge':{'sha256':self.api.shared.sha(build/'forge')}},
                 'recipe_before':{'status':'PASS_RELEASE_ON_RECIPE'},'commands':[{'leader_reaped':True,'all_group_members_after_reap':[]}]}
            self.assertEqual(self.api.resume_state(old,build,'freeze')['completed_targets'],['forge'])
            for key,value in [('profile','DEFAULT_OFF'),('source_freeze_sha256','other'),('source_unchanged',False),('build_dir','/other'),('completed_targets',['forge_prof_tests'])]:
                with self.subTest(key=key),self.assertRaises(ValueError):self.api.resume_state(dict(old,**{key:value}),build,'freeze')
            old['commands'][0]['all_group_members_after_reap']=[{'pid':999,'state':'Z'}]
            with self.assertRaises(ValueError):self.api.resume_state(old,build,'freeze')
    def test_actual_flag_audit_rejects_later_ISA_tuning_or_macro_override(self):
        safe=[str(self.api.shared.CXX),*self.api.shared.FLAGS.split(),'-O3','-DNDEBUG','-std=c++20','-DFORGE_PROF=1']
        self.api.check_exact_tokens(safe)
        for bad in ('-march=x86-64','-mtune=generic','-UFORGE_PROF','-DFORGE_NNUE_HIDDEN=128','-DFORGE_PROF=0'):
            with self.subTest(flag=bad),self.assertRaises(ValueError):self.api.check_exact_tokens(safe+[bad])
if __name__=='__main__':unittest.main(verbosity=2)
