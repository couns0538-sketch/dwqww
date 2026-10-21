"""Execute only the exact pure parser AST on preserved producer bytes; no engines."""
import ast, hashlib, json, os, re, sys
from pathlib import Path
assert sys.dont_write_bytecode and os.environ.get('PYTHONDONTWRITEBYTECODE') == '1'
R=Path('/workspace/dwqww'); B=R/'validation/hosted-tt-refresh-strength-20261021'
O=B/'independent-capture-review'; C=B/'capture-preparation/actual-five-captures'
N=R/'validation/tt-refresh-native-20261021/release-signature-wrapper-attempt1'
P=R/'.github/hosted-tt-refresh-strength/run_hosted.py'
inputs={};cases=[]
def read(p):
 b=p.read_bytes();inputs[str(p)]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'mode':p.stat().st_mode&0o7777};return b
def obj(p):return json.loads(read(p))
def write(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
source=read(P).decode();assert hashlib.sha256(source.encode()).hexdigest()=='6da0a0d76f21c90b46fd320b81ac66f4a6cf7dd5e9f731a57e34c6ff65b2c105'
fn=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='verify_candidate_bench_signature')
namespace={'re':re};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(P),'exec'),namespace)
parse=namespace['verify_candidate_bench_signature']
def case(name,out,err,code,nodes,accept,origin):
 try:value=parse(out.decode('ascii'),err.decode('ascii'),code,nodes);actual=True;error=None
 except ValueError as e:value=None;actual=False;error=str(e)
 cases.append({'name':name,'pass':actual==accept,'expected_accept':accept,'actual_accept':actual,'result':value,'error':error,'origin':origin,'stdout_sha256':hashlib.sha256(out).hexdigest(),'stderr_sha256':hashlib.sha256(err).hexdigest(),'returncode_argument':code,'expected_nodes_argument':nodes})
pro=obj(C/'PROVENANCE.json');assert inputs[str(C/'PROVENANCE.json')]['sha256']=='7418f8f3f4fff2ee19acb5e70bb5b97fac7a00ff7b3337279dfe7de8f24a0da1'
command=obj(N/'bench11-command.json');summary=obj(N/'summary.json')
freeze=obj(N.parent/'BENCH-SIGNATURE-FREEZE.json')
out=read(N/'bench11.stdout.bin');err=read(N/'bench11.stderr.bin');stdin=read(N/'bench11.stdin.bin')
assert command['exit_code']==0 and command['error'] is None and command['timed_out'] is False
for k,v in [('stdout',out),('stderr',err),('stdin',stdin)]:
 assert command[k+'_sha256']==hashlib.sha256(v).hexdigest()==freeze['raw_'+k+'_sha256']
assert stdin==b'bench 11\nquit\n' and err==b''
assert summary['status']=='PASS' and summary['source_commit']=='1d3ed25bea2c8b781f7ee5a178af0f66061b3984'
assert summary['bench11_expected_nodes'] is None  # Genuine first-capture schema, not a guessed default.
assert summary['input_sha256_before']==summary['input_sha256_after']
assert freeze['status']=='FROZEN_FIRST_ACTUAL_RELEASE_BENCH11' and freeze['nodes']==292545 and freeze['signature_processes']==1
assert freeze['release_engine_sha256']==summary['input_sha256_before']['candidate/forge']==pro['captures']['candidate']['binary_sha256_before']['forge']
for kind,data in [('stdout',out),('stderr',err),('stdin',stdin)]:write(O/f'original-copy/native23-single-bench.{kind}.bin',data)
case('original_genuine23_single_process',out,err,0,292545,True,{'kind':'complete original native23 single-bench stdout','path':str(N/'bench11.stdout.bin')})
for label in ['baseline','candidate']:
 facts=pro['captures'][label]['process_facts'];path=Path(facts['stdout']);raw=read(path)
 assert hashlib.sha256(raw).hexdigest()==facts['stdout_sha256']
 assert read(Path(facts['stderr']))==b''
 rows=raw.splitlines(keepends=True);assert len(rows)==5 and b''.join(rows)==raw;offset=0
 for i,line in enumerate(rows,1):
  derived=O/f'extracted/{label}-line-{i:02d}.bin';write(derived,line)
  case(f'{label}_byte_extracted_line_{i}',line,b'',0,292545,True,{'kind':'byte-extracted parser input, NOT an independent or complete process capture','path':str(path),'source_sha256':hashlib.sha256(raw).hexdigest(),'byte_start':offset,'byte_end_exclusive':offset+len(line),'derived_path':str(derived)})
  offset+=len(line)
 case(label+'_whole_five_row_stream_rejected',raw,b'',0,292545,False,{'kind':'original complete five-command stream intentionally rejected by single-row consumer','path':str(path)})
controls=[('prefixless',out.replace(b'info string ',b'',1),b'',0,292545),('malformed_time',out.replace(b' time ',b' time BAD',1),b'',0,292545),('duplicate',out+out,b'',0,292545),('stderr',out,b'warning: explicit control\n',0,292545),('nonzero',out,b'',1,292545),('wrong_nodes',out,b'',0,321912),('warning',b'warning: explicit control\n'+out,b'',0,292545),('trailing',out+b'junk\n',b'',0,292545),('signed_nodes',out.replace(b'nodes 292545',b'nodes +292545'),b'',0,292545)]
for name,x,y,code,nodes in controls:
 write(O/f'controls/{name}.stdout.bin',x);write(O/f'controls/{name}.stderr.bin',y)
 case('control_'+name,x,y,code,nodes,False,{'kind':'explicit synthetic mutation/control, NOT engine output','original_path':str(N/'bench11.stdout.bin')})
assert len(cases)==22 and all(c['pass'] for c in cases),[c for c in cases if not c['pass']]
for name,info in inputs.items():
 p=Path(name);assert hashlib.sha256(p.read_bytes()).hexdigest()==info['sha256'] and p.stat().st_mode&0o7777==info['mode']
receipt={'status':'PASS_ACTUAL23_PRODUCER_PURE_PARSER_22_CASES_NO_ENGINE','current_runner_sha256':inputs[str(P)]['sha256'],'function_name':fn.name,'function_source_sha256':hashlib.sha256(ast.get_source_segment(source,fn).encode()).hexdigest(),'function_source_lines':[fn.lineno,fn.end_lineno],'method':'Only the exact current pure function AST was defined/executed with regex dependency; no runner module, helper or driver import. Python-B plus environment bytecode prohibition.','passed_cases':22,'cases':cases,'original_inputs':inputs,'native23_unknown_expected_nodes_preserved_as_none':True,'native23_nodes_origin':'Actual first-exclusive BENCH-SIGNATURE-FREEZE nodes292545 bound to original raw/binary bytes','engine_helper_driver_build_git_network_executions':0,'speed_or_elo_gain':None}
with (O/'PARSER-REVIEW.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
print(json.dumps({'status':receipt['status'],'passed':22,'receipt_sha256':hashlib.sha256((O/'PARSER-REVIEW.json').read_bytes()).hexdigest()}))
