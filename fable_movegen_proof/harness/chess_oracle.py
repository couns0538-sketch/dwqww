"""chess_oracle.py - a small, slow, independent rules oracle (own code, standard library only).

It shares nothing with the engine under test. It is used to check that every edge-suite entry really has the
property its category claims, and to give a third opinion on the legal-move SET and the checkers of the legal
entries (it says nothing about move ORDER, which is the engine's own convention).
Legality is decided the plain way: make the move on a copy and look whether the mover's king is attacked.

Validated by perft counts published for the standard positions (see selfcheck()).
Squares: a1 = 0, b1 = 1, ... h8 = 63, as in the engine.
"""
import sys

FILES = "abcdefgh"
KNIGHT = ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2))
KING = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))
ORTHO = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAG = ((1, 1), (1, -1), (-1, 1), (-1, -1))
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def sq(name):
    return FILES.index(name[0]) + 8 * (int(name[1]) - 1)


def name(s):
    return FILES[s & 7] + str((s >> 3) + 1)


class Pos:
    __slots__ = ("b", "side", "castle", "ep", "half", "full")

    def copy(self):
        p = Pos()
        p.b, p.side, p.castle, p.ep, p.half, p.full = list(self.b), self.side, self.castle, self.ep, self.half, self.full
        return p


def parse_fen(fen):
    parts = fen.split()
    if len(parts) != 6:
        raise ValueError("FEN needs six fields")
    rows = parts[0].split("/")
    if len(rows) != 8:
        raise ValueError("FEN needs eight ranks")
    p = Pos()
    p.b = ["."] * 64
    for r, row in enumerate(rows):
        f = 0
        for ch in row:
            if ch.isdigit():
                f += int(ch)
            else:
                if ch not in "PNBRQKpnbrqk" or f > 7:
                    raise ValueError("bad placement")
                p.b[(7 - r) * 8 + f] = ch
                f += 1
        if f != 8:
            raise ValueError("bad rank length")
    if parts[1] not in ("w", "b"):
        raise ValueError("bad side")
    p.side = parts[1]
    p.castle = "" if parts[2] == "-" else parts[2]
    p.ep = -1 if parts[3] == "-" else sq(parts[3])
    p.half, p.full = int(parts[4]), int(parts[5])
    return p


def fen(p):
    rows = []
    for r in range(7, -1, -1):
        row, gap = "", 0
        for f in range(8):
            ch = p.b[r * 8 + f]
            if ch == ".":
                gap += 1
            else:
                row += (str(gap) if gap else "") + ch
                gap = 0
        rows.append(row + (str(gap) if gap else ""))
    castle = "".join(c for c in "KQkq" if c in p.castle) or "-"
    return f"{'/'.join(rows)} {p.side} {castle} {name(p.ep) if p.ep >= 0 else '-'} {p.half} {p.full}"


def white(ch):
    return ch.isupper()


def other(side):
    return "b" if side == "w" else "w"


def own(ch, side):
    return ch != "." and (ch.isupper() == (side == "w"))


def attackers(b, s, by):
    """Squares of the pieces of colour `by` that attack square s."""
    f, r = s & 7, s >> 3
    out = []
    pawn, knight, bishop, rook, queen, king = ("P", "N", "B", "R", "Q", "K") if by == "w" else ("p", "n", "b", "r", "q", "k")
    pr = r - 1 if by == "w" else r + 1          # a white pawn attacks upward, so it stands one rank below
    if 0 <= pr <= 7:
        for pf in (f - 1, f + 1):
            if 0 <= pf <= 7 and b[pr * 8 + pf] == pawn:
                out.append(pr * 8 + pf)
    for df, dr in KNIGHT:
        nf, nr = f + df, r + dr
        if 0 <= nf <= 7 and 0 <= nr <= 7 and b[nr * 8 + nf] == knight:
            out.append(nr * 8 + nf)
    for df, dr in KING:
        nf, nr = f + df, r + dr
        if 0 <= nf <= 7 and 0 <= nr <= 7 and b[nr * 8 + nf] == king:
            out.append(nr * 8 + nf)
    for dirs, slider in ((ORTHO, rook), (DIAG, bishop)):
        for df, dr in dirs:
            nf, nr = f + df, r + dr
            while 0 <= nf <= 7 and 0 <= nr <= 7:
                ch = b[nr * 8 + nf]
                if ch != ".":
                    if ch == slider or ch == queen:
                        out.append(nr * 8 + nf)
                    break
                nf, nr = nf + df, nr + dr
    return out


