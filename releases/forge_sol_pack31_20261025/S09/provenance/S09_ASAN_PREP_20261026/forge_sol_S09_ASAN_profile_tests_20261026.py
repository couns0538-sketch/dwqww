import ast
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parent
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
b=module('s09_asan_build_tests',HERE/'forge_sol_S09_build_ASAN_20261026.py')
r=module('s09_asan_runtime_tests',HERE/'forge_sol_S09_qualify_ASAN_20261026.py')


class SanitizerProfileTests(unittest.TestCase):
    def tokens(self):
        return [str(b.owned.CXX),*b.FLAGS.split(),'-std=c++20','-O2','-g','-DNDEBUG',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer']

    def test_manual_helpers_are_instrumented_with_same_strict_float_recipe(self):
        command=b.manual_command(Path('/source'),Path('/core.a'),Path('/driver.cpp'),Path('/helper'))
        b.strict_tokens(command)
        for needed in ('-O2','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                       '-ffp-contract=off','-fno-fast-math','-DFORGE_NNUE_HIDDEN=256'):
            self.assertIn(needed,command)
            changed=list(command);changed.remove(needed)
            with self.subTest(missing=needed),self.assertRaises(ValueError):b.strict_tokens(changed)

    def test_debug_sanitizer_math_and_frame_overrides_refused(self):
        b.strict_tokens(self.tokens()+['-ffp-contract=off'])
        for bad in ('-O3','-Ofast','-g0','-fsanitize=address','-fno-sanitize=undefined',
                    '-fomit-frame-pointer','-ffp-contract=fast','-ffast-math','-flto','-fprofile-use'):
            with self.subTest(bad=bad),self.assertRaises(ValueError):b.strict_tokens(self.tokens()+[bad])

    def test_first_receipt_cannot_substitute_release_profile(self):
        first={'profile':'ASAN_UBSAN_STATIC_O2_DEBUG','schema':'forge.S09.first_runtime.v1','status':'PASS',
            'build_receipt_sha256':'build','engine_sha256':'engine','commands_sent':['bench 11','quit'],
            'no_UCI_before_bench':True,'bench_nodes':308972,'returncode':0,'source_unchanged':True,'all_artifacts_unchanged':True}
        r.verify_first(first,'build','engine')
        for bad in (None,'Release','ASAN_SHARED_NODWARF'):
            changed=dict(first);changed['profile']=bad
            with self.subTest(profile=bad),self.assertRaises(ValueError):r.verify_first(changed,'build','engine')

    def test_runtime_has_no_virtual_shadow_address_limit_and_rss_guard_stops(self):
        tree=ast.parse((HERE/'forge_sol_S09_qualify_ASAN_20261026.py').read_text())
        self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='setrlimit' for n in ast.walk(tree)))
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);g=r.RSSGuard(p,p/'stop',time.monotonic()+10)
            with mock.patch.object(r,'owned_subtree_rss',return_value=1024):self.assertIsNone(g.reason())
            with mock.patch.object(r,'owned_subtree_rss',return_value=4*1024**3+1):self.assertEqual(g.reason(),'OWNED_RSS_LIMIT')
            self.assertEqual(g.maximum_owned_RSS_bytes,4*1024**3+1)

    def test_owned_fixture_protocol_uses_frozen_transport_and_reaps_leader(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);fixture=p/'fixture';fixture.write_text('#!'+sys.executable+'\nimport sys\nfor line in sys.stdin:\n if line.strip()=="bench 11": print("info string bench depth 11 nodes 308972 time 1 nps 308972000",flush=True)\n if line.strip()=="quit": break\n');fixture.chmod(0o700)
            g=r.RSSGuard(p,p/'stop',time.monotonic()+10)
            lines=r.q.engine_once(fixture,p,'unit_fixture',['bench 11'],lambda x:x.startswith('info string bench'),g)
            self.assertEqual(len(lines),1)
            import json
            owned=json.loads((p/'unit_fixture.ownership.json').read_text())
            self.assertTrue(owned['leader_reaped']);self.assertEqual(owned['all_group_members_after_reap'],[])
            with self.assertRaises(ProcessLookupError):os.kill(owned['pid'],0)


if __name__=='__main__':unittest.main(verbosity=2)
