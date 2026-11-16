#!/usr/bin/env python3
"""filter_special.py R_FENS G_EPD OUT_FENS PER_CLASS
Classifies every input position with python-chess into the five classes of area 3 job 2 and writes up to
PER_CLASS FENs per class to OUT_FENS (one FEN per line: <class>\t<source>\t<fen>).
Also writes OUT_FENS.counts with the true pre-cap class sizes.

Class A: castling available where the king's TRANSIT square is attacked (the position is legal for python-chess
         only if the king is not in check; the transit square being attacked is exactly the pinned case that
         makes castling illegal, i.e. the engine must NOT generate it).
Class B: an en-passant capture that exists and, when played, would expose our own king to an attack along the
         vacated rank (the classic illegal-ep case). Detected directly: play every ep capture, ask
         board.is_attacked_by(them, our_king_square) AFTER the push (python-chess legality of the move list
         already excludes them, so I check the RAW ep capture instead, see below).
         Implementation: build the position, take the ep square, and construct the ep capture by hand, then test
         whether the resulting board has our king attacked; if so, the position is class B.
Class C: a legal move that is a capture AND a promotion AND gives check (board.gives_check after push).
Class D: the side to move is in check from two or more distinct enemy pieces (double check).
Class E: a legal move of a piece that is pinned to its own king (absolute pin) and captures the pinner.
"""
import sys
import chess


def load(path):
    out = []
    with open(path) as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            out.append(s.split(";")[0].strip() if s[0] in "12345678" and ";" in s else s)
    return out


def transit_squares(board):
    """squares the king crosses (not the origin, not the destination)."""
    return None


def is_class_a(board):
    """castling right present and the transit square attacked -> the engine must not castle."""
    if board.is_check():
        return False
    them = board.turn == chess.WHITE and chess.BLACK or chess.WHITE
    back = chess.A1 if board.turn == chess.WHITE else chess.A8
    side = chess.BLACK if board.turn == chess.WHITE else chess.WHITE
    res = False
    # king side: e->g, transit f
    if board.has_kingside_castling_rights(board.turn):
        transit = chess.F1 if board.turn == chess.WHITE else chess.F8
        dest = chess.G1 if board.turn == chess.WHITE else chess.G8
        r1 = board.attackers(side, transit)
        # the rook may "defend" through the king only in ways python-chess already excludes;
        # accept the position when the transit square is attacked by anything
        if board.is_attacked_by(side, transit) and not board.is_attacked_by(side, dest):
            res = True
    if board.has_queenside_castling_rights(board.turn):
        transit = chess.D1 if board.turn == chess.WHITE else chess.D8
        dest = chess.C1 if board.turn == chess.WHITE else chess.C8
        if board.is_attacked_by(side, transit) and not board.is_attacked_by(side, dest):
            res = True
    return res


def ep_exposes_king(board):
    """there is an ep capture available in the RAW sense and pushing it leaves our king attacked."""
    if board.ep_square is None:
        return False, None
    us = board.turn
    them = not us
    ep = board.ep_square
    # the capture is pawn from ep-8/+8 moving diagonally to ep; the captured pawn sits behind ep
    rank_from = ep + (-8 if us == chess.WHITE else 8)
    cap_sq = ep + (8 if us == chess.WHITE else -8)
    for df in (-1, 1):
        frm = chess.square(chess.square_file(ep) + df, chess.square_rank(rank_from))
        p = board.piece_at(frm)
        if p is None or p.piece_type != chess.PAWN or p.color != us:
            continue
        cap = board.piece_at(cap_sq)
        if cap is None or cap.piece_type != chess.PAWN or cap.color != them:
            continue
        b2 = board.copy(stack=False)
        b2.remove_piece_at(frm)
        b2.remove_piece_at(cap_sq)
        b2.set_piece_at(ep, chess.Piece(chess.PAWN, us))
        ksq = b2.king(us)
        if ksq is not None and b2.is_attacked_by(them, ksq):
            return True, f"{chess.square_name(frm)}{chess.square_name(ep)}"
    return False, None


def is_class_c(board):
    for mv in board.legal_moves:
        if board.is_capture(mv) and mv.promotion is not None:
            b2 = board.copy(stack=False)
            b2.push(mv)
            if b2.is_check():
                return True
    return False


def is_class_d(board):
    if not board.is_check():
        return False
    ksq = board.king(board.turn)
    attackers = board.attackers(not board.turn, ksq)
    return len(attackers) >= 2


def is_class_e(board):
    ksq = board.king(board.turn)
    if ksq is None:
        return False
    for mv in board.legal_moves:
        piece = board.piece_at(mv.from_square)
        if piece is None or piece.piece_type == chess.KING:
            continue
        # is the mover pinned to our king?
        b2 = board.copy(stack=False)
        b2.remove_piece_at(mv.from_square)
        if not b2.is_attacked_by(not board.turn, ksq):
            continue  # removing it does not expose the king -> not pinned
        if mv.to_square == _pinner_square(board, mv.from_square, ksq):
            return True
    return False


def _pinner_square(board, sq, ksq):
    """the enemy piece that would attack ksq if `sq` were empty (first slider on the ray, if it is a slider)."""
    b2 = board.copy(stack=False)
    b2.remove_piece_at(sq)
    for att in b2.attackers(not board.turn, ksq):
        p = b2.piece_at(att)
        if p is not None and p.piece_type in (chess.BISHOP, chess.ROOK, chess.QUEEN):
            return att
    return None


def main():
    rf, gf, outf, per = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    pos = [(f, "R") for f in load(rf)] + [(f, "G") for f in load(gf)]
    counts = {c: 0 for c in "ABCDE"}
    picked = {c: [] for c in "ABCDE"}
    for fen, src in pos:
        b = chess.Board()
        try:
            b.set_fen(fen)
        except Exception:  # noqa: BLE001
            continue
        if not b.is_valid():
            continue
        hits = []
        if is_class_a(b):
            hits.append("A")
        okep, _ = ep_exposes_king(b)
        if okep:
            hits.append("B")
        if is_class_c(b):
            hits.append("C")
        if is_class_d(b):
            hits.append("D")
        if is_class_e(b):
            hits.append("E")
        for c in hits:
            counts[c] += 1
            if len(picked[c]) < per:
                picked[c].append((src, fen))
    with open(outf, "w") as f:
        for c in "ABCDE":
            for src, fen in picked[c]:
                f.write(f"{c}\t{src}\t{fen}\n")
    with open(outf + ".counts", "w") as f:
        for c in "ABCDE":
            f.write(f"{c}\tavailable {counts[c]}\tpicked {len(picked[c])}\n")
    print(open(outf + ".counts").read())


if __name__ == "__main__":
    main()
