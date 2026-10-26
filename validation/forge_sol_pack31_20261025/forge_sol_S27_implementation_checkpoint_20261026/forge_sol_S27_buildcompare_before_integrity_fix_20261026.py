#!/usr/bin/env python3
"""Opt-in isolated build comparison; no speed or playing-strength conclusion.
Idea sources: supplied S27 contract, our S25 grammar, standard CMake/nm interfaces.
"""
from __future__ import annotations
import hashlib,json,os,re,shutil,subprocess
from pathlib import Path

REFS={11:308972,13:745494,16:2460422,20:11901452,22:31111774}
FLAGS='-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256'
SUMMARY=re.compile(rb'info string bench depth ([0-9]+) nodes ([0-9]+) time ([0-9]+) nps ([0-9]+)(\r\n|\n|\Z)')

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def parse_bench(stdout,stderr,exitcode,depth,nodes):
 matches=list(SUMMARY.finditer(stdout));errors=[];gate=False;normalized=None
 if exitcode!=0:errors.append('exit')
 if stderr:errors.append('stderr')
 if len(matches)!=1:errors.append('summary_count')
 if len(matches)==1:
  m=matches[0];observed=(int(m[1]),int(m[2]));gate=exitcode==0 and observed==(depth,nodes)
  normalized={'depth':observed[0],'nodes':observed[1]}
  if not gate:errors.append('reference')
  if not m[5]:errors.append('missing_terminator')
  if m.start():errors.append('prefix_bytes')
  if m.end()!=len(stdout):errors.append('post_summary_bytes')
 return {'status':'FAIL'if errors else'PASS','reference_gate':gate,'errors':errors,'normalized':normalized}

def parse_uci(stdout,stderr,exitcode):
 errors=[];options={};ids=[];id_kinds=set()
 if exitcode!=0:errors.append('exit')
 if stderr:errors.append('stderr')
 try:text=stdout.decode('utf-8').replace('\r\n','\n')
 except UnicodeDecodeError:return {'status':'FAIL','errors':errors+['non_utf8'],'options':[],'ids':[]}
 if '\r'in text or '\x00'in text or not text.endswith('\n'):errors.append('line_ending')
 lines=text.split('\n')[:-1]if text.endswith('\n')else text.split('\n')
 if lines.count('uciok')!=1 or not lines or lines[-1]!='uciok':errors.append('uciok')
 for line in lines:
  if line=='uciok':continue
  identity=re.fullmatch(r'id (name|author) (.+)',line)
  if identity:
   if identity[1]in id_kinds:errors.append('duplicate_id')
   id_kinds.add(identity[1]);ids.append(line);continue
  row=None
  match=re.fullmatch(r'option name (.+) type spin default (-?\d+) min (-?\d+) max (-?\d+)',line)
  if match:
   row={'name':match[1],'type':'spin','default':int(match[2]),'min':int(match[3]),'max':int(match[4])}
   if not row['min']<=row['default']<=row['max']:errors.append('spin_bounds')
  if row is None:
   match=re.fullmatch(r'option name (.+) type check default (true|false)',line)
   if match:row={'name':match[1],'type':'check','default':match[2]=='true'}
  if row is None:
   match=re.fullmatch(r'option name (.+) type string default (.*)',line)
   if match:row={'name':match[1],'type':'string','default':match[2]}
  if row is None:
   match=re.fullmatch(r'option name (.+) type button',line)
   if match:row={'name':match[1],'type':'button'}
  if row is None:errors.append('unknown_or_malformed_line');continue
  key=row['name'].casefold()
  if key in options:errors.append('duplicate_option')
  options[key]=row
 return {'status':'FAIL'if errors else'PASS','errors':errors,'options':sorted(options.values(),key=lambda x:x['name']),'ids':sorted(ids)}

def parse_symbols(stdout,stderr,exitcode):
 errors=[];normalized=[]
 if exitcode!=0:errors.append('exit')
 if stderr:errors.append('stderr')
 try:
  for line in stdout.decode('utf-8').splitlines():
   m=re.fullmatch(r'\s*[0-9a-fA-F]+\s+([A-Za-z?])\s+(.+)',line)
   if not m:errors.append('malformed_symbol');continue
   normalized.append([m[1],m[2]])
 except UnicodeDecodeError:errors.append('non_utf8')
 if not normalized:errors.append('empty_symbols')
 return {'status':'FAIL'if errors else'PASS','errors':errors,'normalized':sorted(normalized)}

