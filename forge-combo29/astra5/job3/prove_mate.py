"""Enumerate the legal moves in the job 3 position, using the chess 1.11.2 library."""
import chess


FEN = "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1"


def mates_in_one(board):
    mates = []
    for move in sorted(board.legal_moves, key=lambda m: m.uci()):
        board.push(move)
        if board.is_checkmate():
            mates.append(move.uci())
        board.pop()
    return mates


def main():
    board = chess.Board(FEN)
    assert board.is_valid()
    print(f"python-chess chess module {chess.__version__}\nFEN {FEN}")
    first_moves = sorted(board.legal_moves, key=lambda m: m.uci())
    instant = mates_in_one(board)
    print(f"White legal first moves: {len(first_moves)}\nWhite mates in one: {instant}")
    print("\nOther first moves and a legal Black reply leaving no mate in one:")
    forced = {}
    for first in first_moves:
        board.push(first)
        replies = {}
        for black in sorted(board.legal_moves, key=lambda m: m.uci()):
            board.push(black)
            mates = mates_in_one(board)
            board.pop()
            if not mates:
                print(first.uci(), black.uci())
                break
            replies[black.uci()] = mates
        else:
            if replies:
                forced[first.uci()] = replies
        board.pop()
    print(f"\nFirst moves forcing mate in exactly two: {sorted(forced)}")
    assert not instant and list(forced) == ["g3g6"]
    replies = forced["g3g6"]
    print(f"Black legal replies to g3g6: {len(replies)}\nBlack reply | all legal checkmates")
    supplied_moves = {"f7g6": "e5g6", "e6f5": "e5f7"}
    alternatives = 0
    for reply, mates in replies.items():
        expected = supplied_moves.get(reply, "g6h7")
        assert expected in mates, (reply, expected, mates)
        print(f"{reply} | {' '.join(mates)}")
        alternatives += len(mates) > 1
    assert len(replies) == 34
    print(f"All 34 listed continuations from the job deliver checkmate. "
          f"Replies admitting additional mates in one: {alternatives}.")


if __name__ == "__main__":
    main()
