import datetime, hashlib, json, pathlib, re, subprocess, time
root=pathlib.Path('/tmp/astra-al1-full');exe=root/'forge-al1';out=pathlib.Path('/tmp/forge-astra-bullet-export/validation/astra-bullet-export/lock_native/full_engine')
summary={'source_revision':'294dbed3a15dfd821aaf9d4edc6e5f62832fd460','binary_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'checks':[],'claims':'Exact OFF benchmark node counts and move generation correctness only; no speed or playing-strength claim.'}
setup='uci\nsetoption name Threads value 1\nsetoption name OwnBook value false\nisready\n'
def check(name,commands,pattern,expected):
    stdin=setup+commands+'\nquit\n';(out/(name+'.stdin')).write_text(stdin)
    argv=[str(exe)];start=time.monotonic();started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    p=subprocess.run(argv,input=stdin,text=True,capture_output=True,cwd=root,timeout=300)
    (out/(name+'.stdout.log')).write_text(p.stdout);(out/(name+'.stderr.log')).write_text(p.stderr)
    m=re.search(pattern,p.stdout);actual=int(m.group(1)) if m else None
    result={'name':name,'argv':argv,'cwd':str(root),'stdin_file':name+'.stdin','started_utc':started,'elapsed_seconds':time.monotonic()-start,'exit_code':p.returncode,'expected_nodes':expected,'actual_nodes':actual,'pass':p.returncode==0 and actual==expected}
    summary['checks'].append(result);(out/'qualification.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(result),flush=True)
for depth,nodes in [(11,312866),(13,862329),(16,3024920),(20,12389307),(22,34048354)]:
    check('off_bench_'+str(depth),'bench '+str(depth),r'info string bench depth '+str(depth)+r' nodes (\d+) ',nodes)
check('perft_startpos_5','position startpos\ngo perft 5',r'(?m)^nodes (\d+)$',4865609)
check('perft_kiwipete_5','position fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1\ngo perft 5',r'(?m)^nodes (\d+)$',193690690)
cmd=['objdump','-d',str(exe)];p=subprocess.run(cmd,capture_output=True,text=True,check=True)
(out/'objdump.stdout.log').write_text(p.stdout);(out/'objdump.stderr.log').write_text(p.stderr)
fma=[line for line in p.stdout.splitlines() if re.search(r'\bv(?:fmadd|fmsub|fnmadd|fnmsub)[a-z0-9]*\b',line)]
(out/'fma_matches.txt').write_text('\n'.join(fma)+ ('\n' if fma else ''))
summary['fma']={'argv':cmd,'exit_code':p.returncode,'count':len(fma),'pass':len(fma)==0,'scan':'entire executable disassembly'}
summary['all_checks_pass']=all(x['pass'] for x in summary['checks']) and len(fma)==0
summary['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(out/'qualification.json').write_text(json.dumps(summary,indent=2)+'\n')
files=sorted(x for x in out.iterdir() if x.is_file() and x.name!='SHA256SUMS')
(out/'SHA256SUMS').write_text(''.join(hashlib.sha256(x.read_bytes()).hexdigest()+'  '+x.name+'\n' for x in files))
print(json.dumps(summary,indent=2),flush=True)
