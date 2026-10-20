"""Targeted RED/GREEN pending-source guard; no processes, proof or capture claims."""
import copy,importlib.util,json,os,unittest
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parent;PKG=ROOT.parents[1]/'.github/hosted-pawn-span-performance'
TARGET=Path(os.environ.get('PAWN_COMMON_UNDER_TEST',str(PKG/'common.py')))
spec=importlib.util.spec_from_file_location('pending_pin_guard',TARGET)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PendingPin(unittest.TestCase):
    def test_fully_faked_ready_metadata_cannot_authorize_pending_source(self):
        cfg=json.loads((PKG/'protocol.json').read_text())
        cfg.update(status=m.READY,source_gates_status='PASSED',parity_review_status='PASSED',capture_review_status='PASSED',root_review_status='PASSED',independent_review_status='PASSED',workflow_status='FROZEN',workflow_sha256='1'*64,operational_qualification_status='authorized_for_one_fresh_host_calibration_attempt_with_prior_anomalies_unresolved')
        cfg['correctness_evidence_sha256']={p:'2'*64 for p in m.REQUIRED_PROOFS}
        cfg['transport_captures']={'baseline':{},'candidate':{}}
        cfg['candidate_sha']='PENDING_FROZEN_CANDIDATE_20_SHA'
        with patch.object(m,'CANDIDATE',cfg['candidate_sha']),self.assertRaisesRegex(ValueError,'source is not frozen'):
            m.require_ready(cfg)
if __name__=='__main__':unittest.main(verbosity=2)
