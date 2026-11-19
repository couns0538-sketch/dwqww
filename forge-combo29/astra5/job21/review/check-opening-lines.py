"""Check the job 21 source line schedules against the original UHO file and historic openings."""
from collections import defaultdict
import csv
import hashlib
import os
from pathlib import Path
import re
import sys
sys.path.insert(0,'/workspace/work/j10fens/vendor')
import chess
w=Path('/workspace/work')
books=w/'j21book'
archive=w/'astra5/forge-combo29/astra5'
if 0 in os.sched_getaffinity(0):os.sched_setaffinity(0,{0})
def key(fen):
    board,side,rights=fen.split()[:3]
    return ' '.join((board,side,''.join(ch for ch in 'KQkq' if ch in rights) or '-'))
def rows(path):
    with path.open() as f:return list(csv.DictReader(f,delimiter='\t'))
schedules={stage:rows(books/f'{stage}-lines.tsv') for stage in ('C21','B1','B2')}
chosen={int(row['original_epd_line']) for records in schedules.values() for row in records}
assert len(chosen)==1300
historical=set()
for job in (8,9,11,12,13,14,15):
    for p in (archive/f'job{job}').glob('*.pgn'):
        historical.update(key(s.split('"')[1]) for s in p.read_text().splitlines() if s.startswith('[FEN "'))
for line in (archive/'job15/T1b/opening-overlap.txt').read_text().splitlines():
    m=re.match(r'^(?:T1 prior|T1b current) round (?:56|57|58|59): (.*)$',line)
    if m:historical.add(key(m[1]))
ids=set()
openings={}
for job in range(16,21):
    for p in (archive/f'job{job}').glob('*/games.tsv'):
        records=rows(p)
        if not records: continue
        if int(records[0]['book_line'])<400000:
            ids.update(int(row['book_line']) for row in records)
        else:
            for row in rows(p.parent/'openings.tsv'):
                if row['game'] in openings:assert openings[row['game']]==row['moves']
                openings[row['game']]=row['moves']
for moves in openings.values():
    b=chess.Board()
    for m in moves.split():b.push_uci(m)
    historical.add(key(b.fen()))
selected={}
with (w/'j8gate/UHO_Lichess_4852_v1.epd').open('rb') as stream:
    for n,line in enumerate(stream,1):
        if n in ids:historical.add(key(line.decode()))
        if n in chosen:selected[n]=key(line.decode())
assert len(selected)==len(chosen) and len(set(selected.values()))==1300
assert len(historical)==11815 and not set(selected.values())&historical
for stage,rows_ in schedules.items():
    per_stage={selected[int(r['original_epd_line'])] for r in rows_}
    derived={key(x) for x in (books/f'{stage}.epd').read_text().splitlines()}
    assert per_stage==derived
    for r in rows_:
        assert hashlib.sha256(selected[int(r['original_epd_line'])].encode()).hexdigest()==r['position_key_sha256']
    print(f'{stage} {len(rows_)} distinct original physical lines, correct stored key hashes and matching derived EPD positions, no intersection with the historical or other job 21 keys.')
print(f'All {len(chosen)} selected lines verified against {n} source entries and {len(historical)} distinct historical keys after normalizing side, placement and castling. Earlier PGN pairs, interrupted clock roots and jobs 16–20 physical and randomly generated roots were included.')
