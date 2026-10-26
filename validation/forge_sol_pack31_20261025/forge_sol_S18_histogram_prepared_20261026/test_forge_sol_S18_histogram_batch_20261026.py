"""Pure wrapper controls. No live data, Popen, proc, Torch or histogram run."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('s18_hist_batch',HERE/'forge_sol_S18_histogram_batch_20261026.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class WrapperTests(unittest.TestCase):
    def fixture(self):
        def hist(n):return {'rows':n,**{k:{'fixture':n} for k in ['phase','piece_count','white_result','stm_result','score_sign','absolute_score_band']},
           'disagreement':{str(t):{'consistent':n} for t in [200,300,400,500]}}
        r={'threshold':200,'filter_seed':20261025,'source_summary_sha256':'s','source_output_manifest':{'sha256':'m'},
          'phase_definition':{'source_sha256':'p'},'all_histograms_reconcile':True,'source_inputs_unchanged':True,
          'training_performed':False,'input':hist(4),'kept':hist(2),'dropped':hist(2),'supplied_holdout_overlap':0,'dedupe':{'output_duplicate_positions':0}}
        p={'arms':{'t200':{'threshold':200,'summary_sha256':'s','manifest_sha256':'m','source_totals_reference_not_histogram_observation':{'input':4,'kept':2,'dropped':2}}},'phase_header_sha256':'p'}
        return r,p
    def validate_fixture(self,r,p):
        with tempfile.TemporaryDirectory(prefix='S18_hist_pure_') as temp:
            q=Path(temp)/'new.json';q.write_text(json.dumps(r));q.chmod(0o444)
            return m.validate_output(q,p,'t200')
    def test_complete_fixture(self):
        r,p=self.fixture();self.assertEqual(self.validate_fixture(r,p)['input']['rows'],4)
    def test_missing_disagreement_threshold_rejected(self):
        r,p=self.fixture();r['input']['disagreement'].pop('500')
        with self.assertRaises(ValueError):self.validate_fixture(r,p)
    def test_false_reconstruction_flag_rejected(self):
        r,p=self.fixture();r['input']['phase']={'foreign_bucket':4}
        with self.assertRaises(ValueError):self.validate_fixture(r,p)
    def test_bad_bucket_sum_rejected(self):
        r,p=self.fixture();r['input']['phase']['fixture']=1
        with self.assertRaises(ValueError):self.validate_fixture(r,p)
    def test_changed_source_rejected(self):
        r,p=self.fixture();r['source_summary_sha256']='other'
        with self.assertRaises(ValueError):self.validate_fixture(r,p)
    def test_training_or_missing_reconcile_rejected(self):
        for key,value in [('training_performed',True),('all_histograms_reconcile',False),('source_inputs_unchanged',False)]:
            r,p=self.fixture();r[key]=value
            with self.assertRaises(ValueError):self.validate_fixture(r,p)
    def test_new_output_guards(self):
        with tempfile.TemporaryDirectory(prefix='S18_hist_pure_') as temp:
            p=Path(temp)
            self.assertEqual(m.new_output(p/'new',[]),p/'new')
            for path in [p,p/'..'/'new',p/'baseline'/'new',p/'protected'/'new']:
                with self.assertRaises(ValueError):m.new_output(path,[p/'protected'])
    def test_describe_never_executes(self):
        with mock.patch.object(m.subprocess,'Popen',side_effect=AssertionError('must not spawn')),mock.patch('builtins.print'):
            self.assertEqual(m.main(['--describe']),0)
    def test_argv_has_only_readonly_histogram_tool(self):
        p=m.pins();a=m.arguments(p,'t500',Path('/tmp/NEW/h.json'))
        self.assertEqual(a[2],p['tool']);self.assertEqual(a[a.index('--arm')+1],p['arms']['t500']['path'])
        self.assertNotIn('--train',a);self.assertNotIn('--execute-data',a)

if __name__=='__main__':unittest.main()
