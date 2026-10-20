"""Read package/historical proof bytes and write this preparation's static evidence only."""
from pathlib import Path
import hashlib,importlib.util,json
EV=Path(__file__).resolve().parent;ROOT=EV.parents[1];PKG=ROOT/'.github/hosted-pawn-span-performance'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
records={}
for p in sorted((EV/'skills').glob('*.READ-RESULT.json')):
    d=json.loads(p.read_text());raw=d['actual_tool_result']['contents'];skill=p.with_name(p.name.replace('.READ-RESULT.json','.SKILL.md'))
    assert skill.read_text()==raw
    records[d['package']]={'resource':d['actual_tool_result']['resource'],'read_result_sha256':sha(p),'contents_sha256':sha(skill),'contents_matches_actual_tool_result':True}
save(EV/'skills/PROVENANCE.json',{'scope':'Actual tools.skills__read succeeded in this preparer subagent; root direct cloud reads were unavailable. This is not a root/global installation claim.','records':records,'project_strength_skill':{'path':'.agents/skills/validating-chess-strength/SKILL.md','sha256':sha(ROOT/'.agents/skills/validating-chess-strength/SKILL.md')}})
workflow=ROOT/'.github/workflows/forge-hosted-pawn-span-performance.yml';text=workflow.read_text();assert 'on: []' in text and '    if: false' in text and '\n  push:' not in text
spec=importlib.util.spec_from_file_location('prepared_common',PKG/'common.py');common=importlib.util.module_from_spec(spec);spec.loader.exec_module(common);cfg=json.loads((PKG/'protocol.json').read_text())
assert cfg['bootstrap_seed']==20261028 and not cfg['transport_captures'] and not cfg['correctness_evidence_sha256']
try:common.require_ready(cfg)
except ValueError as error:blocked=str(error)
else:raise AssertionError('Draft became READY')
paths=common.inventory(ROOT,PKG);frozen=common.snapshot(paths);assert common.rehash(frozen)['status']=='passed'
save(EV/'PREPARER-STATIC-CHECKS.json',{'status':'PASS_DISABLED_PREPARATION_ONLY','workflow_sha256':sha(workflow),'workflow_disabled':True,'blocked_qualification_gate_observed':blocked,'baseline_sha':cfg['baseline_sha'],'candidate_sha':cfg['candidate_sha'],'source_identity_scope':'Frozen identity only; complete native/Windows/captures/reviews remain pending','actual20_native_windows_capture_source_qualification':'BLOCKED_PENDING_GENUINE_INPUTS','package_inventory_paths_including_manifest':len(paths),'package_manifest_sha256':sha(PKG/'PACKAGE-SHA256SUMS'),'frozen_package_workflow_bytes_modes':frozen,'final_rehash':common.rehash(frozen),'actual_candidate20_captures_in_package':0,'engine_compiler_bench_network_git_launches':0})
print('PASS disabled workflow, rejected qualification, exact package byte/mode rehash and scoped skill-read provenance.')
