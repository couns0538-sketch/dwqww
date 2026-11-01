"""Recorded synthetic timing fixtures, not engine NPS measurements."""
import copy,hashlib,importlib.util,json,pathlib,subprocess,sys,tempfile,unittest
from unittest import mock
SCRIPT=pathlib.Path(__file__).resolve().parents[1]/'skills/abba-nps-timing/scripts/summarize_abba.py'
class Abba(unittest.TestCase):
 def setUp(self):
  self.assertTrue(SCRIPT.is_file(),'ABBA checker not implemented')
  s=importlib.util.spec_from_file_location('crew_abba',SCRIPT);self.m=importlib.util.module_from_spec(s);s.loader.exec_module(self.m)
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=pathlib.Path(self.tmp.name)
  for name in ('a.bin','b.bin','net','options-a','options-b','native.log','host.log','plan.json'):(self.root/name).write_text(name)
  self.record={'schema':1,'baseline':self.ref('a.bin'),'candidate':self.ref('b.bin'),'network':self.ref('net'),'baseline_options':self.ref('options-a'),'candidate_options':self.ref('options-b'),'native_log':self.ref('native.log'),'host_evidence':self.ref('host.log'),'protocol':self.ref('plan.json'),'host':{'os':'fixture-only','cpu_model':'synthetic','logical_cpu':2,'threads':1,'quiet_confirmed':True},'nodes':{'d13-pos1':1000,'d16-pos2':2000},'noise_gate':{'max_median_deviation_pct':1.0,'max_range_pct':2.0},'calibration':{'binary_sha256':self.ref('a.bin')['sha256'],'samples':None},'comparison':{'samples':None}}
  self.writeplan();self.samples('aa',factor=1);self.samples('ab',factor=2);self.record['calibration']['samples']=self.ref('aa');self.record['comparison']['samples']=self.ref('ab')
 def writeplan(self):
  (self.root/'plan.json').write_text(json.dumps({'nodes':self.record['nodes'],'noise_gate':self.record['noise_gate'],'logical_cpu':2,'threads':1,'order':'ABBA','minimum_blocks':10,**{key+'_sha256':self.record[key]['sha256'] for key in ('baseline','candidate','network','baseline_options','candidate_options')}}));self.record['protocol']=self.ref('plan.json')
 def ref(self,n):return {'path':n,'sha256':hashlib.sha256((self.root/n).read_bytes()).hexdigest()}
 def samples(self,name,factor=1,blocks=10):
  rows=[];clock=1 if name=='aa' else 1000000000
  for block in range(blocks):
   for run,arm in enumerate('ABBA'):
    for position,nodes in [('d13-pos1',1000),('d16-pos2',2000)]:
     elapsed=1000000 if arm=='A' else int(1000000/factor)
     rows.append({'block':block,'run':run,'arm':arm,'position':position,'nodes':nodes,'start_ns':clock,'end_ns':clock+elapsed,'wall_ns':elapsed,'logical_cpu':2,'threads':1,'binary_sha256':self.ref('a.bin' if name=='aa' or arm=='A' else 'b.bin')['sha256'],'network_sha256':self.ref('net')['sha256'],'options_sha256':self.ref('options-a' if name=='aa' or arm=='A' else 'options-b')['sha256'],'protocol_sha256':self.ref('plan.json')['sha256']});clock+=elapsed+1
  (self.root/name).write_text(''.join(json.dumps(r)+'\n' for r in rows));return rows
 def mutate(self,name,func):
  rows=[json.loads(x) for x in (self.root/name).read_text().splitlines()];func(rows);(self.root/name).write_text(''.join(json.dumps(r)+'\n' for r in rows));self.record['comparison' if name=='ab' else 'calibration']['samples']=self.ref(name)
 def runcheck(self):
  p=self.root/'record.json';p.write_text(json.dumps(self.record));return self.m.check(p)
 def test_complete_abba_reports_geometric_block_ratio_and_spread(self):
  r=self.runcheck();self.assertEqual(r['status'],'PASS');self.assertEqual(r['comparison']['blocks'],10);self.assertEqual(r['comparison']['median_ratio'],2.0);self.assertEqual(r['comparison']['iqr_ratio'],0.0)
 def test_replaced_binary_with_updated_record_and_plan_rejects_old_samples(self):
  (self.root/'b.bin').write_text('new candidate');self.record['candidate']=self.ref('b.bin');self.writeplan();self.assertEqual(self.runcheck()['status'],'FAIL')
 def test_wrong_binary_in_one_b_sample_fails(self):
  self.mutate('ab',lambda rows:rows[2].update(binary_sha256=self.ref('a.bin')['sha256']));self.assertEqual(self.runcheck()['status'],'FAIL')
 def test_transient_samples_rewrite_restored_after_parse_cannot_pass(self):
  good=(self.root/'ab').read_bytes();self.mutate('ab',lambda rows:rows[3].update(nodes=2001));bad=(self.root/'ab').read_bytes();original=self.m.measure
  def replaced(path,*args,**kwargs):
   if path.name!='ab':return original(path,*args,**kwargs)
   path.write_bytes(good)
   try:return original(path,*args,**kwargs)
   finally:path.write_bytes(bad)
  with mock.patch.object(self.m,'measure',side_effect=replaced):self.assertEqual(self.runcheck()['status'],'FAIL')
  self.assertEqual((self.root/'ab').read_bytes(),bad)
 def test_protocol_parse_cannot_use_temporary_different_plan(self):
  path=self.root/'plan.json';plan=json.loads(path.read_text());plan['minimum_blocks']=11;path.write_text(json.dumps(plan));original_bytes=path.read_bytes();self.record['protocol']=self.ref('plan.json')
  for name in ('aa','ab'):self.mutate(name,lambda rows:[r.update(protocol_sha256=self.record['protocol']['sha256']) for r in rows])
  plan['minimum_blocks']=10;transient=json.dumps(plan).encode();read_text=pathlib.Path.read_text
  def replaced(selected,*args,**kwargs):
   if selected!=path:return read_text(selected,*args,**kwargs)
   path.write_bytes(transient)
   try:return read_text(selected,*args,**kwargs)
   finally:path.write_bytes(original_bytes)
  with mock.patch.object(pathlib.Path,'read_text',replaced):self.assertEqual(self.runcheck()['status'],'FAIL')
  self.assertEqual(path.read_bytes(),original_bytes)
 def test_missing_repeat_is_not_accepted(self):
  self.mutate('ab',lambda rows:rows.pop());self.assertNotEqual(self.runcheck()['status'],'PASS')
 def test_wrong_order_rejected(self):
  self.mutate('ab',lambda rows:rows[2].update(arm='A'));self.assertNotEqual(self.runcheck()['status'],'PASS')
 def test_node_drift_blocks_timing_claim(self):
  self.mutate('ab',lambda rows:rows[3].update(nodes=2001));self.assertEqual(self.runcheck()['status'],'FAIL')
 def test_insufficient_blocks_rejected(self):
  self.samples('ab',2,9);self.record['comparison']['samples']=self.ref('ab');self.assertNotEqual(self.runcheck()['status'],'PASS')
 def test_parallel_or_inconsistent_timestamps_rejected(self):
  self.mutate('ab',lambda rows:rows[1].update(start_ns=rows[0]['start_ns'],end_ns=rows[0]['end_ns']));self.assertNotEqual(self.runcheck()['status'],'PASS')
 def test_two_threads_or_wrong_cpu_rejected(self):
  self.mutate('ab',lambda rows:rows[0].update(threads=2));self.assertEqual(self.runcheck()['status'],'FAIL')
 def test_noise_calibration_failure_blocks_comparison(self):
  self.samples('aa',1.1);self.record['calibration']['samples']=self.ref('aa');r=self.runcheck();self.assertEqual(r['status'],'FAIL');self.assertNotIn('comparison',r)
 def test_aa_binary_must_match_actual_baseline(self):
  self.record['calibration']['binary_sha256']=self.ref('b.bin')['sha256'];self.assertEqual(self.runcheck()['status'],'FAIL')
 def test_quietness_cannot_be_missing(self):
  self.record['host']['quiet_confirmed']=False;self.assertEqual(self.runcheck()['status'],'FAIL')
 def test_sample_hash_change_fails(self):
  with (self.root/'ab').open('a') as f:f.write('\n')
  self.assertEqual(self.runcheck()['status'],'FAIL')
 def test_nonfinite_tolerance_invalid(self):
  self.record['noise_gate']['max_range_pct']=float('nan');self.assertEqual(self.runcheck()['status'],'INVALID')
 def test_cli_read_only_and_exit_zero(self):
  p=self.root/'record.json';p.write_text(json.dumps(self.record));before=set(self.root.iterdir());r=subprocess.run([sys.executable,str(SCRIPT),str(p)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertEqual(before,set(self.root.iterdir()))
if __name__=='__main__':unittest.main()
