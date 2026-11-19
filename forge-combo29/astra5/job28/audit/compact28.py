"""Recount Job 28 from the committed per-search/per-game tables and literal hold lines."""
from argparse import ArgumentParser
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path

import chess

from replay28 import BOOK_SHA, OPTIONS, check, score2
from score28 import ARMS, collect
from stage28 import read_compact, tab_from


def validate_terminal(board, move_count):
    if board.is_checkmate():
        return 'checkmate', ('0-1' if board.turn else '1-0')
    if board.is_stalemate():
        return 'stalemate', '1/2-1/2'
    if board.is_insufficient_material():
        return 'insufficient', '1/2-1/2'
    if board.can_claim_threefold_repetition():
        return 'threefold', '1/2-1/2'
    if board.can_claim_fifty_moves():
        return 'fifty', '1/2-1/2'
    if move_count==600:
        return 'cap', '1/2-1/2'
    return None, None


def replay(rec, rows, fen, hold_counts, stage, process_by_game):
    i=int(rec['game']);k=int(rec['opening'])
    check(k==(i+1)//2 and rec['white']==('A' if i%2 else 'B'),rec)
    board=chess.Board(fen);clocks={'W':6000,'B':6000}
    count=Counter();spent=Counter();nodes=Counter();holds=Counter();holdlines=Counter();flag=None
    positions=0;ending,result=validate_terminal(board,positions)
    for ply,r in enumerate(rows,1):
        side='W' if board.turn else 'B';player=rec['white'] if board.turn else rec['black']
        check(not ending and r['game']==str(i) and r['ply']==str(ply) and r['side']==side and r['engine']==player,(stage,i,ply))
        n=int(r['soft_line'].removeprefix('info string softnodes nodes '));used=n//100
        move=r['move_line'].split();check(move[:1]==['bestmove'] and r['bestmove']==move[1],r)
        check(n==int(r['N']) and used==int(r['used']) and r['soft_line']==f'info string softnodes nodes {n}',r)
        check((int(r['wtime']),int(r['btime']),int(r['clock_before']))==(clocks['W'],clocks['B'],clocks[side]),r)
        mark=int(r['holds']);check(mark==hold_counts[(i,ply,side,player)],('hold mismatch',i,ply,mark))
        check(not mark or player=='A' and stage=='M4',r)
        count[player]+=1;spent[player]+=used;nodes[player]+=n;holds[player]+=mark>0;holdlines[player]+=mark
        chosen=board.parse_uci(move[1]);check(chosen in board.legal_moves,(i,ply,'illegal move'))
        before=clocks[side]
        if used>before:
            flag=[i,ply,side,player,n,used,before];ending='time';result='0-1' if board.turn else '1-0'
        else:
            clocks[side]+=60-used
            board.push(chosen);positions+=1
            ending,result=validate_terminal(board,positions)
        check(int(r['clock_after'])==clocks[side],r)
    check((ending,result,positions,clocks['W'],clocks['B'])==(rec['ending'],rec['result'],int(rec['plies']),int(rec['wclock']),int(rec['bclock'])),(stage,rec))
    return dict(game=i,opening=k,white=rec['white'],score=score2(rec),result=result,ending=ending,plies=positions,clocks=clocks,
        count=dict(count),spent=dict(spent),holds=dict(holds),holdlines=dict(holdlines),nodes=dict(nodes),flag=flag,
        start=rec['started_utc'],finish=rec['ended_utc'],processes=process_by_game[i])


def read_arm(path,book):
    receipt=json.loads((path/'receipt.json').read_text());scope=receipt['stage']
    for name,desc in receipt['files'].items():
        raw=(path/name).read_bytes()
        check((len(raw),sha256(raw).hexdigest())==(desc['bytes'],desc['sha256']),(path,name))
    holds_dir=path/'hold-evidence'
    if not holds_dir.is_dir():
        holds_dir=path.parents[2]/'hold-evidence'/path.parent.name/scope
    hold_receipt=json.loads((holds_dir/'receipt.json').read_text())
    check(hold_receipt['arm_receipt_sha256']==sha256((path/'receipt.json').read_bytes()).hexdigest(),
          (path,'hold addendum identifies different arm'))
    for name,desc in hold_receipt['files'].items():
        raw=(holds_dir/name).read_bytes()
        check((len(raw),sha256(raw).hexdigest())==(desc['bytes'],desc['sha256']),(path,name,'hold file digest'))
    held=Counter()
    for x in tab_from(read_compact(holds_dir,'holds.tsv')):
        if x['disposition']!='finished_game':
            continue
        check(x['uci_line'].startswith('info string TmFinishIteration hold'),x)
        held[int(x['game']),int(x['ply']),x['side'],x['engine']]+=1
    profiles=json.loads((path/'option-profiles.json').read_text())
    extra={'M4':['TmFinishIteration true','TmSoftDivisor 20'],'M5':['TmSoftDivisor 16'],'M6':['TmSoftDivisor 30']}
    process_by_game=defaultdict(list);proc_sides=defaultdict(set)
    for r in tab_from(read_compact(path,'engines.tsv')):
        i=int(r['game']);side=r['color'];role=r['role']
        check(side in ('W','B') and role==('A' if ((i % 2 == 1)==(side=='W')) else 'B'),(path,i,side,role))
        expected=OPTIONS+['NodeClock 100']+(extra[scope] if role=='A' else [])
        check([' '.join(x) for x in profiles[r['option_profile']]]==expected,(path,i,role,'stored option order'))
        check(side not in proc_sides[i],(path,i,'duplicate process side'))
        proc_sides[i].add(side);process_by_game[i].append((int(r['pid']),int(r['start_ticks'])))
    searches=defaultdict(list)
    for r in tab_from(read_compact(path,'searches.tsv')):
        searches[int(r['game'])].append(r)
    openings={int(r['opening']):r['fen'] for r in tab_from(read_compact(path,'openings.tsv'))}
    check(all(book[k-1]==fen for k,fen in openings.items()),(path,'L27 line mismatch'))
    games=[replay(r,searches[int(r['game'])],book[int(r['opening'])-1],held,scope,process_by_game) for r in tab_from(read_compact(path,'games.tsv'))]
    check(all(proc_sides[g['game']]=={'W','B'} for g in games),(path,'two fresh sides per completed game'))
    check(sum(sum(g['holdlines'].values()) for g in games)==sum(held.values()),(path,'unlinked hold'))
    check(sum(sum(g['count'].values()) for g in games)==receipt['searches'],(path,'search count'))
    wanted=set(range(2*receipt['opening_first']-1,2*receipt['opening_last']+1))
    done={g['game'] for g in games};wait=set(receipt['unfinished_game_ids']);skipped=set(receipt['not_started_game_ids'])
    check(len(done)==len(games) and not (done & wait or wait & skipped or skipped & done)
          and done|wait|skipped==wanted and len(done|wait)==receipt['started_games'],(path,'claimed coverage'))
    check(sum(sum(g['holds'].values()) for g in games)==hold_receipt['finished_searches_with_holds'],(path,'hold search aggregate'))

    return dict(block=receipt['block'],stage=scope,complete=receipt['complete'],started=receipt['started_games'],finished=len(games),games=games,
        searches=receipt['searches'],finished_ids=receipt['finished_game_ids'],unfinished=receipt['unfinished_game_ids'],unstarted=receipt['not_started_game_ids'],
        unfinished_searches=receipt['unfinished_searches'],frozen_utc=receipt['frozen_utc'])


if __name__=='__main__':
    p=ArgumentParser(description=__doc__);p.add_argument('match_archive',type=Path);p.add_argument('L27',type=Path);p.add_argument('out',type=Path);p.add_argument('--final',action='store_true')
    a=p.parse_args();raw=a.L27.read_bytes();check(sha256(raw).hexdigest()==BOOK_SHA,'L27 SHA256')
    assert chess.__version__=='1.11.2'
    arms=[read_arm(x.parent,raw.decode().splitlines()) for x in sorted(a.match_archive.glob('block*/M?/receipt.json'))]
    result=collect(a.out,arms,a.match_archive,a.final)
    print('Verified',result['common_blocks'],'common blocks,',result['common_openings'],'pairs per arm.')
