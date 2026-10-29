import sys, pathlib, subprocess, json, hashlib, re, datetime, os
exe=pathlib.Path(sys.argv[1]).resolve(); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=False)
sets=json.loads(sys.argv[3]) if len(sys.argv)>3 else {'OFF':[]}
records=[]
for mode,options in sets.items():
 for depth,pin in [(11,312866),(13,862329),(16,3024920),(20,12389307),(22,34048354)]:
  commands='\n'.join(['uci','setoption name Threads value 1','setoption name Hash value 16','setoption name OwnBook value false']+options+['isready',f'bench {depth}','quit',''])
  stem=out/f'{mode}_d{depth}'
  stem.with_suffix('.stdin').write_text(commands)
  run=subprocess.run([str(exe)],input=commands.encode(),capture_output=True,timeout=300)
  stem.with_suffix('.stdout').write_bytes(run.stdout); stem.with_suffix('.stderr').write_bytes(run.stderr)
  lines=re.findall(rb'^info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)',run.stdout,re.M)
  row={'mode':mode,'depth':depth,'returncode':run.returncode,'matches':[list(map(int,x)) for x in lines]}
  row['pass']=run.returncode==0 and len(lines)==1 and int(lines[0][0])==depth and (mode!='OFF' or int(lines[0][1])==pin)
  records.append(row); print(json.dumps(row),flush=True)
  (out/'results.json').write_text(json.dumps({'binary':str(exe),'sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'records':records},indent=2)+'\n')
commands='position startpos\ngo perft 5\nquit\n'
run=subprocess.run([str(exe)],input=commands.encode(),capture_output=True,timeout=120)
(out/'perft.stdout').write_bytes(run.stdout); (out/'perft.stderr').write_bytes(run.stderr);(out/'perft.stdin').write_text(commands)
ok=run.returncode==0 and re.search(rb'^nodes 4865609$',run.stdout,re.M) is not None
print(json.dumps({'perft5':ok,'returncode':run.returncode}),flush=True)
sys.exit(0 if ok and all(r['pass'] for r in records) else 1)
