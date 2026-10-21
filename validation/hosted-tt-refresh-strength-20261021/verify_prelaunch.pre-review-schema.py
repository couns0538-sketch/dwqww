"""Root final data-only authorization gate: no engine, build or trigger."""
import hashlib, io, json, stat, subprocess
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
R=Path('/workspace/dwqww'); V=Path(__file__).resolve().parent
P=R/'.github/hosted-tt-refresh-strength'; W=R/'.github/workflows/forge-hosted-tt-refresh-strength.yml'
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def facts(p): return {'sha256':sha(p),'mode':stat.S_IMODE(p.stat().st_mode)}
def rehash(m):
 for name, expected in m.items():
  p=Path(name); assert p.is_file() and not p.is_symlink(),name
  assert facts(p)==expected,name
 return len(m)
def local_manifest(base,name):
 seen=set()
 for line in (base/name).read_text().splitlines():
  digest,rel=line.split('  ',1); p=PurePosixPath(rel)
  assert not p.is_absolute() and '..' not in p.parts and rel not in seen,rel
  seen.add(rel); path=base/rel
  assert path.resolve().is_relative_to(base.resolve()) and not path.is_symlink(),rel
  assert sha(path)==digest,rel
 return len(seen)
review=read(V/'independent-final-enabled-review/FINAL-REVIEW.json')
assert review['status']=='PASS_FINAL_ENABLED_METADATA_REVIEW_NO_TRIGGER'
review_records=local_manifest(V/'independent-final-enabled-review','SHA256SUMS')
auth=read(V/'ROOT-ONE-ATTEMPT-AUTHORIZATION.json'); assert auth['authorized'] is True and auth['attempts']==1
assert auth['retry_resume_pool_allowed'] is False
cfg=read(P/'protocol.json'); assert cfg['status']=='PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH'
assert cfg['baseline_sha']=='ff2e269c6058be84456e3b98344826d17b0056eb'
assert cfg['candidate_sha']=='1d3ed25bea2c8b781f7ee5a178af0f66061b3984'
for name,digest in auth['reviewed_execution_code_sha256'].items(): assert sha(R/name)==digest,name
assert len(auth['reviewed_execution_code_sha256'])==6
ready=read(V/'ready-transition/READY-METADATA.json'); frozen=ready['frozen_inputs'].copy()
doc=read(V/'ready-documentation/RECEIPT.json')
assert set(doc['changed_paths'])=={str(P/'README.md'),str(P/'PACKAGE-SHA256SUMS')}
for name in doc['changed_paths']:
 assert frozen[name]==doc['before'][name],name
 frozen[name]=doc['after'][name]
assert rehash(frozen)==504
for name,digest in cfg['correctness_evidence_sha256'].items():
 rel=PurePosixPath(name); assert not rel.is_absolute() and '..' not in rel.parts,name
 assert sha(R/name)==digest,name
assert len(cfg['correctness_evidence_sha256'])==317
inventory=0
for line in (P/'PACKAGE-SHA256SUMS').read_text().splitlines():
 digest,name=line.split('  ',1); assert sha(R/name)==digest,name; inventory+=1
assert inventory==24
capture=read(V/'capture-preparation/actual-five-captures/PROVENANCE.json'); assert rehash(capture['frozen_inputs'])==189
scope=read(V/'ready-binding-preparation/SOURCE-GATE.json')
assert len(scope['changed_paths'])==4 and scope['unchanged_count']==73
source_blobs=0
for label,ref in [('baseline',cfg['baseline_sha']),('candidate',cfg['candidate_sha'])]:
 m=scope['source_maps'][label]; assert len(m)==77
 result=subprocess.run(['git','cat-file','--batch'],cwd=R,input=''.join(ref+':'+n+'\n' for n in m).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
 assert not result.stderr; stream=io.BytesIO(result.stdout)
 for name,digest in m.items():
  header=stream.readline().decode().split(); assert len(header)==3 and header[1]=='blob',name
  data=stream.read(int(header[2])); assert stream.read(1)==b'\n'
  assert hashlib.sha256(data).hexdigest()==digest,name
  if label=='candidate': assert sha(R/name)==digest,name
  source_blobs+=1
 assert not stream.read()
for name,expected in read(V/'IMMUTABLE22-REFERENCES.json').items(): assert sha(R/name)==expected['sha256'],name
prior=subprocess.run(['git','ls-remote','origin','refs/heads/forge/hosted-tt-refresh-strength-20261021-*'],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
(V/'ROOT-PRIOR-TRIGGERS.stdout').write_bytes(prior.stdout);(V/'ROOT-PRIOR-TRIGGERS.stderr').write_bytes(prior.stderr)
assert not prior.stdout,'Previous23trigger exists; do not duplicate'
record={'status':'ROOT_FINAL_ENABLED_REVIEW_FRESH504_REHASH_PASS_AUTHORIZE_SOLE_TRIGGER_AFTER_FIXED_PAYLOAD_PUBLIC_READBACK','utc':datetime.now(timezone.utc).isoformat(),'baseline_sha':cfg['baseline_sha'],'candidate_sha':cfg['candidate_sha'],'final_review_sha256':sha(V/'independent-final-enabled-review/FINAL-REVIEW.json'),'final_review_records_rehashed':review_records,'protocol_sha256':sha(P/'protocol.json'),'workflow_sha256':sha(W),'inventory_sha256':sha(P/'PACKAGE-SHA256SUMS'),'proofs':317,'consumed_inputs_rehashed':504,'capture_byte_mode_inputs_rehashed':189,'actual_git_source_blobs_verified':source_blobs,'execution_code_pins':6,'previous_triggers_found':0,'one_attempt_only':True,'public_readback':'REQUIRED_BEFORE_TRIGGER','frozen_inputs':frozen,'engine_build_trigger_execution':False,'verifier_sha256':sha(Path(__file__))}
with (V/'ROOT-FINAL-PRELAUNCH.json').open('x') as f:f.write(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k!='frozen_inputs'}))
