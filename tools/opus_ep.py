#!/usr/bin/env python3
"""opus_ep.py - en-passant normaliser for FEN rows (R14 finish, Opus; own code, standard library only).

"Legal-capture-only": a FEN keeps its en-passant square only when the side to move has a LEGAL en-passant capture
(the capturing pawn stands next to the double-pushed pawn, and after the capture its own king is not attacked).
Otherwise the field becomes "-". Two rows that differ only in a non-capturable EP square are then the same chess
position (same pieces, side to move, castling rights and legal moves).

  ep_status(placement, side, ep) -> 'none' | 'legal' | 'no_capture' | 'invalid'
      none        the field is "-"
      legal       at least one legal en-passant capture exists
      no_capture  a well-formed EP square (a double-pushed pawn in front of it, the square and the pawn's origin
                  empty) without a legal capture
      invalid     the EP square does not fit the board (wrong rank for the side, no enemy pawn in front of it, the
                  square or the origin square occupied); callers must fail closed on it, never normalise it away
  normalize_fen(fen) -> fen with the EP field kept only for 'legal' (raises ValueError for 'invalid')

CLI self-check against python-chess (used as a test oracle only, never by the normaliser):
  python opus_ep.py --oracle <selfplay.txt> [--limit N]   compares every row with an EP square
"""
import argparse
import sys

FILES = 'abcdefgh'
KNIGHT_STEPS = ((1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1))
KING_STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
ROOK_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
BISHOP_DIRS = ((1, 1), (1, -1), (-1, 1), (-1, -1))


def squares(placement):
    """64-entry list, index rank * 8 + file (rank 0 = rank 1); None for an empty square. Strict: ValueError."""
    ranks = placement.split('/')
    if len(ranks) != 8:
        raise ValueError('placement needs 8 ranks')
    board = [None] * 64
    for i, text in enumerate(ranks):
        rank, file = 7 - i, 0
        for ch in text:
            if ch in '12345678':
                file += int(ch)
            elif ch in 'PNBRQKpnbrqk':
                if file > 7:
                    raise ValueError('rank too long')
                board[rank * 8 + file] = ch
                file += 1
            else:
                raise ValueError(f'bad placement character {ch!r}')
        if file != 8:
            raise ValueError('rank width is not 8')
    return board


def attacked(board, target, by_white):
    """True if a piece of the given colour attacks square `target` on `board`."""
    r, f = divmod(target, 8)
    pawn, knight, king = ('P', 'N', 'K') if by_white else ('p', 'n', 'k')
    straight, diagonal = (('R', 'Q'), ('B', 'Q')) if by_white else (('r', 'q'), ('b', 'q'))
    pr = r - 1 if by_white else r + 1          # a white pawn attacks upwards, so it stands one rank below
    if 0 <= pr < 8:
        for pf in (f - 1, f + 1):
            if 0 <= pf < 8 and board[pr * 8 + pf] == pawn:
                return True
    for dr, df in KNIGHT_STEPS:
        rr, ff = r + dr, f + df
        if 0 <= rr < 8 and 0 <= ff < 8 and board[rr * 8 + ff] == knight:
            return True
    for dr, df in KING_STEPS:
        rr, ff = r + dr, f + df
        if 0 <= rr < 8 and 0 <= ff < 8 and board[rr * 8 + ff] == king:
            return True
    for dirs, sliders in ((ROOK_DIRS, straight), (BISHOP_DIRS, diagonal)):
        for dr, df in dirs:
            rr, ff = r + dr, f + df
            while 0 <= rr < 8 and 0 <= ff < 8:
                piece = board[rr * 8 + ff]
                if piece is not None:
                    if piece in sliders:
                        return True
                    break
                rr, ff = rr + dr, ff + df
    return False


def ep_status(placement, side, ep):
    if ep == '-':
        return 'none'
    if side not in ('w', 'b') or len(ep) != 2 or ep[0] not in FILES or ep[1] not in '36':
        return 'invalid'
    white = side == 'w'
    file, rank = FILES.index(ep[0]), int(ep[1]) - 1
    if rank != (5 if white else 2):
        return 'invalid'
    board = squares(placement)
    step = -1 if white else 1                       # from the EP square towards the double-pushed pawn
    victim = (rank + step) * 8 + file
    origin = (rank - step) * 8 + file               # where the double-pushed pawn started
    if board[victim] != ('p' if white else 'P') or board[rank * 8 + file] is not None or board[origin] is not None:
        return 'invalid'
    pawn, king = ('P', 'K') if white else ('p', 'k')
    if board.count(king) != 1:
        return 'invalid'
    king_square = board.index(king)
    for capturer_file in (file - 1, file + 1):
        if not 0 <= capturer_file < 8:
            continue
        frm = (rank + step) * 8 + capturer_file
        if board[frm] != pawn:
            continue
        after = list(board)
        after[frm] = None
        after[victim] = None
        after[rank * 8 + file] = pawn
        if not attacked(after, king_square, not white):
            return 'legal'
    return 'no_capture'


def normalize_fields(fields):
    """fields = the six FEN fields (list or tuple). Returns the list with the EP field normalised."""
    status = ep_status(fields[0], fields[1], fields[3])
    if status == 'invalid':
        raise ValueError(f'invalid en-passant field {fields[3]!r} for this board')
    out = list(fields)
    if status != 'legal':
        out[3] = '-'
    return out


def normalize_fen(fen):
    fields = fen.split()
    if len(fields) != 6:
        raise ValueError('six FEN fields required')
    return ' '.join(normalize_fields(fields))


def oracle(path, limit):
    import chess  # test oracle only
    checked = agree = invalid = 0
    disagreements = []
    with open(path, 'rb') as stream:
        for line_no, raw in enumerate(stream, 1):
            fen = raw.split(b'|', 1)[0].decode('ascii').strip()
            fields = fen.split()
            if fields[3] == '-':
                continue
            status = ep_status(fields[0], fields[1], fields[3])
            if status == 'invalid':
                invalid += 1
                continue
            # Compare the EP field only: python-chess also rewrites castling rights it considers unusable.
            mine = normalize_fields(fields)[3]
            reference = chess.Board(fen).fen(en_passant='legal').split()[3]
            checked += 1
            if mine == reference:
                agree += 1
            elif len(disagreements) < 20:
                disagreements.append((line_no, fen, mine, reference))
            if limit and checked >= limit:
                break
    for item in disagreements:
        print('DISAGREE line %d: %s -> mine %s | oracle %s' % item)
    ok = checked > 0 and agree == checked
    print(f"oracle {'PASS' if ok else 'FAIL'}: {checked} EP rows compared, {agree} equal, {invalid} invalid EP rows")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--oracle', required=True)
    ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args()
    sys.exit(oracle(a.oracle, a.limit))


if __name__ == '__main__':
    main()
