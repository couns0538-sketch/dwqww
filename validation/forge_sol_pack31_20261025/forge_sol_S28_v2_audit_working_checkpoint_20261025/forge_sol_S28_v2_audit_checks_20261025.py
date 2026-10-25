#!/usr/bin/env python3
"""Read-only S47-derived audits of explicit snapshots/metadata, not live AUTO-LOCK approval."""
from __future__ import annotations
import argparse,hashlib,json,re,stat
from pathlib import Path,PurePosixPath

MISSING=object(); DEPTHS={'11','13','16','20','22'}
SPEC_MISSING=['Original numbered 11-point first-AUTOLOCK checklist was not supplied; these checks derive from S47 prose.','CAP-LATE definition/fixtures were not supplied; no rule is inferred.']

def digest(value,n):return isinstance(value,str) and re.fullmatch('[0-9a-f]{'+str(n)+'}',value) is not None

def integer(value):return type(value) is int and value>=0

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)

# Only these explicit source/text suffixes may have CRLF folded. Assets and
# unknown suffixes are always raw, even if their contents happen to be ASCII.
TEXT_SOURCE_SUFFIXES=frozenset({'.c','.cc','.cpp','.cxx','.h','.hh','.hpp','.hxx',
 '.inc','.inl','.cmake','.py','.sh','.ps1','.txt','.md','.rst','.json','.csv',
 '.tsv','.yaml','.yml','.toml','.ini','.cfg'})

def normalized_file_bytes(path,data):
 if Path(path).suffix.lower() not in TEXT_SOURCE_SUFFIXES:return data,'RAW_UNSUPPORTED_SUFFIX'
 if b'\x00' in data:return data,'RAW_NUL_BYTES'
 try:data.decode('utf-8',errors='strict')
 except UnicodeDecodeError:return data,'RAW_INVALID_UTF8'
 return data.replace(b'\r\n',b'\n'),'CRLF_TO_LF_UTF8_TEXT'

def tree_snapshot(root,normalize=True,details=False):
 root=Path(root)
 if root.is_symlink():raise ValueError('Snapshot root is a symlink')
 if not root.exists():raise FileNotFoundError(str(root))
 if not root.is_dir():raise ValueError('Snapshot root is not a directory')
 result={};raw_hashes={};policies={}
 for p in sorted(root.rglob('*')):
  mode=p.lstat().st_mode
  if stat.S_ISLNK(mode):raise ValueError('Symlink in snapshot: '+p.relative_to(root).as_posix())
  if stat.S_ISDIR(mode):continue
  if not stat.S_ISREG(mode):raise ValueError('Nonregular snapshot entry: '+p.relative_to(root).as_posix())
  raw=p.read_bytes();data,policy=normalized_file_bytes(p,raw) if normalize else(raw,'RAW_REQUESTED')
  name=p.relative_to(root).as_posix();raw_hashes[name]=hashlib.sha256(raw).hexdigest()
  result[name]=hashlib.sha256(data).hexdigest();policies[name]=policy
 return {'raw_sha256':raw_hashes,'normalized_sha256':result,'normalization_policy':policies} if details else result

def netonly_tree(lock_dir,candidate_dir,expected_net_md5):
 """Hash every regular file in caller-defined source snapshots; skip nothing implicitly."""
 result={'status':'UNVERIFIED','diff':[],'normalization':'CRLF->LF only for explicitly supported UTF-8 source/text suffixes without NUL; binary/unknown always raw; no implicit skips','normalization_supported_suffixes':sorted(TEXT_SOURCE_SUFFIXES)}
 if not digest(expected_net_md5,32):return {**result,'status':'FAIL','reason':'Expected net MD5 must be 32 lowercase hex characters'}
 try:
  snapshots={'lock':tree_snapshot(lock_dir,details=True),'candidate':tree_snapshot(candidate_dir,details=True)}
  before,after=snapshots['lock']['normalized_sha256'],snapshots['candidate']['normalized_sha256']
  for field in ('raw_sha256','normalized_sha256','normalization_policy'):result[field]={key:value[field] for key,value in snapshots.items()}
  result['diff']=[{'path':k,'lock_sha256':before.get(k),'candidate_sha256':after.get(k)} for k in sorted(before.keys()|after.keys()) if before.get(k)!=after.get(k)]
  old_dirs={p.relative_to(lock_dir).as_posix() for p in Path(lock_dir).rglob('*') if p.is_dir()}
  new_dirs={p.relative_to(candidate_dir).as_posix() for p in Path(candidate_dir).rglob('*') if p.is_dir()}
  result['diff'] += [{'path':k+'/', 'directory_change':'added' if k in new_dirs else 'removed'} for k in sorted(old_dirs^new_dirs)]
  net=Path(candidate_dir)/'src/nnue_weights.inc'
  if not net.is_file():return {**result,'status':'FAIL','reason':'Candidate net absent'}
  raw=net.read_bytes();normalized,policy=normalized_file_bytes(net,raw)
  result['candidate_net_raw_md5']=hashlib.md5(raw).hexdigest();result['candidate_net_normalized_md5']=hashlib.md5(normalized).hexdigest()
  only_net=len(result['diff'])==1 and result['diff'][0]['path']=='src/nnue_weights.inc' and 'src/nnue_weights.inc' in before and 'src/nnue_weights.inc' in after
  okay=only_net and result['candidate_net_normalized_md5']==expected_net_md5
  return {**result,'status':'PASS' if okay else 'FAIL','reason':'Only existing net differs and policy-normalized MD5 matches' if okay else 'Source additions/removals, non-net differences, unchanged net, or wrong net MD5'}
 except ValueError as e:return {**result,'status':'FAIL','reason':str(e)}
 except OSError as e:return {**result,'reason':type(e).__name__+': '+str(e)}

