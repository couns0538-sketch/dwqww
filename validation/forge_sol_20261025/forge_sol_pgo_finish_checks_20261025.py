from pathlib import Path
import subprocess,re,hashlib,json,datetime,os,resource,collections
h=Path('/workspace/forge-sol-20261025');run=Path('/workspace/forge-sol-20261025-pgo/forge_sol_pgo_linux_proof_20261025');out=h/'forge_sol_pgo_linux_extra_checks_20261025';out.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def limits():
 os.sched_setaffinity(0,{0,1,2,3});os.nice(19);resource.setrlimit(resource.RLIMIT_AS,(3*1024**3,3*1024**3))
rows=[]
for label,name in [('baseline','forge_sol_pgo_baseline_20261025.exe'),('pgo','forge_sol_pgo_final_20261025.exe')]:
 exe=run/'bin'/name;digest=sha(exe)
 # Both immutable builds already passed their mandatory FIRST d11 gate and all5.
 receipt=json.loads((run/'receipts'/('check-baseline.PASS.json' if label=='baseline' else 'check-use.PASS.json')).read_text());assert receipt['binary_sha256']==digest
 payload='uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nposition startpos\ngo perft 5\nposition fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1\ngo perft 5\nquit\n';(out/f'forge_sol_pgo_{label}_perft_20261025.stdin').write_text(payload)
 done=subprocess.run([str(exe)],input=payload.encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,preexec_fn=limits)
 (out/f'forge_sol_pgo_{label}_perft_20261025.stdout').write_bytes(done.stdout);(out/f'forge_sol_pgo_{label}_perft_20261025.stderr').write_bytes(done.stderr)
 counts=list(map(int,re.findall(rb'^nodes (\d+)\r?$',done.stdout,re.M)));assert done.returncode==0 and not done.stderr and counts==[4865609,193690690]
 argv=['objdump','-d','-C','--no-show-raw-insn',str(exe)];p=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE);current=None;functions={};external=collections.Counter();allhash=hashlib.sha256();totalbytes=0;nnue_text=[]
 for line in iter(p.stdout.readline,b''):
  allhash.update(line);totalbytes+=len(line);t=line.decode('utf-8','replace');header=re.match(r'^\s*([0-9a-fA-F]+) <(.+)>:\s*$',t)
  if header:
   current=header[2]
   if 'forge::nnue::' in current:functions.setdefault(current,{'address':header[1],'instructions':0,'vfmadd':0,'all_fma':0});nnue_text.append(t)
   continue
  ins=re.match(r'^\s*[0-9a-fA-F]+:\s+([A-Za-z][A-Za-z0-9_.]*)\b',t)
  if not ins:continue
  m=ins[1].lower();fma=bool(re.match(r'^v?f(?:madd|msub|nmadd|nmsub)',m))
  if current and 'forge::nnue::' in current:
   assert m not in ['.byte','.word'] and '(bad)' not in t
   f=functions[current];f['instructions']+=1;f['vfmadd']+=m.startswith('vfmadd');f['all_fma']+=fma;nnue_text.append(t)
  elif fma:external[current or 'UNKNOWN']+=1
 stderr=p.stderr.read();code=p.wait();assert code==0 and not stderr
 for api in ['refresh','update','evaluate']:assert any(n.startswith('forge::nnue::'+api+'(') and v['instructions']>0 for n,v in functions.items())
 assert functions and all(v['instructions']>0 and v['all_fma']==0 for v in functions.values()) and external['UNKNOWN']==0
 (out/f'forge_sol_pgo_{label}_nnue_disassembly_20261025.txt').write_text(''.join(nnue_text))
 assert sha(exe)==digest
 rows.append({'label':label,'exe':str(exe),'exe_sha256':digest,'prior_first_d11_and_all5_receipt':str(run/'receipts'/('check-baseline.PASS.json' if label=='baseline' else 'check-use.PASS.json')),'perft_actual_exit':done.returncode,'perft5':counts,'objdump_argv':argv,'objdump_actual_exit':code,'full_disassembly_stream_sha256':allhash.hexdigest(),'full_disassembly_bytes':totalbytes,'retention':'NNUE ranges retained; full stream hashed only per compact-evidence contract','nnue_symbols':functions,'nnue_FMA':0,'external_FMA':dict(external)})
result={'status':'PASS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'LinuxGCC14.2; no speed or Windows/Zen5 claim','rows':rows};(out/'forge_sol_pgo_linux_extra_results_20261025.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'PASS','perft':[[r['label'],r['perft5']] for r in rows],'NNUE_FMA':[[r['label'],r['nnue_FMA'],len(r['nnue_symbols'])] for r in rows]}))
