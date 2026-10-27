"""Pure contract fixtures, NOT runtime/training evidence.
The actual frozen controller is executed with Popen/diagnostic/owned-scope
fully mocked and tiny NON-FPOS/NON-TORCH files. No real process, Torch,
original sample staging, kernel signal, source edit or network occurs.
"""
import ast
from contextlib import ExitStack, nullcontext
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
NEW=HERE/'forge_sol_S18_train_selected_v4_20261027.py'
OLD=Path('/tmp/forge_sol_S18_TRAIN_SMOKE_PREP_20261026/forge_sol_S18_train_selected_20261026.py')

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

new=load(NEW,'S18_contract_current');old=load(OLD,'S18_contract_old_frozen')
NATIVE=b'FINAL FULL HOLDOUT n=49,152: net mse_teacher=0.100000 mse_b0.6=0.200000 mse_b0.8=0.300000 | HCE 0.400000/0.500000/b0.8 0.600000\n'

class Fixture:
    def __init__(self,tool,root):
        self.tool=tool;self.root=root;self.out=root/'NEW_PURE_FIXTURE_NOT_RUNTIME'
        self.original=root/'fixture_original';self.original.mkdir()
        for suffix in ('pos','hce'):(self.original/('h000.'+suffix)).write_bytes(('NOT_REAL_FPOS_FHCE_'+suffix).encode())
        self.trainer=root/'fixture_trainer.py';self.trainer.write_text('# NOT REAL TRAINER\n')
        self.protocol=root/'fixture_protocol.json';self.protocol.write_text('{"PURE_FIXTURE":true}\n')
        self.pins={self.trainer:tool.sha(self.trainer),self.protocol:tool.sha(self.protocol),**{self.original/('h000.'+s):tool.sha(self.original/('h000.'+s)) for s in ('pos','hce')}}
    def stage(self,out,plans,inputs):
        data=out/'none'/'data';data.mkdir(parents=True)
        for s in ('pos','hce'):
            q=data/('h000.'+s);q.write_bytes((self.original/('h000.'+s)).read_bytes());q.chmod(0o444)
        run=out/'none'/'trainer-run';run.mkdir();self.checkpoint=self.tool.final_checkpoint(run,200000);self.checkpoint.write_bytes(b'NOT_A_TORCH_CHECKPOINT_PURE_SCHEMA_FIXTURE')
        return {'none':{'data':str(data),'train':[],'inventory':{}}}
    def valid(self):
        t=self.tool;data=self.out/'none'/'data'
        return {'rows':50000,'batch_size':8192,'batch_sizes':[8192]*6+[848],'last_batch_rows':848,'dropped_tail_rows':0,
                'checkpoint_selection':'FINAL_EPOCH2_PRESELECTED','checkpoint':self.checkpoint.name,
                'checkpoint_sha256_before':t.sha(self.checkpoint),'checkpoint_sha256_after':t.sha(self.checkpoint),
                'net_MSE':{'1.0':.1,'0.6':.2,'0.8':.3},'HCE_baseline_MSE':{'1.0':.4,'0.6':.5,'0.8':.6},
                'aggregation':'float64 squared errors summed by rows /50000; original float32 predictions/targets promoted before subtraction',
                'model_state_sha256_before':'a'*64,'model_state_sha256_after':'a'*64,'state_unchanged':True,
                'holdout_before':{str(data/('h000.'+s)):t.fingerprint(data/('h000.'+s)) for s in ('pos','hce')},'holdout_unchanged':True,
                'weight_updates':0,'exports':0,'original_trainer_sha256':self.pins[self.trainer],
                'preregistration_sha256':self.pins[self.protocol],'Torch_RNG_preserved':True,
                'Torch_RNG_sha256_before':'b'*64,'Torch_RNG_sha256_after':'b'*64}
    def patches(self):
        return [patch.object(self.tool,'HOLDOUT',self.original),patch.object(self.tool,'TRAINER',self.trainer),
                patch.object(self.tool,'POSTSCORE_PROTOCOL',self.protocol),patch.object(self.tool,'PINS',self.pins)]