def uci_option_name(line):
 """Validate basic UCI option metadata and return its case-insensitive name."""
 if not isinstance(line,str) or any(ord(c)<32 for c in line):raise ValueError('Invalid UCI option line')
 match=re.fullmatch(r'option name (\S(?:.*?\S)?) type (check|spin|combo|button|string)(?: (.*))?',line)
 if not match:raise ValueError('Expected option name ... type ... metadata')
 name,kind,payload=match.groups();payload=payload or ''
 if kind=='button' and payload:raise ValueError('Button option has unexpected metadata')
 if kind=='check' and payload not in ('default true','default false'):raise ValueError('Invalid check default')
 if kind=='spin':
  fields=re.fullmatch(r'default (-?\d+) min (-?\d+) max (-?\d+)',payload)
  if not fields:raise ValueError('Invalid spin default/min/max')
  default,minimum,maximum=map(int,fields.groups())
  if not minimum<=default<=maximum:raise ValueError('Spin default outside bounds')
 if kind=='string' and payload!='default' and not payload.startswith('default '):raise ValueError('Missing string default')
 if kind=='combo':
  choices=payload.split(' var ')
  if not choices[0].startswith('default ') or len(choices)<2 or any(not v for v in choices[1:]) or choices[0][8:] not in choices[1:]:raise ValueError('Invalid combo default/choices')
 return name.casefold()

