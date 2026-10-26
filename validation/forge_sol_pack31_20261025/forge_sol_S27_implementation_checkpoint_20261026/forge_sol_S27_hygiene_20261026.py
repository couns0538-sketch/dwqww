#!/usr/bin/env python3
"""Source-only Forge patch checks; isolated native comparison is explicitly optional."""
from __future__ import annotations
import argparse,base64,difflib,hashlib,importlib.util,json,os,re,shutil,stat,subprocess,sys,zipfile
from pathlib import Path,PurePosixPath
MAX_INPUT=8*1024*1024
MAX_MEMBER=8*1024*1024
MAX_TREE=32*1024*1024
MAX_UNPACKED=64*1024*1024
MAX_FILES=2048
MAX_RATIO=200
BUFFIX_SHA='9ce56b3d9b5291e450679209ac991c4d560bf40f64aa0281492c53ad37d96a5c'
BUFFIX_REVIEW_SHA='6bf7fa63d950227effe2513fa3f89380abbb0c39912a8288a757c8df74707516'
BUFFIX_SCOPE={'CMakeLists.txt','src/search.cpp','tests/bad_capture_tests.cpp'}
VENDOR_TOKEN=''.join(chr(n) for n in (79,112,101,110,65,73)).casefold()
COPY_NOTICE=re.compile(r'\b'+'copy'+'right'+r'\b',re.I)
LICENSE_NOTICE=re.compile(r'MIT\s+'+'License|Permission is hereby granted',re.I)
ABBREVIATED=re.compile(r'\b[0-9a-fA-F]{4,63}(?:\.{3}|\u2026)[0-9a-fA-F]{2,63}\b')
OPTION=re.compile(r'option name\s+(.+?)\s+type\s+(check|spin|string|button|combo)\b([^"\r\n]*)')
HANDLER=re.compile(r'\bname\s*==\s*"([^"\r\n]+)"')
BUILD_OPTION=re.compile(r'option\(\s*(\w+)\s+"[^"]*"\s+(ON|OFF)\s*\)',re.I)
HUNK=re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')
class HygieneError(ValueError):
 def __init__(self,code,message,path=None):super().__init__(message);self.code,self.path=code,path

def sha_bytes(data):return hashlib.sha256(data).hexdigest()
def sha_file(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()

def safe_path(value,*,directory=False):
 value=value[:-1] if directory and value.endswith('/') else value
 if not value or '\\' in value or '\x00' in value or ':' in value or not re.fullmatch(r'[A-Za-z0-9_./+\-]+',value):raise HygieneError('unsafe_path','Unsupported or unsafe relative path',value)
 parts=value.split('/')
 if any(p in {'','.','..'} for p in parts) or value.startswith('/'):raise HygieneError('unsafe_path','Absolute or traversing path',value)
 if any(p.casefold()=='.git' for p in parts):raise HygieneError('protected_path','Git metadata path rejected',value)
 dirs=parts if directory else parts[:-1]
 if any(p.casefold() in {'baseline','lock','locks','.git'} or p.casefold().startswith('dist-v') for p in dirs):raise HygieneError('protected_path','Protected output directory',value)
 return str(PurePosixPath(value))

def tree_inventory(root):
 root=Path(root)
 if root.is_symlink() or not root.is_dir():raise HygieneError('base_tree','Base must be a real directory')
 result={};size=0
 for here,dirs,files in os.walk(root,followlinks=False):
  dirs.sort();files.sort()
  for name in list(dirs):
   p=Path(here)/name
   if p.is_symlink():raise HygieneError('base_symlink','Directory symlink in source',str(p.relative_to(root)))
   if name.casefold()=='.git':dirs.remove(name)
  for name in files:
   p=Path(here)/name;st=p.lstat()
   if not stat.S_ISREG(st.st_mode):raise HygieneError('base_special_file','Non-regular source input',str(p.relative_to(root)))
   if name.casefold()=='.git':continue
   size+=st.st_size
   if size>MAX_TREE or len(result)>=MAX_FILES:raise HygieneError('base_limit','Source-tree resource limit exceeded')
   result[str(p.relative_to(root))]={'bytes':st.st_size,'sha256':sha_file(p)}
 return result

def copy_tree(root,dest,inventory):
 dest.mkdir()
 for rel in inventory:
  p=dest/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/rel,p)
 if tree_inventory(dest)!=inventory:raise HygieneError('source_changed','Copy differs from frozen input')

