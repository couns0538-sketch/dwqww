"""Compare staged Git blobs with raw working bytes, without text filters."""
import argparse
import subprocess
from run_policy import free_guard, write_json

def git(*args,**kwargs):
    return subprocess.run(['git',*args],check=True,stdout=subprocess.PIPE,**kwargs).stdout

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',required=True)
parser.add_argument('--threads',required=True,type=int,choices=[1])
args=parser.parse_args()
free_guard(16*1024*1024)
tokens=git('diff','--cached','--raw','-z','--no-abbrev').split(b'\0')
paths=[]
expected=[]
for i in range(0,len(tokens)-1,2):
    fields=tokens[i].split()
    if fields[-1] not in (b'A',b'M'):
        raise ValueError('unexpected staged change kind')
    paths.append(tokens[i+1])
    expected.append(fields[3])
actual=git('hash-object','--no-filters','--stdin-paths',input=b'\n'.join(paths)+b'\n').splitlines()
if actual!=expected:
    raise ValueError('staged blob differs from original working bytes')
write_json(args.output,dict(status='PASS',files=len(paths),method='Git index blob IDs equal hash-object --no-filters on exact working bytes',
                           paths=[p.decode('utf-8') for p in paths]))
print(f'PASS: {len(paths)} staged files retain exact working bytes.')