def audit_packet(packet):
 """Validate eleven S47-derived checks; input metadata is evidence, never live state."""
 if not isinstance(packet,dict):return {'status':'FAIL','checks':[],'reason':'Packet must be an object','live_autolock_verified':False,'missing_spec_inputs':SPEC_MISSING}
 checks=[]
 def check(name,fields,fn):
  values=[packet.get(k,MISSING) for k in fields]
  try:
   status,reason=fn(*values)
  except (TypeError,ValueError,KeyError,AttributeError) as e:status,reason='FAIL','Invalid metadata: '+str(e)
  checks.append({'check':name,'status':status,'reason':reason})
 def unknown(values):return any(v is MISSING for v in values)
 def pair(a,b,valid,label):
  for v in (a,b):
   if v is not MISSING and not valid(v):return 'FAIL','Invalid '+label
  if unknown((a,b)):return 'UNVERIFIED','Missing '+label
  return ('PASS','Equal '+label) if canonical(a)==canonical(b) else('FAIL','Different '+label)
 def snapshots(a,b,root):
  valid=lambda v:isinstance(v,dict) and bool(v) and all(isinstance(k,str) and digest(h,64) for k,h in v.items())
  state=pair(a,b,valid,'old-lock SHA256 snapshots')
  if state[0]=='FAIL':return state
  if root is MISSING:return 'UNVERIFIED','Missing old-lock snapshot path'
  try:actual=tree_snapshot(root,normalize=False)
  except OSError as e:return 'UNVERIFIED','Old-lock snapshot unavailable: '+str(e)
  if b is not MISSING and b!=actual:return 'FAIL','Old-lock manifest is stale or not the complete current snapshot'
  return state
 check('01_old_lock_unchanged',['old_before','old_after','old_lock_dir'],snapshots)
 def directories(a,b,existed):
  if existed is not MISSING and type(existed) is not bool:return 'FAIL','new_dir_existed_before must be Boolean'
  if existed is True:return 'FAIL','New directory existed before transition'
  for p in (a,b):
   if p is not MISSING and (not isinstance(p,str) or not p):return 'FAIL','Invalid directory path'
  if unknown((a,b,existed)):return 'UNVERIFIED','Missing directory identity/history'
  x,y=Path(a).resolve(),Path(b).resolve()
  if x==y or x in y.parents or y in x.parents:return 'FAIL','Old/new snapshot directories overlap'
  return 'PASS','Distinct directories; supplied before-state says new directory absent'
 check('02_new_directory',['old_lock_dir','new_lock_dir','new_dir_existed_before'],directories)
 check('03_gated_net',['candidate_net_md5','gated_net_md5'],lambda a,b:pair(a,b,lambda v:digest(v,32),'net MD5'))
 def executable(a,b,fa,fb):
  states=[pair(a,b,lambda v:digest(v,64),'executable SHA256'),pair(fa,fb,lambda v:isinstance(v,str) and bool(v),'build flavour')]
  return next((s for s in states if s[0]=='FAIL'),next((s for s in states if s[0]=='UNVERIFIED'),('PASS','Same gated executable and build flavour')))
 check('04_gated_executable',['candidate_exe_sha256','gated_exe_sha256','candidate_build_flavour','gated_build_flavour'],executable)
 def benches(expected,first,repeat,reference):
  for v in (expected,first,repeat):
   if v is not MISSING and (not isinstance(v,dict) or set(v)!=DEPTHS or not all(type(n) is int and n>0 for n in v.values())):return 'FAIL','Bench requires exactly five depth keys and positive integer nodes (not Boolean)'
  if reference is not MISSING and not digest(reference,64):return 'FAIL','Invalid external fixed-reference SHA256'
  present=[v for v in (expected,first,repeat) if v is not MISSING]
  if len(present)>1 and any(v!=present[0] for v in present[1:]):return 'FAIL','Bench node drift against fixed reference or repeated run'
  if unknown((expected,first,repeat,reference)):return 'UNVERIFIED','Missing fixed-reference identity or bench run'
  return 'PASS','Both five-depth runs equal explicitly supplied fixed reference'
 check('05_bench_twice',['bench_expected','bench_first','bench_repeat','bench_reference_sha256'],benches)
 def perfts(a,b):
  for value,expected in ((a,4865609),(b,193690690)):
   if value is not MISSING and (not integer(value) or value!=expected):return 'FAIL','Perft/kiwipete mismatch or invalid count'
  return ('UNVERIFIED','Missing perft result') if unknown((a,b)) else('PASS','Both fixed perft5 totals exact')
 check('06_perfts',['perft5','kiwipete5'],perfts)
 def fma(v):
  if v is MISSING:return 'UNVERIFIED','Missing whole-executable FMA count'
  return ('PASS','Whole-executable FMA count zero') if type(v) is int and v==0 else('FAIL','FMA count nonzero or invalid integer')
 check('07_whole_fma',['whole_executable_fma'],fma)
 def uci(a,b,flavour):
  for v in (a,b):
   if v is not MISSING:
    if not isinstance(v,dict) or not isinstance(v.get('build_flavour'),str) or not isinstance(v.get('options'),list) or not v['options']:return 'FAIL','Missing/invalid UCI metadata or flavour'
    names=[uci_option_name(line) for line in v['options']]
    if len(names)!=len(set(names)):return 'FAIL','Duplicate UCI option names'
  if a is not MISSING and b is not MISSING and a!=b:return 'FAIL','UCI metadata or build flavours differ'
  for v in (a,b):
   if v is not MISSING and flavour is not MISSING and v['build_flavour']!=flavour:return 'FAIL','UCI flavour differs from candidate executable'
  return ('UNVERIFIED','Missing like-flavour UCI metadata') if unknown((a,b,flavour)) else('PASS','Exact like-flavour option metadata equal')
 check('08_uci_metadata',['uci_before','uci_after','candidate_build_flavour'],uci)
 def openings(gate,confirm):
  for v in (gate,confirm):
   if v is not MISSING and (not isinstance(v,dict) or any(k not in v or not integer(v[k]) for k in ('srand','start'))):return 'FAIL','Invalid gate/confirm srand/start'
  if unknown((gate,confirm)):return 'UNVERIFIED','Missing gate or confirm'
  return ('FAIL','Confirm reuses gate srand or start') if any(gate[k]==confirm[k] for k in ('srand','start')) else('PASS','Confirm srand and start both differ')
 check('09_fresh_confirm',['gate','confirm'],openings)
 def pins(before,after,review,actual_files,actual_patch):
  def files(value):
   if not isinstance(value,list):return False
   for row in value:
    if not isinstance(row,dict) or set(row)!={'path','before_sha256','after_sha256'}:return False
    path=row['path']
    if not isinstance(path,str) or not path or PurePosixPath(path).is_absolute() or '..' in PurePosixPath(path).parts or '\\' in path:return False
    if not digest(row['before_sha256'],64) or not digest(row['after_sha256'],64) or row['before_sha256']==row['after_sha256']:return False
   return len(value)==len({v['path'] for v in value})

  for v in (before,after):
   if v is not MISSING and (not isinstance(v,dict) or not v):return 'FAIL','Pins must be nonempty mappings'
  changes=MISSING
  if not unknown((before,after)):
   if set(before)!=set(after):return 'FAIL','Pin keys added/removed'
   changes={k for k in before if canonical(before[k])!=canonical(after[k])}
  if actual_files is not MISSING and not files(actual_files):return 'FAIL','Invalid actual pin file delta'
  if actual_patch is not MISSING and not digest(actual_patch,64):return 'FAIL','Invalid applied pin patch SHA256'
  no_files=(actual_files is MISSING or actual_files==[]) and actual_patch is MISSING
  if changes is MISSING and no_files:return 'UNVERIFIED','Missing pin snapshot'
  if not changes and no_files:return 'PASS','Pins/files unchanged'
  if review is MISSING:return 'FAIL','Edited pin/files lack reviewed allow-list'
  if not isinstance(review,dict) or not digest(review.get('review_sha256'),64) or not digest(review.get('patch_sha256'),64) or not isinstance(review.get('changes'),list):return 'FAIL','Invalid reviewed pin diff metadata'
  if actual_patch is MISSING or actual_files is MISSING:return 'FAIL','Edited pin/files lack actual applied patch/file proof'
  if review['patch_sha256']!=actual_patch:return 'FAIL','Applied pin patch differs from externally reviewed patch hash'
  expected_files=review.get('expected_file_changes')
  if not files(expected_files) or not expected_files:return 'FAIL','Missing/invalid reviewed per-file SHA256 delta'
  if canonical(sorted(actual_files,key=lambda v:v['path']))!=canonical(sorted(expected_files,key=lambda v:v['path'])):return 'FAIL','Actual file changes differ from externally reviewed allow-list'

  if changes is MISSING:return 'UNVERIFIED','Missing pin snapshot; supplied file proof matched review'
  allowed=review['changes']
  if len(allowed)!=len(changes) or any(not isinstance(v,dict) or set(v)!={'key','before','after'} for v in allowed):return 'FAIL','Reviewed changes do not exactly cover pin edits'
  if {v['key'] for v in allowed}!=changes:return 'FAIL','Unexpected or duplicate reviewed pin keys'
  if any(canonical(v['before'])!=canonical(before[v['key']]) or canonical(v['after'])!=canonical(after[v['key']]) for v in allowed):return 'FAIL','Edited pin values differ from reviewed diff'
  return 'PASS','Only exact externally reviewed patch, per-file hashes and pin changes'
 check('10_reviewed_pins',['pins_before','pins_after','reviewed_pin_diff','file_changes','applied_pin_patch_sha256'],pins)
 def netcheck(a,b,md5):
  if unknown((a,b,md5)):return 'UNVERIFIED','Missing net-only source snapshot input'
  result=netonly_tree(a,b,md5);return result['status'],result['reason']
 check('11_netonly_tree',['old_lock_dir','new_lock_dir','candidate_net_md5'],netcheck)
 status='FAIL' if any(c['status']=='FAIL' for c in checks) else('UNVERIFIED' if any(c['status']=='UNVERIFIED' for c in checks) else 'PASS')
 part_b='FAIL' if any(c['status']=='FAIL' for c in checks[:10]) else('UNVERIFIED' if any(c['status']=='UNVERIFIED' for c in checks[:10]) else 'PASS')
 return {'status':status,'part_b_status':part_b,'strict_netonly_status':checks[10]['status'],'classification':'REVIEWED_DELTA' if part_b=='PASS' and packet.get('file_changes') else 'SUPPLIED_S47_PACKET','scope':'Eleven checks derived from S47 prose; supplied metadata/source snapshots only','checks':checks,'live_autolock_verified':False,'missing_spec_inputs':SPEC_MISSING}

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
 t=sub.add_parser('netonly');t.add_argument('lock');t.add_argument('candidate');t.add_argument('expected_md5')
 p=sub.add_parser('packet');p.add_argument('input',type=Path);args=parser.parse_args()
 result=netonly_tree(args.lock,args.candidate,args.expected_md5) if args.command=='netonly' else audit_packet(json.loads(args.input.read_text()))
 print(json.dumps(result,indent=2,sort_keys=True));raise SystemExit(0 if result['status']=='PASS' else 1)