def load_history(path):
 data=json.loads(Path(path).read_text(encoding='utf-8'));rows=data.get('reviewed_submission_sha256') if isinstance(data,dict) else data
 if not isinstance(rows,list) or any(not isinstance(s,str) or not re.fullmatch(r'[0-9a-f]{64}',s) for s in rows):raise HygieneError('history_format','History requires full lowercase SHA256 values')
 if len(set(rows))!=len(rows):raise HygieneError('history_format','Duplicate history values')
 return sorted(rows)

def patch_header_path(value):
 if value=='/dev/null':return None
 if not value.startswith(('a/','b/')):raise HygieneError('patch_prefix','Patch requires a/ and b/ path prefixes',value)
 return safe_path(value[2:])

def parse_patch(payload):
 try:text=payload.decode('utf-8')
 except UnicodeError as exc:raise HygieneError('patch_utf8','Patch must be UTF-8') from exc
 if '\x00' in text or 'GIT binary patch' in text or re.search(r'^Binary files ',text,re.M):raise HygieneError('binary_patch','Binary patch changes unsupported')
 changes=[];pending=None;active=None;left_old=left_new=next_new=0
 for line in text.splitlines():
  if left_old or left_new:
   if line.startswith('\\ No newline at end of file'):continue
   if line.startswith('+'):
    if left_new<=0:raise HygieneError('patch_hunk','Excess added hunk line')
    active['added'].append((next_new,line[1:]));next_new+=1;left_new-=1
   elif line.startswith('-'):
    if left_old<=0:raise HygieneError('patch_hunk','Excess removed hunk line')
    active['removed'].append(line[1:]);left_old-=1
   elif line.startswith(' '):
    if left_old<=0 or left_new<=0:raise HygieneError('patch_hunk','Excess context line')
    left_old-=1;left_new-=1;next_new+=1
   else:raise HygieneError('patch_hunk','Invalid unified hunk line')
   continue
  if line.startswith(('rename from ','rename to ','copy from ','copy to ')):raise HygieneError('patch_rename','Rename/copy metadata unsupported')
  if line.startswith(('new file mode ','old mode ','new mode ','deleted file mode ')) and line.rsplit(' ',1)[-1] not in {'100644','100755'}:raise HygieneError('patch_special_file','Only regular file modes supported')
  if line.startswith('--- '):pending=patch_header_path(line[4:]);active=None
  elif line.startswith('+++ '):
   new=patch_header_path(line[4:])
   if pending is not None and new is not None and pending!=new:raise HygieneError('patch_rename','Old/new paths differ')
   path=new or pending
   if path is None:raise HygieneError('patch_header','Both paths are null')
   if any(c['path'].casefold()==path.casefold() for c in changes):raise HygieneError('patch_duplicate_path','Duplicate/case-colliding patch path',path)
   active={'path':path,'old':pending,'new':new,'added':[],'removed':[]};changes.append(active)
  elif (m:=HUNK.match(line)):
   if active is None:raise HygieneError('patch_header','Hunk without file headers')
   left_old=int(m[2] or '1');left_new=int(m[4] or '1');next_new=int(m[3])
 if left_old or left_new:raise HygieneError('patch_hunk','Incomplete unified hunk')
 if not changes or not any(c['added'] or c['removed'] for c in changes):raise HygieneError('empty_patch','No textual file changes found')
 return changes

