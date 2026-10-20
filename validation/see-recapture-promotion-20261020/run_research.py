#!/usr/bin/env python3
"""Freeze a bounded legal oracle corpus, link an existing API object, and probe source16."""
from pathlib import Path
import csv, datetime, hashlib, json, os, shutil, subprocess, time
import chess

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent.parent
REV='553caef144ae2e1b696ba35d7a0eb1a50a03fde9'
BUILD=Path('/workspace/.cloud-setup/forge-pin-mask-release')
PRIOR=REPO/'validation/pin-see-filter-cost-20261020'
VALUES={None:0,chess.PAWN:100,chess.KNIGHT:300,chess.BISHOP:300,chess.ROOK:500,chess.QUEEN:900,chess.KING:0}
THRESHOLDS=[-2000,-1000,-900,-800,-600,-500,-300,-1,0,1,99,100,101,299,300,500,899,900,901,1700]
ENV=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
RECORD={'source_commit':REV,'oracle':'python-chess '+chess.__version__,
        'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'engine_budget_seconds':30,'engine_elapsed_seconds_budget_accounting_only':0,
        'phases':[],'status':'PREPARING_ORACLE','board_compiles':0,'driver_compiles':0,
        'performance_claim':None,'strength_claim':None}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def save():write(ROOT/'record.json',RECORD)
def run(label,args,timeout,engine=False):
    if engine and RECORD['engine_elapsed_seconds_budget_accounting_only']+timeout>30:
        raise RuntimeError('Engine budget exhausted')
    start=time.monotonic()
    try:
        p=subprocess.run([str(x) for x in args],cwd=ROOT,env=ENV,capture_output=True,timeout=timeout)
        rc,stdout,stderr=p.returncode,p.stdout,p.stderr
    except subprocess.TimeoutExpired as exc:
        rc,stdout,stderr=124,exc.stdout or b'',exc.stderr or b''
    elapsed=time.monotonic()-start
    for ext,data in [('stdout',stdout),('stderr',stderr)]: (ROOT/(label+'.'+ext)).write_bytes(data)
    RECORD['phases'].append({'label':label,'command':[str(x) for x in args],
                            'timeout_seconds':timeout,'exit_code':rc,'engine_execution':engine,
                            'elapsed_seconds_operational_only':elapsed,
                            'stdout_sha256':sha(ROOT/(label+'.stdout')),
                            'stderr_sha256':sha(ROOT/(label+'.stderr'))})
    if engine:RECORD['engine_elapsed_seconds_budget_accounting_only']+=elapsed
    save()
    if rc:raise RuntimeError(label+' exit '+str(rc))
    return stdout

def gain(board,move):
    captured=100 if board.is_en_passant(move) else VALUES[board.piece_type_at(move.to_square)]
    bonus=VALUES[move.promotion]-100 if move.promotion else 0
    return captured+bonus,captured,bonus

def exchange(board,target):
    options=[]
    for move in sorted(board.legal_moves,key=lambda m:m.uci()):
        if move.to_square!=target or not board.is_capture(move):continue
        immediate,captured,bonus=gain(board,move)
        board.push(move); reply,children=exchange(board,target); board.pop()
        options.append({'move':move.uci(),'captured_value':captured,'promotion_gain':bonus,
                        'immediate_gain':immediate,'best_reply':reply,'net':immediate-reply,
                        'children':children})
    return max([0]+[x['net'] for x in options]),options

