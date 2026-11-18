#!/usr/bin/env python3
"""Independently reconstruct completed G1 searches from the UCI and monotonic-clock logs."""

import argparse
import csv
from datetime import datetime, timedelta
import hashlib
from itertools import islice
import json
from pathlib import Path
import re

import chess


ARCHIVE = Path('/workspace/work/forge-sol3/forge-combo29/sol3')
FIXTURE = '3c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521'
EXE = 'bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6'
NET_SHA = 'c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7'
FORECAST = datetime.fromisoformat('2026-11-18T16:50:37+00:00')
COMPLETE = re.compile(r'^(\S+) G1 game (\d+) complete with (\d+) legal plies and recorded rows$')
REFUSAL = re.compile(r'unknown option|invalid value|invalid FEN|\bERROR\b', re.I)
FINAL = re.compile(r'info string softnodes nodes (\d+)')
MOVE = r'[a-h][1-8][a-h][1-8][qrbn]?'
BEST = re.compile(rf'bestmove ({MOVE})(?: ponder {MOVE})?')


def hash_file(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def tsv(path):
    with path.open(encoding='ascii', newline='') as stream:
        return list(csv.DictReader(stream, delimiter='\t'))


def utc_value(text):
    return datetime.fromisoformat(text.replace('Z', '+00:00'))


def extract_iteration(line):
    data = line.split()
    return int(data[2]), int(data[data.index('nodes')+1]), int(data[data.index('time')+1]), data[data.index('pv')+1:]


def raw_frames(path, num_plies):
    lines = (path/'engine.stdout.txt').read_text(encoding='ascii').splitlines()
    stderr = (path/'engine.stderr.txt').read_text(encoding='ascii').splitlines()
    assert not any(REFUSAL.search(line) for line in (*lines,*stderr))
    acknowledgments = [n for n,line in enumerate(lines) if line=='readyok']
    assert len(acknowledgments)==num_plies+1 and lines.count('uciok')==1
    active = [(i,line) for i,line in enumerate(lines) if line.startswith('info string NNUE v3 active:')]
    assert len(active)==1 and lines.index('uciok')<active[0][0]<acknowledgments[0]
    assert all(x in active[0][1] for x in (' hidden 768 ', ' checksum 30ab43b4ba5db5f3 ', ' kernel avx512'))
    assert not any(line.startswith(('info depth ','bestmove ','info string softnodes nodes ')) for line in lines[:acknowledgments[0]+1])
    if not num_plies:
        assert acknowledgments[0]+1==len(lines)
        return
    assert acknowledgments[1]==acknowledgments[0]+1
    for start,end in zip(acknowledgments[1:], [*acknowledgments[2:],len(lines)], strict=True):
        frame=lines[start+1:end]
        assert len(frame)>=3
        best=BEST.fullmatch(frame[-1]); final=FINAL.fullmatch(frame[-2])
        assert best is not None and final is not None
        assert not any(line.startswith(('bestmove ','info string softnodes nodes ')) for line in frame[:-2])
        snapshots=[extract_iteration(line) for line in frame[:-2] if line.startswith('info depth ')]
        assert snapshots and [x[0] for x in snapshots]==list(range(1,len(snapshots)+1))
        assert all(a[1]<=b[1] and a[2]<=b[2] for a,b in zip(snapshots,snapshots[1:]))
        yield snapshots,int(final[1]),best[1],frame


def read_game(archive, game, fens, header, fixture_commit_time, ply_count):
    run=archive/'g1/games'/f'{game:03d}'
    summary=json.loads((run/'summary.json').read_text(encoding='ascii'))
    start=utc_value(summary['started_utc']); end=utc_value(summary['finished_utc'])
    assert FORECAST < start <= end < fixture_commit_time + timedelta(seconds=1)
    assert summary['error'] is None and summary['game']==game and summary['plies']==ply_count
    assert summary['workload']=='G1' and summary['build']=='r15d' and summary['exe_sha256']==EXE
    assert summary['net_sha256']==NET_SHA and summary['fixture_sha256']==FIXTURE and summary['python_chess']==chess.__version__
    assert (summary['soft_nodes'],summary['hard_nodes'],summary['ply_cap'],summary['claim_draw'])==(2000,8000,200,True)
    for name,sha in summary['files_sha256'].items():
        assert hash_file(run/name)==sha,(game,name)
    root_fen=fens[game-1]
    assert summary['start_fen']==root_fen
    board=chess.Board(root_fen)
    assert board.is_valid()
    labels=tsv(run/'rows.tsv'); timing=tsv(run/'timings.tsv')
    assert len(labels)==len(timing)==ply_count
    expect_input=[*header,'ucinewgame']
    moves=[]; rows=[]; timings=[]; notices=[]
    for ply,(raw,clock,label) in enumerate(zip(raw_frames(run,ply_count),timing,labels,strict=True),1):
        assert not board.is_game_over(claim_draw=True) and ply<=200
        assert (int(clock['game']),int(clock['ply']))==(game,ply)
        begin=int(clock['monotonic_go_write_ns']); finish=int(clock['monotonic_bestmove_parsed_ns'])
        assert finish>begin>0 and (not timings or begin>timings[-1][1])
        timings.append((begin,finish))
        wall=finish-begin
        iters,final,move,frame=raw
        dep,nodes,info_ms,pv=iters[-1]
        assert 0<nodes<=final
        cap=final>nodes
        prev=iters[-2][:2] if len(iters)>1 else ('','')
        prev2=iters[-3][:2] if len(iters)>2 else ('','')
        expect_input.extend((' '.join(('position fen',root_fen,'moves',*moves)), 'isready', 'go softnodes 2000'))
        row={'game':game,'ply':ply,'pieces':len(board.piece_map()),'last_depth':dep,'last_nodes':nodes,
             'last_time_ms':info_ms,'final_nodes':final,'wall_ns':wall,'cap':int(cap),'prev_depth':prev[0],
             'prev_nodes':prev[1],'prev2_depth':prev2[0],'prev2_nodes':prev2[1],'bestmove':move,
             'root_fen':board.fen()}
        assert {k:str(v) for k,v in row.items()}==label,(game,ply)
        message=[]
        if cap and (final<8000 or nodes>=2000):
            message.append('final above last info with unexpected relation to node limits')
        if final>8000 or (not cap and final==8000):
            message.append('final nodes at or above hard cap with an unexpected exact marker relationship')
        if wall<info_ms*1_000_000:
            message.append('last engine info time exceeds measured inclusive wall time')
        if not pv or pv[0]!=move:
            message.append('last finished PV head differs from final bestmove or is absent')
        for reason in message:
            notices.append({'game':game,'ply':ply,'root_fen':board.fen(),'severity':'notice','message':reason,'search_stdout':frame})
        selected=chess.Move.from_uci(move)
        assert selected in board.legal_moves
        board.push(selected)
        moves.append(move)
        rows.append(row)
    assert [*expect_input,'quit']==(run/'engine.commands.txt').read_text(encoding='ascii').splitlines()
    assert moves==summary['moves'] and board.fen()==summary['final_fen']
    finished=board.outcome(claim_draw=True)
    if finished is not None:
        assert summary['stop']==finished.termination.name and summary['result']==finished.result()
    else:
        assert (ply_count,summary['stop'],summary['result'])==(200,'PLY_CAP','*')
    assert notices==list(map(json.loads,(run/'anomalies.jsonl').read_text().splitlines())) and len(notices)==summary['notices']
    return rows,labels,timings,notices,{'game':game,'plies':ply_count,'started_utc':start.isoformat(),
           'finished_utc':end.isoformat(),'end':summary['stop'],'files_sha256':summary['files_sha256']}


def totals(rows):
    capped=[row for row in rows if row['cap']]
    final=sum(row['final_nodes'] for row in rows)
    last=sum(row['last_nodes'] for row in rows)
    wall=sum(row['wall_ns'] for row in rows)
    after=sum(row['wall_ns']-row['last_time_ms']*1_000_000 for row in capped)
    assert final-last==sum(r['final_nodes']-r['last_nodes'] for r in capped)
    return {'all_searches':len(rows),'capped_searches':len(capped),'capped_search_share':len(capped)/len(rows),
            'all_final_nodes':final,'all_last_info_nodes':last,'unreported_nodes':final-last,
            'unreported_node_share':(final-last)/final,'cap_final_nodes':sum(r['final_nodes'] for r in capped),
            'cap_last_info_nodes':sum(r['last_nodes'] for r in capped),'all_wall_ns':wall,
            'capped_wall_ns':sum(row['wall_ns'] for row in capped),'capped_after_last_wall_ns':after,
            'capped_after_last_wall_share':after/wall,'capped_after_last_wall_ns_is_negative':sum(
                r['wall_ns']<r['last_time_ms']*1_000_000 for r in capped),
            'cap_without_excess':sum(r['final_nodes']>=8000 and not r['cap'] for r in rows),
            'excess_below_cap':sum(r['final_nodes']<8000 for r in capped),
            'cap_above_8000':sum(r['final_nodes']>8000 for r in rows)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--partial-ok',action='store_true',help='audit only the prefix of stamped whole games')
    args=parser.parse_args()
    assert chess.__version__=='1.11.2'
    archive=ARCHIVE/'job21'
    stamps=[m.groups() for line in (archive/'stamps.txt').read_text().splitlines() if (m:=COMPLETE.fullmatch(line))]
    identifiers=[int(item[1]) for item in stamps]
    assert identifiers==list(range(41,41+len(identifiers))) and (len(identifiers)==100 or args.partial_ok)
    fixture=ARCHIVE/'job19/positions.txt'
    assert hash_file(fixture)==FIXTURE
    fens=fixture.read_text(encoding='ascii').splitlines()
    assert len(fens)==1000
    startup=(ARCHIVE/'job19/W1/r15d/engine.commands.txt').read_text(encoding='ascii').splitlines()
    header=startup[:startup.index('ucinewgame')]
    rows=[]; labels=[]; all_timings=[]; anomalies=[]; games=[]
    for timestamp,id_text,plies_text in stamps:
        redone,claimed,timings,notices,game=read_game(archive,int(id_text),fens,header,utc_value(timestamp),int(plies_text))
        rows.extend(redone); labels.extend(claimed); all_timings.extend(timings); anomalies.extend(notices); games.append(game)
    assert all(a[1]<b[0] for a,b in zip(all_timings,all_timings[1:]))
    with (archive/'g1/rows.tsv').open(encoding='ascii', newline='') as file:
        reader=csv.DictReader(file,delimiter='\t')
        aggregate=list(islice(reader,len(labels)) if args.partial_ok else reader)
    assert aggregate==labels
    result={'game_count':len(games),'first_game':identifiers[0],'last_game':identifiers[-1],
            'all_game_stamps_seen':len(identifiers)==100,'aggregate_rows_match':True,'all_clock_pairs_nonoverlapping':True,
            'node_and_time_totals':totals(rows),'anomaly_count':len(anomalies),
            'anomaly_counts_by_message':{reason:sum(row['message']==reason for row in anomalies)
                                         for reason in sorted({row['message'] for row in anomalies})},
            'first_capped':next((row for row in rows if row['cap']),None),'games':games}
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
