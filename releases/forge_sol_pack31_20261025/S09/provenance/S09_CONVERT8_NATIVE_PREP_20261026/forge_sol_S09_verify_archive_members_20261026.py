"""Verify actual reused object bytes against members of the frozen parent archive."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=json.loads(Path(sys.argv[1]).read_text());archive=Path(p['parent_artifacts']['core_archive']['path']);before=sha(archive)
if before!=p['parent_artifacts']['core_archive']['sha256']:raise ValueError('parent archive changed')
rows=[]
for item in p['object_closure']:
    if not item['reused']:continue
    path=Path(item['path']);command=['/usr/bin/x86_64-linux-gnu-ar','p',str(archive),path.name]
    child=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    actual=hashlib.sha256(child.stdout).hexdigest()
    if child.returncode!=0 or child.stderr or sha(path)!=item['sha256'] or actual!=item['sha256']:raise ValueError('archive/object mismatch: '+str(path))
    rows.append({'path':str(path),'member':path.name,'command':command,'returncode':child.returncode,'bytes':len(child.stdout),'sha256':actual})
if len(rows)!=6 or sha(archive)!=before:raise ValueError('wrong six-object closure or archive changed')
print(json.dumps({'status':'PASS','archive_sha256':before,'members':rows},sort_keys=True))