def read_zip(path):
 entries={};total=0;seen=set();files=set()
 try:
  with zipfile.ZipFile(path) as archive:
   infos=archive.infolist()
   if len(infos)>MAX_FILES:raise HygieneError('zip_limit','Too many archive members')
   for info in infos:
    directory=info.is_dir();name=safe_path(info.filename,directory=directory);key=name.casefold()
    if key in seen:raise HygieneError('zip_duplicate','Duplicate/case-colliding archive path',name)
    seen.add(key);mode=info.external_attr>>16;kind=stat.S_IFMT(mode)
    if kind not in {0,stat.S_IFREG,stat.S_IFDIR} or (kind==stat.S_IFDIR and not directory):raise HygieneError('zip_special_file','Archive symlink/special file rejected',name)
    if info.flag_bits&1:raise HygieneError('zip_encrypted','Encrypted archive member unsupported',name)
    if directory:continue
    files.add(key);total+=info.file_size
    if info.file_size>MAX_MEMBER or total>MAX_UNPACKED:raise HygieneError('zip_limit','Archive size limit exceeded',name)
    if info.file_size>1024*1024 and info.file_size>MAX_RATIO*max(1,info.compress_size):raise HygieneError('zip_ratio','Archive compression ratio limit exceeded',name)
    data=archive.read(info)
    if len(data)!=info.file_size:raise HygieneError('zip_size','Archive size mismatch',name)
    entries[name]=data
   for name in seen:
    if any(str(parent).casefold() in files for parent in PurePosixPath(name).parents):raise HygieneError('zip_shape','Archive file/directory collision',name)
 except (zipfile.BadZipFile,RuntimeError,NotImplementedError) as exc:raise HygieneError('zip_invalid','Invalid or unsupported archive') from exc
 return entries

def overlay_patch(entries,base):
 pieces=[]
 for name,after in sorted(entries.items()):
  f=base/name;before=f.read_bytes() if f.is_file() else b''
  if before==after:continue
  try:a,b=before.decode('utf-8'),after.decode('utf-8')
  except UnicodeError as exc:raise HygieneError('binary_overlay','Changed member is not UTF-8 text',name) from exc
  if '\x00' in a or '\x00' in b:raise HygieneError('binary_overlay','Changed member contains NUL',name)
  body=list(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+name if f.exists() else '/dev/null',tofile='b/'+name,n=5));fixed=[]
  for line in body:fixed.append(line if line.endswith('\n') else line+'\n\\ No newline at end of file\n')
  header='diff --git a/'+name+' b/'+name+'\n'
  if not f.exists():header+='new file mode 100644\n'
  pieces.append(header+''.join(fixed))
 if not pieces:raise HygieneError('empty_patch','Archive has no changed members')
 return ''.join(pieces).encode()

def expression_value(expr,off):
 expr=re.sub(r'/\*.*?\*/|//.*$','',expr).strip()
 tokens=re.findall(r'&&|\|\||[A-Za-z_]\w*|\d+|[^\s]',expr);index=0
 def take():
  nonlocal index
  if index>=len(tokens):raise ValueError('missing token')
  value=tokens[index];index+=1;return value
 def unary():
  value=take()
  if value=='!':
   v=unary();return None if v is None else not v
  if value=='(':
   v=disjunction()
   if take()!=')':raise ValueError('unbalanced expression')
   return v
  if value=='defined':
   name=take()
   if name=='(':
    name=take()
    if take()!=')':raise ValueError('unbalanced defined')
   if not re.fullmatch(r'[A-Za-z_]\w*',name):raise ValueError('invalid defined')
   return False if name in off else None
  if value.casefold() in {'0','false','off'}:return False
  if value.casefold() in {'1','true','on'}:return True
  if re.fullmatch(r'[A-Za-z_]\w*',value):return False if value in off else None
  raise ValueError('unsupported token')
 def conjunction():
  nonlocal index
  result=unary()
  while index<len(tokens) and tokens[index]=='&&':
   index+=1;other=unary();result=False if result is False or other is False else True if result is True and other is True else None
  return result
 def disjunction():
  nonlocal index
  result=conjunction()
  while index<len(tokens) and tokens[index]=='||':
   index+=1;other=conjunction();result=True if result is True or other is True else False if result is False and other is False else None
  return result
 try:
  result=disjunction();return result if index==len(tokens) else None
 except ValueError:return None

