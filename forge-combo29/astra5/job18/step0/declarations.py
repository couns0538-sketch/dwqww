from pathlib import Path
import hashlib,re,subprocess
d=Path('/workspace/work')
out=d/'j18gate/evidence'
paths={'r15d':d/'j7base/build/forge','kF':d/'j16kf/build/forge'}
expected={'r15d':'9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671','kF':'c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb','net768':'c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7'}
script=(d/'job18.md').read_text().split('THE 40 SETTINGS (name, start, min, max, step; start = the PC\'s value, else the exe\'s own)\n')[1].split('THE FIVE VALUE SETS')[0]
names=re.findall(r'\b(\w+)\s+\d+\s+\d+\s+\d+\s+\d+',script)
assert len(names)==len(set(names))==40 and names[0]=='DrawJitter' and names[-1]=='EvalSwingMult'
with (out/'identities.txt').open('x') as f:
 for k,p in {**paths,'net768':d/'j7net/net768.nnue'}.items():
  with p.open('rb') as raw:sha=hashlib.file_digest(raw,'sha256').hexdigest()
  print(f'{k} sha256 {sha} {p}',file=f);assert expected[k]==sha
 proc_count=int(subprocess.check_output(['nproc'],text=True))
 print('nproc',proc_count,file=f)
 print('S max per build for driver F',(proc_count-1)//2,file=f)
 print('UTC',subprocess.check_output(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],text=True).strip(),file=f)
for key,p in paths.items():
 target=out/key
 target.mkdir(exist_ok=True)
 commands='uci\nquit\n'
 result=subprocess.run([str(p)],input=commands,text=True,capture_output=True,timeout=15,cwd=p.parent)
 (target/'uci-raw.txt').write_text('INPUT\n'+commands+'STDOUT\n'+result.stdout+'STDERR\n'+result.stderr)
 assert not result.stderr and result.returncode==0 and result.stdout.splitlines().count('uciok')==1
 entries=[]
 for name in names:
  decl=[s for s in result.stdout.splitlines() if s.startswith('option name '+name+' type ')]
  assert len(decl)==1,(name,decl)
  entries.extend(decl)
 (target/'40-uci.txt').write_text('\n'.join(entries)+'\n')
 print(key,len(entries),'ordered declarations')
print((out/'identities.txt').read_text())
