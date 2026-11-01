"""Original fixture tests; these are not Forge fens12k measurements."""
import hashlib, importlib.util, json, pathlib, subprocess, sys, tempfile, unittest
from unittest import mock
SCRIPT=pathlib.Path(__file__).resolve().parents[1]/'skills/eval-exact-simd-port/scripts/check_eval_parity.py'
class EvalParity(unittest.TestCase):
 def setUp(self):
  self.assertTrue(SCRIPT.is_file(),'parity checker not implemented')
  spec=importlib.util.spec_from_file_location('crew_eval',SCRIPT);self.mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.mod)
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=pathlib.Path(self.tmp.name)
  self.fen='8/8/8/8/8/8/6k1/K7 w - - 0 1';self.fsha=hashlib.sha256(self.fen.encode()).hexdigest()
  (self.root/'fens').write_text((self.fen+'\n')*12000)
  for name,data in [('scalar.bin',b'scalar'),('candidate.bin',b'candidate'),('net',b'0123456789'),('badnet',b'012X456789'),('native.log',b'original fixture transcript'),('scalar-options',b'{"FixtureSIMD":false}'),('candidate-options',b'{"FixtureSIMD":true}')]: (self.root/name).write_bytes(data)
  self.trace('scalar');self.trace('candidate');self.trace('negative',badrow=100)
  self.record={'schema':1,'candidate_path':{'name':'FixtureSIMD','active_evaluations':12000},'encoding':'f32-bits','fens':self.ref('fens'),'scalar_binary':self.ref('scalar.bin'),'candidate_binary':self.ref('candidate.bin'),'network':self.ref('net'),'scalar_options':self.ref('scalar-options'),'candidate_options':self.ref('candidate-options'),'native_log':self.ref('native.log'),'scalar_trace':self.ref('scalar'),'candidate_trace':self.ref('candidate'),'negative_control':{'network':self.ref('badnet'),'trace':self.ref('negative'),'tensor':'fixture_weight','offset':3,'width':1}}
 def ref(self,name): return {'path':name,'sha256':hashlib.sha256((self.root/name).read_bytes()).hexdigest()}
 def trace(self,name,badrow=None,short=False):
  with (self.root/name).open('w') as f:
   f.write(json.dumps({'schema':1,'kind':'eval-trace','encoding':'f32-bits','implementation':'scalar' if name=='scalar' else 'FixtureSIMD','binary_sha256':self.ref('scalar.bin' if name=='scalar' else 'candidate.bin')['sha256'],'network_sha256':self.ref('badnet' if name=='negative' else 'net')['sha256'],'fens_sha256':self.ref('fens')['sha256'],'options_sha256':self.ref('scalar-options' if name=='scalar' else 'candidate-options')['sha256']})+'\n')
   for i in range(11999 if short else 12000): f.write(json.dumps({'row':i,'fen_sha256':self.fsha,'eval_bits':'00000001' if i==badrow else '00000000'})+'\n')
 def runcheck(self):
  p=self.root/'record.json';p.write_text(json.dumps(self.record));return self.mod.check(p)
 def test_complete_raw_bit_parity_and_negative_control(self):
  result=self.runcheck();self.assertEqual(result['status'],'PASS');self.assertEqual(result['compared_rows'],12000);self.assertEqual(result['mismatches'],0);self.assertEqual(result['negative_control_mismatches'],1)
 def test_windows_uppercase_header_digests_are_accepted(self):
  for name in ('scalar','candidate','negative'):
   lines=(self.root/name).read_text().splitlines();header=json.loads(lines[0]);header.update({k:v.upper() for k,v in header.items() if k.endswith('_sha256')});lines[0]=json.dumps(header);(self.root/name).write_text('\n'.join(lines)+'\n')
  self.record['scalar_trace']=self.ref('scalar');self.record['candidate_trace']=self.ref('candidate');self.record['negative_control']['trace']=self.ref('negative');self.assertEqual(self.runcheck()['status'],'PASS')
 def test_transient_trace_rewrite_restored_after_parse_cannot_pass(self):
  good=(self.root/'candidate').read_bytes();self.trace('candidate',badrow=2);bad=(self.root/'candidate').read_bytes();self.record['candidate_trace']=self.ref('candidate');original=self.mod.values
  def replaced(path,*args,**kwargs):
   if path.name!='candidate':return original(path,*args,**kwargs)
   path.write_bytes(good)
   try:return original(path,*args,**kwargs)
   finally:path.write_bytes(bad)
  with mock.patch.object(self.mod,'values',side_effect=replaced):self.assertEqual(self.runcheck()['status'],'FAIL')
  self.assertEqual((self.root/'candidate').read_bytes(),bad)
 def test_one_bit_error_blocks_timing(self):
  self.trace('candidate',badrow=2);self.record['candidate_trace']=self.ref('candidate');r=self.runcheck();self.assertEqual(r['status'],'FAIL');self.assertFalse(r['parity_gate_satisfied'])
 def test_candidate_path_must_be_active_for_the_suite(self):
  self.record['candidate_path']['active_evaluations']=0;self.assertEqual(self.runcheck()['status'],'FAIL')
 def test_rounded_cp_or_wrong_width_rejected(self):
  self.record['encoding']='cp';self.assertEqual(self.runcheck()['status'],'INVALID')
 def test_missing_row_never_passes(self):
  self.trace('candidate',short=True);self.record['candidate_trace']=self.ref('candidate');self.assertNotEqual(self.runcheck()['status'],'PASS')
 def test_replaced_candidate_binary_with_updated_hash_cannot_reuse_old_trace(self):
  (self.root/'candidate.bin').write_bytes(b'new candidate');self.record['candidate_binary']=self.ref('candidate.bin');self.assertEqual(self.runcheck()['status'],'FAIL')
 def test_negative_control_trace_must_bind_corrupt_network(self):
  lines=(self.root/'negative').read_text().splitlines();header=json.loads(lines[0]);header['network_sha256']=self.ref('net')['sha256'];lines[0]=json.dumps(header);(self.root/'negative').write_text('\n'.join(lines)+'\n');self.record['negative_control']['trace']=self.ref('negative');self.assertEqual(self.runcheck()['status'],'FAIL')
 def test_changed_network_hash_fails(self):
  (self.root/'net').write_bytes(b'mutated');self.assertEqual(self.runcheck()['status'],'FAIL')
 def test_negative_control_must_have_eval_mismatch(self):
  self.trace('negative');self.record['negative_control']['trace']=self.ref('negative');self.assertEqual(self.runcheck()['status'],'FAIL')
 def test_control_change_outside_selected_weight_fails(self):
  (self.root/'badnet').write_bytes(b'X12X456789');self.record['negative_control']['network']=self.ref('badnet');self.assertEqual(self.runcheck()['status'],'FAIL')
 def test_boolean_row_and_fen_misalignment_fail(self):
  lines=(self.root/'candidate').read_text().splitlines();lines[0]=json.dumps({'row':False,'fen_sha256':'0'*64,'eval_bits':'00000000'});(self.root/'candidate').write_text('\n'.join(lines)+'\n');self.record['candidate_trace']=self.ref('candidate');self.assertNotEqual(self.runcheck()['status'],'PASS')
 def test_cli_nonzero_and_no_output_files(self):
  self.record['encoding']='cp';p=self.root/'record.json';p.write_text(json.dumps(self.record));before=set(self.root.iterdir());r=subprocess.run([sys.executable,str(SCRIPT),str(p)],capture_output=True,text=True);self.assertEqual(r.returncode,2);self.assertEqual(before,set(self.root.iterdir()))
if __name__=='__main__': unittest.main()
