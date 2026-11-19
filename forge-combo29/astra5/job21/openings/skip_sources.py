"""Identify prior PGNs supplying the two skipped candidates in the effective schedule."""
from pathlib import Path
import csv,re,hashlib
W=Path('/workspace/work')
OUT=W/'j21book'
A=W/'astra5/forge-combo29/astra5'
found=[]
wanted={}
for arm in ('C21','B1','B2'):
    with (OUT/(arm+'-skips.tsv')).open() as f:
        for row in csv.DictReader(f,delimiter='\t'):
            wanted[int(row['original_epd_line'])]=(arm,int(row['full_book_seed_rank']))
def key(f): return tuple(f.split()[:3])
roots={}
with (W/'j8gate/UHO_Lichess_4852_v1.epd').open() as f:
    for i,fen in enumerate(f,1):
        if i in wanted: roots[key(fen)]=(i,*wanted[i])
        if i>=max(wanted):break
for j in (8,9,11,12,13,14,15):
    for p in sorted((A/f'job{j}').glob('*.pgn')):
        for h in re.findall(rb'(?m)^\[Event [^\n]*(?:\n\[[^\n]+)*',p.read_bytes()):
            fen=re.search(rb'(?m)^\[FEN "([^"]+)"\]',h)[1].decode()
            if key(fen) in roots:
                i,arm,rank=roots[key(fen)]
                rnd=int(re.search(rb'(?m)^\[Round "(\d+)"\]',h)[1])
                found.append((arm,rank,i,str(p.relative_to(A)),rnd,hashlib.sha256(' '.join(key(fen)).encode()).hexdigest()))
assert set(r[2] for r in found)==set(wanted)
with (OUT/'skipped-history.tsv').open('w') as f:
    w=csv.writer(f,delimiter='\t',lineterminator='\n');w.writerow(['match','seed_rank','original_epd_line','previous_match_pgn','previous_round','position_key_sha256']);w.writerows(sorted(set(found)))
