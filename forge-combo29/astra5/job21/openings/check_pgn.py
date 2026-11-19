"""Map actual PGN openings and all controller starts to original book lines."""
import argparse,csv,hashlib,re
from pathlib import Path
from collections import defaultdict,Counter

arg=argparse.ArgumentParser()
arg.add_argument('match',choices=('C21','B1','B2'))
arg.add_argument('--source',type=Path,default=Path('/workspace/work/j8gate/UHO_Lichess_4852_v1.epd'))
arg.add_argument('--schedule',type=Path,default=Path('/workspace/work/j21book'))
arg.add_argument('--match-files',type=Path,default=Path('/workspace/work/j21match/results'))
arg.add_argument('--out',type=Path,default=Path('/workspace/work/j21book'))
a=arg.parse_args();stage=a.match
with (a.schedule/f'{stage}-lines.tsv').open() as f: rows=list(csv.DictReader(f,delimiter='\t'))
needed={int(row['original_epd_line']) for row in rows}
fens={}
with a.source.open() as f:
    for i,s in enumerate(f,1):
        if i in needed:fens[i]=s.strip()
        if len(fens)==len(needed):break
assert set(fens)==needed
for row in rows:
    assert hashlib.sha256(' '.join(fens[int(row['original_epd_line'])].split()[:3]).encode()).hexdigest()==row['position_key_sha256']
pgn=(a.match_files/f'{stage}.pgn').read_bytes();out=(a.match_files/f'{stage}.out').read_bytes();meta=(a.match_files/f'{stage}.meta').read_text()
assert re.search(r'^\S+ '+stage+r' end$',meta,re.M)
starts={int(i) for i in re.findall(rb'^Started game (\d+) of ',out,re.M)}
finish={int(i) for i in re.findall(rb'^Finished game (\d+) .*?: (?:1-0|0-1|1/2-1/2) ',out,re.M)}
group=defaultdict(set); exact6=0; raw_count=0; raw_games=set()
for header in re.findall(rb'(?m)^\[Event [^\n]*(?:\n\[[^\n]+)*',pgn):
    def tag(t):return re.search(rb'(?m)^\['+t.encode()+rb' "(.*?)"\]',header)[1].decode()
    round_id=int(tag('Round'));fen=tag('FEN'); expected=fens[int(rows[round_id-1]['original_epd_line'])]
    assert fen.split()[:4]==expected.split()[:4],(round_id,fen,expected)
    white=tag('White'); black=tag('Black')
    assert {white,black}=={stage+'-A',stage+'-B'}
    game=(2*round_id-1) if white==stage+'-A' else 2*round_id
    assert game in starts and game not in raw_games
    group[round_id].add(white);raw_games.add(game)
    raw_count+=1; exact6+=(fen==expected)
assert raw_games==finish
all_starts={(gid+1)//2 for gid in starts}
assert set(group)<=all_starts
miss=sorted(all_starts-set(group))
complete=sum(len(cols)==2 for cols in group.values())
single=sum(len(cols)==1 for cols in group.values())
text=[f'{stage}: {len(rows)} scheduled distinct EPD lines; {len(all_starts)} rounds started, {raw_count} finished PGN game records from {len(group)} rounds ({complete} complete pairs, {single} singletons).',
      f'Original book line match: {raw_count}/{raw_count} PGN start FENs equal in the first four fields, {exact6}/{raw_count} equal in all six fields. Runner finished IDs and PGN game IDs agree.',
      'Original selected lines are in round order in '+stage+'-lines.tsv. Each started round maps to selected line round−1 in zero-based indexing.',
      'Started rounds without a finished PGN: '+(', '.join(f'{r} (line {rows[r-1]["original_epd_line"]})' for r in miss) or 'none')+'.',
      f'PGN SHA-256 {hashlib.sha256(pgn).hexdigest()}; controller output SHA-256 {hashlib.sha256(out).hexdigest()}.']
(a.out/f'{stage}-opening-readback.txt').write_text('\n'.join(text)+'\n')
print('\n'.join(text[:2]))
