"""Pure fixture controls only; no compiler, engine or performance execution."""
from pathlib import Path
import copy,importlib.util,json,re,tempfile,unittest
from unittest import mock

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('s11_runtime_fixture',HERE/'forge_sol_S11_qualify_native_20261026.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class QualificationTests(unittest.TestCase):
    def test_first_is_exact_and_closed_before_full(self):
        good={'schema':'forge.S11.first_runtime.v1','status':'PASS','profile':'Release',
            'build_receipt_sha256':'fixture-build','engine_sha256':'fixture-engine',
            'commands_sent':['bench 11','quit'],'no_UCI_before_bench':True,'bench_nodes':308972,
            'returncode':0,'source_unchanged':True,'all_artifacts_unchanged':True,'all_engine_groups_closed':True}
        m.verify_first(good,'fixture-build','fixture-engine','Release')
        for field,value in [('schema','forge.S09.first_runtime.v1'),('status','FAIL'),('profile','ASAN'),
                ('build_receipt_sha256','stale'),('engine_sha256','stale'),('commands_sent',['uci','bench 11','quit']),
                ('no_UCI_before_bench',False),('bench_nodes',308971),('returncode',False),('returncode',1),
                ('source_unchanged',False),('all_artifacts_unchanged',False),('all_engine_groups_closed',False)]:
            bad=dict(good);bad[field]=value
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):m.verify_first(bad,'fixture-build','fixture-engine','Release')

    def test_full_ctest_uses_each_actual_source_inventory_and_keeps_known_findings(self):
        for base,count in [('Lprime',14),('B',15)]:
            source,_=m.build_api.selected_source(base,'candidate')
            names=re.findall(r'add_test\(NAME\s+(\w+)',(source/'CMakeLists.txt').read_text());self.assertEqual(len(names),count)
            with tempfile.TemporaryDirectory() as tmp:
                junit=Path(tmp)/'UNIT_fixture.xml';junit.write_text('<testsuite>'+''.join('<testcase name="'+n+'"/>' for n in names)+'</testsuite>')
                text='\n'.join(m.q.KNOWN)+f'\n100% tests passed, 0 tests failed out of {count}\n'
                self.assertEqual(m.previous.verify_ctest(text,0,names,junit)['registered_tests'],count)
                for bad in [text.replace('got 661','got 660'),text+'FAIL: unit synthetic unexpected\n',text.replace(m.q.KNOWN[0],''),text.replace(f'out of {count}',f'out of {count-1}')]:
                    with self.assertRaises(ValueError):m.previous.verify_ctest(bad,0,names,junit)
                junit.write_text('<testsuite>'+''.join('<testcase name="'+n+'"/>' for n in names[:-1])+'</testsuite>')
                with self.assertRaises(ValueError):m.previous.verify_ctest(text,0,names,junit)

    def test_closed_artifact_and_recipe_binding_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'UNIT_source';source.mkdir();(source/'fixture').write_text('unit fixture, not engine source')
            build=root/'build';build.mkdir();receipt=root/'receipt.json';expected={'fixture':m.shared.sha(source/'fixture')}
            artifacts={}
            for name,filename in [('forge','forge'),('core_archive','libforge_core.a')]:
                p=build/filename;p.write_text('UNIT fixture artifact, not an ELF: '+name);artifacts[name]={'path':str(p),'sha256':m.shared.sha(p),'bytes':p.stat().st_size}
            data={'schema':'forge.S11.build.v1','status':'PASS_BUILD_ONLY','source_unchanged':True,'profile':'ASAN',
                'source_inventory_sha256':m.build_api.INVENTORY_SHA,'patch_sha256':m.build_api.PATCH_SHA,
                'compiler_sha256':m.build_api.owned.CXX_SHA,'qualified_build_adapter_sha256':m.build_api.PROFILE_SHAS['ASAN'],
                'source':str(source),'base':'B','role':'candidate','source_before':expected,'source_after':expected,
                'environment':{'PYTHONDONTWRITEBYTECODE':'1'},'S10_published_commit':'1'*40,
                'commands':[{'returncode':0,'leader_reaped':True,'all_group_members_after_reap':[],'stop_reason':None}],
                'target_artifacts':artifacts,'recipe_after':{'UNIT_recipe':True}}
            auditor=mock.Mock();auditor.audit_recipe.return_value={'UNIT_recipe':True}
            def save(value):receipt.write_text(json.dumps(value))
            with mock.patch.object(m.build_api,'selected_source',return_value=(source,expected)),mock.patch.object(m.build_api,'permitted',return_value=True),mock.patch.object(m.build_api,'artifact_names',return_value=list(artifacts)),mock.patch.object(m.build_api,'load',return_value=auditor):
                save(data);self.assertEqual(m.verify_build(receipt)[2],build)
                for kind in ['compiler','patch','inventory','recipe_adapter','wrong_source','source_changed','missing_artifact','artifact_hash','artifact_bytes','artifact_path','unclosed','bool_rc','wrong_recipe','no_S10']:
                    bad=copy.deepcopy(data)
                    if kind=='compiler':bad['compiler_sha256']='0'*64
                    elif kind=='patch':bad['patch_sha256']='0'*64
                    elif kind=='inventory':bad['source_inventory_sha256']='0'*64
                    elif kind=='recipe_adapter':bad['qualified_build_adapter_sha256']='0'*64
                    elif kind=='wrong_source':bad['source']=str(root/'different')
                    elif kind=='source_changed':bad['source_after']={}
                    elif kind=='missing_artifact':del bad['target_artifacts']['core_archive']
                    elif kind=='artifact_hash':bad['target_artifacts']['forge']['sha256']='0'*64
                    elif kind=='artifact_bytes':bad['target_artifacts']['forge']['bytes']+=1
                    elif kind=='artifact_path':bad['target_artifacts']['forge']['path']=str(root/'foreign')
                    elif kind=='unclosed':bad['commands'][0]['all_group_members_after_reap']=[{'pid':123,'UNIT_fixture':True}]
                    elif kind=='bool_rc':bad['commands'][0]['returncode']=False
                    elif kind=='wrong_recipe':bad['recipe_after']={}
                    else:bad['S10_published_commit']=''
                    save(bad)
                    with self.subTest(kind=kind),self.assertRaises(ValueError):m.verify_build(receipt)

if __name__=='__main__':unittest.main(verbosity=2)
