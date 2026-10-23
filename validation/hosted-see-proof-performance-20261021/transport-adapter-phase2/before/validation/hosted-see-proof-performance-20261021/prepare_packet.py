"""One local source-only adaptation; never launches build or timing processes."""
import ast,difflib,hashlib,json,shutil
from pathlib import Path
R=Path('/workspace/dwqww');V=R/'validation/hosted-see-proof-performance-20261021';OLD=R/'.github/hosted-nearest-pawn-performance';P=R/'.github/hosted-see-proof-performance'
BASE='1d3ed25bea2c8b781f7ee5a178af0f66061b3984';CAND='7db08eac6ead99d641834c56ccec06a06600586a';SEED=20261102
P.mkdir()
for name in ['common.py','analysis.py','archive_results.py','owned_process.py','prepare_hosted.py','run_hosted.py','build_evidence.py']:
 shutil.copy2(OLD/name,P/name)
# Preserve the qualified numerical/timing implementation, changing only experiment signature/seed.
p=P/'analysis.py';s=p.read_text().replace('EXPECTED_NODES=321912','EXPECTED_NODES=None  # Pending actual24 first signature and matched producer captures.').replace('BOOTSTRAP_SEED=20261029',f'BOOTSTRAP_SEED={SEED}')
s=s.replace("    if not isinstance(raw,bytes):raise ValueError('Original benchmark bytes required')","    if type(EXPECTED_NODES) is not int or EXPECTED_NODES<=0:raise ValueError('Candidate24 benchmark signature is not frozen')\n    if not isinstance(raw,bytes):raise ValueError('Original benchmark bytes required')")
p.write_text(s)
required=[
 'validation/tt-refresh-20261021/root-verification/NATIVE.json',
 'validation/tt-refresh-native-20261021/ROOT-FROZEN-SOURCE-GATES.json',
 'validation/tt-refresh-native-20261021/FINAL-RECEIPT.json',
 'validation/see-proof-reuse-candidate-20261021/root-verification/NATIVE.json',
 'validation/see-proof-reuse-native-20261021/ROOT-FROZEN-SOURCE-GATES.json',
 'validation/see-proof-reuse-native-20261021/FINAL-RECEIPT.json',
 'validation/see-proof-reuse-native-20261021/release-parity-wrapper-attempt1/summary.json',
 'validation/see-proof-reuse-candidate-20261021/independent-source-review/REVIEW.json',
 'validation/see-proof-reuse-20261021/RESULT.json',
 'validation/hosted-see-proof-performance-20261021/actual-five-captures/PROVENANCE.json',
 'validation/hosted-see-proof-performance-20261021/ROOT-PREPARATION-REVIEW.json',
 'validation/hosted-see-proof-performance-20261021/ROOT-ONE-ATTEMPT-AUTHORIZATION.json',
 'validation/hosted-see-proof-performance-20261021/independent-review/REVIEW.json']
