"""Run unchanged applicable packet tests after actual authorized READY transition.
Exactly four historical actual-DRAFT assertions remain retained and explicit.
"""
import hashlib,json,os,sys,time,unittest
from pathlib import Path
V=Path(__file__).resolve().parents[1];R=V.parents[1]
assert sys.dont_write_bytecode and os.environ.get('PYTHONDONTWRITEBYTECODE')=='1'
assert os.environ.get('LIFECYCLE_RUNNER')==str(R/'.github/hosted-see-proof-performance/run_hosted.py')
OMIT={
 'test_pending_gates.Pending.test_unknown_signature_cannot_be_waived_by_declared_ready_metadata',
 'test_pending_gates.Pending.test_unknown_parser_signature_rejects_parent_rows',
 'test_pending_gates.Pending.test_actual_draft_remains_blocked_even_with_unit_signature_patch',
 'test_pending_gates.Pending.test_disabled_workflow_has_no_event_and_false_job',
}
def flatten(suite):
 for x in suite:
  if isinstance(x,unittest.TestSuite):yield from flatten(x)
  else:yield x
alltests=list(flatten(unittest.defaultTestLoader.discover(str(V),pattern='test_*.py')))
ids={t.id() for t in alltests};assert len(alltests)==46 and OMIT<=ids
chosen=[t for t in alltests if t.id() not in OMIT];assert len(chosen)==42
hashes={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(V.glob('test_*.py'))};assert len(hashes)==6
scope={'status':'ACTUAL_READY_APPLICABLE_EXISTING_TEST_SCOPE','original_postcapture_DRAFT_tests':46,'selected':42,'omitted_historical_actual_DRAFT_assertions':sorted(OMIT),'omission_reason':'These unchanged source assertions require current actual unknown signature/DRAFT/disabled workflow. READY behavior is checked separately against the genuine full map and actual current bytes.','test_sources_changed_for_READY':False,'test_source_sha256':hashes}
with (V/'ready-binding-phase3/READY-TEST-SCOPE.json').open('x') as f:json.dump(scope,f,indent=2);f.write('\n')
started=time.monotonic();result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(chosen));elapsed=time.monotonic()-started
out={'status':'PASS_42_APPLICABLE_READY_OFFLINE_TESTS' if result.wasSuccessful() else 'FAIL_READY_OFFLINE_TESTS','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'runner_wall_seconds':elapsed,'test_sources_changed_for_READY':False,'tests_source_sha256':hashes,'omitted_historical_DRAFT_assertions':sorted(OMIT),'engines_builds_helpers_matches_git_network_workflow_execution':0}
with (V/'ready-binding-phase3/READY-OFFLINE-RESULT.partial.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
raise SystemExit(0 if result.wasSuccessful() else 1)
