"""Audit a whole-game UCI record comparison against the book and driver receipts."""
import argparse
import csv
from datetime import datetime
import hashlib
from itertools import islice, zip_longest
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
try:
    import chess
except ImportError:
    sys.path.insert(0, str(WORK / 'j10fens/vendor'))
    import chess

ARMS = {
    'K17': ('K17-1', 'K17-2', 3401, 3410),
    'C17': ('K17-1', 'C17', 3401, 3410),
    'G1': ('G1-r15d', 'G1-kF', 3401, 3600),
    'G2': ('G2-r15d', 'G2-kF', 3601, 3640),
}
RECORD = re.compile(rb'([1-9][0-9]*) ([1-9][0-9]*) ([a-h][1-8][a-h][1-8][nbrq]?) (NA|0|[1-9][0-9]*)\n')
REPLAY = {}
def rows(path):
    with path.open(newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))
def table(path, names, data):
    with path.open('w', newline='') as f:
        writer = csv.writer(f, delimiter='\t', lineterminator='\n')
        writer.writerow(names)
        writer.writerows(data)
def load_book(path, start, end):
    with path.open() as f:
        return dict(enumerate((line.strip() for line in islice(f,start-1,end)),start))
def replay(fen, moves):
    key = (fen, tuple(moves))
    if key not in REPLAY:
        board = chess.Board(fen)
        for ply, move in enumerate(moves,1):
            assert not board.is_game_over(claim_draw=True), (fen, ply, 'record after terminal position')
            board.push(board.parse_uci(move))
        outcome = board.outcome(claim_draw=True)
        assert outcome or len(moves) == 300, (fen, len(moves), 'reported start/end are not a full game')
        assert len(moves) <= 300
        REPLAY[key] = (outcome.result(),outcome.termination.name) if outcome else ('*','PLY_LIMIT')
    return REPLAY[key]
def parse_records(raw,first,last):
    games={}
    previous=None
    for number,line in enumerate(raw.splitlines(keepends=True),1):
        match=RECORD.fullmatch(line)
        assert match,(number,line)
        gid,ply,move,nodes=match.groups()
        gid,ply=int(gid),int(ply)
        assert first<=gid<=last and (previous is None or previous<(gid,ply)),(number,gid,ply,previous)
        previous=(gid,ply)
        items=games.setdefault(gid,[])
        assert ply==len(items)+1,(number,gid,ply)
        items.append((move.decode('ascii'),None if nodes==b'NA' else int(nodes),line))
    return games

def measure_game(book,gid,items):
    raw=b''.join(x[2] for x in items)
    p1_white=book[gid].split()[1]=='w'
    na_by_color=[0,0]
    records_by_color=[0,0]
    sum_by_color=[0,0]
    for move,nodes,line in items:
        side=0 if p1_white else 1
        records_by_color[side]+=1
        if nodes is None:na_by_color[side]+=1
        else:sum_by_color[side]+=nodes
        p1_white=not p1_white
    result,termination=replay(book[gid],[x[0] for x in items])
    return dict(records=len(items),na=sum(na_by_color),nodes=sum(sum_by_color),raw=raw,
        result=result,termination=termination,records_by_color=records_by_color,
        na_by_color=na_by_color,sum_by_color=sum_by_color)

