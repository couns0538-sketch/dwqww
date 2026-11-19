"""Reconcile fastchess raw game IDs and select all and only completed colour pairs before the deadline."""
from collections import Counter
from datetime import datetime
import hashlib
from pathlib import Path
import re
import sys

root=Path(__file__).resolve().parent
stage=sys.argv[1]
target={'C21':200,'B1':1200,'B2':1200}[stage]
folder=root/'results'
deadline=datetime.fromisoformat('2026-11-19T02:22:00+00:00')
pg=folder/f'{stage}.pgn'
lg=folder/f'{stage}.out'
md=folder/f'{stage}.meta'
start_ids=[int(i) for i in re.findall(rb'^Started game (\d+) of ',lg.read_bytes(),re.M)]
finish_ids=[int(i) for i in re.findall(rb'^Finished game (\d+) ',lg.read_bytes(),re.M)]
if len(finish_ids)!=len(set(finish_ids)):
    raise ValueError('duplicate finished game IDs')
actual={}
raw={}
ends={}
latest=None
for block in re.split(rb'(?=^\[Event )',pg.read_bytes(),flags=re.M)[1:]:
    tags={k.decode():v.decode() for k,v in re.findall(rb'^\[(\w+) "([^"]*)"\]',block,re.M)}
    game=2*int(tags['Round'])-(tags['White']==f'{stage}-A')
    if game in raw:
        raise ValueError(f'duplicate raw game {game}')
    raw[game]=block
    if tags['Result'] not in {'1-0','0-1','1/2-1/2'}:
        continue
    stop=datetime.strptime(tags['GameEndTime'],'%Y-%m-%dT%H:%M:%S %z')
    ends[game]=stop
    if latest is None or stop>latest:
        latest=stop
    if stop<deadline:
        actual[game]=tags
all_f=set(finish_ids)
if set(ends)!=all_f:
    raise ValueError(f'PGN vs controller completion differs, PGN only {set(ends)-all_f}, controller only {all_f-set(ends)}')
pairs={int(tags['Round']) for tags in actual.values() if 2*int(tags['Round']) in actual and 2*int(tags['Round'])-1 in actual}
included={game for game,tags in actual.items() if int(tags['Round']) in pairs}
singles=set(actual)-included
excluded=all_f-included
incomplete=len(included)<target
hash_at=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
evidence=[f'{stage} status '+('INCOMPLETE' if incomplete else 'COMPLETE'),f'target games {target}',
          f'raw started game IDs ({len(start_ids)}) '+','.join(map(str,sorted(start_ids))),
          f'raw finished game IDs ({len(finish_ids)}) '+','.join(map(str,sorted(finish_ids))),
          f'UTC cutoff {deadline.isoformat()}; latest finished PGN time {latest.astimezone(deadline.tzinfo).isoformat() if latest else "none"}',
          f'fully before cutoff {len(actual)}; scoreable games {len(included)}; whole opening pairs {len(pairs)}',
          'included opening rounds '+','.join(map(str,sorted(pairs))),
          'unpaired completed game IDs '+(','.join(map(str,sorted(singles))) or 'none'),
          'finished at or after cutoff '+(','.join(map(str,sorted(all_f-set(actual)))) or 'none'),
          'started but unfinished game IDs '+(','.join(map(str,sorted(set(start_ids)-all_f))) or 'none'),
          f'{hash_at(pg)}  {pg.name} (full raw original)',
          f'{hash_at(lg)}  {lg.name} (full raw original)']
if excluded or set(raw)-included:
    dst=folder/f'{stage}-whole-pairs.pgn'
    dst.write_bytes(b''.join(block for game,block in raw.items() if game in included))
    evidence.append(f'{hash_at(dst)}  {dst.name} (verbatim blocks of complete pre-cutoff pairs)')
else:
    evidence.append('Every finished game belongs to a complete pre-cutoff pair; use full raw PGN for scoring.')
evidence.extend(line for line in md.read_text().splitlines() if ' stop request;' in line or line.startswith('status ') or line.startswith('exit ') or line.endswith(f' {stage} end'))
(folder/f'{stage}-cutoff.txt').write_text('\n'.join(evidence)+'\n')
print(f'{stage}: {len(included)}/{target} scoreable games, {len(pairs)} pairs, {len(singles)} completed singletons, {len(all_f-set(actual))} late.')