def king_square(b, side):
    return b.index("K" if side == "w" else "k")


def checkers(p):
    return sorted(attackers(p.b, king_square(p.b, p.side), other(p.side)))


def pseudo(p):
    """Pseudo-legal moves (from, to, promotion letter or '', kind). Castling is generated only when it is fully
    legal (rights, empty path, king not in check, king's squares not attacked)."""
    b, side = p.b, p.side
    moves = []
    up = 1 if side == "w" else -1
    start_rank, promo_rank = (1, 7) if side == "w" else (6, 0)
    for s in range(64):
        ch = b[s]
        if not own(ch, side):
            continue
        f, r = s & 7, s >> 3
        t = ch.upper()
        if t == "P":
            nr = r + up
            if 0 <= nr <= 7:
                to = nr * 8 + f
                if b[to] == ".":
                    if nr == promo_rank:
                        moves += [(s, to, x, "") for x in "qrbn"]
                    else:
                        moves.append((s, to, "", ""))
                        if r == start_rank and b[(r + 2 * up) * 8 + f] == ".":
                            moves.append((s, (r + 2 * up) * 8 + f, "", "double"))
                for nf in (f - 1, f + 1):
                    if not 0 <= nf <= 7:
                        continue
                    to = nr * 8 + nf
                    if b[to] != "." and not own(b[to], side):
                        if nr == promo_rank:
                            moves += [(s, to, x, "") for x in "qrbn"]
                        else:
                            moves.append((s, to, "", ""))
                    elif to == p.ep and b[to] == ".":
                        moves.append((s, to, "", "ep"))
        elif t in "NK":
            for df, dr in (KNIGHT if t == "N" else KING):
                nf, nr = f + df, r + dr
                if 0 <= nf <= 7 and 0 <= nr <= 7 and not own(b[nr * 8 + nf], side):
                    moves.append((s, nr * 8 + nf, "", ""))
        else:
            dirs = ORTHO if t == "R" else DIAG if t == "B" else ORTHO + DIAG
            for df, dr in dirs:
                nf, nr = f + df, r + dr
                while 0 <= nf <= 7 and 0 <= nr <= 7:
                    to = nr * 8 + nf
                    if own(b[to], side):
                        break
                    moves.append((s, to, "", ""))
                    if b[to] != ".":
                        break
                    nf, nr = nf + df, nr + dr
    # castling
    home = 4 if side == "w" else 60
    k, rk = ("K", "R") if side == "w" else ("k", "r")
    ks, qs = ("K", "Q") if side == "w" else ("k", "q")
    opp = other(side)
    if b[home] == k and not attackers(b, home, opp):
        if ks in p.castle and b[home + 3] == rk and b[home + 1] == "." and b[home + 2] == "." \
                and not attackers(b, home + 1, opp) and not attackers(b, home + 2, opp):
            moves.append((home, home + 2, "", "castle"))
        if qs in p.castle and b[home - 4] == rk and b[home - 1] == "." and b[home - 2] == "." and b[home - 3] == "." \
                and not attackers(b, home - 1, opp) and not attackers(b, home - 2, opp):
            moves.append((home, home - 2, "", "castle"))
    return moves


def make(p, m):
    s, to, promo, kind = m
    q = p.copy()
    b = q.b
    ch = b[s]
    captured = b[to]
    b[to] = ch
    b[s] = "."
    up = 8 if p.side == "w" else -8
    if kind == "ep":
        b[to - up] = "."
    if promo:
        b[to] = promo.upper() if p.side == "w" else promo
    if kind == "castle":
        if to > s:
            b[to - 1], b[to + 1] = b[to + 1], "."
        else:
            b[to + 1], b[to - 2] = b[to - 2], "."
    rights = q.castle
    for square, lost in ((4, "KQ"), (0, "Q"), (7, "K"), (60, "kq"), (56, "q"), (63, "k")):
        if s == square or to == square:
            for c in lost:
                rights = rights.replace(c, "")
    q.castle = rights
    q.ep = to - up if kind == "double" else -1
    q.half = 0 if ch.upper() == "P" or captured != "." else p.half + 1
    q.full = p.full + (1 if p.side == "b" else 0)
    q.side = other(p.side)
    return q


