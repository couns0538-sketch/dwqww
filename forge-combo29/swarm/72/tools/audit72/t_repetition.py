"""Repetition: is the position key FIDE-complete, and is the threshold right?

Uses two independent channels:
  * `build/probe seq` for the engine's own key + is_repetition() verdict.
  * python-chess for the oracle count, via is_repetition(n) -- never a hand
    count of the move list.
"""

import subprocess

import chess

PROBE = "build/probe"


def probe(fen, moves=()):
    args = [PROBE, "seq", fen, *moves]
    out = subprocess.run(args, capture_output=True, text=True, timeout=30)
    if out.returncode != 0:
        raise RuntimeError("probe failed: %s %s" % (out.stdout.strip(), out.stderr.strip()))
    rows = []
    for line in out.stdout.splitlines():
        if not line.startswith(("PLY0", "PLY ")):
            continue
        fields = {}
        head, _, rest = line.partition(' fen="')
        fen_text, _, tail = rest.partition('"')
        for tok in head.split():
            if "=" in tok:
                k, v = tok.split("=", 1)
                fields[k] = v
        for tok in tail.split():
            if "=" in tok:
                k, v = tok.split("=", 1)
                fields[k] = v
        fields["fen"] = fen_text
        rows.append(fields)
    return rows


def oracle_count(fen, moves):
    board = chess.Board(fen)
    for m in moves:
        board.push_uci(m)
    n = 1
    while board.is_repetition(n + 1):
        n += 1
    return n, board


# A rook shuffle that returns to the same position repeatedly.  Uses real
# material so is_insufficient_material() cannot mask the repetition verdict.
BASE = "4k3/8/8/8/8/8/8/1R2K3 w - - 0 1"
CYCLE = ["b1b2", "e8d8", "b2b1", "d8e8"]  # 4 plies, back to start


def build(n_cycles):
    moves = []
    for _ in range(n_cycles):
        moves.extend(CYCLE)
    return moves


def main():
    print("=" * 78)
    print("REPETITION THRESHOLD: 1..5 occurrences")
    print("=" * 78)
    print("%-4s %-6s %-4s %-10s %-12s %s" % ("occ", "plies", "n", "oracle", "engine_rep", "engine_fen_roundtrip"))
    for n_cycles in range(0, 5):
        moves = build(n_cycles)
        rows = probe(BASE, moves)
        last = rows[-1]
        occ, board = oracle_count(BASE, moves)
        ok_fen = last["fen"].split(" ")[0:4] == board.fen().split(" ")[0:4]
        print("%-4d %-6d %-4d %-10d %-12s %s" % (
            occ, len(moves), len(moves), occ, last["repetition"], "ok" if ok_fen else "MISMATCH"))
        assert int(last["key"], 16) != 0

    print()
    print("=" * 78)
    print("CASTLING RIGHTS in key (positions differing ONLY in rights)")
    print("=" * 78)
    pairs = [
        ("4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1", "4k3/8/8/8/8/8/8/R3K2R w - - 0 1", "KQ vs none"),
        ("4k3/8/8/8/8/8/8/R3K2R w K - 0 1", "4k3/8/8/8/8/8/8/R3K2R w Q - 0 1", "K vs Q"),
        ("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", "r3k2r/8/8/8/8/8/8/R3K2R w KQ - 0 1", "lose black rights"),
    ]
    for a, b, label in pairs:
        ba, bb = chess.Board(a), chess.Board(b)
        ka = int(probe(a)[0]["key"], 16)
        kb = int(probe(b)[0]["key"], 16)
        same_placement = ba.board_fen() == bb.board_fen() and ba.turn == bb.turn
        print("%-22s placement_same=%-5s key_same=%-5s  oracle_same_position=%s" % (
            label, same_placement, ka == kb, "n/a (FIDE: different)"))

    print()
    print("=" * 78)
    print("EN PASSANT in key (differing ONLY in ep availability)")
    print("=" * 78)
    ep_cases = [
        # (fen_with_ep, fen_without_ep, label, keys_must_match)
        ("4k3/8/8/8/3pP3/8/8/4K3 b - e3 0 1", "4k3/8/8/8/3pP3/8/8/4K3 b - - 0 1",
         "ep capture legal -> keys MUST differ", False),
        ("4k3/8/8/8/4P3/8/8/4K3 b - e3 0 1", "4k3/8/8/8/4P3/8/8/4K3 b - - 0 1",
         "no capturer -> keys MUST match (9.2.2.1)", True),
        ("k3r3/8/8/3pP3/8/8/8/4K3 w - d6 0 2", "k3r3/8/8/3pP3/8/8/8/4K3 w - - 0 2",
         "ep pseudo-legal but pinned -> keys MUST match", True),
    ]
    ep_fails = []
    for a, b, label, must_match in ep_cases:
        ba, bb = chess.Board(a), chess.Board(b)
        pseudo = [m.uci() for m in ba.generate_pseudo_legal_ep()]
        legal = [m.uci() for m in ba.legal_moves if ba.is_en_passant(m)]
        ka = int(probe(a)[0]["key"], 16)
        kb = int(probe(b)[0]["key"], 16)
        same = ka == kb
        verdict = "OK" if same == must_match else "WRONG"
        if same != must_match:
            ep_fails.append(label)
        print("%-46s key_same=%-5s want=%-5s %-5s pseudo=%s legal=%s" % (
            label, same, must_match, verdict, pseudo or "-", legal or "-"))
    return ep_fails


if __name__ == "__main__":
    main()
