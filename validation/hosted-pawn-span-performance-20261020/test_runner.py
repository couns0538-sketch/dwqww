"""Offline orchestration/gates; real producer bytes, synthetic timing only. No engine."""
import copy,importlib.util,json,os,shutil,sys,tempfile,time,unittest
from contextlib import contextmanager
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[1];PKG=REPO/'.github/hosted-pawn-span-performance'
spec=importlib.util.spec_from_file_location('runner_under_test',PKG/'run_hosted.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
CFG=json.loads((PKG/'protocol.json').read_text());CAPTURE=REPO/'validation/hosted-runtime-psqt-performance-20261020/actual-five-captures'
class Runner(unittest.TestCase):
    def test_historical_original_rows_and_facts_are_parser_bytes_only(self):
        for label in ('baseline','candidate'):
            facts=json.loads((CAPTURE/label/'status.json').read_text())
            self.assertEqual(len(m.validate_sample(facts,CAPTURE/label,facts['cpu'])),5)
            for stream in ('stdin','stdout','stderr'):
                self.assertEqual((CAPTURE/label/(stream+'.txt')).read_bytes(),(PKG/'fixtures/historical-18-19'/(label+'-five.'+stream+'.bin')).read_bytes())
        draft=json.loads((ROOT/'pre-enable-disabled/package/protocol.json').read_text())
        self.assertEqual(draft['transport_captures'],{})
        for entry in CFG['transport_captures'].values():
            self.assertNotIn('fixtures/historical-18-19',entry['stdout_path'])
    def test_derived_crlf_historical_rows_remain_canonical(self):
        for label in ('baseline','candidate'):
            self.assertEqual(len(m.analysis.parse_bench((CAPTURE/label/'stdout.txt').read_bytes().replace(b'\n',b'\r\n'))),5)
    def test_old19_capture_cannot_be_declared_actual20(self):
        cfg=json.loads((REPO/'.github/hosted-runtime-psqt-performance/protocol.json').read_text())
        # First establish the genuine historical positive under its original pins.
        with mock.patch.object(m.common,'BASELINE',cfg['baseline_sha']),mock.patch.object(m.common,'CANDIDATE',cfg['candidate_sha']):
            self.assertEqual(len(m.common.transport_paths(REPO,cfg,m.analysis)),12)
        # Deliberately relabel the declaration20; retained original19 PROVENANCE must fail.
        cfg['transport_captures']['candidate']['source_commit']='0'*38+'20'
        with mock.patch.object(m.common,'BASELINE',cfg['baseline_sha']),mock.patch.object(m.common,'CANDIDATE','0'*38+'20'):
            with self.assertRaisesRegex(ValueError,'Actual capture label/source/binary/process provenance'):
                m.common.transport_paths(REPO,cfg,m.analysis)
    def test_real_capture_facts_faults_rejected(self):
        actual=json.loads((CAPTURE/'candidate/status.json').read_text())
        for key,value in [('returncode',1),('returncode_before_verdict',None),('timed_out',True),('owned_group_empty_before_verdict',False),('owned_group_empty_after_cleanup',False),('measurement_affinity',[0,1]),('cpu_seconds_before_verdict',float('nan')),('wall_seconds_before_verdict',0),('user_seconds_before_verdict',-1),('stdout_sha256','0'*64),('wall_stop_reason','after_cleanup'),('error','injected')]:
            facts=copy.deepcopy(actual);facts[key]=value
            with self.subTest(key=key),self.assertRaises((ValueError,TypeError)):m.validate_sample(facts,CAPTURE/'candidate',actual['cpu'])
    def sampler(self,root,aa_bias=False):
        calls=[];raw=(CAPTURE/'baseline/stdout.txt').read_bytes()
        def sample(argv,stdin,out,cpu,limit):
            calls.append((argv[0],out.name,limit))
            self.assertEqual(stdin,m.common.STDIN);self.assertGreater(limit,0);self.assertLessEqual(limit,60)
            sample.streams[out/'stdout.txt']=raw;sample.streams[out/'stderr.txt']=b''
            phase,block,pos=out.name.split('-');variant=('ABBA' if int(block)%2==0 else 'BAAB')[int(pos)]
            # Explicit synthetic durations, never capture-derived performance observations.
            duration=(1.02 if variant=='A' else 1.) if aa_bias and phase=='aa' else (1. if phase=='aa' or argv[0]=='candidate-inert' else 2.)
            facts={'returncode_before_verdict':0,'returncode':0,'timed_out':False,'timeout_seconds':limit,'owned_group_empty_before_verdict':True,'owned_group_empty_after_cleanup':True,'measurement_affinity':[cpu],'wall_stop_reason':'wait4_leader_observed','cpu_seconds_before_verdict':duration,'wall_seconds_before_verdict':duration,'user_seconds_before_verdict':duration,'system_seconds_before_verdict':0.}
            for stream in ('stdout','stderr'):
                facts[stream+'_sha256']=facts[stream+'_sha256_before_verdict']=m.common.sha(out/(stream+'.txt'))
            sample.facts[out/'status.json']=facts;return facts
        sample.streams={};sample.facts={}
        return calls,sample
    @contextmanager
    def simulation(self,sampler):
        original=Path.read_bytes
        # Only synthetic 188-process orchestration streams live in memory. Each
        # unique raw path still passes the REAL hash/parser/sample validator.
        # Actual capture and benign-process tests continue using original files.
        def read(path):return sampler.streams[path] if path in sampler.streams else original(path)
        with mock.patch.object(Path,'read_bytes',read),mock.patch.object(m.common,'save'):
            yield
    def test_complete188samples_and_correct_roles_warmup_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);calls,sampler=self.sampler(out);report={}
            with self.simulation(sampler):
                m.run_experiment(CFG,'baseline-inert','candidate-inert',out,0,time.monotonic()+60,report,sampler)
            self.assertEqual(len(calls),188);self.assertEqual(len(report['all_samples']),188)
            self.assertEqual(len(sampler.streams),376);self.assertEqual(len(sampler.facts),188)
            self.assertTrue(report['warmup']['excluded_from_analysis']);self.assertTrue(report['calibration']['passed']);self.assertTrue(report['gain_qualifies_before_final_rehash'])
            self.assertTrue(all(binary=='baseline-inert' for binary,name,_ in calls if name.startswith('aa-')))
            self.assertEqual(len(report['aa_blocks']),15);self.assertEqual(len(report['ab_blocks']),31)
            self.assertEqual([x['binary_label'] for x in report['ab_blocks'][1]['samples']],['candidate','baseline','baseline','candidate'])
    def test_aa_failure_stops_exactly_after64_no_ab(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);calls,sampler=self.sampler(out,True);report={}
            with self.simulation(sampler),self.assertRaisesRegex(ValueError,'STOP'):
                m.run_experiment(CFG,'baseline-inert','candidate-inert',out,0,time.monotonic()+60,report,sampler)
            self.assertEqual(len(calls),64);self.assertFalse(any(name.startswith('ab-') for _,name,_ in calls));self.assertFalse(report['calibration']['passed'])
    def test_aggregate_deadline_before_any_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            sampler=mock.Mock()
            with self.assertRaises(TimeoutError):m.run_experiment(CFG,'a','b',Path(tmp),0,time.monotonic()-1,{},sampler)
            sampler.assert_not_called()
    def test_final_sample_crossing_aggregate_deadline_invalidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);calls,sample=self.sampler(out);clock=[0.];report={}
            def sampler(*args):
                result=sample(*args)
                if len(calls)==188:clock[0]=101.
                return result
            with mock.patch.object(m.time,'monotonic',side_effect=lambda:clock[0]),self.simulation(sample),self.assertRaises(TimeoutError):
                m.run_experiment(CFG,'baseline-inert','candidate-inert',out,0,100.,report,sampler)
            self.assertEqual(len(calls),188);self.assertNotIn('gain_qualifies_before_final_rehash',report)
