"""Check the restarted C26 suite against the interrupted attempt, including the unfinished game prefix."""
import csv
from hashlib import sha256
import json
from pathlib import Path
import sys

from audit_games import read_wire, table, table_out

root=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
old=root/'C26-attempt1';new=root/'C26'
prior={int(r['game']):r for r in table(old/'games.tsv')}
fresh={int(r['game']):r for r in table(new/'games.tsv')}
assert set(fresh)==set(range(1,21)) and prior.keys()<fresh.keys() and len(prior)==19
assert (old/'inputs.json').read_bytes()==(new/'inputs.json').read_bytes()
oend=json.loads((old/'end.json').read_text());nend=json.loads((new/'end.json').read_text())
assert oend['complete_pairs']==9 and 'BrokenPipeError' in oend['reason']
assert nend['complete_pairs']==10
oldids=set();newids=set();details=[];completed_rows=0;partial_rows=0
for game in sorted(fresh):
    p,q=old/f'g{game:04d}',new/f'g{game:04d}'
    ocfg=json.loads((p/'engines.json').read_text());ncfg=json.loads((q/'engines.json').read_text())
    for side in ['W','B']:
        assert ocfg[side]['options']==ncfg[side]['options'] and ocfg[side]['exe']==ncfg[side]['exe'] and ocfg[side]['role']==ncfg[side]['role']
        oldids.add((ocfg[side]['pid'],ocfg[side]['start_ticks']));newids.add((ncfg[side]['pid'],ncfg[side]['start_ticks']))
    assert (p/'opening.txt').read_bytes()==(q/'opening.txt').read_bytes()
    a=table(p/'searches.tsv');b=table(q/'searches.tsv')
    assert a==b[:len(a)]
    x,y,z=read_wire(p/'wire.txt');xx,yy,zz=read_wire(q/'wire.txt')
    assert x==xx and y==yy
    assert z[:len(a)]==zz[:len(a)]
    if game in prior:
        assert all(prior[game][k]==fresh[game][k] for k in ['game','opening','white','black','result','ending','plies','wclock','bclock'])
        assert a==b and z==zz
        completed_rows+=len(a)
        details.append((game,'first game complete',len(a),len(b),'all search rows and terminal result/clocks agree','-'))
    else:
        assert len(a)<len(b) and len(z)==len(a)+1
        op,np=z[-1],zz[len(a)]
        assert op['pos']==np['pos'] and op['go']==np['go'] and op['s']==np['s']
        assert np['hold'][:len(op['hold'])]==op['hold'] and np['soft'][:len(op['soft'])]==op['soft'] and not op['moves']
        first=(p/'interruption.txt').read_text().splitlines()[0]
        assert 'CancelledError' in first
        partial_rows=len(a)
        details.append((game,'first game canceled',len(a),len(b),'all finished searches agree; in-flight position/go and any observed markers agree',first))
assert len(oldids)==len(newids)==40 and oldids.isdisjoint(newids)
table_out(out/'attempt1-vs-repeat.tsv',['game','status_in_attempt1','completed_searches_in_attempt1','searches_in_full_repeat','comparison','interruption_line'],details)
rows=[
    'C26 attempt 1 versus the fresh complete repeat (all 20 games were restarted).',
    f'First run termination: {oend["reason"]}; UTC {oend["utc"]}. Source C26-attempt1/end.json and stop.txt.',
    f'Initial completed games: {len(prior)} of 20, forming {oend["complete_pairs"]} pairs. Repeat: 20 of 20 games, {nend["complete_pairs"]} complete pairs.',
    f'All {completed_rows} completed search rows, with moves, literal final N, floor charges, pre/post clocks and hold text, agree across the 19 finished games. Their results, endings, applied plies and both final clocks also agree.',
    f'Canceled game {next(iter(fresh.keys()-prior.keys()))}: all {partial_rows} completed search rows match. The next search was sent the same position/go, had no bestmove in the canceled attempt and is never counted as a completed row from that attempt.',
    'The two attempts used identical input receipts and per-color options, and disjoint sets of 40 PID/start-tick identities each.',
    'Sources: each attempt\'s inputs.json, games.tsv, gNNNN/engines.json, opening.txt, searches.tsv and wire.txt; canceled game interruption.txt. attempt1-vs-repeat.tsv provides individual counts.',
]
(out/'attempt1-vs-repeat.txt').write_text('\n'.join(rows)+'\n')
print('\n'.join(rows))
