"""Apply only root-authorized six exact proposal files, no launch or Git."""
import hashlib,json,shutil,stat
from pathlib import Path
R=Path('/workspace/dwqww');V=R/'validation/hosted-see-proof-performance-20261021';D=V/'ready-binding-phase3';P=R/'.github/hosted-see-proof-performance';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proposal=json.loads((D/'PROPOSED-BINDING.json').read_text());assert proposal['status']=='PASS_ACTUAL_READY_PROPOSAL_NOT_APPLIED_NOT_LAUNCHED'
assert sha(D/'proposals/common.py')=='6d7dbc4ec362012aa913f999e31fe8f5e2725ed1bc1d23cbbeac3c17f10b7520'
assert sha(D/'proposals/analysis.py')=='d386c0f42b48a023eb65c7f38e5e1fa6ef3f7120f05a9f63f8ca7d4c054cfe9c'
assert sha(D/'proposals/forge-hosted-see-proof-performance.yml')=='f8a14a43ea60fb9b23af3d23f9323a80dfb2c513e02305ace50dba0a389301a5'
for name,row in proposal['frozen_inputs'].items():
 p=Path(name);assert sha(p)==row['sha256'] and stat.S_IMODE(p.stat().st_mode)==row['mode'],name
before=D/'before-ready';before.mkdir()
for p in sorted(P.rglob('*'))+[R/'.github/workflows/forge-hosted-see-proof-performance.yml']:
 if p.is_file():
  t=before/p.relative_to(R);t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,t)
tests={p.relative_to(R).as_posix():sha(p) for p in V.glob('test_*.py')};assert len(tests)==6
(D/'BEFORE-READY.json').write_text(json.dumps({'status':'PRESERVED_AUTHORIZED_TRANSITION_PREIMAGE','frozen_inputs':proposal['frozen_inputs'],'test_sources_sha256':tests,'root_launch_authorized_now':False},indent=2)+'\n')
assert len(proposal['proposed_replacements'])==6
for name,row in proposal['proposed_replacements'].items():
 p=Path(name);q=Path(row['proposal_path']);assert sha(p)==row['current_sha256'] and sha(q)==row['sha256'] and stat.S_IMODE(p.stat().st_mode)==row['current_mode']
 p.write_bytes(q.read_bytes());assert sha(p)==row['sha256'] and stat.S_IMODE(p.stat().st_mode)==row['current_mode']
expected=dict(proposal['frozen_inputs'])
for name,row in proposal['proposed_replacements'].items():expected[name]={'sha256':row['sha256'],'mode':row['current_mode']}
for name,row in expected.items():
 p=Path(name);assert sha(p)==row['sha256'] and stat.S_IMODE(p.stat().st_mode)==row['mode']
for name,digest in tests.items():assert sha(R/name)==digest
receipt={'status':'APPLIED_EXACT_ROOT_AUTHORIZED_READY_PROPOSAL_NOT_LAUNCHED','proposal_sha256':sha(D/'PROPOSED-BINDING.json'),'changed_paths':list(proposal['proposed_replacements']),'after_files':{n:{'sha256':v['sha256'],'mode':v['current_mode']} for n,v in proposal['proposed_replacements'].items()},'actualproofs':proposal['actual_proof_count'],'frozen_inputs':expected,'tests_unchanged':True,'test_source_sha256':tests,'root_authorization_unchanged':sha(V/'ROOT-ONE-ATTEMPT-AUTHORIZATION.json')==proposal['root_authorization_sha256'],'no_launch':True,'engines_builds_helpers_tests_git_network_workflow_actions':0}
(D/'APPLIED.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':receipt['status'],'changed_files':6,'proofs':receipt['actualproofs'],'frozen_inputs':len(expected),'protocol_sha256':sha(P/'protocol.json'),'workflow_sha256':sha(R/'.github/workflows/forge-hosted-see-proof-performance.yml'),'inventory_sha256':sha(P/'PACKAGE-SHA256SUMS')}))
