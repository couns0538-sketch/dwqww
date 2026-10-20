#!/usr/bin/env python3
"""Supplement the saved 300-case corpus with both dynamic diagonal controls."""
from pathlib import Path
import csv, hashlib, json, subprocess, time
import chess

ROOT=Path(__file__).resolve().parent
VALUES={None:0,1:100,2:300,3:300,4:500,5:900,6:0}
THRESHOLDS=[-2000,-1000,-900,-800,-600,-500,-300,-1,0,1,99,100,101,299,300,500,899,900,901,1700]
def gain(board,move): return VALUES[board.piece_type_at(move.to_square)]+(VALUES[move.promotion]-100 if move.promotion else 0)
def exchange(board,target):
    best=0; tree=[]
    for move in list(board.legal_moves):
        if move.to_square!=target or not board.is_capture(move): continue
        value=gain(board,move); board.push(move); reply,children=exchange(board,target); board.pop()
        tree.append({'move':move.uci(),'net':value-reply,'children':children}); best=max(best,value-reply)
    return best,tree
cases=[]
for name,fen,uci in [
 ('ghost_diagonal_target_pinner_removed','k7/8/8/8/8/2p2N2/3b4/3QK3 w - - 0 1','d1d2'),
 ('newly_exposed_diagonal_pin','b7/7k/8/8/3Q1p2/5r2/6N1/7K w - - 0 1','d4f4'),
]:
    board=chess.Board(fen); move=chess.Move.from_uci(uci)
    assert board.is_valid() and move in board.legal_moves,(name,fen,uci)
    for color,b,m in [('white',board,move),('black',board.mirror(),chess.Move(chess.square_mirror(move.from_square),chess.square_mirror(move.to_square)))]:
        assert b.is_valid() and m in b.legal_moves
        before=b.fen(); value=gain(b,m); b.push(m)
        recaptures=sorted(x.uci() for x in b.legal_moves if x.to_square==m.to_square and b.is_capture(x))
        reply,tree=exchange(b,m.to_square)
        cases.append({'id':name+'_'+color,'fen':before,'move':m.uci(),'oracle_exchange':value-reply,'legal_recaptures':recaptures,'exchange_tree':tree})
(ROOT/'supplement-oracle.json').write_text(json.dumps(cases,indent=2)+'\n')
tsv=ROOT/'supplement-cases.tsv'; tsv.write_text(''.join(c['id']+'\t'+c['fen']+'\t'+c['move']+'\n' for c in cases))
record={'pre_run_corpus_sha256':hashlib.sha256((ROOT/'supplement-oracle.json').read_bytes()).hexdigest(),'phases':[]}
(ROOT/'supplement-record.json').write_text(json.dumps(record,indent=2)+'\n')
outputs={}
for kind in ['baseline','candidate']:
    args=[str(ROOT/('see-'+kind)),str(tsv)]; start=time.monotonic()
    p=subprocess.run(args,capture_output=True,timeout=10)
    for ext,data in [('stdout',p.stdout),('stderr',p.stderr)]: (ROOT/('supplement-'+kind+'.'+ext)).write_bytes(data)
    record['phases'].append({'command':args,'return_code':p.returncode,'elapsed_seconds':time.monotonic()-start,'timeout_seconds':10})
    (ROOT/'supplement-record.json').write_text(json.dumps(record,indent=2)+'\n')
    assert p.returncode==0
    outputs[kind]={r['id']:r for r in csv.DictReader(p.stdout.decode().splitlines(),delimiter='\t')}
record['comparisons']=[]; failures=[]
for c in cases:
    row=outputs['candidate'][c['id']]; expected=c['oracle_exchange']
    if row['initial_legal']!='1' or int(row['static_exchange'])!=expected: failures.append(c['id']+' legality/exchange')
    recaptures=sorted(row['legal_recaptures'].split(',')) if row['legal_recaptures'] else []
    if recaptures!=c['legal_recaptures']: failures.append(c['id']+' recaptures')
    for t in THRESHOLDS:
        if bool(int(row['ge'+str(t)]))!=(expected>=t): failures.append(c['id']+' ge'+str(t))
    record['comparisons'].append({'id':c['id'],'baseline':int(outputs['baseline'][c['id']]['static_exchange']),'candidate':int(row['static_exchange']),'oracle':expected})
record['failures']=failures; record['status']='PASS' if not failures else 'FAILED_preserve_candidate'
(ROOT/'supplement-record.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
raise SystemExit(bool(failures))
