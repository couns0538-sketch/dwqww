from pathlib import Path
import json,os,signal,subprocess,time,hashlib
repo=Path('/workspace/dwqww');here=Path(__file__).resolve().parent
out=here/'bench-diagnosis-attempt1';out.mkdir(exist_ok=False)
full=(repo/'validation/upstream-clock-reconcile-20261020/parity-frozen-cecf0b9-attempt1/bench-candidate/stdin.bin').read_bytes()
cases=[('bare-candidate','/workspace/.cloud-setup/forge-extension-path-release/forge',b'bench 11\nquit\n'),('full-candidate','/workspace/.cloud-setup/forge-extension-path-release/forge',full),('full-parent','/workspace/.cloud-setup/forge-clock-contract-release/forge',full)]
rows=[]
for label,binary,stdin in cases:
 command=['strace','-f','-tt','-T','-s','256','-e','trace=read,write,futex,close,exit_group','-o',str(out/(label+'.strace')),binary]
 (out/(label+'.stdin')).write_bytes(stdin)
 start=time.monotonic()
 p=subprocess.Popen(command,cwd=repo,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
 deadline=False
 try:stdout,stderr=p.communicate(stdin,timeout=5)
 except subprocess.TimeoutExpired:
  deadline=True;os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate(timeout=5)
 (out/(label+'.stdout')).write_bytes(stdout);(out/(label+'.stderr')).write_bytes(stderr)
 row={'label':label,'command':command,'timeout_seconds':5,'deadline':deadline,'exit_code':p.returncode,'elapsed_diagnostic_only':time.monotonic()-start,'engine_sha256':hashlib.sha256(Path(binary).read_bytes()).hexdigest(),'stdin_sha256':hashlib.sha256(stdin).hexdigest(),'stdout_bytes':len(stdout),'stderr_bytes':len(stderr)}
 rows.append(row);(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