def cmake_default_states(text,off):
 stack=[];states={}
 for number,line in enumerate(text.splitlines(),1):
  stripped=line.strip()
  if (m:=re.match(r'if\s*\((.*)\)\s*$',stripped,re.I)):
   value=expression_value(m[1],off);stack.append({'seen':value,'current':value})
  elif re.match(r'else\s*\(',stripped,re.I) and stack:
   value=stack[-1]['seen'];stack[-1]['current']=None if value is None else not value;stack[-1]['seen']=True
  elif (m:=re.match(r'elseif\s*\((.*)\)\s*$',stripped,re.I)) and stack:
   old=stack[-1]['seen'];value=expression_value(m[1],off);stack[-1]['current']=False if old is True else value if old is False else None
   stack[-1]['seen']=True if old is True or value is True else False if old is False and value is False else None
  elif re.match(r'endif\s*\(',stripped,re.I) and stack:stack.pop()
  values=[item['current'] for item in stack];states[number]=False if False in values else None if None in values else True
 return states

def default_states(text,off):
 stack=[];states={};block_comment=False
 for number,line in enumerate(text.splitlines(),1):
  directive=re.match(r'^\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b(.*)',line)
  if directive:
   kind,expr=directive.groups()
   if kind in {'if','ifdef','ifndef'}:
    value=expression_value(expr if kind=='if' else 'defined('+expr.strip()+')',off)
    if kind=='ifndef':value=None if value is None else not value
    stack.append({'seen':value,'current':value})
   elif kind=='else' and stack:
    value=stack[-1]['seen'];stack[-1]['current']=None if value is None else not value;stack[-1]['seen']=True
   elif kind=='elif' and stack:
    previous=stack[-1]['seen'];value=expression_value(expr,off);stack[-1]['current']=False if previous is True else value if previous is False else None
    stack[-1]['seen']=True if previous is True or value is True else False if previous is False and value is False else None
   elif kind=='endif' and stack:stack.pop()
   states[number]=(False,'');continue
  cleaned=line
  if block_comment:
   if '*/' not in cleaned:states[number]=(False,'');continue
   cleaned=cleaned.split('*/',1)[1];block_comment=False
  while '/*' in cleaned:
   pre,rest=cleaned.split('/*',1)
   if '*/' not in rest:cleaned=pre;block_comment=True;break
   cleaned=pre+rest.split('*/',1)[1]
  cleaned=re.sub(r'//.*$','',cleaned).strip();values=[s['current'] for s in stack];active=False if False in values else None if None in values else True
  states[number]=(active,cleaned)
 return states

def content_findings(path,text,base):
 found=[]
 if re.fullmatch(r'(?:LICENSE|COPYING)(?:\.[A-Za-z0-9_+\-]+)?',PurePosixPath(path).name,re.I):found.append({'code':'forbidden_license_file','base':base,'path':path})
 if COPY_NOTICE.search(text) or LICENSE_NOTICE.search(text):found.append({'code':'forbidden_notice','base':base,'path':path})
 if VENDOR_TOKEN in text.casefold():found.append({'code':'forbidden_vendor','base':base,'path':path})
 if PurePosixPath(path).suffix.lower() in {'.md','.txt','.rst'} and ABBREVIATED.search(text):found.append({'code':'abbreviated_hash','base':base,'path':path})
 return found

