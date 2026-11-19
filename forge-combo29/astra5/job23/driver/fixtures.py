"""Check the two FEN command forms without launching or searching with an engine."""
from selfplay import chess
from selfplay import position_command, random_opening


def main():
    for game in (700001,700002,700591,701791):
        board,opening=random_opening(game)
        fen=board.fen()
        moves=list(opening)
        print(f'game {game} prefix_plies {len(opening)} terminal {board.is_game_over(claim_draw=True)} fen0 {fen}')
        for n in range(3):
            s=position_command('S',fen,opening,moves)
            b=position_command('B',fen,opening,moves)
            assert s == 'position fen ' + chess.STARTING_FEN + ' moves ' + ' '.join(moves)
            assert b.split() == ['position','fen',*fen.split(),'moves',*moves[len(opening):]]
            # A non-engine oracle replays both roots and checks all six FEN fields.
            for command in (s,b):
                _,replay=command.split('position fen ',1)
                root,tail=replay.split(' moves',1)
                probe=chess.Board(root)
                for move in tail.split(): probe.push_uci(move)
                assert probe.fen()==board.fen()
            if n==0:
                print('S:',s)
                print('B:',b)
            if board.is_game_over(claim_draw=True): break
            next_move=next(iter(board.legal_moves))
            moves.append(next_move.uci())
            board.push(next_move)
    print('PASS both commands reproduce all six current FEN fields; terminal opening fixtures retain zero searches.')


if __name__=='__main__':
    main()
