#!/usr/bin/env python3
"""Twelve fixed legal API controls; no compiler/source changes or SEE selection."""
from pathlib import Path
import csv, datetime, hashlib, json, subprocess, time
import chess

ROOT=Path(__file__).resolve().parent
PROTO=ROOT.parent/'pinned-see-prototype-20261020'
VALUES={None:0,1:100,2:300,3:300,4:500,5:900,6:0}
THRESHOLDS=[-2000,-1000,-900,-800,-600,-500,-300,-1,0,1,99,100,101,299,300,500,899,900,901,1700]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def gain(b,m): return (100 if b.is_en_passant(m) else VALUES[b.piece_type_at(m.to_square)])+(VALUES[m.promotion]-100 if m.promotion else 0)
def exchange(b,target):
    best=0; tree=[]
    for m in list(b.legal_moves):
        if m.to_square!=target or not b.is_capture(m): continue
        value=gain(b,m); b.push(m); reply,children=exchange(b,target); b.pop()
        tree.append({'move':m.uci(),'net':value-reply,'children':children}); best=max(best,value-reply)
    return best,tree

def paired(name,fen,uci,limitation=False):
    b=chess.Board(fen); m=chess.Move.from_uci(uci)
    return [dict(id=name+'_white',fen=fen,move=uci,limitation=limitation),
            dict(id=name+'_black',fen=b.mirror().fen(en_passant='fen'),move=chess.Move(chess.square_mirror(m.from_square),chess.square_mirror(m.to_square),m.promotion).uci(),limitation=limitation)]

cases=[]
cases+=paired('ep_opens_two_square_rank_pin','8/8/8/R2pPn1k/8/8/8/K7 w - d6 0 1','e5d6')
cases+=paired('legal_quiet_absolute_pin','4k3/4n3/8/8/8/8/8/3QR1K1 w - - 0 1','d1d5')
cases+=paired('three_recaptures_pin_released','3qk3/8/8/8/3Q4/4n3/8/3bR1K1 w - - 0 1','d4d1')
cases+=[dict(id='all_nonking_rejected_then_legal_king',fen='8/8/R3nk2/6p1/8/8/8/6QK w - - 0 1',move='g1g5',limitation=False),
        dict(id='all_nonking_rejected_king_blocked_by_pinned_defender',fen='7r/8/R3nk2/6p1/8/7N/8/6QK w - - 0 1',move='g1g5',limitation=False),
        dict(id='initial_check_evasion_capture_pinned_recapturer',fen='4k3/8/8/8/4n3/5QrK/8/4R3 w - - 0 1',move='f3g3',limitation=False),
        dict(id='initial_discovered_check_invalidates_unrelated_recapture',fen='8/1k6/8/4n3/8/3p1Q2/6B1/7K w - - 0 1',move='f3d3',limitation=False)]
cases+=paired('inherited_recapture_promotion','7k/8/8/8/8/1Q5K/p7/1r6 w - - 0 1','b3b1',True)
assert len(cases)==12
record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'preparing_fixed_corpus','oracle':'python-chess '+chess.__version__,'engine_budget_seconds':60,'selection_rule':'Twelve authored legal controls fixed before running SEE; no selection on diagnostic outcomes. Two recapture-promotion cases are separately tested inherited limitations, never green exact-SEE assertions.','phases':[]}
attempt=[]
for c in cases:
    b=chess.Board(c['fen']); m=chess.Move.from_uci(c['move'])
    c['valid_position']=b.is_valid(); c['initial_legal']=m in b.legal_moves; c['initial_in_check']=b.is_check(); c['gives_check']=b.gives_check(m) if c['initial_legal'] else None
    attempt.append({'id':c['id'],'fen':c['fen'],'move':c['move'],'valid_position':c['valid_position'],'initial_legal':c['initial_legal'],'board_status':int(b.status())})
(ROOT/'authored-attempt1.json').write_text(json.dumps(attempt,indent=2)+'\n')
invalid=[c for c in cases if not c['valid_position'] or not c['initial_legal']]
if invalid:
    record['status']='invalid_authored_fixture_pre_engine'; record['invalid_fixtures']=invalid
    (ROOT/'record.json').write_text(json.dumps(record,indent=2)+'\n')
    raise AssertionError(invalid)