def read_arm(path, first, last, book):
    combined_log=(path/'run.log').read_text()
    terminal=next(s.split()[1] for s in reversed(combined_log.splitlines()) if s.startswith('status '))
    assert terminal in ('COMPLETE','INCOMPLETE'),(path,terminal)
    raw=(path/'records.txt').read_bytes()
    canonical=parse_records(raw,first,last)
    recorded=rows(path/'games.tsv')
    ids=[int(r['book_line']) for r in recorded]
    assert ids==sorted(set(ids)),(path,ids)
    assert set(canonical)<=set(ids),(path,'canonical record IDs absent from completion receipts')
    if terminal=='COMPLETE':assert ids==list(range(first,last+1)),path
    receipt={int(r['book_line']):r for r in recorded}
    pids=set()
    digest=hashlib.sha256(raw).hexdigest()
    notes=[];sums=[];totals={};nslots=2
    build='kF' if path.name.endswith('-kF') else 'r15d'
    limit=250000 if first==3601 else 50000
    lmr=60 if path.name=='C17' else 93
    assert f'arm {path.name} build {build} book_lines {first} {last} go nodes {limit} LmrQuietBase {lmr}' in combined_log.splitlines()
    assert 'nproc 5 S 2' in combined_log.splitlines()
    allna=[]
    for k in range(1,nslots+1):
        slot=path/f'slot{k}'
        log=(slot/'run.log').read_text()
        sstatus=next(s.split()[1] for s in reversed(log.splitlines()) if s.startswith('status '))
        if terminal=='COMPLETE':assert sstatus=='COMPLETE'
        assert not re.search(r'unknown option|invalid value',log,re.I),slot
        core=re.findall(r'^arm '+path.name+r' build '+build+rf' slot {k} nproc 5 S 2 logical_cpu (\d+) book_range {first} {last} slot_first {first+k-1} stride 2$',log,re.M)
        assert len(core)==1,slot
        assert f'python_chess {chess.__version__} hard_node_limit {limit} claim_draw True max_plies 300' in log.splitlines()
        for setting in ('Threads value 1','Hash value 16','LmrQuietBase value '+str(lmr)):
            assert 'both setoption name '+setting in log.splitlines(),(slot,setting)
        logged_pair=[]
        for role in ('P1_White','P2_Black'):
            child=re.findall(r'^'+role+r' pid (\d+) child_cpu_affinity \['+core[0]+r'\]$',log,re.M)
            assert len(child)==1,(slot,role,child)
            logged_pair.append(child[0])
            for mode in ('loaded','active'):
                markers=[s for s in log.splitlines() if s.startswith(role+' info string NNUE v3 '+mode) and 'checksum 30ab43b4ba5db5f3' in s]
                assert len(markers)==1,(slot,role,mode,markers)
        localraw=(slot/'records.txt').read_bytes()
        localgames=parse_records(localraw,first,last)
        completed=rows(slot/'games.tsv')
        sids=[int(r['book_line']) for r in completed]
        assert sids==list(range(first+k-1,first+k-1+len(sids)*nslots,nslots)),(slot,sids)
        assert set(localgames)<=set(sids),(path,'slot record IDs absent from completion receipts')
        pair=set((r['p1_pid'],r['p2_pid']) for r in completed)
        assert len(pair)<=1,(slot,'persistent PID pair changed',pair)
        if pair:
            pp=next(iter(pair))
            assert pp==tuple(logged_pair),(slot,pp,logged_pair)
            assert pp[0]!=pp[1] and not set(pp)&pids,(slot,pp,pids)
            pids.update(pp)
        searched=[0,0];missing=[0,0];offset=0;na_events=[]
        for r in completed:
            gid=int(r['book_line'])
            assert int(r['slot'])==k and gid in receipt
            assert {c:v for c,v in r.items() if c!='record_bytes'}=={c:v for c,v in receipt[gid].items() if c!='record_bytes'},(path,gid,'canonical/slot receipt')
            items=localgames.setdefault(gid,[])
            assert canonical.setdefault(gid,[])==items,(path,gid,'slot/canonical bytes or order')
            g=measure_game(book,gid,items)
            totals[gid]=g
            assert g['result']==r['result'] and g['termination']==r['termination'],(path,gid,r)
            assert (g['records'],g['na'],g['nodes'])==tuple(int(r[c]) for c in ('plies','na','nodes')),(path,gid,'counts')
            assert g['records_by_color']==[int(r[c]) for c in ('p1_search','p2_search')],(path,gid,'side search counts')
            assert g['na_by_color']==[int(r[c]) for c in ('p1_na','p2_na')],(path,gid,'side NA counts')
            for side in (0,1):
                searched[side]+=g['records_by_color'][side]
                missing[side]+=g['na_by_color'][side]
            white=book[gid].split()[1]=='w'
            for ply,(move,nodes,_) in enumerate(items,1):
                if nodes is None:na_events.append((gid,ply,white,r['p1_pid' if white else 'p2_pid'],move))
                white=not white
            assert localraw[offset:offset+len(g['raw'])]==g['raw'],(path,gid,'slot row bytes')
            offset+=len(g['raw'])
            assert offset==int(r['record_bytes']), (slot,gid,'receipt byte offset')
            assert datetime.fromisoformat(r['end_utc'])<datetime.fromisoformat('2026-11-19T01:08:17Z'),(slot,gid,'after cutoff')
            sums.append((path.name,k,gid,g['records'],g['na'],g['nodes'],len(g['raw']),hashlib.sha256(g['raw']).hexdigest(),g['result'],g['termination']))
        assert offset==len(localraw),(path,'slot partial records counted')
        started=re.findall(r'^game_start (\d+) (\S+) readyok_both (\d+) (\d+)$',log,re.M)
        starts=[int(x[0]) for x in started]
        assert starts[:len(sids)]==sids and len(starts)-len(sids) in (0,1),(slot,starts,sids)
        assert starts==list(range(first+k-1,first+k-1+len(starts)*nslots,nslots)),(slot,starts)
        assert all(list(s[2:])==logged_pair for s in started),(slot,started)
        if sstatus=='COMPLETE':assert len(starts)==len(sids)
        for key,value in dict(games=len(completed),records=sum(searched),na_records=sum(missing),sum_nodes=sum(totals[g]['nodes'] for g in sids),records_sha256=hashlib.sha256(localraw).hexdigest(),p1_search=searched[0],p2_search=searched[1],p1_na=missing[0],p2_na=missing[1]).items():
            assert re.findall(r'^'+key+r' (\S+)$',log,re.M)==[str(value)],(slot,key,value)
        actual=[]
        for r in rows(slot/'no-info.tsv'):
            side=r['side'].upper()
            assert side in ('W','WHITE','P1','B','BLACK','P2'),(slot,side)
            actual.append((int(r['book_line']),int(r['ply']),side in ('W','WHITE','P1'),r['engine_pid'],r['bestmove']))
        assert sorted(actual)==sorted(na_events),(slot,'no-info side, PID, move, book line or ply')
        allna.extend(na_events)
        ident=' and '.join(pp) if pair else 'no completed-game receipt'
        notes.append(f'{path.name} slot {k}: {len(completed)} fixed-stride games, P1 White/P2 Black PIDs {ident}, {searched[0]}/{searched[1]} searches, {missing[0]}/{missing[1]} NA. Both process logs confirm net768 load and activation checksum 30ab43b4ba5db5f3.')
    assert set(totals)==set(ids)
    offset=0
    for gid in ids:
        g=totals[gid]
        assert raw[offset:offset+len(g['raw'])]==g['raw'],(path,gid,'canonical row bytes')
        offset+=len(g['raw'])
        assert offset==int(receipt[gid]['record_bytes'])
    assert offset==len(raw),(path,'partial rows in canonical output')
    nr=sum(g['records'] for g in totals.values())
    nn=sum(g['nodes'] for g in totals.values())
    na=len(allna)
    canonical_na=rows(path/'no-info.tsv')
    assert [(int(r['book_line']),int(r['ply']),r['side']=='White',r['engine_pid'],r['bestmove']) for r in canonical_na]==sorted(allna),(path,'canonical no-info table')
    footer=combined_log.split('END slot2 log')[-1]
    for key,val in dict(games=len(ids),records=nr,na_records=na,sum_nodes=nn,records_sha256=digest).items():
        assert re.findall(r'^'+key+r' (\S+)$',footer,re.M)==[str(val)],(path,key,val)
    return dict(name=path.name,status=terminal,games=canonical,sums=sorted(sums,key=lambda x:x[2]),raw=raw,
        records=nr,nodes=nn,na=na,digest=digest,notes=notes)