def _new_out(path):
 path=Path(path).absolute()
 if path.resolve()!=path or path.is_symlink()or path.exists():raise ValueError('Comparison output must be NEW without symlink ancestors')
 path.mkdir(parents=True,exist_ok=False);return path

def _snapshot(root):
 result={}
 for p in sorted(Path(root).rglob('*')):
  if p.is_symlink():raise ValueError('Source symlink unsupported: '+str(p))
  if p.is_file():result[str(p.relative_to(root))]={'bytes':p.stat().st_size,'sha256':sha(p)}
  elif not p.is_dir():raise ValueError('Source special file unsupported')
 return result

class _Capture:
 def __init__(self,out):
  self.out=out;self.commands=[];self.tmp=out/'forge_sol_S27_tmp_20261026';self.tmp.mkdir()
 def run(self,label,argv,stdin=None,timeout=600):
  env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(self.tmp));prefix=self.out/('forge_sol_S27_%03d_%s_20261026'%(len(self.commands),label));timed_out=False
  try:
   p=subprocess.run([str(x)for x in argv],input=stdin,capture_output=True,env=env,timeout=timeout)
   code,stdout,stderr=p.returncode,p.stdout,p.stderr
  except subprocess.TimeoutExpired as error:
   timed_out=True;code=None;stdout=error.stdout or b'';stderr=error.stderr or b''
  row={'label':label,'argv':[str(x)for x in argv],'exit':code,'timeout':timed_out,'timeout_seconds':timeout,'EOF_and_normal_child_exit':not timed_out,'environment_overrides':{'PYTHONDONTWRITEBYTECODE':'1','TMPDIR':str(self.tmp)}}
  for name,data in [('stdin',stdin),('stdout',stdout),('stderr',stderr)]:
   if data is None:row[name]=None;continue
   target=prefix.with_suffix('.'+name);target.write_bytes(data);row[name]={'path':str(target),'bytes':len(data),'sha256':sha(target)}
  self.commands.append(row);(self.out/'forge_sol_S27_commands_20261026.json').write_text(json.dumps(self.commands,indent=2)+'\n');return code,stdout,stderr

def _probe(exe,label,cap,expected_nodes,depths):
 exe=Path(exe).resolve(strict=True)
 if not exe.is_file()or not os.access(exe,os.X_OK):raise ValueError('Executable required')
 result={'exe':str(exe),'sha256':sha(exe),'bench':{}}
 code,stdout,stderr=cap.run(label+'_first_d11',[exe],b'bench 11\nquit\n')
 first=parse_bench(stdout,stderr,code,11,expected_nodes[11]);result['first_d11']=first;result['bench']['11']=first
 if first['reference_gate']:
  code,stdout,stderr=cap.run(label+'_uci',[exe],b'uci\nquit\n');result['uci']=parse_uci(stdout,stderr,code)
  for depth in depths:
   if depth==11:continue
   code,stdout,stderr=cap.run(label+'_bench_%s'%depth,[exe],('bench %s\nquit\n'%depth).encode());result['bench'][str(depth)]=parse_bench(stdout,stderr,code,depth,expected_nodes[depth])
 else:result['uci']={'status':'UNVERIFIED','reason':'Failed first numeric d11 gate'}
 code,stdout,stderr=cap.run(label+'_symbols',['nm','--defined-only','-C',exe]);result['symbols']=parse_symbols(stdout,stderr,code)
 checks=list(result['bench'].values())+[result['uci'],result['symbols']];result['status']='PASS'if all(x['status']=='PASS'for x in checks)else'FAIL';return result

def _assess(a,b):
 errors=[]
 for label,case in [('base',a),('candidate',b)]:
  if case['status']!='PASS':errors.append(label+'_protocol_or_symbols')
 for key in ['options','ids']:
  if a['uci'].get(key)!=b['uci'].get(key):errors.append('default_uci_'+key+'_changed')
 if a['symbols']['normalized']!=b['symbols']['normalized']:errors.append('default_defined_symbols_changed')
 if {k:v['normalized']for k,v in a['bench'].items()}!={k:v['normalized']for k,v in b['bench'].items()}:errors.append('default_bench_changed')
 return errors

