"""Root-authorized four-file metadata/signature transition; no engine or Git."""
from pathlib import Path
import json,hashlib,shutil,difflib,stat
R=Path('/workspace/dwqww');V=R/'validation/hosted-tt-refresh-strength-20261021';H=Path(__file__).resolve().parent;P=R/'.github/hosted-tt-refresh-strength';W=R/'.github/workflows/forge-hosted-tt-refresh-strength.yml';B=V/'ready-binding-preparation';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=json.loads((B/'PROPOSED-BINDING.json').read_text());assert sha(B/'PROPOSED-BINDING.json')=='4c17088cb7c3a39d91da1ade6f8d295eb98fe0dcc427e99226411109075d41b4';assert d['status']=='PASS_COMPLETE_PROPOSED_READY_BINDING_ONLY_NO_CANONICAL_EDIT_OR_TRIGGER';assert len(d['frozen_inputs'])==504 and d['proofs']==317
for name,facts in d['frozen_inputs'].items():
 p=Path(name);assert not p.is_symlink() and sha(p)==facts['sha256'] and stat.S_IMODE(p.stat().st_mode)==facts['mode'],name
for name,digest in d['proposed_protocol']['correctness_evidence_sha256'].items():assert sha(R/name)==digest,name
before=H/'before';before.mkdir(exist_ok=False)
paths=[P/'protocol.json',P/'run_hosted.py',W,P/'PACKAGE-SHA256SUMS']
originals={str(p.relative_to(R)):{'sha256':sha(p),'mode':stat.S_IMODE(p.stat().st_mode)} for p in paths}
for p in paths:shutil.copy2(p,before/p.name)
(before/'FULL-504-INPUTS.json').write_text(json.dumps(d['frozen_inputs'],indent=2)+'\n')
(before/'FOUR-FILES.json').write_text(json.dumps(originals,indent=2)+'\n')
(before/'TEST-SOURCE-HASHES.json').write_text(json.dumps({str(p.relative_to(R)):sha(p) for p in V.glob('test_*.py')},indent=2)+'\n')
shutil.copy2(V/'test_draft_gates.py',before/'test_draft_gates.py')
(P/'protocol.json').write_text(json.dumps(d['proposed_protocol'],indent=2)+'\n')
shutil.copy2(B/'PROPOSED-run_hosted.py',P/'run_hosted.py');(P/'run_hosted.py').chmod(originals[str((P/'run_hosted.py').relative_to(R))]['mode'])
W.write_text(d['proposed_workflow_text'])
lines=(before/'PACKAGE-SHA256SUMS').read_text().splitlines();assert len(lines)==24
(P/'PACKAGE-SHA256SUMS').write_text(''.join(sha(R/line[66:])+'  '+line[66:]+'\n' for line in lines))
changed=[]
for name,facts in d['frozen_inputs'].items():
 p=Path(name)
 if sha(p)!=facts['sha256'] or stat.S_IMODE(p.stat().st_mode)!=facts['mode']:changed.append(name)
assert set(changed)=={str(p) for p in paths},changed
for p in paths:(H/(p.name+'.diff')).write_text(''.join(difflib.unified_diff((before/p.name).read_text().splitlines(True),p.read_text().splitlines(True),fromfile='disabled/'+p.name,tofile='ready/'+p.name)))
for name,digest in d['proposed_protocol']['correctness_evidence_sha256'].items():assert sha(R/name)==digest,name
for name,facts in json.loads((V/'IMMUTABLE22-REFERENCES.json').read_text()).items():assert sha(R/name)==facts['sha256'],name
result={'status':'APPLIED_EXACT_ROOT_AUTHORIZED_FOUR_FILE_PROPOSAL_NOT_LAUNCHED','proposal_sha256':sha(B/'PROPOSED-BINDING.json'),'initial504_inputs_verified':504,'proofs317_unchanged':317,'changed_paths':changed,'after_files':{str(p.relative_to(R)):{'sha256':sha(p),'mode':stat.S_IMODE(p.stat().st_mode)} for p in paths},'original22_unchanged':True,'tests_modified':False,'engine_git_hosted_actions':0}
(H/'APPLIED.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
