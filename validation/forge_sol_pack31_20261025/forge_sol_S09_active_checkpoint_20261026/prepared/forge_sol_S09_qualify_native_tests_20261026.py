import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('qualification',HERE/'forge_sol_S09_qualify_native_20261026.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class RuntimeTests(unittest.TestCase):
    def test_fma_success_requires_explicit_pass_and_zero(self):
        m.verify_fma({'status':'PASS','fma_count':0})
        for bad in ({},{'status':'FAIL','fma_count':0},{'status':'PASS','fma_count':1},{'status':'PASS','fma_count':False}):
            with self.subTest(value=bad),self.assertRaisesRegex(ValueError,'FMA'):m.verify_fma(bad)

    def test_full_reuses_original_first_raw_capture_with_eof_and_order(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);receipt=p/'result.json';receipt.write_text('{}')
            (p/'FIRST_bare11.stdin').write_bytes(b'bench 11\nquit\n')
            (p/'FIRST_bare11.stdout').write_bytes(b'info string bench depth 11 nodes 308972 time 1 nps 308972000\n')
            (p/'FIRST_bare11.stderr').write_bytes(b'')
            (p/'FIRST_bare11.receipt.json').write_text(json.dumps({'returncode':0,'stdout_complete':True,'stderr_complete':True}))
            d={'first_captures':{name:m.q.shared.sha(p/name) for name in ('FIRST_bare11.stdin','FIRST_bare11.stdout','FIRST_bare11.stderr','FIRST_bare11.receipt.json')}}
            m.verify_first_files(receipt,d)
            for name in d['first_captures']:
                q=p/name;original=q.read_bytes();q.write_bytes(original+b'changed')
                with self.subTest(name=name),self.assertRaises(ValueError):m.verify_first_files(receipt,d)
                q.write_bytes(original)
            (p/'FIRST_bare11.stdin').write_bytes(b'uci\nbench 11\nquit\n');d['first_captures']['FIRST_bare11.stdin']=m.q.shared.sha(p/'FIRST_bare11.stdin')
            with self.assertRaisesRegex(ValueError,'order'):m.verify_first_files(receipt,d)

    def test_first_requires_exact_build_order_nodes_and_unchanged_inputs(self):
        d={'schema':'forge.S09.first_runtime.v1','status':'PASS','build_receipt_sha256':'build','engine_sha256':'engine','commands_sent':['bench 11','quit'],'no_UCI_before_bench':True,'bench_nodes':308972,'returncode':0,'source_unchanged':True,'all_artifacts_unchanged':True}
        m.verify_first(d,'build','engine')
        for field,value in [('schema','other'),('status','FAIL'),('build_receipt_sha256','stale'),('engine_sha256','stale'),('commands_sent',['uci','bench 11','quit']),('no_UCI_before_bench',False),('bench_nodes',308971),('returncode',1),('source_unchanged',False),('all_artifacts_unchanged',False)]:
            changed=dict(d);changed[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):m.verify_first(changed,'build','engine')

    def test_complete_ctest_inventory_and_source_known_cases(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'result.xml';names=['unit_a','unit_b'];p.write_text('<testsuite><testcase name="unit_a"/><testcase name="unit_b"/></testsuite>')
            text='\n'.join(m.q.KNOWN)+'\n100% tests passed, 0 tests failed out of 2\n'
            self.assertEqual(m.verify_ctest(text,0,names,p)['registered_tests'],2)
            for changed in (text.replace('got 661','got 660'),text.replace('score 642','score 100'),text+'FAIL: new failure\n',text.replace('out of 2','out of 1'),text.replace(m.q.KNOWN[0],'')):
                with self.assertRaises(ValueError):m.verify_ctest(changed,0,names,p)
            with self.assertRaises(ValueError):m.verify_ctest(text,1,names,p)
            p.write_text('<testsuite><testcase name="unit_a"/></testsuite>')
            with self.assertRaisesRegex(ValueError,'JUnit'):m.verify_ctest(text,0,names,p)
            p.write_text('<testsuite><testcase name="unit_a"/><testcase name="unit_b"><skipped/></testcase></testsuite>')
            with self.assertRaisesRegex(ValueError,'JUnit'):m.verify_ctest(text,0,names,p)

    def test_closed_build_binds_all_actual_artifacts_and_generated_recipe(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);src=p/'src';src.mkdir();(src/'fixture').write_text('source');build=p/'build';build.mkdir();receipt=p/'receipt.json'
            api=mock.Mock();api.inventory.return_value={'fixture':'source-sha'};api.verify_all_baselines.return_value={'L':{'unchanged':True}}
            required=set(m.build_api.STDLIB_TARGETS)|{'forge_nnue_heads_parity','forge_nnue_bit_snapshot','core_archive'}
            artifacts={}
            for n in required:
                q=build/('libforge_core.a' if n=='core_archive' else n);q.write_text('unit artifact '+n);artifacts[n]={'path':str(q),'sha256':m.q.shared.sha(q)}
            data={'schema':'forge.S09.build.v1','status':'PASS_BUILD_ONLY','source':str(src),'source_before':{'fixture':'source-sha'},'source_after':{'fixture':'source-sha'},'source_unchanged':True,'environment':{'PYTHONDONTWRITEBYTECODE':'1'},'commands':[{'returncode':0,'leader_reaped':True,'all_group_members_after_reap':[],'stop_reason':None}],'target_artifacts':artifacts,'role':'reference','recipe_after':{'fixture':'recipe'}}
            def save(d):receipt.write_text(json.dumps(d))
            save(data)
            with mock.patch.object(m,'api',api),mock.patch.object(m.build_api,'permitted',return_value=True),mock.patch.object(m.build_api,'audit_recipe',return_value={'fixture':'recipe'}):
                self.assertEqual(m.verify_build(receipt)[2],build)
                (src/'tests').mkdir();bad=src/'tests/bad_capture_tests.cpp';bad.write_text('unit B badcapture source')
                with self.assertRaisesRegex(ValueError,'artifact inventory'):m.verify_build(receipt)
                bad.unlink()
                for mutation in ('missing','path','hash','recipe','source','unclosed','boolean_rc'):
                    d=copy.deepcopy(data)
                    if mutation=='missing':d['target_artifacts'].pop('core_archive')
                    elif mutation=='path':d['target_artifacts']['core_archive']['path']=str(build/'forge')
                    elif mutation=='hash':d['target_artifacts']['forge']['sha256']='0'*64
                    elif mutation=='recipe':d['recipe_after']={}
                    elif mutation=='source':d['source_after']={}
                    elif mutation=='unclosed':d['commands'][0]['all_group_members_after_reap']=[{'pid':123,'synthetic':True}]
                    else:d['commands'][0]['returncode']=False
                    save(d)
                    with self.subTest(mutation=mutation),self.assertRaises(ValueError):m.verify_build(receipt)

if __name__=='__main__':unittest.main(verbosity=2)
