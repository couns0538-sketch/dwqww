"""Pure source/recipe controls. No compiler, CMake or native process launched."""
import copy
import importlib.util
from pathlib import Path
import types
import unittest
from unittest import mock
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('build_test',HERE/'forge_sol_S11_build_native_20261026.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class BuildTests(unittest.TestCase):
    def test_actual_compiler_owned_helper_and_adapter_hashes_checked(self):
        checks={m.PROFILE_SOURCES['Release']:m.PROFILE_SHAS['Release'],m.owned.CXX:m.owned.CXX_SHA,m.release.SHARED:m.release.SHARED_SHA}
        with mock.patch.object(m.owned,'sha',side_effect=lambda p:checks[Path(p)]):m.verify_dependencies('Release')
        for path in checks:
            corrupted=dict(checks);corrupted[path]='0'*64
            with self.subTest(path=str(path)),mock.patch.object(m.owned,'sha',side_effect=lambda p:corrupted[Path(p)]),self.assertRaisesRegex(ValueError,'dependency'):m.verify_dependencies('Release')

    def test_frozen_source_roles_and_no_undeclared_delta(self):
        baseline={'src/search.cpp':'old','README.md':'old-doc','IDEA_SOURCE.md':'old-ideas','include/forge/nnue.hpp':'same-header'}
        candidate=dict(baseline,**{'src/search.cpp':'new','README.md':'new-doc','IDEA_SOURCE.md':'new-ideas'})
        roots={k:Path('/tmp/unit_base')/k for k in ('L','Lprime','B')};views={k:Path('/tmp/unit_cand')/k for k in roots}
        inv={'source_views':{k:str(v) for k,v in views.items()},'original_source_freezes':{k:dict(baseline) for k in roots},'source_freezes':{k:dict(candidate) for k in roots}}
        actual={**{p:dict(baseline) for p in roots.values()},**{p:dict(candidate) for p in views.values()}}
        api=types.SimpleNamespace(BASES=roots,inventory=lambda root:actual[Path(root)])
        with mock.patch.object(m,'sources',api),mock.patch.object(m,'frozen',return_value=inv):
            self.assertEqual(m.selected_source('Lprime','baseline')[0],roots['Lprime']);self.assertEqual(m.selected_source('B','candidate')[0],views['B'])
            actual[views['B']]['include/forge/nnue.hpp']='drift'
            with self.assertRaisesRegex(ValueError,'actual source'):m.selected_source('B','candidate')
            actual[views['B']]['include/forge/nnue.hpp']='same-header';actual[roots['L']]['new-file']='unexpected'
            with self.assertRaisesRegex(ValueError,'original'):m.selected_source('Lprime','candidate')
            del actual[roots['L']]['new-file'];inv['source_freezes']['B']['include/forge/nnue.hpp']='drift';actual[views['B']]['include/forge/nnue.hpp']='drift'
            with self.assertRaisesRegex(ValueError,'three declared files'):m.selected_source('B','candidate')

    def test_normally_compiled_material_oracle_with_candidate_only_marker(self):
        source=Path('/tmp/unit_source');build=Path('/tmp/unit_build')
        for role in ('baseline','candidate'):
            argv=m.oracle_command(m.release,source,build,role);m.release.strict_tokens(argv)
            self.assertEqual(argv.count(str(m.ORACLE)),1);self.assertIn('-I'+str(source),argv)
            self.assertEqual([x for x in argv if x.startswith('-DS11_REQUIRE_TABLE')],['-DS11_REQUIRE_TABLE=1'] if role=='candidate' else [])
            self.assertIn('-Wl,-Map,'+str(build/'forge_sol_S11_materialkey_oracle.map'),argv)
            self.assertFalse(any(x.startswith('-U__') for x in argv))

if __name__=='__main__':unittest.main(verbosity=2)
