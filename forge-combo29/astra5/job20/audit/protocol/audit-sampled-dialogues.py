"""Check selections independently against complete search reply samples from the actual arms."""
from pathlib import Path
import re
import sys
W=Path('/workspace/work/j20match/results')
def verify(arm):
    path=W/arm/'sample-uci.txt'
    text=path.read_text()
    total=soft=mate=na=0
    for section in text.split('begin ')[1:]:
        bits=section.splitlines()
        if not bits or bits[-1]!='end': raise ValueError(path)
        game,ply=bits[0].split()
        replies=[s.removeprefix('< ') for s in bits if s.startswith('< ')]
        best=replies[-1].split()
        assert best[0]=='bestmove'
        indices=[i for i,s in enumerate(replies[:-1]) if s.startswith('info depth ')]
        if indices:
            n=indices[-1]
            parts=re.fullmatch(r'(info depth .*? nodes [0-9]+) nps [0-9]+( hashfull [0-9]+) time [0-9]+( pv.*)',replies[n])
            assert parts,replies[n]
            expected=''.join(parts.groups())
            if any(s.startswith('info string softnodes nodes ') for s in replies[n+1:-1]):soft+=1
        else:
            expected='NA';na+=1
        if ' score mate ' in expected:mate+=1
        assert f'record {game} {ply} {best[1]} {expected}'==bits[-2]
        total+=1
    return total,soft,mate,na
arms=sys.argv[1:] or ['K20-1','K20-2','C20']+[f'P{i}-{b}' for i in (1,2,3) for b in ('r15d','kF')]
print('arm\tfull_search_dialogues\tlater_softnodes_supplement\tselected_mate\tselected_NA')
for a in arms:
    print(a,*verify(a),sep='\t')
