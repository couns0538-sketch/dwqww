"""Check arithmetic edge cases in the offline reader using an explicit two-ply artificial forfeiture."""
import csv
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import chess
from audit_games import OPTIONS, replay_game

book=Path(sys.argv[1]).read_text().splitlines()
assert chess.__version__=='1.11.2'
fen=chess.Board(book[0]).fen()
headers='game ply side engine N used clock_before clock_after bestmove holds wtime btime soft_line move_line'.split()
game_header='game opening white black result ending plies wclock bclock started_utc ended_utc'.split()
game_row=['1','1','A','B','1-0','time','1','60','6000','2026-11-19T18:00:00Z','2026-11-19T18:00:01Z']
with TemporaryDirectory() as d:
    root=Path(d);dest=root/'g0001';dest.mkdir();(root/'inputs.json').write_text(json.dumps({'exe':'nc'}))
    (dest/'opening.txt').write_text('1\t'+fen+'\n')
    (dest/'result.tsv').write_text('\t'.join(game_header)+'\n'+'\t'.join(game_row)+'\n')
    board=chess.Board(fen);moves=[];wire=[];rows=[];proc={}
    for side,role,node,hold in [('W','A',2000,True),('B','B',1000,False)]:
        opts=[*OPTIONS,f'NodeClock {node}',f'TmFinishIteration {str(hold).lower()}']
        proc[side]={'exe':'nc','role':role,'options':[x.rsplit(' ',1) for x in opts],'pid':1 if side=='W' else 2,'start_ticks':1}
        wire.extend([side+' > uci',side+' < uciok'])
        wire.extend(side+' > setoption name '+x.rsplit(' ',1)[0]+' value '+x.rsplit(' ',1)[1] for x in opts)
        wire.extend([side+' > ucinewgame',side+' > isready',side+' < readyok'])
    for ply,(side,role,n,w,b,after,holds) in enumerate([('W','A',6000999,6000,6000,60,2),('B','B',6001000,60,6000,6000,0)],1):
        move=next(iter(board.legal_moves)).uci();soft=f'info string softnodes nodes {n}';best='bestmove '+move
        wire.extend([side+' > position fen '+fen+' moves'+(' '+' '.join(moves) if moves else ''),side+f' > go wtime {w} btime {b} winc 60 binc 60'])
        wire.extend([side+' < info string TmFinishIteration hold example']*holds);wire.extend([side+' < '+soft,side+' < '+best])
        rows.append([1,ply,side,role,n,n//1000,6000,after,move,holds,w,b,soft,best])
        board.push_uci(move);moves.append(move)
    (dest/'wire.txt').write_text('\n'.join(wire)+'\n');(dest/'engines.json').write_text(json.dumps(proc))
    with (dest/'searches.tsv').open('w') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n');w.writerow(headers);w.writerows(rows)
    out=replay_game(root,dict(zip(game_header,game_row)),'C26',book)
    assert out['spent']=={'A':6000,'B':6001} and out['holds']=={'A':1,'B':0} and out['holdlines']=={'A':2,'B':0}
    assert out['plies']==1 and out['flag']==(1,2,'B','B',6001000,6001,6000)
    assert out['clocks']=={'W':60,'B':6000}
print('Artificial reader fixture only; no engine or match games.')
print('PASS C26 A with NodeClock 2000, N=6000999 is charged 6000, equality allows the move and leaves 60 after increment.')
print('PASS 2 hold markers in one A search count as 1 triggering search.')
print('PASS B uses 6001 with clock 6000, forfeits without recording its bestmove as a played move, final clock is unchanged.')
