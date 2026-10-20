#!/usr/bin/env python3
"""Independent python-chess legal-capture oracle and actual frozen-core API tests.

Corpus is preregistered before running the diagnostic. All seeded captures are
retained, including generic SEE approximation disagreements and crashes.
"""
from pathlib import Path
import csv, datetime, hashlib, json, os, random, subprocess, time
import chess

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
WORK = Path('/workspace/pinned-see-prototype-20261020')
VALUES = {None:0,chess.PAWN:100,chess.KNIGHT:300,chess.BISHOP:300,chess.ROOK:500,chess.QUEEN:900,chess.KING:0}
THRESHOLDS = [-2000,-1000,-900,-800,-600,-500,-300,-1,0,1,99,100,101,299,300,500,899,900,901,1700]
RECORD = {'oracle':'python-chess '+chess.__version__, 'seed':20261020, 'corpus_rule':'original 12 + mirrored authored controls + first 256 legal captures from seeded valid sparse positions; no filtering by SEE result', 'phases':[], 'engine_execution_budget_seconds':120}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(): (ROOT/'matrix-record.json').write_text(json.dumps(RECORD,indent=2)+'\n')
def phase(label,args,timeout):
    start=time.monotonic()
    try:
        p=subprocess.run(args,cwd=WORK,capture_output=True,timeout=timeout)
        rc=p.returncode; out=p.stdout; err=p.stderr
    except subprocess.TimeoutExpired as e:
        rc=124; out=e.stdout or b''; err=e.stderr or b''
    for ext,data in [('stdout',out),('stderr',err)]: (ROOT/(label+'.'+ext)).write_bytes(data)
    RECORD['phases'].append({'label':label,'command':[str(x) for x in args],'return_code':rc,'elapsed_seconds':time.monotonic()-start,'timeout_seconds':timeout})
    save()
    if rc: raise RuntimeError(label+' failed rc='+str(rc))

def material_gain(board,move):
    return (100 if board.is_en_passant(move) else VALUES[board.piece_type_at(move.to_square)]) + (VALUES[move.promotion]-100 if move.promotion else 0)
def exchange(board,target):
    options=[]
    for move in list(board.legal_moves):
        if move.to_square!=target or not board.is_capture(move): continue
        gain=material_gain(board,move)
        board.push(move)
        reply,children=exchange(board,target)
        board.pop()
        options.append({'move':move.uci(),'net':gain-reply,'children':children})
    return max([0]+[x['net'] for x in options]),options

cases=[]
for line in (REPO/'validation/next-search-20261020/pinned-see-red/cases.tsv').read_text().splitlines():
    name,fen,move=line.split('\t'); cases.append({'id':name,'fen':fen,'move':move,'group':'original12','strict':not name.startswith('illegal_initial')})
authored=[
 ('ghost_target_pinner_removed','k7/8/8/8/8/2Np4/4r3/3QK3 w - - 0 1','d1e2'),
 ('newly_exposed_orthogonal_pin','k3r3/8/8/8/3p4/4b3/4N3/3QK3 w - - 0 1','d1d4'),
 ('absolute_diagonal_pin','7k/6n1/8/5p2/8/8/8/B4Q1K w - - 0 1','f1f5'),
 ('legal_along_diagonal_pin','7k/8/5b2/8/3p4/8/8/B2Q3K w - - 0 1','d1d4'),
 ('pinner_departed_origin','4k3/8/8/8/8/4n3/8/3bR1K1 w - - 0 1','e1d1'),
 ('first_pinned_second_legal_knight','4k3/8/5n2/3p4/8/4n3/8/3QR1K1 w - - 0 1','d1d5'),
 ('ep_unrecaptured','7k/8/8/3pP3/8/8/8/7K w - d6 0 1','e5d6'),
 ('ep_rook_recapture','3r3k/8/8/3pP3/8/8/8/7K w - d6 0 1','e5d6'),
]
for promotion in 'qrbn':
    authored += [('initial_capture_promotion_'+promotion,'r6k/1P6/8/8/8/8/8/7K w - - 0 1','b7a8'+promotion),('initial_quiet_promotion_'+promotion,'1r5k/P7/8/8/8/8/8/7K w - - 0 1','a7a8'+promotion)]
for name,fen,uci in authored:
    board=chess.Board(fen); move=chess.Move.from_uci(uci)
    assert board.is_valid() and move in board.legal_moves, (name,fen,uci)
    cases.append({'id':name+'_white','fen':fen,'move':uci,'group':'authored','strict':True})
    mirror=board.mirror(); mirrored=chess.Move(chess.square_mirror(move.from_square),chess.square_mirror(move.to_square),move.promotion)
    assert mirror.is_valid() and mirrored in mirror.legal_moves
    cases.append({'id':name+'_black','fen':mirror.fen(en_passant='fen'),'move':mirrored.uci(),'group':'authored','strict':True})

