"""Read-only explicit-base checks; metadata/links reused from prior skill validator."""
from pathlib import Path,PurePosixPath
import hashlib,json,re,stat,tempfile,datetime,traceback,sys
ROOT=Path('/workspace/dwqww');OUT=ROOT/'validation/checksum-base-skill-20261021'
SKILL=ROOT/'.agents/skills/validating-chess-strength/SKILL.md'
NATIVE=ROOT/'validation/tt-refresh-native-20261021';CAPTURE=ROOT/'validation/hosted-tt-refresh-strength-20261021/capture-preparation'
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  while data:=stream.read(1048576):h.update(data)
 return h.hexdigest()
def regular_no_symlinks(path):
 current=Path(path.anchor)
 for part in path.parts[1:]:
  current=current/part;s=current.lstat()
  if stat.S_ISLNK(s.st_mode):raise ValueError('Symlink component: '+str(current))
 if not stat.S_ISREG(path.lstat().st_mode):raise ValueError('Notregular: '+str(path))
def validate(lines,base,scope,hash_files=True):
 if not isinstance(base,Path) or not base.is_absolute():raise ValueError('Explicit absolute base required')
 if not isinstance(scope,Path) or not scope.is_absolute():raise ValueError('Explicit absolute scope required')
 rows=[];seen=set()
 for line in lines:
  m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line)
  if not m:raise ValueError('Malformed checksum record')
  expected,name=m.groups();relative=PurePosixPath(name)
  if relative.is_absolute() or any(p in ('','.','..') for p in name.split('/')) or str(relative)!=name or any(c in name for c in ['\\',':','\x00']):raise ValueError('Unsafe or noncanonical entry')
  path=base/name
  if not path.is_relative_to(scope):raise ValueError('Outside allowed proof scope')
  if str(path) in seen:raise ValueError('Duplicate resolved entry')
  seen.add(str(path));regular_no_symlinks(path);rows.append((expected,name,path))
 result=[]
 for expected,name,path in rows:
  before=path.stat();actual=sha(path) if hash_files else None;after=path.stat()
  if (before.st_size,before.st_mtime_ns,before.st_mode)!=(after.st_size,after.st_mtime_ns,after.st_mode):raise ValueError('Changed while reading: '+str(path))
  if hash_files and actual!=expected:raise ValueError('SHA mismatch: '+str(path))
  result.append({'entry':name,'resolved':str(path),'expected_sha256':expected,'observed_sha256':actual,'size':after.st_size,'unchanged_during_read':True})
 return result
