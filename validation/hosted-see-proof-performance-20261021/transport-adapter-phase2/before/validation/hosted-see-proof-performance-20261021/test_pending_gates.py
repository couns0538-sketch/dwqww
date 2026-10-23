"""Synthetic metadata/parser controls only; never evidence of actual24 execution."""
import copy,importlib.util,json,unittest
from pathlib import Path
from unittest.mock import patch
R=Path(__file__).resolve().parents[2];P=R/'.github/hosted-see-proof-performance'
def load(name,file):
 spec=importlib.util.spec_from_file_location(name,P/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=load('see_common_test','common.py');a=load('see_analysis_test','analysis.py');CFG=json.loads((P/'protocol.json').read_text())
class Pending(unittest.TestCase):
 def synthetic_ready(self):
  c=copy.deepcopy(CFG);c.update(status=m.READY,expected_nodes=292545,source_gates_status='PASSED',parity_review_status='PASSED',capture_review_status='PASSED',root_review_status='PASSED',independent_review_status='PASSED',workflow_status='FROZEN',workflow_sha256='1'*64,operational_qualification_status='authorized_for_one_fresh_host_calibration_attempt_with_prior_anomalies_unresolved')
  c['correctness_evidence_sha256']={p:'2'*64 for p in m.REQUIRED_PROOFS};c['transport_captures']={'baseline':{},'candidate':{}}
  return c
 def test_unknown_signature_cannot_be_waived_by_declared_ready_metadata(self):
  self.assertIsNone(m.EXPECTED_NODES)
  with self.assertRaisesRegex(ValueError,'signature is not frozen'):m.require_ready(self.synthetic_ready())
 def test_unknown_parser_signature_rejects_parent_rows(self):
  self.assertIsNone(a.EXPECTED_NODES)
  raw=(R/'validation/tt-refresh-native-20261021/release-signature-wrapper-attempt1/bench11.stdout').read_bytes() if (R/'validation/tt-refresh-native-20261021/release-signature-wrapper-attempt1/bench11.stdout').exists() else b'info string bench depth 11 nodes 292545 time 100 nps 2925450\n'
  with self.assertRaisesRegex(ValueError,'signature is not frozen'):a.parse_bench(raw*5)
 def test_actual_draft_remains_blocked_even_with_unit_signature_patch(self):
  with patch.object(m,'EXPECTED_NODES',292545),self.assertRaisesRegex(ValueError,'remains blocked'):m.require_ready(CFG)
 def test_all_13_required_metadata_bindings_fail_closed_when_omitted(self):
  c=self.synthetic_ready()
  with patch.object(m,'EXPECTED_NODES',292545):
   m.require_ready(c) # Presence-only synthetic metadata acceptance, NOT proof byte verification.
   for p in m.REQUIRED_PROOFS:
    case=copy.deepcopy(c);del case['correctness_evidence_sha256'][p]
    with self.subTest(path=p),self.assertRaisesRegex(ValueError,'proof binding'):m.require_ready(case)
 def test_missing_actual_capture_declarations_reject_after_other_unit_gates(self):
  c=self.synthetic_ready();c['transport_captures']={}
  with patch.object(m,'EXPECTED_NODES',292545),self.assertRaisesRegex(ValueError,'captures pending'):m.require_ready(c)
 def test_absent_or_changed_proof_bytes_fail_closed(self):
  with self.assertRaisesRegex(ValueError,'Missing/unsafe'):m.proof_paths(R,{'correctness_evidence_sha256':{'validation/hosted-see-proof-performance-20261021/THIS-ACTUAL-PROOF-DOES-NOT-EXIST.json':'0'*64}})
 def test_disabled_workflow_has_no_event_and_false_job(self):
  s=(R/m.WORKFLOW).read_text();self.assertIn('on: []\n',s);self.assertIn('    if: ${{ false }}\n',s);self.assertNotIn('workflow_dispatch',s);self.assertNotIn('\n  push:',s)
if __name__=='__main__':unittest.main(verbosity=2)