def compare(a,b,book,out,stage,first,last):
    left,right = a['games'],b['games']
    common=sorted(left.keys() & right.keys())
    left_only=sorted(left.keys() - right.keys()); right_only=sorted(right.keys() - left.keys())
    diff=[];first_diff=None
    left_offsets={gid:1+sum(len(left[i]) for i in left if i<gid) for gid in common}
    for gid in common:
        left_rows,right_rows = left[gid],right[gid]
        first_ply=None; unequal_moves=unequal_nodes=extra=0
        for ply,(u,v) in enumerate(zip_longest(left_rows,right_rows),1):
            if u==v:
                continue
            if first_ply is None:
                first_ply=ply
            if u is None or v is None:extra+=1
            else:
                unequal_moves+=int(u[0]!=v[0]); unequal_nodes+=int(u[1]!=v[1])
            if first_diff is None:
                first_diff=(gid,ply,left_offsets[gid]+ply-1,u,v,left_rows[:ply-1],right_rows[:ply-1])
        if first_ply is not None:diff.append((gid,first_ply,len(left_rows),len(right_rows),unequal_moves,unequal_nodes,extra))
    whole=a['status']==b['status']=='COMPLETE'
    equal=a['raw']==b['raw']
    cmpcode=subprocess.run(['cmp','-s',str(args.results/a['name']/'records.txt'),str(args.results/b['name']/'records.txt')]).returncode
    assert cmpcode==int(not equal),(cmpcode,equal)
    if whole:assert equal==(not diff)
    table(out/'differences.tsv',('book_line','first_differing_ply','left_plies','right_plies','unequal_moves_on_shared_plies','unequal_nodes_on_shared_plies','unmatched_plies'),diff)
    detail=['No differing record in games completed by both arms.']
    if first_diff:
        gid,ply,line,u,v,before_a,before_b=first_diff
        board=chess.Board(book[gid])
        for m in before_a:board.push_uci(m[0])
        detail=[f'Book line {gid}, ply {ply}, record line {line} in left file.', 'Opening FEN '+book[gid], 'FEN before differing ply '+board.fen(en_passant='fen')]
        for arm,rec,before in [(a,u,before_a),(b,v,before_b)]:
            detail.append(arm['name']+' record '+(rec[2].decode('ascii').rstrip('\n') if rec else '(missing)'))
            detail.append(arm['name']+' preceding UCI moves '+(' '.join(r[0] for r in before) or '(none)'))
    (out/'first-difference.txt').write_text('\n'.join(detail)+'\n')
    gameword='IDENTICAL' if equal else 'DIFFERS'
    if not whole:
        gameword='INCOMPLETE; '+('DIFFERS on common completed games' if diff else 'no differences in common completed games')
    report=[f'{stage} {gameword}', f'Book lines {first}–{last}. Requested games per arm {last-first+1}.',
        'Four ASCII fields per line, canonical decimal book line and ply, legal UCI move, integer nodes or NA, LF terminator and no header. Numeric sort by book and ply verified.',
        'Replayed each distinct opening and complete UCI move sequence with python-chess '+chess.__version__+'. No move follows a claimable game end. Last position is terminal under claim_draw=True or reaches 300 plies.',
        'The strided slot assignments, complete sorted receipts, terminal result, node sum and number of NA rows agree with independent replay and record parsing.',
        f'cmp -s exit {cmpcode}. Record files byte-equal {equal}. Common completed games {len(common)}, differing games {len(diff)}.',
        f'Games with a differing move on shared plies {sum(d[4]>0 for d in diff)}; games with a differing node count on shared plies {sum(d[5]>0 for d in diff)}; games with unequal ply counts {sum(d[6]>0 for d in diff)}.',
        f'Games completed only in {a["name"]}: {left_only}. Games completed only in {b["name"]}: {right_only}.']
    for arm in (a,b):
        report.append(f'{arm["name"]} {arm["status"]}, {len(arm["games"])} games, {arm["records"]} records, {arm["na"]} NA, {arm["nodes"]} numeric nodes, {len(arm["raw"])} bytes, SHA-256 {arm["digest"]}.')
        report.extend(arm["notes"])
    report.extend(detail)
    (out/'summary.txt').write_text('\n'.join(report)+'\n')
    table(out/'arms.tsv',('arm','status','games','records','na_records','nodes','bytes','sha256'),[(r['name'],r['status'],len(r['games']),r['records'],r['na'],r['nodes'],len(r['raw']),r['digest']) for r in (a,b)])
    table(out/'games.tsv',('arm','slot','book_line','plies','na_records','nodes','bytes','sha256','result','termination'),a['sums']+b['sums'])
    print('\n'.join(report),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=ARMS)
    p.add_argument('--book',type=Path,default=WORK/'j8gate/UHO_Lichess_4852_v1.epd')
    p.add_argument('--results',type=Path,default=WORK/'j17match/results')
    p.add_argument('--output',type=Path,default=HERE)
    args=p.parse_args()
    a,b,lo,hi=ARMS[args.stage]
    book=load_book(args.book,lo,hi)
    out=args.output/args.stage
    out.mkdir(parents=True,exist_ok=True)
    compare(read_arm(args.results/a,lo,hi,book),read_arm(args.results/b,lo,hi,book),book,out,args.stage,lo,hi)