def is_legal(p, m):
    q = make(p, m)
    return not attackers(q.b, king_square(q.b, p.side), q.side)


def legal(p):
    return [m for m in pseudo(p) if is_legal(p, m)]


def pseudo_all(p):
    """Like pseudo(), plus castling moves whose only defect is an attacked square (for 'through / into attack')."""
    return pseudo(p)


def uci(m):
    return name(m[0]) + name(m[1]) + m[2]


def find(p, text, moves=None):
    for m in (moves if moves is not None else pseudo(p)):
        if uci(m) == text:
            return m
    return None


def perft(p, depth):
    if depth == 0:
        return 1
    ms = legal(p)
    if depth == 1:
        return len(ms)
    return sum(perft(make(p, m), depth - 1) for m in ms)


def static_problem(p):
    """'' when the position passes the static validity checks, else the reason."""
    if p.b.count("K") != 1 or p.b.count("k") != 1:
        return "each side needs exactly one king"
    if any(p.b[i] in "Pp" for i in list(range(8)) + list(range(56, 64))):
        return "pawn on the first or last rank"
    wk, bk = king_square(p.b, "w"), king_square(p.b, "b")
    if abs((wk & 7) - (bk & 7)) <= 1 and abs((wk >> 3) - (bk >> 3)) <= 1:
        return "adjacent kings"
    if attackers(p.b, king_square(p.b, other(p.side)), p.side):
        return "the side that is not to move is in check"
    return ""


# ---------------------------------------------------------------- FEN transforms for the suite
def colour_mirror(f):
    """Swap the colours and flip the board top to bottom: the same position seen from the other side."""
    board, side, castle, ep, half, full = f.split()
    rows = [row.swapcase() for row in reversed(board.split("/"))]
    castle2 = "".join(c for c in "KQkq" if c in castle.swapcase()) or "-"
    ep2 = "-" if ep == "-" else ep[0] + ("6" if ep[1] == "3" else "3")
    return f"{'/'.join(rows)} {'b' if side == 'w' else 'w'} {castle2} {ep2} {half} {full}"


def file_mirror(f):
    """Swap the a-side and the h-side. Only for positions without castling rights (returns None otherwise)."""
    board, side, castle, ep, half, full = f.split()
    if castle != "-":
        return None
    rows = []
    for row in board.split("/"):
        cells = "".join("." * int(ch) if ch.isdigit() else ch for ch in row)[::-1]
        out, gap = "", 0
        for ch in cells:
            if ch == ".":
                gap += 1
            else:
                out += (str(gap) if gap else "") + ch
                gap = 0
        rows.append(out + (str(gap) if gap else ""))
    ep2 = "-" if ep == "-" else FILES[7 - FILES.index(ep[0])] + ep[1]
    return f"{'/'.join(rows)} {side} - {ep2} {half} {full}"


# ---------------------------------------------------------------- predicates of the suite
PIECE = {"P": "P", "N": "N", "B": "B", "R": "R", "Q": "Q", "K": "K"}


def after(p, text):
    m = find(p, text, legal(p))
    return (m, make(p, m)) if m else (None, None)


def holds(p, atom):
    """One predicate atom on a position. Unknown atoms raise."""
    key, _, val = atom.partition("=")
    ms = legal(p)
    names = [uci(m) for m in ms]
    ck = checkers(p)
    if key == "checkers":
        return len(ck) == int(val)
    if key == "checker":
        return "".join(sorted(p.b[s].upper() for s in ck)) == "".join(sorted(val))
    if key == "legal":
        return len(ms) == int(val)
    if atom.startswith("legal>="):
        return len(ms) >= int(atom[7:])
    if key == "has":
        return val in names
    if key == "no":
        return val not in names
    if key == "pseudo":
        return any(uci(m) == val for m in pseudo(p))
    if key == "mate":
        return not ms and bool(ck)
    if key == "stalemate":
        return not ms and not ck
    if key in ("gives_check", "no_check", "discovered", "double_after"):
        m, q = after(p, val)
        if m is None:
            return False
        c2 = checkers(q)
        if key == "gives_check":
            return bool(c2)
        if key == "no_check":
            return not c2
        if key == "discovered":
            return any(s != m[1] for s in c2)
        return len(c2) >= 2
    if key == "ep_legal":
        return any(m[3] == "ep" for m in ms)
    if key == "ep_illegal":
        return any(m[3] == "ep" for m in pseudo(p)) and not any(m[3] == "ep" for m in ms)
    if key == "promos":
        return all(val + x in names for x in "qrbn")
    if key in ("castle", "nocastle"):
        home = "e1" if p.side == "w" else "e8"
        to = ("g" if val == "K" else "c") + home[1]
        right = (val if p.side == "w" else val.lower()) in p.castle
        return (home + to in names) if key == "castle" else (right and home + to not in names)
    raise ValueError(f"unknown predicate atom {atom}")