for c in cases:
    b=chess.Board(c['fen']); m=chess.Move.from_uci(c['move']); value=gain(b,m); b.push(m)
    c['legal_recaptures']=sorted(x.uci() for x in b.legal_moves if x.to_square==m.to_square and b.is_capture(x))
    reply,tree=exchange(b,m.to_square); c['oracle_exchange']=value-reply; c['exchange_tree']=tree
(ROOT/'oracle-corpus.json').write_text(json.dumps(cases,indent=2)+'\n')
tsv=ROOT/'cases.tsv'; tsv.write_text(''.join(c['id']+'\t'+c['fen']+'\t'+c['move']+'\n' for c in cases))
record.update({'status':'corpus_frozen_before_engine','oracle_corpus_sha256':sha(ROOT/'oracle-corpus.json'),'cases_sha256':sha(tsv),'thresholds':THRESHOLDS,'input_exe_sha256':{kind:sha(PROTO/('see-'+kind)) for kind in ['baseline','candidate']}})
(ROOT/'record.json').write_text(json.dumps(record,indent=2)+'\n')
outputs={}
for kind in ['baseline','candidate']:
    args=[str(PROTO/('see-'+kind)),str(tsv)]; start=time.monotonic()
    try:
        p=subprocess.run(args,capture_output=True,timeout=20); rc=p.returncode; stdout=p.stdout; stderr=p.stderr
    except subprocess.TimeoutExpired as e:
        rc=124; stdout=e.stdout or b''; stderr=e.stderr or b''
    for ext,data in [('stdout',stdout),('stderr',stderr)]: (ROOT/(kind+'.'+ext)).write_bytes(data)
    record['phases'].append({'command':args,'return_code':rc,'elapsed_seconds_budget_only':time.monotonic()-start,'timeout_seconds':20})
    (ROOT/'record.json').write_text(json.dumps(record,indent=2)+'\n')
    assert rc==0,(kind,rc)
    outputs[kind]={r['id']:r for r in csv.DictReader(stdout.decode().splitlines(),delimiter='\t')}
    assert len(outputs[kind])==12
failures=[]; inherited=[]; comparisons=[]
for c in cases:
    comparison={'id':c['id'],'oracle':c['oracle_exchange'],'limitation':c['limitation']}
    for kind in ['baseline','candidate']:
        row=outputs[kind][c['id']]; actual=int(row['static_exchange']); expected=c['oracle_exchange']
        recaptures=sorted(row['legal_recaptures'].split(',')) if row['legal_recaptures'] else []
        if row['initial_legal']!='1' or recaptures!=c['legal_recaptures']: failures.append({'id':c['id'],'kind':kind,'type':'legality_or_recapture_set'})
        bad=[t for t in THRESHOLDS if bool(int(row['ge'+str(t)]))!=(expected>=t)]
        comparison[kind]={'static_exchange':actual,'bad_thresholds':bad}
        if c['limitation']:
            inherited.append({'id':c['id'],'kind':kind,'actual':actual,'oracle':expected,'bad_thresholds':bad})
        elif kind=='candidate' and (actual!=expected or bad): failures.append({'id':c['id'],'kind':kind,'type':'exchange_or_threshold','actual':actual,'oracle':expected,'bad_thresholds':bad})
    comparisons.append(comparison)
record.update({'comparisons':comparisons,'candidate_control_failures':failures,'separate_inherited_limitations':inherited,'actual_cases':12,'pin_controls':10,'known_limitation_cases':2,'status':'PASS_targeted_controls_WITH_inherited_SEE_limitation' if not failures else 'FAILED_preserve_all_outcomes','total_engine_seconds_budget_only':sum(x['elapsed_seconds_budget_only'] for x in record['phases']),'input_exe_sha256_after':{kind:sha(PROTO/('see-'+kind)) for kind in ['baseline','candidate']}})
assert record['input_exe_sha256']==record['input_exe_sha256_after']
(ROOT/'record.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
raise SystemExit(bool(failures))
