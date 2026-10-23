"""Read actual23 producer bytes under their ORIGINAL candidate label.
Role remapping is a consumer-only UNIT schema test; never an actual24 capture.
"""
import copy,hashlib,importlib.util,json,unittest
from pathlib import Path
from unittest.mock import patch
R=Path(__file__).resolve().parents[2];P=R/'.github/hosted-see-proof-performance';BASE='1d3ed25bea2c8b781f7ee5a178af0f66061b3984'
ROOT='validation/hosted-tt-refresh-strength-20261021/capture-preparation/actual-five-captures'
def load(name,file):
 s=importlib.util.spec_from_file_location(name,P/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=load('capture_role_common','common.py');a=load('capture_role_analysis','analysis.py')
def cfg():
 prov=json.loads((R/ROOT/'PROVENANCE.json').read_text());c=prov['captures']['candidate']
 entry={'source_commit':BASE,'engine_sha256':c['binary_sha256_before']['forge'],'provenance_capture_label':'candidate','source_manifest_path':'validation/tt-refresh-native-20261021/ROOT-FROZEN-SOURCE-GATES.json'}
 for stream in ['stdin','stdout','stderr']:entry[stream+'_path']=ROOT+'/candidate/'+stream+'.txt'
 entry['facts_path']=ROOT+'/candidate/status.json';entry['provenance_path']=ROOT+'/PROVENANCE.json'
 paths=[v for k,v in entry.items() if k.endswith('_path')]
 return {'transport_captures':{'baseline':copy.deepcopy(entry),'candidate':copy.deepcopy(entry)},'correctness_evidence_sha256':{p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in paths}}
class Actual23Consumer(unittest.TestCase):
 def validate(self,c):
  with patch.object(m,'CANDIDATE',BASE),patch.object(a,'EXPECTED_NODES',292545):return m.transport_paths(R,c,a)
 def test_actual23_original_candidate_side_can_serve_new_baseline_role(self):
  self.assertEqual(hashlib.sha256((R/ROOT/'owned_process.executed.py').read_bytes()).hexdigest(),'461a65d2fecdf208994749cb0d44c56bf2f8524610f211a4bf76bd019c25704d')
  paths=self.validate(cfg());self.assertIn(R/ROOT/'candidate/stdout.txt',paths)
 def test_unmodified_original22_side_cannot_be_relabeled23(self):
  c=cfg();c['transport_captures']['baseline']['provenance_capture_label']='baseline'
  with self.assertRaisesRegex(ValueError,'provenance differs'):self.validate(c)
 def test_wrong_engine_pin_cannot_bypass_original_source_binary_record(self):
  c=cfg();c['transport_captures']['baseline']['engine_sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'provenance differs'):self.validate(c)
if __name__=='__main__':unittest.main(verbosity=2)