def exercise_controller(tool,change,child_returncode=0):
    """Execute the REAL acceptance function, with all process/kernel work mocked."""
    with tempfile.TemporaryDirectory(prefix='S18_PURE_ACCEPTANCE_') as temp:
        f=Fixture(tool,Path(temp));args=SimpleNamespace(out=f.out,cpu=4,arms_index=f.root/'fixture_index',root_grant=f.root/'fixture_grant',scope='synthetic_pipeline_only')
        grant={'arms':['none'],'work_seconds_per_arm':300,'hard_seconds_per_arm':360,'rss_limit_bytes':3221225472,'minimum_free_disk_bytes':6979321856}
        class Process:
            pid=987654;returncode=child_returncode
            def poll(self):return self.returncode
            def wait(self,*a,**k):return self.returncode
        def popen(*a,**k):k['stdout'].write(NATIVE);k['stdout'].flush();return Process()
        def monitor(process,armout,*a,**k):
            value=f.valid();child={'work_complete':True}
            changed=change(value)
            if changed!='MISSING':child['separate_post_training_all50000']=changed
            (armout/'child_result.json').write_text(json.dumps(child))
            return {'returncode':child_returncode,'stop_reason':None,'observer_error':None}
        owned=SimpleNamespace(SubreaperScope=nullcontext,_reap_group=lambda _: ([],[]),_all_members=lambda _:[],
                             _close_group=lambda _: (_ for _ in ()).throw(AssertionError('pure fixture must not signal')))
        diagnostic=SimpleNamespace(monitor_process=monitor)
        def module(path,name):return diagnostic if path==tool.DIAGNOSTIC else owned
        plans={'none':{'rows':200000,'files':[],'steps_per_epoch':24,'total_steps':48}}
        with ExitStack() as stack:
            for p in f.patches():stack.enter_context(p)
            for p in [patch.object(tool,'OUTROOT',f.root),patch.object(tool,'source_plan',return_value={'PURE_FIXTURE':True}),
                      patch.object(tool,'require_disk_reserve',return_value=10*2**30),patch.object(tool,'stage_views',side_effect=f.stage),
                      patch.object(tool,'module',side_effect=module),patch.object(tool,'verify_pins',return_value={}),
                      patch.object(tool.os,'sched_getaffinity',return_value={4}),patch.object(tool.os,'getpriority',return_value=19),
                      patch.object(tool.subprocess,'Popen',side_effect=popen),patch.object(tool.os,'killpg',side_effect=AssertionError('no kernel signals permitted'))]:stack.enter_context(p)
            code=tool.run_controller(args,grant,{},plans,{},'PIPELINE_ONLY_SYNTHETIC')
        report=json.loads((f.out/'forge_sol_S18_training_result_20261026.json').read_text())
        return code,report


