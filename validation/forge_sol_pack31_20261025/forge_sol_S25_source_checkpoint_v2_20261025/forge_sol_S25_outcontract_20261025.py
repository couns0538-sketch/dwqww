#!/usr/bin/env python3
"""Exact normal-release bench EOF and typed UCI option contract checks."""
from __future__ import annotations
import argparse,base64,hashlib,json,os,re,subprocess,tempfile
from pathlib import Path

SUMMARY=re.compile(rb'(?m)^info string bench depth ([0-9]+) nodes ([0-9]+) time ([0-9]+) nps ([0-9]+)(\r\n|\n|\Z)')

def inspect_bench(stdout,stderr,exitcode,depth=11,nodes=308972):
 errors=[];matches=list(SUMMARY.finditer(stdout));gate=False
 if exitcode!=0:errors.append({'code':'bench_exit','actual':exitcode})
 if stderr:errors.append({'code':'bench_stderr','bytes':len(stderr),'sha256':hashlib.sha256(stderr).hexdigest()})
 if len(matches)!=1:errors.append({'code':'bench_summary_count','expected':1,'actual':len(matches)})
 if len(matches)==1:
  m=matches[0];actual_depth=int(m[1]);actual_nodes=int(m[2]);gate=exitcode==0 and actual_depth==depth and actual_nodes==nodes
  if actual_depth!=depth or actual_nodes!=nodes:errors.append({'code':'bench_reference','expected_depth':depth,'actual_depth':actual_depth,'expected_nodes':nodes,'actual_nodes':actual_nodes})
  if not m[5]:errors.append({'code':'bench_missing_line_ending'})
  if m.start()!=0:errors.append({'code':'bench_prefix_bytes','bytes':m.start()})
  tail=stdout[m.end():]
  if tail:errors.append({'code':'bench_post_summary_bytes','bytes':len(tail),'sha256':hashlib.sha256(tail).hexdigest(),'base64':base64.b64encode(tail).decode()})
 return {'status':'PASS' if not errors else'FAIL','first_d11_reference_gate_passed':gate,'summary_count':len(matches),'errors':errors}

def parse_option(line):
 patterns=[('spin',r'option name (.+) type spin default (-?[0-9]+) min (-?[0-9]+) max (-?[0-9]+)'),('check',r'option name (.+) type check default (true|false)'),('string',r'option name (.+) type string default (.*)'),('button',r'option name (.+) type button')]
 for kind,pattern in patterns:
  m=re.fullmatch(pattern,line)
  if not m:continue
  result={'name':m[1],'type':kind}
  if kind=='spin':result.update(default=int(m[2]),min=int(m[3]),max=int(m[4]))
  elif kind=='check':result['default']=m[2]=='true'
  elif kind=='string':result['default']=m[2]
  return result
 raise ValueError('malformed or unsupported option declaration')

def inspect_uci(stdout,stderr,exitcode,approved):
 errors=[];actual={};duplicate=[]
 if exitcode!=0:errors.append({'code':'uci_exit','actual':exitcode})
 if stderr:errors.append({'code':'uci_stderr','bytes':len(stderr),'sha256':hashlib.sha256(stderr).hexdigest()})
 try:lines=stdout.decode('utf-8').splitlines()
 except UnicodeDecodeError:return {'status':'FAIL','options':[],'errors':errors+[{'code':'uci_non_utf8'}]}
 if lines.count('uciok')!=1:errors.append({'code':'uciok_count','expected':1,'actual':lines.count('uciok')})
 for line in lines:
  if not line.lstrip().lower().startswith('option'):continue
  try:item=parse_option(line)
  except ValueError:errors.append({'code':'malformed_option','line_base64':base64.b64encode(line.encode()).decode()});continue
  name=item['name']
  if name in actual:duplicate.append(name);errors.append({'code':'duplicate_option','name':name})
  else:actual[name]=item
 expected={r['name']:r for r in approved};assert len(expected)==len(approved)
 for name in sorted(expected):
  if name not in actual:errors.append({'code':'missing_option','name':name})
  elif expected[name]!=actual[name]:errors.append({'code':'option_metadata_mismatch','name':name,'expected':expected[name],'actual':actual[name]})
 for name in sorted(actual.keys()-expected.keys()):errors.append({'code':'unexpected_option','name':name,'actual':actual[name]})
 return {'status':'PASS' if not errors else'FAIL','options':[actual[n] for n in sorted(actual)],'duplicate_names':duplicate,'errors':errors}

def capture(exe,stdin,path):
 child=subprocess.Popen([str(exe)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);stdout,stderr=child.communicate(stdin)
 record={'argv':[str(exe)],'stdin_base64':base64.b64encode(stdin).decode(),'exit':child.returncode,'EOF_and_child_exit_observed':True}
 for name,data in [('stdout',stdout),('stderr',stderr)]:record[name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'base64':base64.b64encode(data).decode()}
 path.write_text(json.dumps(record,indent=2)+'\n');return stdout,stderr,child.returncode

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('exe',type=Path);g=p.add_mutually_exclusive_group();g.add_argument('--out',type=Path);g.add_argument('--out-root',type=Path);a=p.parse_args();exe=a.exe.resolve(strict=True)
 if not exe.is_file() or not os.access(exe,os.X_OK):raise SystemExit('readable executable required')
 if a.out:out=a.out;out.mkdir(parents=False,exist_ok=False)
 else:
  root=a.out_root or Path.cwd();root.mkdir(parents=True,exist_ok=True);out=Path(tempfile.mkdtemp(prefix='forge_sol_S25_run_20261025_',dir=root))
 allow=Path(__file__).with_name('forge_sol_S25_options_20261025.json');data=json.loads(allow.read_text());result={'status':'INCOMPLETE','engine_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'allowlist_sha256':hashlib.sha256(allow.read_bytes()).hexdigest(),'errors':[]}
 # The bare default d11 gate is the first engine invocation. Tail errors do not
 # hide a second option-list failure if the published node precondition holds.
 stdout,stderr,code=capture(exe,b'bench 11\nquit\n',out/'forge_sol_S25_bench_raw_20261025.json');bench=inspect_bench(stdout,stderr,code,data['bench']['depth'],data['bench']['nodes']);result['bench']=bench;result['errors']+=bench['errors']
 if bench['first_d11_reference_gate_passed']:
  stdout,stderr,code=capture(exe,b'uci\nquit\n',out/'forge_sol_S25_uci_raw_20261025.json');uci=inspect_uci(stdout,stderr,code,data['options']);result['uci']=uci;result['errors']+=uci['errors']
 else:result['uci']={'status':'UNVERIFIED','reason':'Skipped after failed first-d11 reference gate'}
 result['status']='PASS' if not result['errors'] else'FAIL';(out/'forge_sol_S25_contract_result_20261025.json').write_text(json.dumps(result,indent=2)+'\n');print('OUTPUT_CONTRACT_'+result['status'],'bench='+bench['status'],'uci='+result['uci']['status'],'errors='+','.join(r['code'] for r in result['errors']));return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
