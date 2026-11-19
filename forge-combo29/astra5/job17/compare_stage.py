"""Run cmp on the sorted records and report opening-by-opening differences."""
from itertools import zip_longest
import subprocess
import sys
from arm import read_games
from selfplay import RESULTS

def compare(stage):
    pairs = {'K17':('K17-1','K17-2'), 'C17':('K17-1','C17')}
    arms = pairs.get(stage,(f'{stage}-r15d',f'{stage}-kF'))
    data = [read_games(arm) for arm in arms]
    paths = [RESULTS/arm/'records.txt' for arm in arms]
    if not all((p.parent/'run.log').read_text().endswith('status COMPLETE\n') for p in paths):
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
    return 0 if (stage=='C17')==bool(unequal) or stage not in ('C17','K17') else 1

if __name__=='__main__':
    sys.exit(compare(sys.argv[1]))