report={'status':'RUNNING','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'engines_builds_matches_git_network_or_installation_executed':False,'checks':{},'manifests':[],'negative_controls':[]}
try:
 text=SKILL.read_text();front=text.split('---\n',2)[1];metadata={}
 for line in front.splitlines():
  key,value=line.split(':',1)
  assert key not in metadata
  metadata[key]=value.strip()
 assert text.startswith('---\n') and len(front)<=1024 and set(metadata)=={'name','description'} and re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*',metadata['name']) and metadata['name']==SKILL.parent.name and metadata['description'].startswith('Use when ') and len(metadata['description'])<500
 report['metadata']=metadata;report['checks']['frontmatter_current_two_scalar_schema_valid']=True
 links=[]
 for p in [SKILL,SKILL.with_name('scenarios.md')]:
  for target in re.findall(r'(?<!!)\[[^\]]+\]\(([^)]+)\)',p.read_text()):
   if '://' in target or target.startswith('#'):continue
   resolved=(p.parent/target.split('#',1)[0]).resolve();assert resolved.is_file()
   links.append({'source':str(p.relative_to(ROOT)),'target':target,'resolved':str(resolved.relative_to(ROOT))})
 expected_links=[]
 for source_path,snapshot_name in [(SKILL,'before-SKILL.md'),(SKILL.with_name('scenarios.md'),'before-scenarios.md')]:
  for target in re.findall(r'(?<!!)\[[^\]]+\]\(([^)]+)\)',(OUT/snapshot_name).read_text()):
   if '://' not in target and not target.startswith('#'):expected_links.append((str(source_path.relative_to(ROOT)),target))
 assert [(x['source'],x['target']) for x in links]==expected_links
 report['relative_links']=links;report['relative_link_count']=len(links);report['checks']['exact_existing_link_set_retained']=True
 change=json.loads((OUT/'CHANGE.json').read_text());assert text.replace(change['inserted_paragraph'],'',1)==(OUT/'before-SKILL.md').read_text() and text.count(change['inserted_paragraph'])==1
 assert SKILL.with_name('scenarios.md').read_bytes()==(OUT/'before-scenarios.md').read_bytes()
 report['checks']['one_insertion_all_preexisting_AA_stopping_schema_lifecycle_bytes_unchanged']=True;report['checks']['scenarios_unchanged']=True
 old=json.loads((ROOT/'validation/strength-skill-cleanup-20261020/OLD-PROOF-PRESERVATION.json').read_text());assert all(sha(ROOT/path)==h for path,h in old.items());report['checks']['six_original_prior_proofs_unchanged']=len(old)==6
 contracts=[('native',NATIVE/'EVIDENCE-SHA256SUMS',NATIVE,NATIVE,138,'native-EVIDENCE.before'),('capture',CAPTURE/'SUPPORT-SHA256SUMS',ROOT,CAPTURE,19,'capture-SUPPORT.before')]
 for label,manifest,base,scope,count,snapshot in contracts:
  before=manifest.read_bytes();assert before==(OUT/snapshot).read_bytes();lines=before.decode().splitlines();assert len(lines)==count
  samples=[{'entry':line.split('  ',1)[1],'resolved':str(base/line.split('  ',1)[1])} for line in lines[:3]]
  validated=validate(lines,base,scope);assert manifest.read_bytes()==before
  report['manifests'].append({'name':label,'manifest':str(manifest.relative_to(ROOT)),'manifest_sha256':sha(manifest),'explicit_base':str(base),'allowed_scope':str(scope),'sample_exact_paths_inspected':samples,'record_count':len(validated),'entries':validated,'manifest_unchanged':True})
 def reject(label,lines,base,scope):
  try:validate(lines,base,scope)
  except (ValueError,FileNotFoundError,NotADirectoryError) as error:report['negative_controls'].append({'name':label,'rejected':True,'type':type(error).__name__,'message':str(error)});return
  raise AssertionError('Negativecontrolaccepted: '+label)
 native=(NATIVE/'EVIDENCE-SHA256SUMS').read_text().splitlines();capture=(CAPTURE/'SUPPORT-SHA256SUMS').read_text().splitlines()
 reject('wrong_native_repository_base',native,ROOT,NATIVE)
 reject('wrong_capture_namespace_base',capture,CAPTURE,CAPTURE)
 reject('missing_explicit_base',native,None,NATIVE)
 reject('duplicate_manifest_entry',[native[0],native[0]],NATIVE,NATIVE)
 h= native[0].split('  ',1)[0]
 reject('parent_traversal',[h+'  ../outside'],NATIVE,NATIVE)
 reject('absolute_entry',[h+'  '+str(NATIVE/'ACTIVE-UCI-PROTOCOL.json')],NATIVE,NATIVE)
 reject('normalizing_dot_entry',[h+'  ./ACTIVE-UCI-PROTOCOL.json'],NATIVE,NATIVE)
 with tempfile.TemporaryDirectory(prefix='checksum-base-skill-data-',dir='/tmp') as temp:
  fixture=Path(temp);payload=fixture/'payload.txt';payload.write_bytes(b'data-only checksum fixture\n');(fixture/'link.txt').symlink_to(payload)
  reject('symlink_component',[sha(payload)+'  link.txt'],fixture,fixture)
 report['hashes_verified']=sum(x['record_count'] for x in report['manifests']);assert report['hashes_verified']==157 and len(report['negative_controls'])==8
 note=ROOT/'validation/hosted-tt-refresh-strength-20261021/capture-preparation/ROOT-PREAUTH-CHECK-NOTE.json';assert note.read_bytes()==(OUT/'ROOT-PREAUTH-CHECK-NOTE.original.json').read_bytes()
 report['checks']['original_preauth_failure_note_unchanged']=True;report['skill_sha256']=sha(SKILL);report['global_or_cloud_skill_installation_claim']=False;report['status']='PASS_LOCAL_SKILL_AND_157_READONLY_HASHES_WITH_8_NEGATIVES'
except Exception as error:
 report.update(status='FAILED',error_type=type(error).__name__,error=str(error));traceback.print_exc()
finally:
 with (OUT/'CHECKS-corrected.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['manifests','relative_links','metadata']},indent=2))
sys.exit(0 if report['status'].startswith('PASS_') else 1)