class ContractControls(unittest.TestCase):
    def test_frozen_old_controller_accepts_the_bad_contract_fixtures(self):
        # This positive old-bug observation is not a native/training PASS.
        for change in [lambda r:'MISSING',lambda r:None,lambda r:{'rows':1}]:
            code,r=exercise_controller(old,change)
            self.assertEqual(code,0);self.assertEqual(r['status'],'PASS_SELECTED_SYNTHETIC_PIPELINE_ARMS')
    def test_new_controller_refuses_missing_postscore(self):
        code,r=exercise_controller(new,lambda r:'MISSING');self.assertNotEqual(code,0);self.assertEqual(r['status'],'FAIL_S18_TRAINING')
    def test_new_controller_refuses_none_postscore(self):
        code,r=exercise_controller(new,lambda r:None);self.assertNotEqual(code,0);self.assertEqual(r['status'],'FAIL_S18_TRAINING')
    def test_new_controller_refuses_malformed_postscore(self):
        code,r=exercise_controller(new,lambda r:{'rows':1});self.assertNotEqual(code,0);self.assertEqual(r['status'],'FAIL_S18_TRAINING')
    def test_new_controller_accepts_complete_schema_fixture_only(self):
        code,r=exercise_controller(new,lambda r:r);self.assertEqual(code,0)
    def test_postscore_retains_old_math_prefix_and_returns_result(self):
        a=next(n for n in ast.parse(OLD.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='postscore_final_checkpoint')
        b=next(n for n in ast.parse(NEW.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='postscore_final_checkpoint')
        self.assertEqual([ast.dump(n) for n in a.body[:-1]],[ast.dump(n) for n in b.body[:len(a.body)-1]])
        self.assertEqual(ast.dump(a.body[-1]),ast.dump(b.body[-1]))
        self.assertEqual(len(b.body),len(a.body)+2)
        self.assertIsInstance(b.body[-1],ast.Return);self.assertIsInstance(b.body[-1].value,ast.Name);self.assertEqual(b.body[-1].value.id,'result')
    def test_required_contract_negative_matrix(self):
        self.assertTrue(callable(getattr(new,'validate_postscore_result',None)),'fail-closed postscore validator missing')
        changes=[('float batch count',lambda r:r.update(batch_sizes=[8192.0]*6+[848.0])),('short rows',lambda r:r.update(rows=49152)),('missing tail',lambda r:r.update(batch_sizes=[8192]*6)),
          ('wrong last batch',lambda r:r.update(last_batch_rows=8192)),('tail dropped',lambda r:r.update(dropped_tail_rows=848)),
          ('missing blend',lambda r:r['net_MSE'].pop('0.8')),('NaN net',lambda r:r['net_MSE'].update({'1.0':float('nan')})),
          ('infinite HCE',lambda r:r['HCE_baseline_MSE'].update({'0.6':float('inf')})),('non numeric loss',lambda r:r['net_MSE'].update({'0.8':'0.1'})),
          ('epoch1',lambda r:r.update(checkpoint='epoch001-step000000024.pt')),('wrong checkpoint bytes',lambda r:r.update(checkpoint_sha256_after='c'*64)),
          ('wrong source',lambda r:r.update(original_trainer_sha256='c'*64)),('wrong protocol',lambda r:r.update(preregistration_sha256='c'*64)),
          ('state drift',lambda r:r.update(model_state_sha256_after='c'*64)),('state absent',lambda r:r.pop('model_state_sha256_before')),
          ('RNG drift',lambda r:r.update(Torch_RNG_sha256_after='c'*64)),('RNG unchecked',lambda r:r.update(Torch_RNG_preserved=False)),
          ('changed holdout',lambda r:r['holdout_before'].clear()),('updates',lambda r:r.update(weight_updates=1)),('exports',lambda r:r.update(exports=1)),
          ('bool update count',lambda r:r.update(weight_updates=False)),('wrong method',lambda r:r.update(aggregation='unweighted batch means'))]
        for label,change in changes:
            with self.subTest(label=label),tempfile.TemporaryDirectory(prefix='S18_PURE_SCHEMA_') as temp:
                f=Fixture(new,Path(temp));f.out.mkdir();f.stage(f.out,{},{});r=f.valid();change(r)
                with ExitStack() as stack:
                    for p in f.patches():stack.enter_context(p)
                    with self.assertRaises(ValueError):new.validate_postscore_result(r,f.out/'none'/'trainer-run',200000,f.out/'none'/'data')
    def test_actual_holdout_or_checkpoint_mutation_rejected(self):
        self.assertTrue(callable(getattr(new,'validate_postscore_result',None)))
        for which in ['holdout','checkpoint']:
            with self.subTest(which=which),tempfile.TemporaryDirectory(prefix='S18_PURE_IDENTITY_') as temp:
                f=Fixture(new,Path(temp));f.out.mkdir();f.stage(f.out,{},{});r=f.valid()
                q=f.out/'none'/'data'/'h000.pos' if which=='holdout' else f.checkpoint;q.chmod(0o644);q.write_bytes(b'CHANGED_PURE_FIXTURE')
                with ExitStack() as stack:
                    for p in f.patches():stack.enter_context(p)
                    with self.assertRaises(ValueError):new.validate_postscore_result(r,f.out/'none'/'trainer-run',200000,f.out/'none'/'data')

if __name__=='__main__':unittest.main()