rng=random.Random(20261020); generated=0; attempts=0
while generated<256:
    attempts+=1
    assert attempts<100000
    board=chess.Board(None)
    squares=rng.sample(range(64),rng.randint(4,8))
    board.set_piece_at(squares[0],chess.Piece(chess.KING,chess.WHITE)); board.set_piece_at(squares[1],chess.Piece(chess.KING,chess.BLACK))
    for square in squares[2:]:
        types=[chess.KNIGHT,chess.BISHOP,chess.ROOK,chess.QUEEN]+([chess.PAWN] if 0<chess.square_rank(square)<7 else [])
        board.set_piece_at(square,chess.Piece(rng.choice(types),rng.choice([True,False])))
    board.turn=rng.choice([True,False])
    if not board.is_valid(): continue
    captures=sorted((m for m in board.legal_moves if board.is_capture(m)),key=lambda m:m.uci())
    for move in captures:
        cases.append({'id':'sparse_'+str(generated).zfill(3),'fen':board.fen(),'move':move.uci(),'group':'seeded_sparse','strict':False})
        generated+=1
        if generated>=256: break

for case in cases:
    board=chess.Board(case['fen']); move=chess.Move.from_uci(case['move']); legal=move in board.legal_moves
    case['valid_position']=board.is_valid(); case['initial_legal']=legal
    if legal:
        gain=material_gain(board,move); board.push(move)
        case['legal_recaptures']=sorted(m.uci() for m in board.legal_moves if m.to_square==move.to_square and board.is_capture(m))
        response,tree=exchange(board,move.to_square)
        case['oracle_exchange']=gain-response; case['exchange_tree']=tree
    else: case['legal_recaptures']=[]
(ROOT/'oracle-corpus.json').write_text(json.dumps(cases,indent=2)+'\n')
tsv=ROOT/'cases.tsv'; tsv.write_text(''.join(c['id']+'\t'+c['fen']+'\t'+c['move']+'\n' for c in cases))
RECORD.update({'cases':len(cases),'generation_attempts':attempts,'oracle_corpus_sha256':sha(ROOT/'oracle-corpus.json'),'cases_sha256':sha(tsv),'thresholds':THRESHOLDS,'pre_run_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
save()
flags=next(line.split(' = ',1)[1].split() for line in (ROOT/'original-flags.make').read_text().splitlines() if line.startswith('CXX_FLAGS = '))
for kind in ['baseline','candidate']:
    exe=ROOT/('see-'+kind)
    phase('compile-driver-'+kind,['/usr/bin/c++',*flags,'-I'+str(WORK/'source/include'),str(ROOT/'see_diagnostic.cpp'),str(ROOT/(kind+'-libforge_core.a')),'-pthread','-o',str(exe)],45)
    RECORD[kind+'_exe_sha256']=sha(exe); save()
    phase('run-'+kind,[str(exe),str(tsv)],20)

outputs={}
for kind in ['baseline','candidate']:
    with (ROOT/('run-'+kind+'.stdout')).open() as f: outputs[kind]={r['id']:r for r in csv.DictReader(f,delimiter='\t')}
    assert len(outputs[kind])==len(cases)
failures=[]; mismatches={kind:[] for kind in outputs}; improvements=[]; regressions=[]
for case in cases:
    name=case['id']
    for kind,rows in outputs.items():
        row=rows[name]
        if bool(int(row['initial_legal']))!=case['initial_legal']: failures.append([name,kind,'initial legality'])
        if not case['initial_legal']: continue
        actual_recaptures=sorted(row['legal_recaptures'].split(',')) if row['legal_recaptures'] else []
        if actual_recaptures!=case['legal_recaptures']: failures.append([name,kind,'legal recapture set'])
        expected=case['oracle_exchange']
        bad=[threshold for threshold in THRESHOLDS if bool(int(row['ge'+str(threshold)]))!=(expected>=threshold)]
        if int(row['static_exchange'])!=max(-2000,min(2000,expected)) or bad:
            mismatches[kind].append({'id':name,'group':case['group'],'strict':case['strict'],'oracle':expected,'actual':int(row['static_exchange']),'bad_thresholds':bad})
    if case['initial_legal']:
        before=int(outputs['baseline'][name]['static_exchange']); after=int(outputs['candidate'][name]['static_exchange']); expected=case['oracle_exchange']
        if before!=after:
            change={'id':name,'baseline':before,'candidate':after,'oracle':expected}
            if after==expected: improvements.append(change)
            elif before==expected or abs(after-expected)>abs(before-expected): regressions.append(change)
strict_failures=[x for x in mismatches['candidate'] if x['strict']]
RECORD.update({'api_oracle_failures':failures,'oracle_mismatches':mismatches,'strict_candidate_failures':strict_failures,'improvements':improvements,'new_or_worse_mismatches':regressions,'status':'PASS_bounded_prototype_correctness' if not failures and not strict_failures and not regressions else 'FAILED_or_BLOCKED_preserve_candidate','scope':'actual public Board API; serial one-board compile only; no full engine gates, NPS, strength or integration acceptance'})
save()
print(json.dumps({k:RECORD[k] for k in ['status','cases','strict_candidate_failures','new_or_worse_mismatches','improvements']}))
raise SystemExit(1 if failures or strict_failures or regressions else 0)
