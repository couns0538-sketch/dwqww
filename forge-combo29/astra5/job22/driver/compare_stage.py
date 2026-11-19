"""Run cmp on the sorted records and report opening-by-opening differences."""
import csv
from itertools import zip_longest
import subprocess
import sys
from selfplay import RESULTS

def complete_games(arm):
    dest=RESULTS/arm
    result={}
    offset=0
    with (dest/'records.txt').open('rb') as raw, (dest/'games.tsv').open() as ix:
        for row in csv.DictReader(ix,delimiter='\t'):
            end=int(row['record_bytes'])
            chunk=raw.read(end-offset)
            if len(chunk)!=end-offset: raise ValueError('truncated game')
            result[int(row['book_line'])]=(row,chunk)
            offset=end
        if raw.read(1): raise ValueError('unreceipted records')
    return result

def compare(stage):
    pairs = {'K22':('K22-1','K22-2'), 'C22':('K22-1','C22')}
    arms = pairs.get(stage,(f'{stage}-r15d',f'{stage}-kF'))
    data = [complete_games(arm) for arm in arms]
    paths = [RESULTS/arm/'records.txt' for arm in arms]
    if not all((p.parent/'run.log').read_text().endswith(('status COMPLETE\n','status CUT_MINUTE40\n')) for p in paths):
        raise RuntimeError('cannot grade incomplete arms')
    run = subprocess.run(['cmp',*paths],capture_output=True,text=True)
    if run.returncode not in (0,1):
        raise RuntimeError(run.stderr)
    assert data[0].keys()==data[1].keys()
    unequal = [n for n in sorted(data[0]) if data[0][n][1]!=data[1][n][1]]
    assert bool(unequal)==bool(run.returncode)
    with (RESULTS/f'{stage}-cmp.txt').open('x') as out:
        print('cmp',*paths,file=out)
        print('exit',run.returncode,file=out)
        if run.stdout.strip(): print(run.stdout.strip(),file=out)
        if run.stderr.strip(): print(run.stderr.strip(),file=out)
        print('full game records differ in',f'{len(unequal)}/{len(data[0])}','games',file=out)
        if unequal:
            print('differing book lines',*unequal,file=out)
            x,y = next((x,y) for x,y in zip_longest(*(paths[i].read_bytes().splitlines() for i in (0,1))) if x!=y)
            print('first differing complete records:',file=out)
            for arm,line in zip(arms,(x,y)): print(arm,line.decode() if line else 'EOF',file=out)
        else:
            print('every node column and every bestmove equal',file=out)
    return 0 if (stage=='C22')==bool(unequal) or stage not in ('C22','K22') else 1

if __name__=='__main__':
    sys.exit(compare(sys.argv[1]))