def compare_existing(base_exe,candidate_exe,out,*,expected_nodes=None,depths=None):
 out=_new_out(out);cap=_Capture(out);expected_nodes=REFS if expected_nodes is None else expected_nodes;depths=[11]if depths is None else depths
 if 11 not in expected_nodes or any(d not in expected_nodes for d in depths):raise ValueError('Published depth oracle required')
 a=_probe(base_exe,'base',cap,expected_nodes,depths);b=_probe(candidate_exe,'candidate',cap,expected_nodes,depths);errors=_assess(a,b)
 result={'status':'FAIL'if errors else'PASS','mode':'EXISTING_EXECUTABLES_NO_BUILD','base':a,'candidate':b,'errors':errors,'commands':cap.commands,'scope':'Protocol/symbol compatibility only; no speed, Elo or fresh-build claim.'}
 (out/'forge_sol_S27_comparison_20261026.json').write_text(json.dumps(result,indent=2)+'\n');return result

def run_compare(base_tree,candidate_tree,out,*,cmake,expected_nodes,depths):
 roots=[Path(base_tree).resolve(strict=True),Path(candidate_tree).resolve(strict=True)];target=Path(out).absolute()
 for root in roots:
  if not root.is_dir()or target.is_relative_to(root)or root.is_relative_to(target):raise ValueError('Separate source and build-output paths required')
 if 11 not in expected_nodes or any(d not in expected_nodes for d in depths):raise ValueError('Published oracle required')
 out=_new_out(out);cap=_Capture(out);state={'status':'INCOMPLETE','mode':'FRESH_DEFAULT_RELEASE_BUILDS','commands':cap.commands,'recipe':{'cmake':str(cmake),'flags':FLAGS,'parallel':2},'sources':[],'cases':[]};receipt=out/'forge_sol_S27_comparison_20261026.json'
 def save():receipt.write_text(json.dumps(state,indent=2)+'\n')
 save()
 try:
  if shutil.disk_usage(out).free<24*1048576:raise RuntimeError('Insufficient free space:24MiB required before builds')
  for label,root in zip(['base','candidate'],roots):
   inventory=_snapshot(root);state['sources'].append({'label':label,'root':str(root),'files':inventory});build=out/('forge_sol_S27_'+label+'_build_20261026')
   code,_,_=cap.run(label+'_configure',[cmake,'-S',root,'-B',build,'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_CXX_FLAGS='+FLAGS,'-DCMAKE_EXPORT_COMPILE_COMMANDS=ON','-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF'])
   if code!=0:raise RuntimeError(label+' CMake configure failed')
   cache=(build/'CMakeCache.txt').read_text();compiler=re.search(r'^CMAKE_CXX_COMPILER:FILEPATH=(.+)$',cache,re.M)
   if not compiler:raise RuntimeError('Compiler identity not found')
   code,_,_=cap.run(label+'_compiler_version',[compiler[1],'-dumpfullversion','-dumpversion'])
   if code!=0:raise RuntimeError('Compiler version query failed')
   state['sources'][-1]['compiler']={'path':compiler[1],'sha256':sha(Path(compiler[1]).resolve())}
   code,_,_=cap.run(label+'_build',[cmake,'--build',build,'--target','forge','--parallel','2'])
   if code!=0:raise RuntimeError(label+' CMake build failed')
   state['cases'].append(_probe(build/'forge',label,cap,expected_nodes,depths));recipes=[]
   for p in sorted(build.rglob('*')):
    if p.is_file()and p.name in {'flags.make','link.txt','compile_commands.json'}:recipes.append({'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)})
   state['sources'][-1]['generated_recipes']=recipes
   if _snapshot(root)!=inventory:raise RuntimeError('Input source changed during build')
   save()
  state['errors']=_assess(*state['cases']);state['status']='FAIL'if state['errors']else'PASS'
 except Exception as error:state['status']='FAIL';state['error']=str(error)
 state['scope']='Fresh default builds; fixed-node/protocol/symbol checks only. No NPS, speed, Elo, PC or acceptance claim.';save();return state

def recipe_signature(*args): return None
