"""Recount each raw wire transcript, checking the 200 search identities and tabulated metrics."""
import csv
import hashlib
import re
import sys
from pathlib import Path

root,epd,settings=map(Path,sys.argv[1:])
fens=[' '.join(line.split()[:4])+' 0 1' for line in epd.read_text().splitlines()]
assert len(fens)==200 and hashlib.sha256(epd.read_bytes()).hexdigest()=='02d59eaf2515a4e11aecb78c5736db193812516f42ab8a6aa0b2411332186300'
expected_options=settings.read_text().splitlines()
assert len(expected_options)==22 and expected_options[-1]=='setoption name CorrHistV2 value true'
combined=[]
for limit in (500,1000,2000,4000,8000):
    folder=root/str(limit)
    wire=(folder/'wire.txt').read_text().splitlines()
    commands=[line[2:] for line in wire if line.startswith('> ')]
    expected=['uci',*expected_options]
    for fen in fens:expected.extend(['ucinewgame','isready','position fen '+fen,f'go softnodes {limit}'])
    assert commands==expected+['quit']
    assert wire.count('< readyok')==200
    rows=[]; details=[]; ns=[]; ds=[]; no_score=0; lastnodes=[]; caps=[]
    for i,seg in enumerate(('\n'.join(wire)).split(f'> go softnodes {limit}\n')[1:],1):
        replies=seg.split('> ',1)[0].splitlines()
        footer=[int(r.split()[-1]) for r in replies if r.startswith('< info string softnodes nodes ')]
        assert len(footer)==1 and replies[-1].startswith('< bestmove ')
        n=footer[0];move=replies[-1].split()[2]
        depthnums=[int(m[1]) for r in replies if (m:=re.search(r'^< info .*?\bdepth (\d+)\b',r))]
        has_score=any(re.search(r'^< info .*?\bscore (?:cp|mate) -?\d+\b',r) for r in replies)
        finished=[int(m[1]) for r in replies if (m:=re.search(r'^< info depth \d+ .*?\bnodes (\d+)\b',r))]
        ns.append(n);ds.append(depthnums[-1] if depthnums else 0);no_score+=not has_score;lastnodes.append(finished[-1] if finished else 0)
        if n>=4*limit:caps.append(i)
        rows.append(f'{i} {n} {move}\n')
    payload=''.join(rows).encode('ascii')
    assert len(rows)==200 and payload==(folder/'rows.txt').read_bytes()
    summary=(folder/'summary.tsv').read_text().splitlines()
    if not combined:combined.append(summary[0])
    combined.append(summary[1])
    official=next(csv.DictReader(summary,delimiter='\t'))
    got=tuple(map(int,(official['sum_n'],official['sum_depth'],official['n_ge_4N'],official['no_score'],official['sum_last_depth_nodes'])))
    assert got==(sum(ns),sum(ds),len(caps),no_score,sum(lastnodes))
    assert hashlib.sha256(payload).hexdigest()[:16]==official['row_sha16']
    print(f'{limit} PASS. 22 ordered settings, 200 resets and 200 readyok, every FEN, literal n and bestmove, row SHA and every metric verified. Cap rows: {caps}.')
(root/'table.tsv').write_text('\n'.join(combined)+'\n')
