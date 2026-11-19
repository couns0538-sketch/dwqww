"""Reproduce Job 21's three report intervals using the pinned source and score receipts."""
import csv
from hashlib import sha256
from io import StringIO
from pathlib import Path
import subprocess
import sys

from stats_seed import evaluate

ref='040834de294a31f81a3d6aa54a605af692a4fcb4'
base='forge-combo29/astra5/job21'
repo=Path(sys.argv[1])
def read(name):
    return subprocess.check_output(['git','-C',str(repo),'show',f'{ref}:{base}/{name}'])
src=read('audit/stats_seed.py')
assert src==Path(__file__).with_name('stats_seed.py').read_bytes()
print('archive',ref,base,'audit/stats_seed.py sha256',sha256(src).hexdigest())
for stage in ('C21','B1','B2'):
    data=read(stage+'/score.tsv')
    row=next(csv.DictReader(StringIO(data.decode()),delimiter='\t'))
    bins=[int(row[k]) for k in ('penta0','penta05','penta1','penta15','penta2')]
    scores=[i/4 for i,count in enumerate(bins) for _ in range(count)]
    value,low,high=evaluate(scores)
    result=[f'{x:+.8f}' for x in (value,low,high)]
    assert result==[row[k] for k in ('elo','lower95','upper95')]
    print(stage,','.join(map(str,bins)),*result,'PASS',sha256(data).hexdigest())