try:
    proposed=[
        ('later_own_promotion_saves_capture','1r6/P1Q5/2n4k/8/8/8/8/7K w - - 0 1','c7b8'),
        ('first_enemy_promotion_poisons_capture','7k/8/8/8/8/7K/p2N4/1r6 w - - 0 1','d2b1'),
        ('pinned_promotion_pawn_cannot_recapture','k7/8/8/8/8/7K/p2N4/Rr6 w - - 0 1','d2b1'),
        ('promoted_recapturer_taken_by_king','7k/8/8/8/8/8/p2N4/1rK5 w - - 0 1','d2b1'),
        ('original_inherited_limitation','7k/8/8/8/8/1Q5K/p7/1r6 w - - 0 1','b3b1'),
    ]
    write(ROOT/'authored-proposals-attempt1.json',[{'id':n,'fen':f,'move':m} for n,f,m in proposed])
    cases=[]; invalid=[]
    for name,fen,uci in proposed:
        original=chess.Board(fen); initial=chess.Move.from_uci(uci)
        mirror=original.mirror()
        mirrored_move=chess.Move(chess.square_mirror(initial.from_square),chess.square_mirror(initial.to_square),initial.promotion)
        for color,board,move in [('white',original,initial),('black',mirror,mirrored_move)]:
            case={'id':name+'_'+color,'fen':board.fen(en_passant='fen'),'move':move.uci(),
                  'known_control':name=='original_inherited_limitation',
                  'valid_position':board.is_valid(),'position_status':int(board.status()),
                  'initial_legal':move in board.legal_moves,'initial_in_check':board.is_check()}
            if not case['valid_position'] or not case['initial_legal']:
                invalid.append(case); continue
            value,captured,bonus=gain(board,move)
            board.push(move)
            case['legal_recaptures']=sorted(m.uci() for m in board.legal_moves if m.to_square==move.to_square and board.is_capture(m))
            reply,tree=exchange(board,move.to_square); board.pop()
            case.update({'initial_gain':value,'initial_captured_value':captured,
                         'initial_promotion_gain':bonus,'oracle_exchange':value-reply,
                         'exchange_tree':tree,
                         'oracle_thresholds':{str(t):value-reply>=t for t in THRESHOLDS}})
            cases.append(case)
    write(ROOT/'invalid-fixtures-attempt1.json',invalid)
    if invalid:raise RuntimeError('Invalid authored fixture(s); no API run allowed')
    assert len(cases)==10 and sum(not c['known_control'] for c in cases)==8
    write(ROOT/'oracle-corpus.json',cases)
    write(ROOT/'thresholds.json',THRESHOLDS)
    (ROOT/'cases.tsv').write_text(''.join(c['id']+'\t'+c['fen']+'\t'+c['move']+'\n' for c in cases))
    frozen={'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'cases':len(cases),'new_cases':8,'known_controls':2,
            'oracle':'full legal same-target capture minimax with optional stopping and promotion gains',
            'files_sha256':{n:sha(ROOT/n) for n in ['authored-proposals-attempt1.json','invalid-fixtures-attempt1.json','oracle-corpus.json','thresholds.json','cases.tsv']}}
    write(ROOT/'PRE-RUN-FREEZE.json',frozen)
    RECORD['oracle_frozen_before_link_or_execution']=True
    RECORD['freeze_sha256']=sha(ROOT/'PRE-RUN-FREEZE.json')
    RECORD['status']='ORACLE_FROZEN';save()

    # Link only: reuse the unchanged compiled diagnostic driver object and copied source16 core.
    core=BUILD/'libforge_core.a'
    immutable_paths=[core,PRIOR/'see_diagnostic.o',PRIOR/'see_diagnostic.cpp',PRIOR/'complete-evidence.zip',
                     REPO/'validation/pin-see-coverage-20261020/known-limitation.json']
    immutable={str(p):sha(p) for p in immutable_paths}
    assert immutable[str(core)]=='a7718ec0555715e45b3aa96789754047e03db3104748a0fe8e03404e8695c267'
    board_source=subprocess.check_output(['git','show',REV+':src/board.cpp'],cwd=REPO)
    assert hashlib.sha256(board_source).hexdigest()==sha(REPO/'src/board.cpp')
    (ROOT/'source16-board.cpp').write_bytes(board_source)
    source_headers={}
    for name in ['include/forge/board.hpp','include/forge/bitboard.hpp']:
        source16=subprocess.check_output(['git','show',REV+':'+name],cwd=REPO)
        source15=subprocess.check_output(['git','show','8d303e4:'+name],cwd=REPO)
        assert source16==source15
        source_headers[name]=hashlib.sha256(source16).hexdigest()
    RECORD['source16_board_sha256']=sha(ROOT/'source16-board.cpp')
    RECORD['driver_headers_unchanged_from_compiled_source15']=source_headers
    RECORD['original_inputs_sha256_before']=immutable
    shutil.copy2(core,ROOT/'source16-libforge_core.a')
    shutil.copy2(PRIOR/'see_diagnostic.o',ROOT/'see_diagnostic.o')
    shutil.copy2(PRIOR/'see_diagnostic.cpp',ROOT/'see_diagnostic.cpp')
    flags_file=BUILD/'CMakeFiles/forge_core.dir/flags.make'
    shutil.copy2(flags_file,ROOT/'original-flags.make')
    flags=next(line.split(' = ',1)[1].split() for line in flags_file.read_text().splitlines() if line.startswith('CXX_FLAGS = '))
    RECORD['driver_object_sha256']=sha(ROOT/'see_diagnostic.o')
    RECORD['core_sha256']=sha(ROOT/'source16-libforge_core.a')
    save()
    run('link-source16-api',['/usr/bin/c++',*flags,ROOT/'see_diagnostic.o',ROOT/'source16-libforge_core.a','-pthread','-o',ROOT/'see-source16'],60)
    # Verify the preregistered corpus/threshold/tree bytes immediately before the only API run.
    assert all(sha(ROOT/n)==h for n,h in frozen['files_sha256'].items())
    run('source16-api',[ROOT/'see-source16',ROOT/'cases.tsv'],10,engine=True)
    rows={r['id']:r for r in csv.DictReader((ROOT/'source16-api.stdout').read_text().splitlines(),delimiter='\t')}
    assert len(rows)==len(cases)
    comparisons=[];api_failures=[]
    for case in cases:
        row=rows[case['id']]; actual=int(row['static_exchange']);expected=case['oracle_exchange']
        recaptures=sorted(row['legal_recaptures'].split(',')) if row['legal_recaptures'] else []
        if row['initial_legal']!='1':api_failures.append([case['id'],'initial legality'])
        if recaptures!=case['legal_recaptures']:api_failures.append([case['id'],'first recaptures'])
        bad=[t for t in THRESHOLDS if bool(int(row['ge'+str(t)]))!=(expected>=t)]
        actual_ge0=bool(int(row['ge0']))
        comparisons.append({'id':case['id'],'oracle_exchange':expected,'actual_exchange':actual,
                            'actual_ge0':actual_ge0,'oracle_ge0':expected>=0,
                            'false_negative_at_zero':not actual_ge0 and expected>=0,
                            'false_positive_at_zero':actual_ge0 and expected<0,
                            'bad_thresholds':bad,'known_control':case['known_control']})
    write(ROOT/'comparisons.json',comparisons)
    RECORD.update({'cases':len(cases),'new_cases':8,'known_controls':2,
                   'api_legality_or_recapture_failures':api_failures,
                   'exchange_mismatches':sum(c['actual_exchange']!=c['oracle_exchange'] for c in comparisons),
                   'false_negative_cases_at_zero':[c['id'] for c in comparisons if c['false_negative_at_zero']],
                   'false_positive_cases_at_zero':[c['id'] for c in comparisons if c['false_positive_at_zero']],
                   'bad_threshold_answers':sum(len(c['bad_thresholds']) for c in comparisons),
                   'threshold_answers':len(cases)*len(THRESHOLDS),
                   'executable_sha256':sha(ROOT/'see-source16'),
                   'original_inputs_sha256_after':{p:sha(p) for p in immutable},
                   'production_board_sha256_after':sha(REPO/'src/board.cpp')})
    assert not api_failures
    assert RECORD['original_inputs_sha256_after']==immutable
    assert RECORD['production_board_sha256_after']==RECORD['source16_board_sha256']
    assert all(sha(ROOT/n)==h for n,h in frozen['files_sha256'].items())
    RECORD['all_frozen_inputs_unchanged']=True
    RECORD['status']='COMPLETE_BOUNDED_PROMOTION_RECAPTURE_RESEARCH'
    RECORD['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
    print(json.dumps({'status':RECORD['status'],'comparisons':comparisons,
                      'engine_seconds_budget_accounting_only':RECORD['engine_elapsed_seconds_budget_accounting_only']}))
except BaseException as exc:
    RECORD['status']='FAILED_PRESERVE_ATTEMPT';RECORD['error']=repr(exc);save();raise
