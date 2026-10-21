"""Read-only binding of historical prototype source to frozen21; no probe replay."""
from pathlib import Path
import hashlib,json,stat,difflib
REPO=Path('/workspace/dwqww');HERE=Path(__file__).resolve().parent
V=REPO/'validation/nearest-pawn-distance-20261020';N=REPO/'validation/nearest-pawn-native-20261020'
P=Path('/workspace/.cloud-setup/nearest-pawn-prototype-source');F=Path('/workspace/.cloud-setup/nearest-pawn-native-source')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
metadata=[V/'EXPECTED-SOURCE-76.json',V/'ACTUAL21-SOURCE-PREPARATION.json',V/'public-diff/PROBE-RECEIPT.json',V/'public-diff/public-diff-attempt1/RESULT.json',V/'public-diff/public-diff-attempt1/source-maps-before.json',V/'public-diff/public-diff-attempt1/source-maps-after.json',N/'ROOT-FROZEN-SOURCE-GATES.json',V/'root-verification/NATIVE.json']
a=read(metadata[0]);b=read(metadata[6])['inputs'];assert len(a)==len(b)==76 and set(a)==set(b)
paths=metadata+[P/name for name in a]+[F/name for name in b]
def snapshot():
 out={}
 for p in paths:
  assert p.is_file() and not p.is_symlink();out[str(p)]={'sha256':sha(p),'mode':stat.S_IMODE(p.stat().st_mode),'bytes':p.stat().st_size}
 return out
before=snapshot()
for tree,expected in [(P,a),(F,b)]:
 assert {p.relative_to(tree).as_posix() for p in tree.rglob('*') if p.is_file()}==set(expected)
 assert all(sha(tree/name)==digest for name,digest in expected.items())
prep=read(metadata[1]);assert prep['prototype_source_sha256']==a and prep['candidate_source_sha256']==b
assert read(metadata[4])==read(metadata[5]);assert read(metadata[4])['prototype21_version20']==a
receipt=read(metadata[2]);result=read(metadata[3])
assert receipt['source_commit'] is None and result['source_commit'] is None
assert receipt['prototype_version']==result['prototype_version']=='6.4.20'
assert receipt['rows']==result['rows']==95 and receipt['compared_integer_fields']==result['compared_integer_fields']==61465
for rel in ['public-diff-attempt1/RESULT.json','public-diff-attempt1/source-maps-before.json','public-diff-attempt1/source-maps-after.json']:
 assert receipt['files_sha256'][rel]==sha(V/'public-diff'/rel)
assert read(metadata[6])['source_commit']=='2e151d019bc58dff2ab4e76e99ef99516af8d222'
root=read(metadata[7]);assert root['status']=='PASS_ROOT_FULL_NATIVE21_ORIGINALS_AND_GIT_SOURCE_REVIEW' and root['source_commit']==read(metadata[6])['source_commit'] and root['source_git_blobs_verified']==76
changed=[k for k in a if a[k]!=b[k]];assert changed==['CMakeLists.txt','src/uci.cpp']
diffs={}
for name in changed:
 old=(P/name).read_text();new=(F/name).read_text();assert old.count('6.4.20')==1 and old.replace('6.4.20','6.4.21')==new
 diffs[name]=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='prototype/'+name,tofile='frozen21/'+name))
protected=[name for name in a if name.startswith(('include/','src/')) and name!='src/uci.cpp'];assert all(a[name]==b[name] for name in protected)
after=snapshot();assert before==after
out={'status':'PASS_SOURCE_ONLY_PROTOTYPE_SCOPE_BINDING_NOT_NEW_PROBE','candidate_source_commit':root['source_commit'],'historical_probe_source_commit':None,'historical_probe_version':'6.4.20','source_files_each':76,'only_changed_files':changed,'exact_changes':diffs,'protected_engine_inputs_identical':len(protected),'historical_rows':95,'historical_integer_fields':61465,'consumed_inputs':before,'final_inputs_byte_mode_equal':True,'engine_compiler_probe_git_actions':0,'qualification':'Historical95-row prototype evidence retains source_commit:null/version20. All76 source inputs verified; only one version string each in CMakeLists.txt and src/uci.cpp differs. Fresh actual21 native gates are separate. This is source correspondence, not a claim that historical probes executed frozen21.'}
(HERE/'PROTOTYPE-SOURCE-SCOPE.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'status':out['status'],'source_files_each':76,'changed':changed,'protected_inputs':len(protected),'inputs':len(before)}))