def inspect_changes(changes,reference,candidate,base,approved_buffix):
 findings=[];options=[];cmake=(candidate/'CMakeLists.txt').read_text() if (candidate/'CMakeLists.txt').is_file() else ''
 off={m[1] for m in BUILD_OPTION.finditer(cmake) if m[2].upper()=='OFF'}
 for change in changes:
  path=change['path'];added='\n'.join(line for _,line in change['added']);findings+=content_findings(path,added,base);f=candidate/path
  if path=='CMakeLists.txt':
   added_numbers={number for number,_ in change['added']};cmake_states=cmake_default_states(cmake,off)
   for _,line in change['added']:
    if (m:=BUILD_OPTION.search(line)):
     options.append({'base':base,'kind':'build','name':m[1],'default':m[2].upper()})
     if m[2].upper()=='ON':findings.append({'code':'new_build_option_default_on','base':base,'path':path,'name':m[1]})
   for m in re.finditer(r'\b(target_compile_definitions|target_compile_options|target_link_options|target_sources|target_link_libraries)\s*\(\s*(forge(?:_core)?)\s+[^)]*\)',cmake,re.I|re.S):
    start=cmake.count('\n',0,m.start())+1;end=cmake.count('\n',0,m.end())+1
    for number in sorted(added_numbers.intersection(range(start,end+1))):
     if cmake_states.get(start) is not False:findings.append({'code':'default_build_configuration','base':base,'path':path,'line':number})
  production=path.startswith(('src/','include/')) and PurePosixPath(path).suffix.lower() in {'.cpp','.cc','.cxx','.c','.h','.hpp','.hh','.hxx'}
  if not production or not f.is_file():continue
  states=default_states(f.read_text(encoding='utf-8'),off)
  if approved_buffix and path=='src/search.cpp':continue
  for number,line in change['added']:
   active,cleaned=states.get(number,(None,line.strip()))
   if active is False or not cleaned or re.fullmatch(r'[{};\s]+',cleaned) or re.match(r'^namespace\b.*\{$',cleaned):continue
   findings.append({'code':'unguarded_default_code' if active is True else 'guard_default_unverified','base':base,'path':path,'line':number})
   if re.search(r'(?:stat|counter|refreshes|updates|evaluations|cache_hits)',cleaned,re.I) and re.search(r'\+\+|\+=|fetch_add|thread_local',cleaned):findings.append({'code':'default_instrumentation','base':base,'path':path,'line':number})
   if 'option name ' in cleaned:findings.append({'code':'default_runtime_option','base':base,'path':path,'line':number})
   if re.search(r'info\s+string.*\bstats\b',cleaned):findings.append({'code':'default_bench_statistics','base':base,'path':path,'line':number})
 for path in {c['path'] for c in changes if c['path'].endswith('/uci.cpp')}:
  after=(candidate/path).read_text() if (candidate/path).exists() else '';before=(reference/path).read_text() if (reference/path).exists() else ''
  def adverts(text):return {m[1]:{'name':m[1],'type':m[2],'literal_metadata':m[3].strip()} for m in OPTION.finditer(re.sub(r'"\s*"','',text))}
  old,new=adverts(before),adverts(after)
  for name in sorted(new.keys()-old.keys()):options.append({'base':base,'kind':'runtime',**new[name]})
  for name in sorted(set(HANDLER.findall(after))-set(HANDLER.findall(before))):
   if name not in new:findings.append({'code':'unadvertised_runtime_option','base':base,'path':path,'name':name})
 return findings,options

