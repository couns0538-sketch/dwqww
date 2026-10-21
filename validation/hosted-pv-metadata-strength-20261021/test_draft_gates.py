"""Draft-only gate tests. Any complete future config below is synthetic, not a source proof."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
PACKAGE = REPO / '.github/hosted-pv-metadata-strength'
spec = importlib.util.spec_from_file_location('draft_correction_runner', PACKAGE/'run_hosted.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class DraftSourceAndReviewGates(unittest.TestCase):
    def setUp(self):
        self.cfg = json.loads((PACKAGE/'protocol.json').read_text())

    def complete_mock(self):
        cfg = copy.deepcopy(self.cfg)
        cfg.update(status='PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH', candidate_sha='0000000000000000000000000000000000000022',
            candidate_version='6.4.22', candidate_benchmark_nodes=292545,candidate_bench_capture_status='PASSED_ACTUAL_FROZEN22_CANONICAL_CAPTURE',
            source_gates_status='PASSED', source_scope_review_status='PASSED',
            root_review_status='PASSED', astra_review_status='PASSED',
            correctness_evidence_sha256={'synthetic-unit-only.json':'2'*64},
            operational_qualification_status='authorized_for_one_fresh_host_readiness_attempt_with_prior_anomalies_unresolved',
            workflow_status='FROZEN', workflow_sha256='3'*64)
        return cfg

    def test_actual_draft_keeps_proofs_and_workflow_pending_after_signature_freeze(self):
        self.assertEqual(self.cfg['candidate_sha'],'ff2e269c6058be84456e3b98344826d17b0056eb')
        self.assertEqual(self.cfg['candidate_benchmark_nodes'],292545)
        self.assertEqual(self.cfg['correctness_evidence_sha256'], {})
        workflow=(REPO/'.github/workflows/forge-hosted-pv-metadata-strength.yml').read_text()
        self.assertIn('on: []',workflow)
        self.assertIn('if: ${{ false }}',workflow)
        with self.assertRaises(ValueError): runner.require_launch_protocol(self.cfg)

    def test_planned_source22_signature_does_not_waive_other_gates(self):
        self.assertEqual(runner.CANDIDATE_SHA,'ff2e269c6058be84456e3b98344826d17b0056eb')
        self.assertEqual(runner.CANDIDATE_BENCHMARK_NODES,292545)
        changed=copy.deepcopy(self.cfg);changed['status']='PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH'
        with self.assertRaises(ValueError): runner.require_launch_protocol(changed)

    def test_future_mock_freeze_still_requires_all_independent_reviews(self):
        cfg = self.complete_mock()
        with patch.object(runner,'CANDIDATE_SHA','0000000000000000000000000000000000000022'), patch.object(runner,'CANDIDATE_BENCHMARK_NODES',292545):
            runner.require_launch_protocol(cfg)
            for key in ('source_gates_status','source_scope_review_status','root_review_status','astra_review_status'):
                changed=copy.deepcopy(cfg); changed[key]='PENDING'
                with self.subTest(key=key), self.assertRaises(ValueError): runner.require_launch_protocol(changed)

    def test_old_17_or_shortened_design_cannot_become_this_pv_repair(self):
        cfg=self.complete_mock()
        with patch.object(runner,'CANDIDATE_SHA','0000000000000000000000000000000000000022'), patch.object(runner,'CANDIDATE_BENCHMARK_NODES',292545):
            for key,value in [('pair_cap',128),('game_cap',256),('emergency_seconds',12000),('tc','2+0.02'),('concurrency',2)]:
                changed=copy.deepcopy(cfg);changed['sprt_settings'][key]=value
                with self.subTest(key=key),self.assertRaises(ValueError):runner.require_launch_protocol(changed)

    def test_baseline21_and_fresh_seed_are_pinned(self):
        cfg=self.complete_mock()
        with patch.object(runner,'CANDIDATE_SHA','0000000000000000000000000000000000000022'), patch.object(runner,'CANDIDATE_BENCHMARK_NODES',292545):
            for key,value in [('baseline_sha','21538ec5416c909fc98a08688242a0b3b9710b25'),('baseline_benchmark_nodes',419798),('seed',20261025)]:
                changed=copy.deepcopy(cfg);changed[key]=value
                with self.subTest(key=key),self.assertRaises(ValueError):runner.require_launch_protocol(changed)

    def test_missing_proofs_authorization_or_workflow_still_blocks(self):
        cfg=self.complete_mock()
        with patch.object(runner,'CANDIDATE_SHA','0000000000000000000000000000000000000022'), patch.object(runner,'CANDIDATE_BENCHMARK_NODES',292545):
            for key,value in [('correctness_evidence_sha256',{}),('operational_qualification_status','PENDING_ROOT_ONE_ATTEMPT_AUTHORIZATION'),('workflow_status','NOT_CREATED_PREPARATION_ONLY'),('workflow_sha256',None),('candidate_bench_capture_status','PENDING_ACTUAL_FROZEN22_CAPTURE')]:
                changed=copy.deepcopy(cfg);changed[key]=value
                with self.subTest(key=key),self.assertRaises(ValueError):runner.require_launch_protocol(changed)


class DraftPackageInventory(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT,prefix='inventory-unit-')
        self.addCleanup(self.temp.cleanup)
        self.repo=Path(self.temp.name);self.package=self.repo/'.github/hosted-pv-metadata-strength';self.package.mkdir(parents=True)
        (self.package/'a.txt').write_text('mock package data\n')
        relative=(self.package/'a.txt').relative_to(self.repo).as_posix()
        (self.package/'PACKAGE-SHA256SUMS').write_text(hashlib.sha256((self.package/'a.txt').read_bytes()).hexdigest()+'  '+relative+'\n')

    def test_preparatory_inventory_needs_no_nonexistent_workflow(self):
        self.assertEqual(len(runner.verify_package_inventory(self.repo,self.package)),1)

    def test_changed_or_extra_input_is_rejected(self):
        (self.package/'a.txt').write_text('changed')
        with self.assertRaises(ValueError):runner.verify_package_inventory(self.repo,self.package)
        (self.package/'extra.txt').write_text('extra')
        with self.assertRaises(ValueError):runner.verify_package_inventory(self.repo,self.package)


if __name__=='__main__':unittest.main(verbosity=2)
