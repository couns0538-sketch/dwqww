"""Actual closed23/24 producer bytes; source/data consumers only, no engines.
Malformed/status controls are explicit in-memory derivatives, not process captures.
"""
import copy,hashlib,importlib.util,json,unittest
from pathlib import Path
from unittest.mock import patch
R=Path(__file__).resolve().parents[3];P=R/'.github/hosted-see-proof-performance';V=R/'validation/hosted-see-proof-performance-20261021'
C24='validation/hosted-see-proof-performance-20261021/capture-preparation/actual-five-captures'
def load(name,file):
 spec=importlib.util.spec_from_file_location(name,P/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=load('actual24_transport_common','common.py');a=load('actual24_transport_analysis','analysis.py');original_loads=json.loads
PROV_RAW=(R/C24/'PROVENANCE.json').read_text();P24=original_loads(PROV_RAW)
P23_RAW=(R/P24['reused23_entry']['provenance_path']).read_text()
def cfg():
 candidate={'source_commit':m.CANDIDATE,'engine_sha256':P24['captures']['candidate']['binary_sha256_before']['forge'],'provenance_capture_label':'candidate','source_manifest_path':'validation/see-proof-reuse-native-20261021/ROOT-FROZEN-SOURCE-GATES.json','facts_path':C24+'/candidate/status.json','provenance_path':C24+'/PROVENANCE.json'}
 for k in ['stdin','stdout','stderr']:candidate[k+'_path']=C24+'/candidate/'+k+'.txt'
 entries={'baseline':copy.deepcopy(P24['reused23_entry']),'candidate':candidate};names={p for e in entries.values() for k,p in e.items() if k.endswith('_path')}
 return {'transport_captures':entries,'correctness_evidence_sha256':{n:hashlib.sha256((R/n).read_bytes()).hexdigest() for n in names}}
class GenuineTransport(unittest.TestCase):
 def validate(self,c=None,mutation=None,target='candidate'):
  def loads(raw,*args,**kwargs):
   d=original_loads(raw,*args,**kwargs)
   if mutation and raw==(PROV_RAW if target=='candidate' else P23_RAW):mutation(d)
   return d
  with patch.object(a,'EXPECTED_NODES',292545),patch.object(m.json,'loads',side_effect=loads):return m.transport_paths(R,c or cfg(),a)
 def test_both_actual_sources_and_original_roles_pass(self):
  self.assertEqual(hashlib.sha256((R/C24/'PROVENANCE.json').read_bytes()).hexdigest(),'928769628a1332d2f6abe1271798c9dd7126d6de04e98b4e3da248a1ae301506')
  self.assertEqual(P24['status'],'PASS_ONE_ACTUAL24_FIVE_COMMAND_CAPTURE_NOT_SPEED_EVIDENCE');self.assertEqual(set(P24['captures']),{'candidate'})
  self.assertEqual(P24['captures']['candidate']['source_commit'],m.CANDIDATE)
  paths=self.validate();self.assertIn(R/C24/'candidate/stdout.txt',paths);self.assertIn(R/P24['reused23_entry']['stdout_path'],paths)
 def test_candidate24_cannot_use_old_both_status(self):
  with self.assertRaises(ValueError):self.validate(mutation=lambda d:d.update(status='PASS_BOTH_ACTUAL_FIVE_COMMAND_CAPTURES_NOT_SPEED_EVIDENCE'))
 def test_reused23_cannot_use_new_single24_status(self):
  with self.assertRaises(ValueError):self.validate(target='baseline',mutation=lambda d:d.update(status='PASS_ONE_ACTUAL24_FIVE_COMMAND_CAPTURE_NOT_SPEED_EVIDENCE'))
 def test_single24_receipt_cannot_contain_an_extra_baseline(self):
  def add(d):d['captures']['baseline']=copy.deepcopy(d['captures']['candidate'])
  with self.assertRaises(ValueError):self.validate(mutation=add)
 def test_reused23_must_keep_original_candidate_label(self):
  c=cfg();c['transport_captures']['baseline']['provenance_capture_label']='baseline'
  with self.assertRaises(ValueError):self.validate(c)
 def test_new24_source_and_engine_cannot_be_relabelled(self):
  for key,value in [('source_commit',m.BASELINE),('engine_sha256','0'*64)]:
   c=cfg();c['transport_captures']['candidate'][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.validate(c)
 def test_actual24_bytes_reject_derived_duplicate_or_warning(self):
  raw=(R/C24/'candidate/stdout.txt').read_bytes();first=raw.splitlines(keepends=True)[0]
  with patch.object(a,'EXPECTED_NODES',292545):
   self.assertEqual(len(a.parse_bench(raw)),5)
   for derived in [raw+first,raw+b'warning\n',raw.rstrip(b'\n'),raw.replace(b'nodes 292545',b'nodes 292546')]:
    with self.subTest(derived=derived[:80]),self.assertRaises(ValueError):a.parse_bench(derived)
if __name__=='__main__':unittest.main(verbosity=2)