def check_submission(input_path,bases,out,history=None,*,control_role=None,review_record=None,build_compare=False,cmake='cmake',expected_nodes=None,depths=None):
 input_path,out=Path(input_path),Path(out).absolute();resolved=out.resolve(strict=False)
 if resolved!=out or out.exists() or out.is_symlink():raise ValueError('Output must be a NEW non-symlink canonical path')
 if any(p.casefold() in {'baseline','lock','locks','.git'} or p.casefold().startswith('dist-v') for p in out.parts):raise ValueError('Output is under a protected directory')
 roots={}
 for name,source in sorted(bases.items()):
  if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}',name):raise ValueError('Invalid base label')
  source=Path(source).absolute()
  if source.is_symlink() or not source.is_dir() or source.resolve()!=source:raise ValueError('Base must be a real canonical directory')
  if out.is_relative_to(source) or source.is_relative_to(out):raise ValueError('Output overlaps immutable source')
  roots[name]=source
 if not roots:raise ValueError('At least one labelled source base required')
 if history is None:history=[]
 if not isinstance(history,list) or any(not isinstance(x,str) or not re.fullmatch(r'[0-9a-f]{64}',x) for x in history):raise ValueError('History requires full lowercase SHA256 values')
 out.mkdir(parents=False)
 result={'schema':'forge_sol_S27_hygiene_v1','status':'INCOMPLETE','findings':[],'input':{},'bases':[],'options':[],'raw_records':[],'build_compare':[],'scope':'Static guard and Forge literal-option checks are heuristics, not semantic/strength proof. No engine/compiler without explicit build_compare.'};raw_count=0
 def finding(code,message,path=None,base=None):
  row={'code':code,'message':message}
  if path is not None:row['path']=path
  if base is not None:row['base']=base
  result['findings'].append(row)
 def run(label,argv,cwd):
  nonlocal raw_count
  env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,LC_ALL='C')
  proc=subprocess.run([str(x) for x in argv],cwd=cwd,env=env,input=b'',capture_output=True,timeout=60);raw_count+=1;name=f'forge_sol_S27_raw_{raw_count:04d}_20261026.json'
  row={'label':label,'argv':[str(x) for x in argv],'cwd':str(cwd),'exit':proc.returncode}
  for k,b in [('stdout',proc.stdout),('stderr',proc.stderr)]:row[k]={'bytes':len(b),'sha256':sha_bytes(b),'base64':base64.b64encode(b).decode()}
  (out/name).write_text(json.dumps(row,sort_keys=True,indent=2)+'\n');result['raw_records'].append(name);return proc.returncode
 try:
  if input_path.is_symlink() or not input_path.is_file():raise HygieneError('input_file','Submission must be a regular non-symlink file')
  if input_path.stat().st_size>MAX_INPUT:raise HygieneError('input_limit','Submission size limit exceeded')
  payload=input_path.read_bytes();digest=sha_bytes(payload);result['input']={'sha256':digest,'bytes':len(payload),'kind':'zip' if zipfile.is_zipfile(input_path) else 'patch'}
  if digest in history:finding('duplicate_submission','Exact content SHA256 is already in submission history')
  entries=read_zip(input_path) if result['input']['kind']=='zip' else None;contained=[n for n in entries or {} if n.lower().endswith(('.patch','.diff'))]
  if len(contained)>1:raise HygieneError('zip_patch_count','Multiple contained patches have no explicit order')
  if contained:
   for name,data in entries.items():
    if name==contained[0]:continue
    try:text=data.decode('utf-8')
    except UnicodeError:raise HygieneError('zip_attachment','Non-text patch attachment unsupported',name)
    result['findings']+=content_findings(name,text,None)
   payload=entries[contained[0]]
  approved=False
  if control_role is not None:
   if control_role!='approved_buffix_control' or digest!=BUFFIX_SHA or review_record is None or sha_file(Path(review_record))!=BUFFIX_REVIEW_SHA:raise HygieneError('control_authority','Exact supplied patch and authenticated same-diff review required')
   approved=True
  for name,source in roots.items():
   before=tree_inventory(source);area=out/name;area.mkdir();reference,candidate=area/'reference',area/'candidate';copy_tree(source,reference,before);copy_tree(source,candidate,before)
   patch=overlay_patch(entries,reference) if entries is not None and not contained else payload;changes=parse_patch(patch)
   if approved and {c['path'] for c in changes}!=BUFFIX_SCOPE:raise HygieneError('control_scope','Approved storage control scope changed')
   patch_path=area/'forge_sol_S27_checked_input_20261026.patch';patch_path.write_bytes(patch)
   git=run(name+'_git_check',['git','-c','gc.auto=0','apply','--check',str(patch_path)],candidate)
   dry=run(name+'_GNU_F0_dry',['patch','--batch','--forward','--fuzz=0','-p1','--dry-run','-i',str(patch_path)],candidate)
   if git:finding('git_apply_failed','git apply --check rejected exact payload',base=name)
   if dry:finding('GNU_F0_failed','GNU zero-fuzz dry run rejected exact payload',base=name)
   applied=run(name+'_GNU_F0_apply',['patch','--batch','--forward','--fuzz=0','-p1','-i',str(patch_path)],candidate) if dry==0 else None
   if applied not in {None,0}:finding('GNU_apply_failed','GNU zero-fuzz application failed',base=name)
   if applied==0:
    new_findings,options=inspect_changes(changes,reference,candidate,name,approved);result['findings']+=new_findings;result['options']+=options
    if entries is not None and not contained:
     for member,data in entries.items():
      if not (candidate/member).is_file() or (candidate/member).read_bytes()!=data:raise HygieneError('overlay_mismatch','Applied member differs from requested bytes',member)
   if tree_inventory(source)!=before:raise HygieneError('source_changed','Immutable input changed during check')
   result['bases'].append({'name':name,'input_files':len(before),'input_inventory_sha256':sha_bytes(json.dumps(before,sort_keys=True).encode()),'git_check_exit':git,'GNU_dry_exit':dry,'GNU_apply_exit':applied,'inputs_unchanged':True,'control_role':'exact_reviewed_storage_fix' if approved else 'ordinary_candidate'})
   if build_compare and git==0 and applied==0:
    if result['findings']:result['build_compare'].append({'base':name,'status':'UNVERIFIED','reason':'Static findings block execution of candidate code'})
    else:
     module_path=Path(__file__).with_name('forge_sol_S27_buildcompare_20261026.py');spec=importlib.util.spec_from_file_location('forge_s27_compare',module_path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
     compared=module.run_compare(reference,candidate,area/'forge_sol_S27_native_compare_20261026',cmake=cmake,expected_nodes=expected_nodes or {11:308972,13:745494,16:2460422,20:11901452,22:31111774},depths=depths or [11,13,16,20,22]);result['build_compare'].append({'base':name,**compared})
     if compared.get('status')!='PASS':finding('default_build_compare_failed','Default-build comparison did not pass',base=name)
 except HygieneError as exc:finding(exc.code,str(exc),exc.path)
 except (OSError,UnicodeError,subprocess.SubprocessError,ValueError) as exc:finding('observer_error',type(exc).__name__+': '+str(exc))
 result['findings']=sorted(result['findings'],key=lambda x:json.dumps(x,sort_keys=True));result['options']=sorted(result['options'],key=lambda x:json.dumps(x,sort_keys=True));result['status']='FAIL' if result['findings'] else 'PASS'
 canonical={k:result[k] for k in ['input','bases','findings','options','status']};result['deterministic_signature_sha256']=sha_bytes(json.dumps(canonical,sort_keys=True,separators=(',',':')).encode())
 (out/'forge_sol_S27_result_20261026.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');return result

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('submission',type=Path);p.add_argument('--base',action='append',required=True,metavar='LABEL=SOURCE');p.add_argument('--out',type=Path,required=True);p.add_argument('--history',type=Path);p.add_argument('--control-role',choices=['approved_buffix_control']);p.add_argument('--review-record',type=Path);p.add_argument('--build-compare',action='store_true');p.add_argument('--cmake',default='cmake');a=p.parse_args();bases={}
 for value in a.base:
  if '=' not in value:p.error('--base requires LABEL=SOURCE')
  label,path=value.split('=',1)
  if label in bases:p.error('Duplicate base label')
  bases[label]=Path(path)
 try:r=check_submission(a.submission,bases,a.out,load_history(a.history) if a.history else [],control_role=a.control_role,review_record=a.review_record,build_compare=a.build_compare,cmake=a.cmake)
 except (ValueError,OSError) as exc:print('S27 ERROR: '+str(exc),file=sys.stderr);return 2
 print('S27 '+r['status']+' findings='+str(len(r['findings']))+' signature='+r['deterministic_signature_sha256']);return 0 if r['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
