#!/usr/bin/env python3
"""Original strict fixed-reference Linux qualifier. No baseline-derived expectations."""
import argparse,hashlib,json,pathlib,re,subprocess,sys
LOCK={11:308972,13:745494,16:2460422,20:11901452,22:31111774}
KIWI='r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'
def main():
 if not __debug__:raise RuntimeError('Qualification requires assertions enabled; unset PYTHONOPTIMIZE and do not use -O')
 ap=argparse.ArgumentParser();ap.add_argument('--engine',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path,required=True);ap.add_argument('--reference-engine',type=pathlib.Path);ap.add_argument('--compiled-out',action='store_true');a=ap.parse_args();a.engine=a.engine.resolve();a.out.mkdir(parents=True,exist_ok=False)
 record={'compiled_out':a.compiled_out,'engine_sha256':hashlib.sha256(a.engine.read_bytes()).hexdigest(),'fixed_references':LOCK,'status':'FAIL','modes':{}}
 def run(label,commands):
  p=subprocess.run([str(a.engine)],input=commands+'quit\n',text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  (a.out/(label+'.stdout')).write_text(p.stdout);(a.out/(label+'.stderr')).write_text(p.stderr)
  assert p.returncode==0 and not p.stderr,(label,p.returncode,p.stderr);return p.stdout
 try:
  # First actual engine invocation must pass the hard d11 gate.
  first=run('forge_sol_first_off_d11_20261025','bench 11\n');assert re.search(r'bench depth 11 nodes 308972\b',first),'first d11 hard lock'
  uci=run('forge_sol_uci_20261025','uci\n');option='option name NnueExactInt32 type check default false\n';assert uci.count(option)==1
  if a.reference_engine:
   ref=subprocess.run([str(a.reference_engine.resolve())],input='uci\nquit\n',text=True,stdout=subprocess.PIPE,check=True).stdout
   assert uci.replace(option,'')==ref,'uci differs by more than the new option'
  # Inspect complete defined NNUE symbols; runtime/library FMA outside NNUE is separate.
  dis=subprocess.run(['objdump','-d','-C','--no-show-raw-insn',str(a.engine)],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
  blocks=re.split(r'(?m)^(?=[0-9a-f]+ <)',dis.stdout);nnue=[b for b in blocks if re.match(r'[0-9a-f]+ <forge::nnue::',b)]
  assert nnue and all(any('forge::nnue::'+n in b for b in nnue) for n in ['refresh(','update(','evaluate(']),'missing decoded NNUE APIs'
  text=''.join(nnue);(a.out/'forge_sol_nnue_disassembly_20261025.txt').write_text(text)
  fma=re.findall(r'(?m)^\s*[0-9a-f]+:\s+(v?f(?:n?madd|n?msub)\w*)\b',text);assert not fma,('NNUE FMA',fma)
  record['nnue_fma']=0;record['decoded_nnue_symbols']=len(nnue)
  for mode in ['OFF','ON']:
   prefix='setoption name NnueExactInt32 value '+('true' if mode=='ON' else 'false')+'\n';m={};stats=[]
   for depth,expected in LOCK.items():
    out=run('forge_sol_'+mode.lower()+'_bench_d'+str(depth)+'_20261025',prefix+'bench '+str(depth)+'\n')
    mat=re.search(r'bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)',out);assert mat and int(mat[2])==expected,(mode,depth,'fixed node mismatch')
    active=out.count('info string NnueExactInt32 active');assert active==(1 if mode=='ON' and not a.compiled_out else 0),(mode,'active proof')
    line=next((x for x in out.splitlines() if 'NnueExactInt32 stats ' in x),'');assert line,'missing backend counters'
    fields={k:int(v) for k,v in re.findall(r'(\w+) (\d+)',line)};assert fields.get('int32_updates',0)>0 if mode=='ON' and not a.compiled_out else fields.get('int32_updates',-1)==0
    
    if mode=='ON' and a.compiled_out:assert 'NnueExactInt32 unavailable:' in out,'compiled-out false activation'
    stats.append({'depth':depth,**fields});m[str(depth)]={'nodes':int(mat[2]),'nps':int(mat[4])}
   for label,fen,expected in [('startpos',None,4865609),('kiwipete',KIWI,193690690)]:
    out=run('forge_sol_'+mode.lower()+'_'+label+'_20261025',prefix+('position fen '+fen+'\n' if fen else 'position startpos\n')+'go perft 5\n')
    ns=re.findall(r'(?m)^nodes (\d+)\s*$',out);assert ns and int(ns[-1])==expected,(mode,label,'perft mismatch');m[label]=expected
   record['modes'][mode]={'checks':m,'refresh_statistics':stats}
  record['status']='PASS'
 finally:(a.out/'forge_sol_nnue_checks_20261025.json').write_text(json.dumps(record,indent=2)+'\n')
 print(json.dumps(record,indent=2))
if __name__=='__main__':main()