def check_predicate(fen_text, predicate):
    """(all atoms hold, the atoms that fail)."""
    p = parse_fen(fen_text)
    failed = [a for a in predicate.split(";") if a and not holds(p, a)]
    return not failed, failed


def selfcheck():
    """Perft counts published for the standard positions (Chess Programming Wiki, 'Perft Results')."""
    table = [
        ("startpos", START, [20, 400, 8902]),
        ("kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", [48, 2039, 97862]),
        ("position3", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", [14, 191, 2812, 43238]),
        ("position4", "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", [6, 264, 9467]),
        ("position5", "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", [44, 1486, 62379]),
        ("position6", "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10", [46, 2079, 89890]),
    ]
    good = True
    for label, f, want in table:
        got = [perft(parse_fen(f), d + 1) for d in range(len(want))]
        ok = got == want
        good = good and ok
        print(f"{'PASS' if ok else 'FAIL'} oracle perft {label}: {got} (published {want})", flush=True)
    for f in (START, table[1][1], "8/8/8/2k5/3Pp3/8/8/4K3 b - d3 0 1"):
        ok = fen(parse_fen(f)) == f and colour_mirror(colour_mirror(f)) == f
        good = good and ok
        print(f"{'PASS' if ok else 'FAIL'} oracle FEN round trip and double colour mirror: {f}")
    # a mirrored position has the mirrored number of moves at every depth
    k = table[1][1]
    ok = [perft(parse_fen(colour_mirror(k)), d) for d in (1, 2)] == [48, 2039]
    good = good and ok
    print(f"{'PASS' if ok else 'FAIL'} oracle perft of the colour-mirrored kiwipete: 48, 2039")
    # the predicate checker must be able to say no: wrong labels on known positions are refused
    bare = "4k3/8/8/8/8/8/8/4K3 w - - 0 1"
    wrong = [(bare, "checkers=1"), (bare, "mate"), (bare, "stalemate"), (bare, "legal=6"), (bare, "has=e1e3"), (bare, "ep_legal"),
             (bare, "castle=K"), (bare, "nocastle=K"), (START, "no=e2e4"), (START, "gives_check=e2e4"), (START, "promos=a7a8"),
             (k, "legal=47"), ("8/8/8/K2pP2r/8/8/8/7k w - d6 0 1", "ep_legal"), ("4k3/8/8/8/4N3/8/8/4R1K1 w - - 0 1", "no_check=e4d6"),
             ("4r2k/8/8/8/8/3n4/4Q3/4K3 w - - 0 1", "has=e2d3")]
    for f, pred in wrong:
        ok, _ = check_predicate(f, pred)
        good = good and not ok
        print(f"{'PASS' if not ok else 'FAIL'} oracle refuses the wrong label '{pred}' on {f}")
    right = [(bare, "checkers=0;legal=5"), (START, "legal=20;has=e2e4;no_check=e2e4"), ("8/8/8/K2pP2r/8/8/8/7k w - d6 0 1", "ep_illegal")]
    for f, pred in right:
        ok, failed = check_predicate(f, pred)
        good = good and ok
        print(f"{'PASS' if ok else 'FAIL'} oracle accepts the right label '{pred}' on {f} {failed if failed else ''}")
    print("ORACLE " + ("PASS" if good else "FAIL"))
    return 0 if good else 3


if __name__ == "__main__":
    sys.exit(selfcheck())