p=P/'common.py';s=p.read_text().replace("BASELINE='fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e'",f"BASELINE='{BASE}'").replace("CANDIDATE='2e151d019bc58dff2ab4e76e99ef99516af8d222'",f"CANDIDATE='{CAND}'").replace('forge-hosted-nearest-pawn-performance.yml','forge-hosted-see-proof-performance.yml')
a=s.index('REQUIRED_PROOFS=(');b=s.index('\n\nSTDIN=',a)
s=s[:a]+'EXPECTED_NODES=None  # Freeze only from actual24 native signature and producer evidence.\nREQUIRED_PROOFS='+repr(tuple(required))+'\n'+s[b:]
s=s.replace('Candidate21 source','Candidate24 source').replace("    fixed={'status':READY", "    if type(EXPECTED_NODES) is not int or EXPECTED_NODES<=0:raise ValueError('Candidate24 benchmark signature is not frozen')\n    fixed={'status':READY").replace("'source_file_counts':{'baseline':75,'candidate':76}","'source_file_counts':{'baseline':77,'candidate':77}").replace("'expected_nodes':321912","'expected_nodes':EXPECTED_NODES").replace("'bootstrap_seed':20261029",f"'bootstrap_seed':{SEED}").replace('Full current/native/Windows/parity proof binding missing','Full current/native/parity/capture proof binding missing')
p.write_text(s)
# Keep the performance-specific normal-stage/source-command/core-section schema intact.
p=P/'build_evidence.py';s=p.read_text();a=s.index('BASELINE_TESTS=');b=s.index('\ndef sha(',a)
names=('forge_tests','forge_correction_history_tests','forge_runtime_psqt_tests','forge_pawn_span_tests','forge_nearest_pawn_tests','forge_pv_metadata_tests','forge_tt_tests','forge_rule50_tests','forge_legal_witness_tests','match_tool_tests','windows_validation_tests','uci_regression','ponder_regression','ownbook_regression')
s=s[:a]+'BASELINE_TESTS='+repr(names)+"\nCANDIDATE_TESTS=BASELINE_TESTS\nSOURCE_FILE_COUNTS={'baseline':77,'candidate':77}\n"+s[b:];p.write_text(s)
p=P/'prepare_hosted.py';s=p.read_text().replace('Fresh actual20/21source/builds; baseline12/candidate13CTest','Fresh actual23/24source/builds; baseline14/candidate14CTest').replace('forge-hosted-nearest-pawn-performance.yml','forge-hosted-see-proof-performance.yml');p.write_text(s)
# Preserve all run_experiment/statistics/owned-process code; wrap actual main finalization.
p=P/'run_hosted.py';s=p.read_text();start=s.index('    try:\n',s.index('def main():'));end=s.index("\nif __name__=='__main__':main()",start)
body=s[start:end];remove="        try:os.sched_setaffinity(0,old_affinity)\n        except BaseException as error:report['affinity_restore_error']=repr(error)\n";assert remove in body;body=body.replace(remove,'')
outer="    operation_error=None\n    try:\n"+''.join('    '+line+'\n' for line in body.splitlines())
outer+='''    except BaseException as error:
        operation_error=error
        raise
    finally:
        try:os.sched_setaffinity(0,old_affinity)
        except BaseException as restore_error:
            # Independent of input rehash, host-context reads and persistence.
            report.update(status='failed_or_inconclusive_no_verified_gain',verified_hosted_gain=False,affinity_restore_error=repr(restore_error))
            try:common.save(a.out/'summary.json',report)
            except BaseException as save_error:restore_error.add_note('Could not persist affinity failure: '+repr(save_error))
            if operation_error is not None:
                operation_error.add_note('Original affinity restoration also failed: '+repr(restore_error))
                raise operation_error from restore_error
            raise
'''
s=s[:start]+outer+s[end:];ast.parse(s);p.write_text(s)
cfg=json.loads((OLD/'protocol.json').read_text());cfg.update(status='DRAFT_DISABLED_PENDING_ACTUAL24_NATIVE_SIGNATURE_CAPTURES_AND_REVIEWS',experiment='hosted-see-proof-performance-20261021-v1',baseline_sha=BASE,candidate_sha=CAND,baseline_version='6.4.23',candidate_version='6.4.24',expected_nodes=None,baseline_first_native_signature_nodes=292545,candidate_first_native_signature_nodes=None,source_file_counts={'baseline':77,'candidate':77},ab_sources='A baseline23, B candidate24',bootstrap_seed=SEED,source_gates_status='PENDING_ACTUAL24_NATIVE_42_AND_ACTIVE8',parity_review_status='PENDING_ACTUAL24_COLD_WARM_56_PARITY',capture_review_status='PENDING_ACTUAL23_AND24_FIVE_COMMAND_CAPTURES',root_review_status='PENDING',independent_review_status='PENDING',operational_qualification_status='BLOCKED_UNTIL_ACTUAL_PROOFS_AND_ROOT_ONE_ATTEMPT_AUTHORIZATION',correctness_evidence_sha256={},transport_captures={},workflow_status='DISABLED',workflow_sha256=None,mandatory_finite_proof_paths=required,actual_five_capture_gate='PENDING genuine23/24 five-command producer captures; no fabricated bytes or speed evidence',remaining_proof_inputs=['Actual24 complete native42/active8/PV56/TT12/newSEE504 and cold/warm parity','Actual first native24 benchmark signature; both parser constants stay None until a reviewed source-only binding','Actual23 and24 five-command producer captures and independent raw/schema review','Complete current source/proof maps, genuine root preparation/one-attempt authorization','Independent disabled and final enabled metadata review; root sole exact-payload trigger'],prototype_note='Parent23 observer evidence is only query-count/equality evidence, not throughput. Native24 and producer evidence are pending; no historical capture is relabeled24.',retention='All original commands/stdin/stdout/stderr/status/CPU/wall/preverdict/postcleanup facts; exact source TAR/cores/binaries/compilerflags/configs/14baseline+14candidate original CTest/LastTest; finally byte/mode rehash; verified split archives/upload/fresh results branch even on ordinary failure.',scope_exclusions=['Elo/playing strength','native Windows/Ryzen','absolute NPS from info','pure SEE kernel speed','general clock reliability'])
(P/'protocol.json').write_text(json.dumps(cfg,indent=2)+'\n')
w=(R/'.github/workflows/forge-hosted-nearest-pawn-performance.yml').read_text().replace('nearest-pawn','see-proof').replace('nearest-pawn','see-proof').replace('baseline12/candidate13','baseline14/candidate14').replace('fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e',BASE).replace('2e151d019bc58dff2ab4e76e99ef99516af8d222',CAND)
a=w.index('on:\n');b=w.index('permissions:',a);w=w[:a]+'on: []\n'+w[b:];w=w.replace("    if: ${{ github.event_name == 'push' && github.run_attempt == 1 }}","    if: ${{ false }}")
w=w.replace('# Restricted to one reviewed first-attempt push; retain failure evidence.','# DISABLED preparation only: no events and false job guard.').replace('# Final enabled metadata must pass independent review before sole root trigger.','# Actual native/capture gates and final enabled review are required before root sole trigger.')
(R/'.github/workflows/forge-hosted-see-proof-performance.yml').write_text(w)
(P/'README.md').write_text('''# Disabled Forge24 SEE proof-reuse throughput experiment

Preparation only. Workflow has `on: []` and a false job guard. No workflow, engine, build or timing process was launched while preparing this packet.

Baseline23 `1d3ed25bea2c8b781f7ee5a178af0f66061b3984`; candidate24 `7db08eac6ead99d641834c56ccec06a06600586a`. Both source exports require77 files and the same14 named CTests, nearest-pawn fifth/PV sixth. Matched GCC14 Release x86-64-v3 generic flags preserve arithmetic order and disallow LTO/fast-math. Complete source/core/executable/process/compile/CTest evidence is mandatory before readiness.

The actual24 first benchmark signature and native42/active8/cold-warm56 parity are pending. Both parser signature constants remain None; even fabricated READY status/proof declarations cannot authorize a benchmark until the scalar is genuinely bound and reviewed. The parent23 first native signature292545 is recorded separately, not presumed to be24 evidence. Actual23/24 five-command captures are mandatory; no old capture is relabeled24. Source-query counts and504 unit assertions are correctness/work-elimination evidence, not speed measurements.

The qualified21 timing/statistical design is retained: excluded ABBA warmup,15 same-binary A/A counterbalanced blocks, then31 A/B blocks only if both exact-child CPU and whole-process wall calibration gates pass. Each fresh process receives five `bench 11` commands plus quit. Total188 processes/940 bench commands,60s sample timeout,3600s timing work,690s build work. Seed20261102 is preregistered for10000 whole-block bootstrap draws. Positive gain requires both95% lower bounds greater than1 and all final bytes/modes unchanged; no3% floor. Any calibration/process/integrity fault stops acceptance, with no retries/rescue/pooling.

Owned process/helper461a and archive code remain byte-identical to qualified21. A known performance-main finalization weakness is repaired only here using the already-reviewed22/23 outer affinity-finally pattern: rehash/context/save failures cannot skip restoration; restoration failures invalidate any gain. Original21 code and a focused RED/GREEN fault test are retained. All original ordinary-failure evidence is archived/uploaded/published to a fresh unique see-proof results branch. Hard host termination may still prevent finally/upload.

No Elo, pure SEE kernel, Windows/Ryzen or Stockfish superiority claim follows from this protocol. Root must separately bind genuine native/source/capture proofs, review the enabled exact bytes, verify public exact payload, then make a sole authorized trigger. This disabled packet is not authority to launch.
''')
# A reproducible scoped diff; no production/Git mutation.
parts=[]
for p in sorted(P.iterdir()):
 before=(OLD/p.name).read_text() if (OLD/p.name).is_file() else ''
 if p.suffix in ('.py','.md','.json'):parts.extend(difflib.unified_diff(before.splitlines(True),p.read_text().splitlines(True),fromfile='qualified21/'+p.name,tofile='disabled24/'+p.name))
(V/'PACKAGE-ADAPTATION.diff').write_text(''.join(parts))
print(json.dumps({'status':'DRAFT_DISABLED24_PACKET_WRITTEN','files':len(list(P.iterdir())),'source_counts':cfg['source_file_counts'],'candidate_signature':None}))
