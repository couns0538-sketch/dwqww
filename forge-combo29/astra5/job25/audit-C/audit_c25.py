"""Audit a Job 25 fastchess PGN against the engine names, raw scores, openings and terminal rules."""
from argparse import ArgumentParser
from collections import Counter
import csv
from hashlib import sha256
import io
import json
from pathlib import Path
import re

import chess
import chess.pgn


TARGET = {'C1':20, 'C2':60, 'C4':40}
BOOK_SHA = '889e8db12ee327cae68b29ada3458a2fb957cf8f5563d29a7fd13d850ff3f638'
START = re.compile(r'^Started game (\d+) of (\d+) \((\S+) vs (\S+)\)')
FINISH = re.compile(r'^Finished game (\d+) \((\S+) vs (\S+)\): (\S+) \{(.+)\}$')
WLD = re.compile(r'^Games: (\d+), Wins: (\d+), Losses: (\d+), Draws: (\d+), Points: ([.\d]+) ')
PENTA = re.compile(r'^Ptnml\(0-2\): \[([0-9, ]+)\]')
ISSUE = re.compile(r'illegal|disconnect|(?:lost|broken|closed) (?:engine )?connection|stall|(?:lose[st]?|lost|loss|forfeit(?:s|ed)?) on time|time(?:out|d out| forfeit)|time limit exceed|flag fall|crash', re.I)
REASONS = {'White mates','Black mates','Draw by stalemate','Draw by 3-fold repetition','Draw by insufficient mating material','Draw by fifty moves rule'}


class Builder(chess.pgn.GameBuilder):
    def visit_result(self, result):
        self.game.moves_result = result
        super().visit_result(result)


def opening_order(n, seed):
    # std::mt19937_64 followed by fastchess opening_book.hpp's forward shuffle.
    mask = 2**64 - 1
    state = [seed]
    for i in range(1,312):
        state.append((6364136223846793005*(state[-1]^(state[-1]>>62))+i)&mask)
    for i in range(312):
        x=(state[i]&0xffffffff80000000)|(state[(i+1)%312]&0x7fffffff)
        state[i]=state[(i+156)%312]^(x>>1)^(0xb5026f5aa96619e9 if x&1 else 0)
    order=list(range(1,n+1))
    for i in range(n-1):
        x=state[i]
        x ^= (x>>29)&0x5555555555555555
        x ^= (x<<17)&0x71d67fffeda60000
        x ^= (x<<37)&0xfff7eee000000000
        x ^= x>>43
        j=i+x%(n-i)
        order[i],order[j]=order[j],order[i]
    return order


def points2(white, result):
    if result=='1/2-1/2':return 1
    assert result in {'1-0','0-1'}
    return 2 * ((white=='kF') == (result=='1-0'))


def verify_end(board, reason, result):
    if reason=='White mates': return board.is_checkmate() and board.turn==chess.BLACK and result=='1-0'
    if reason=='Black mates': return board.is_checkmate() and board.turn==chess.WHITE and result=='0-1'
    if result!='1/2-1/2': return False
    if reason=='Draw by fifty moves rule':return board.is_fifty_moves()
    if reason=='Draw by stalemate':return board.is_stalemate()
    if reason=='Draw by insufficient mating material':return board.is_insufficient_material()
    if reason=='Draw by 3-fold repetition':return board.is_repetition(3)
    return False


def tsv(path,header,rows):
    with path.open('w',newline='') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n')
        w.writerow(header)
        w.writerows(rows)


