#!/usr/bin/env python3
"""Read-only actual-receipt adapter application; writes only new skill audit files."""
import copy,hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent;S=R/'.agents/skills/validating-chess-strength';E=R/'validation/pawn-span-fill-native-20261020'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
checks=[]
def check(name,value):
 checks.append({'name':name,'pass':bool(value)})
 if not value:raise AssertionError(name)
def field(data,path,kind):
 for part in path.split('.'):
  if not isinstance(data,dict) or part not in data:raise ValueError('missing required field: '+path)
  data=data[part]
 if type(data) is not kind:raise ValueError('wrong field type: '+path)
 return data
# Fixed mapping is intentionally exact to this receipt revision, not a universal schema.
final=load(E/'FINAL-RECEIPT.json');snap=load(E/'ORIGINALS-FINAL-SHA256.json');rev='fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e';mappings=[]
def mapped(doc,label,path,kind,expected,meaning):
 value=field(doc,path,kind);check(label+'.'+path,value==expected);mappings.append({'receipt':label,'path':path,'type':kind.__name__,'expected':expected,'observed':value,'meaning':meaning})
mapped(final,'FINAL-RECEIPT.json','source_commit',str,rev,'Genuine frozen20 source, not historical19')
mapped(final,'FINAL-RECEIPT.json','native_ctests',int,36,'Total recorded CTests across profiles')
for profile in ['release','asan','tsan']:
 base='native_profiles.'+profile
 mapped(final,'FINAL-RECEIPT.json',base+'.attempts',int,1,'Explicit per-profile attempt count; not a default/retry inference')
 mapped(final,'FINAL-RECEIPT.json',base+'.ctest_count',int,12,'Recorded suites for this profile')
 mapped(final,'FINAL-RECEIPT.json',base+'.pawn_span_checks',int,37320,'Current20 pawn-span count')
 mapped(final,'FINAL-RECEIPT.json',base+'.runtime_psqt_checks',int,347,'Current20 runtime-PSQT count')
 data=final['native_profiles'][profile];receipt=E/data['receipt_path'];detail=load(receipt)
 check(profile+'_original_profile_receipt_hash',digest(receipt)==data['receipt_sha256'])
 check(profile+'_actual_profile_revision',detail['source_commit']==rev and detail['profile']==profile and detail['status']=='PASS')
 check(profile+'_actual_ctest_names_count',len(detail['ctest_names'])==12)
for label,count in [('source',75),('release',163),('asan',163),('tsan',163)]:
 files=field(snap,'trees.'+label+'.files',dict);check(label+'_snapshot_explicit_files_count',len(files)==count)
 mappings.append({'receipt':'ORIGINALS-FINAL-SHA256.json','path':'trees.'+label+'.files','type':'dict','expected_count':count,'observed_count':len(files),'meaning':'Per-root original inventory; not nonexistent flat snapshot files'})
check('no_invented_engine_gate_retries_field','engine_gate_retries' not in final)
negative=[]
for label,change in [('missing_attempt',lambda d:d['native_profiles']['release'].pop('attempts')),('bool_attempt',lambda d:d['native_profiles']['release'].__setitem__('attempts',True)),('string_attempt',lambda d:d['native_profiles']['release'].__setitem__('attempts','1'))]:
 altered=copy.deepcopy(final);change(altered)
 try:field(altered,'native_profiles.release.attempts',int)
 except ValueError as error:negative.append({'case':label,'blocked':True,'error':str(error)})
 else:raise AssertionError('negative control accepted '+label)
check('missing_and_wrong_type_fail_closed',len(negative)==3)
text=(S/'SKILL.md').read_text();front=text.split('---\n',2)[1];items=dict(line.split(': ',1) for line in front.strip().splitlines());check('frontmatter_exact_required_simple_scalars',set(items)=={'name','description'} and re.fullmatch('[a-z0-9-]+',items['name']) and items['description'].startswith('Use when ') and len(front)<1024)
links=[]
for name in ['SKILL.md','scenarios.md']:
 for target in re.findall(r'\]\(([^)]+)\)',(S/name).read_text()):
  if '://' not in target and not target.startswith('#'):
   path=(S/target.split('#')[0]).resolve();links.append({'from':name,'target':target,'exists':path.is_file()});check('relative_link:'+name+':'+target,path.is_file())
prior=load(D/'PRIOR-PROOF-HASHES.json');check('all_prior_proofs_unchanged',all((R/p).is_file() and digest(R/p)==h for p,h in prior.items()))
controls=load(D/'SCHEMA-CONTROL.json');check('original_schema_inputs_unchanged',all(Path(p).is_file() and digest(Path(p))==h for p,h in controls['inputs'].items()))
check('before_skill_copies_retained',all((D/('before-'+name)).is_file() for name in ['SKILL.md','scenarios.md']))
producer=E/'run-frozen-validation.py';check('actual_producer_count_dialect_inspected',all(key in producer.read_text() for key in ['expected_pawn_span_checks','expected_runtime_psqt_checks','expected_ctest_per_profile']))
report={'status':'PASS_SOURCE_ONLY_SCHEMA_APPLICATION','checks':checks,'check_count':len(checks),'field_mappings':mappings,'negative_controls':negative,'links':links,'source_revision':rev,'input_sha256':{str(p):digest(p) for p in [E/'FINAL-RECEIPT.json',E/'ORIGINALS-FINAL-SHA256.json',producer,S/'SKILL.md',S/'scenarios.md']},'prior_proof_files_unchanged':len(prior),'engine_build_timing_network_git_execution':False,'scope':'Fresh deterministic source-only field retrieval and negative controls, not a fresh-agent behavior study, universal engine validation, speed/Elo evidence or demonstrated causal efficiency improvement.'}
(D/'APPLICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'checks':len(checks),'prior_proofs':len(prior),'negative_controls':len(negative),'relative_links':len(links)}))
