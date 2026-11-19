"""Compare whole raw record files and independently find differing completed games."""
import csv
from itertools import zip_longest
import re
import subprocess
import sys
from selfplay import RESULTS

def field(line):
    if line is None: return {}
    value=line.decode('ascii').rstrip('\n').split(' ',3)[3]
    if value=='NA': return {'availability':'NA'}
    fields={}
    for name in ('depth','seldepth','score','nodes','hashfull','pv'):
        pat=(r'(?:^|\s)'+name+r'\s+(.*)$') if name=='pv' else (r'(?:^|\s)'+name+r'\s+(\S+\s+\S+)' if name=='score' else r'(?:^|\s)'+name+r'\s+(\S+)')
        m=re.search(pat,value)
        if m: fields[name]=m[1]
    return fields

def compare(stage):
    pairs={'K20':('K20-1','K20-2'),'C20':('K20-1','C20')}
    arms=pairs.get(stage,(stage+'-r15d',stage+'-kF'))
    dirs=[RESULTS/a for a in arms]
    if not all((d/'run.log').read_text().endswith('status COMPLETE\n') for d in dirs): raise RuntimeError('incomplete arm')
    paths=[d/'records.txt' for d in dirs]
    cmp=subprocess.run(['cmp',*paths],capture_output=True,text=True)
    if cmp.returncode not in (0,1): raise RuntimeError(cmp.stderr)
    with (dirs[0]/'games.tsv').open() as ia,(dirs[1]/'games.tsv').open() as ib,paths[0].open('rb') as ra,paths[1].open('rb') as rb:
        offsets=[0,0]
        bad=[]
        diff=None
        total=scored=mate=games=0
        for a,b in zip(csv.DictReader(ia,delimiter='\t'),csv.DictReader(ib,delimiter='\t'),strict=True):
            if a['book_line']!=b['book_line']: raise ValueError('openings differ')
            games+=1
            total+=int(a['plies'])
            scored+=int(a['score'])
            mate+=int(a['mate'])
            blocks=[]
            for i,row,f in ((0,a,ra),(1,b,rb)):
                end=int(row['record_bytes'])
                blocks.append(f.read(end-offsets[i]))
                if len(blocks[-1])!=end-offsets[i]: raise ValueError('incomplete game')
                offsets[i]=end
            if blocks[0]!=blocks[1]:
                bad.append(a['book_line'])
                if diff is None:
                    diff=next((x,y) for x,y in zip_longest(*(v.splitlines(keepends=True) for v in blocks)) if x!=y)
        if ra.read(1) or rb.read(1): raise ValueError('unreceipted rows')
    if bool(bad)!=bool(cmp.returncode): raise ValueError('per-game versus raw comparison')
    with (RESULTS/f'{stage}-cmp.txt').open('x') as f:
        print('cmp',*paths,file=f)
        print('exit',cmp.returncode,file=f)
        if cmp.stdout: f.write(cmp.stdout)
        if cmp.stderr: f.write(cmp.stderr)
        print('full game records differ in',f'{len(bad)}/{games}','games',file=f)
        if bad:
            print('differing game IDs',*bad,file=f)
            print('first differing records:',file=f)
            for arm,row in zip(arms,diff):
                print(arm,row.decode('ascii').removesuffix('\n') if row else 'EOF',file=f)
            left,right=map(field,diff)
            key=next((k for k in ('availability','depth','seldepth','score','nodes','hashfull','pv') if left.get(k)!=right.get(k)), 'other retained bytes or bestmove')
            print('first differing label field',key,file=f)
        else:
            print('all record bytes equal',file=f)
        if stage=='K20': print('score_records',scored,'records',total,'mate_records',mate,file=f)
    if stage=='K20': return int(bool(bad) or total!=scored)
    if stage=='C20': return int(not bad)
    return 0

if __name__=='__main__': sys.exit(compare(sys.argv[1]))