class Integrity(unittest.TestCase):
    def metadata_fixture(self):
        cfg=copy.deepcopy(CFG)
        cfg.update(status=m.common.READY,candidate_sha='0'*38+'20',source_gates_status='PASSED',parity_review_status='PASSED',capture_review_status='PASSED',root_review_status='PASSED',independent_review_status='PASSED',workflow_status='FROZEN',workflow_sha256='1'*64,operational_qualification_status='authorized_for_one_fresh_host_calibration_attempt_with_prior_anomalies_unresolved')
        cfg['correctness_evidence_sha256']={p:'2'*64 for p in m.common.REQUIRED_PROOFS}
        cfg['transport_captures']={'baseline':{},'candidate':{}}
        return cfg
    def test_draft_and_forced_ready_pending_source_fail_before_process(self):
        with mock.patch.object(m.owned,'run_owned') as spawn,self.assertRaisesRegex(ValueError,'blocked'):
            m.common.require_ready({**CFG,'status':'DRAFT_BLOCKED_PREPARATION_ONLY'})
        spawn.assert_not_called()
        cfg=copy.deepcopy(CFG);cfg['status']=m.common.READY;cfg['candidate_sha']='PENDING_FROZEN_CANDIDATE_20_SHA'
        with mock.patch.object(m.common,'CANDIDATE',cfg['candidate_sha']),mock.patch.object(m.owned,'run_owned') as spawn,self.assertRaisesRegex(ValueError,'source is not frozen'):
            m.common.require_ready(cfg)
        spawn.assert_not_called()
    def test_metadata_fixture_requires_all_fullproof_bindings(self):
        cfg=self.metadata_fixture()
        with mock.patch.object(m.common,'CANDIDATE',cfg['candidate_sha']):
            m.common.require_ready(cfg) # Metadata only, never actual proof/capture evidence.
            del cfg['correctness_evidence_sha256'][m.common.REQUIRED_PROOFS[-1]]
            with self.assertRaisesRegex(ValueError,'proof binding'):m.common.require_ready(cfg)
    def test_metadata_fixture_requires_actual_capture_entries(self):
        cfg=self.metadata_fixture();cfg['transport_captures']={}
        with mock.patch.object(m.common,'CANDIDATE',cfg['candidate_sha']),self.assertRaisesRegex(ValueError,'captures pending'):
            m.common.require_ready(cfg)
    def test_missing_or_mutated_proof_bytes_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'proof.json';p.write_bytes(b'actual fixture');cfg={'correctness_evidence_sha256':{'proof.json':m.common.sha(p)}}
            self.assertEqual(m.common.proof_paths(root,cfg),[p]);p.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'changed'):m.common.proof_paths(root,cfg)
            p.unlink()
            with self.assertRaisesRegex(ValueError,'Missing'):m.common.proof_paths(root,cfg)
    def test_final_freeze_catches_bytes_mode_missing_and_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'proof';p.write_bytes(b'one');p.chmod(0o644);frozen=m.common.snapshot([p])
            self.assertEqual(m.common.rehash(frozen)['status'],'passed');p.chmod(0o600);self.assertEqual(m.common.rehash(frozen)['status'],'failed')
            p.chmod(0o644);p.write_bytes(b'two');self.assertEqual(m.common.rehash(frozen)['status'],'failed');p.unlink();self.assertEqual(m.common.rehash(frozen)['status'],'failed')
            p.symlink_to(CAPTURE/'baseline/stdout.txt')
            with self.assertRaises(ValueError):m.common.snapshot([p])
    def test_all_consumed_package_and_workflow_bytes_modes_rehash(self):
        paths=m.common.inventory(REPO,PKG)
        self.assertEqual(m.common.rehash(m.common.snapshot(paths))['status'],'passed')
if __name__=='__main__':unittest.main(verbosity=2)
