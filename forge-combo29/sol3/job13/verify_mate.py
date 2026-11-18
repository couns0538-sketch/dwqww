from pathlib import Path
import sys

import chess

board = chess.Board(Path(sys.argv[1]).read_text().strip())
def immediate_mates(position):
    result = []
    for move in position.legal_moves:
        position.push(move)
        if position.is_checkmate():
            result.append(move.uci())
        position.pop()
    return sorted(result)
print('python-chess', chess.__version__)
print('legal root moves', board.legal_moves.count(), 'mate in one', immediate_mates(board))
forced = {}
for first in list(board.legal_moves):
    board.push(first)
    replies = {}
    for reply in list(board.legal_moves):
        board.push(reply)
        replies[reply.uci()] = immediate_mates(board)
        board.pop()
    if replies and all(replies.values()):
        forced[first.uci()] = replies
    board.pop()
print('mate-in-two first moves', sorted(forced))
assert list(forced) == ['g3g6']
for reply, mates in sorted(forced['g3g6'].items()):
    print(reply, ','.join(mates))
board.push_uci('g3g6')
assert not board.is_check()
board.push(chess.Move.null())
mates = [move for move in immediate_mates(board) if not board.is_capture(chess.Move.from_uci(move))]
assert mates == ['g6h7']
print('quiet mates after g3g6 and Black null', mates)