def audit(part, source, book, out, partial):
    assert chess.__version__=='1.11.2'
    rounds=TARGET[part]
    inputs={s:(source/s).read_bytes() for s in ('argv.json','fastchess.log','games.pgn')}
    book_bytes=book.read_bytes()
    assert sha256(book_bytes).hexdigest()==BOOK_SHA
    booklines={tuple(line.decode().split()[:4]):i for i,line in enumerate(book_bytes.splitlines(),1)}
    assert len(booklines)==234
    args=json.loads(inputs['argv.json']); pos=lambda k:args[args.index(k)+1]
    assert pos('-rounds')==str(rounds) and pos('-games')=='2' and '-repeat' in args and '-recover' in args
    assert pos('-srand')=='2500001' and pos('-each')=='proto=uci' and 'nodes=50000' in args
    assert args.count('option.Threads='+part[1:])==2 and args.count('option.Hash=16')==2
    assert 'name=kF' in args and 'name=r15d' in args and args.index('name=kF') < args.index('name=r15d')
    a=args[args.index('name=kF')+1:args.index('-engine',args.index('name=kF'))]
    b=args[args.index('name=r15d')+1:args.index('-each')]
    assert a==b and len(a)==24 and a[-2].startswith('option.NNUEArchFile=') and a[-1]=='option.NNUEArch=true'
    assert {x for x in a if x in ('option.Hash=16','option.OwnBook=false','option.HistRework=2')}=={'option.Hash=16','option.OwnBook=false','option.HistRework=2'}
    assert 'order=random' in args and 'format=epd' in args
    expected_book=opening_order(234,int(pos('-srand')))
    started={};ended={};score=[];pent=[];issues=[]
    for n,line in enumerate(inputs['fastchess.log'].decode().splitlines(),1):
        if ISSUE.search(line): issues.append((n,line))
        if m:=START.match(line):
            i,count,w,b=m.groups();i=int(i)
            assert i not in started and int(count)==2*rounds and {w,b}=={'kF','r15d'}
            started[i]=(w,b)
        if m:=FINISH.match(line):
            i,w,b,result,reason=m.groups();i=int(i)
            assert started[i]==(w,b) and i not in ended
            ended[i]=(w,b,result,reason,n)
        if m:=WLD.match(line):score.append((tuple(map(int,m.groups()[:4])),float(m[5])))
        if m:=PENTA.match(line):pent.append([int(x) for x in m[1].split(',')])
    ids=set(range(1,2*rounds+1))
    if not partial:assert set(ended)==set(started)==ids
    games={};game_rows=[];endings=Counter();rule_bad=[]
    reader=io.StringIO(inputs['games.pgn'].decode('utf-8-sig'))
    while (g:=chess.pgn.read_game(reader,Visitor=Builder)) is not None:
        h=g.headers
        if partial and h['Result']=='*':continue
        assert not g.errors and h['Result']==g.moves_result and h['SetUp']=='1'
        rnd=int(h['Round']);w,b,result=h['White'],h['Black'],h['Result']
        matches=[i for i in (2*rnd-1,2*rnd) if i in ended and ended[i][:3]==(w,b,result)]
        assert len(matches)==1 and matches[0] not in games
        i=matches[0];reason=ended[i][3]
        board=g.board(); fen=board.fen()
        line=booklines[tuple(fen.split()[:4])]
        assert line==expected_book[rnd-1],(rnd,line,expected_book[rnd-1])
        moves=[]
        for m in g.mainline_moves():
            assert m in board.legal_moves
            moves.append(m.uci());board.push(m)
        assert int(h['PlyCount'])==len(moves)
        assert reason in g.end().comment
        terminal=verify_end(board,reason,result)
        if reason in REASONS:
            assert terminal and h['Termination']=='normal',(i,h,reason,board.fen())
        else:
            rule_bad.append(i)
        games[i]=(w,b,fen,moves,result,reason)
        game_rows.append((i,rnd,line,w,b,result,points2(w,result)/2,reason,h.get('Termination'),len(moves),terminal,fen,' '.join(moves)))
        endings[reason]+=1
    assert set(games)==set(ended)
    pairrows=[];penta=[0]*5;differ=[];badpairs=[];firstprefix=[]
    for rnd in range(1,rounds+1):
        if not {2*rnd-1,2*rnd}<=set(games):continue
        g,h=games[2*rnd-1],games[2*rnd]
        assert g[0]==h[1] and h[0]==g[1] and g[2]==h[2]
        diff=next((i for i,(a,b) in enumerate(zip(g[3],h[3])) if a!=b),min(len(g[3]),len(h[3]))) if g[3]!=h[3] else None
        pts=points2(g[0],g[4])+points2(h[0],h[4]);penta[pts]+=1
        if diff is not None:differ.append(rnd)
        if diff is not None or pts!=2:
            badpairs.append(rnd)
            if not firstprefix:
                firstprefix=[f'round {rnd}; first different played ply {diff+1 if diff is not None else "none"}']
                for game in (g,h):
                    head=game[3][:diff+1] if diff is not None else game[3]
                    if diff is not None and diff==len(game[3]):head=head+['<end>']
                    firstprefix.append(f'{game[0]} vs {game[1]} result {game[4]}: '+ ' '.join(head))
        pairrows.append((rnd,2*rnd-1,2*rnd,g[4],h[4],pts/2,g[3]==h[3],'' if diff is None else diff+1,' '.join(g[3]),' '.join(h[3])))
    kf=Counter(points2(g[0],g[4]) for g in games.values());w,l,d=kf[2],kf[0],kf[1];n=len(games)
    if not partial or score and score[-1][0][0]==n:
        assert score[-1]==((n,w,l,d),w+d/2)
        assert pent[-1]==penta
    verdict=('PASS' if not badpairs and n==2*rounds and w==l else 'FAIL') if part=='C1' else (('PASS' if differ else 'ALL COPY PAIRS') if part=='C2' else 'observed')
    if partial and n!=2*rounds: verdict='PARTIAL'
    out.mkdir(exist_ok=True,parents=True)
    tsv(out/'games-independent.tsv',('game','round','book_line','White','Black','result','kF_points','fastchess_reason','PGN_termination','plies','legal_terminal_rule_verified','opening_FEN','UCI_moves'), sorted(game_rows))
    tsv(out/'pairs-independent.tsv',('round','game_1','game_2','result_1','result_2','kF_points','same_moves','first_differing_played_ply','UCI_moves_game1','UCI_moves_game2'),pairrows)
    tsv(out/'problems-independent.tsv',('log_line','text'),issues)
    summary=dict(part=part,requested_rounds=rounds,complete_rounds=len(pairrows),games_started=len(started),games_finished=n,plies=sum(len(g[3]) for g in games.values()),endings=dict(sorted(endings.items())),wins=w,losses=l,draws=d,kF_points=w+d/2,kF_share=(w+d/2)/n if n else None,pentanomial=penta,same_moves=len(pairrows)-len(differ),different_moves=len(differ),different_rounds=differ,bad_rule_games=rule_bad,abnormal_lines=issues,first_differing_round_details=firstprefix,control=verdict,sha256={s:sha256(blob).hexdigest() for s,blob in inputs.items()})
    (out/'summary-independent.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(part,verdict,n,w,l,d,penta,dict(endings),'different move pairs',len(differ),'issues',len(issues),'abnormal endings',len(rule_bad))


if __name__=='__main__':
    p=ArgumentParser(description=__doc__);p.add_argument('part',choices=TARGET);p.add_argument('source',type=Path);p.add_argument('book',type=Path);p.add_argument('output',type=Path);p.add_argument('--partial',action='store_true')
    a=p.parse_args();audit(a.part,a.source,a.book,a.output,a.partial)
