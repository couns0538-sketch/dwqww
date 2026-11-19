"""Describe the shared missing P1 depth label from existing transcripts and chess history."""
import csv
from pathlib import Path
import sys
sys.path.insert(0,'/workspace/work/j10fens/vendor')
import chess
w=Path('/workspace/work/j20match')
game,ply=601580,84
spring=[]
for label in ['r15d','kF']:
    root=w/'results'/f'P1-{label}'
    sample=(root/'sample-uci.txt').read_text().split(f'begin {game} {ply}\n',1)[1].split('\nend\n',1)[0].splitlines()
    assert sample[1:]==['> go softnodes 2000','< info string softnodes nodes 8000','< bestmove g3g4',f'record {game} {ply} g3g4 NA']
    full_position=sample[0].removeprefix('> position startpos moves ').split()
    assert len(full_position)==ply
    board=chess.Board()
    for m in full_position:board.push_uci(m)
    with (root/'games.tsv').open() as f:receipt=next(r for r in csv.DictReader(f,delimiter='\t') if r['book_line']==str(game))
    raw=next(s.strip() for s in (w/'raw-labels'/f'P1-{label}.txt').open() if s.startswith(f'{game} {ply} '))
    saved=[]
    with (root/'records.txt').open() as f:
        for record in f:
            if record.startswith(f'{game} '): saved.append(record.rstrip('\n'))
            elif saved:break
    assert raw==f'{game} {ply} g3g4 NA'==next(s for s in saved if s.startswith(f'{game} {ply} '))
    with (root/'openings.tsv').open() as f:opening=next(r['moves'].split() for r in csv.DictReader(f,delimiter='\t') if r['game']==str(game))
    previous=[s.split()[2] for s in saved if int(s.split()[1])<ply]
    assert opening+previous==full_position
    assert not board.is_check() and not board.is_game_over(claim_draw=True) and not board.can_claim_draw()
    assert chess.Move.from_uci('g3g4') in board.legal_moves
    quiet_pawn_singles=[m.uci() for m in board.legal_moves if board.piece_type_at(m.from_square)==chess.PAWN and not m.promotion and not board.is_capture(m) and m.to_square-m.from_square==8]
    assert quiet_pawn_singles==['g3g4']
    pre=board.fen()
    legal=board.legal_moves.count()
    board.push_uci('g3g4')
    assert not board.is_game_over(claim_draw=True)
    after=[s.split()[2] for s in saved if int(s.split()[1])>ply]
    for m in after:board.push_uci(m)
    assert board.outcome(claim_draw=True).termination==chess.Termination.CHECKMATE
    spring.append((pre,legal,len(after),saved[-1].split()[:3],receipt['result']))
assert spring[0]==spring[1]
pre,legal,left,last,result=spring[0]
print('P1 game 601580, record ply 84, White to move (43.g4).')
print('Pre-move FEN', pre)
print(f'Replaying the stored opening and moves in python-chess 1.11.2 gave the same position as the saved UCI position command. White had {legal} legal moves, was out of check and could not claim a draw. The move g3g4 was legal. The resulting position remained nonterminal.')
print(f'The game continued for {left} more plies. Black checkmated on recorded ply {last[1]} with {last[2]} for a {result} result.')
print('Both original P1 raw-label files and both normalized record files contain the row “601580 84 g3g4 NA”.')
print('Both saved search replies consisted of “info string softnodes nodes 8000” followed by “bestmove g3g4”. Each lacks an info depth line and a score.')
print('For go softnodes 2000, both engines set a hard ceiling of 4 times 2000 (r15d src/search.cpp:2663, kF:3165). The supplemental reply shows the search reached this exact ceiling. The single-PV code suppresses an unfinished iteration when stopped by the node cap (r15d:3042, kF:3547), emits completed depth labels (r15d:3142, kF:3647) and falls back to the first legal root candidate if no completed best move exists (r15d:3239, kF:3744). These facts support reaching the ceiling during the first iteration. The saved replies contain no internal trace of which variations consumed those nodes.')
print('The recorded g3g4 also matches the first legal root candidate implied by the source. It was the only legal nonpromotion single pawn push. Forge generates those pushes before other moves and preserves order when filtering legality (r15d src/board.cpp lines 481-486 or 615-621 and 712-719, kF lines 482-487 or 616-622 and 713-720).')
print('The position and reply analysis used saved text, board replay and source inspection.')
