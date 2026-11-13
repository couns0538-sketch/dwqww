#!/usr/bin/env python3
"""Compare Forge move legality with python-chess.

Covers castling, en passant, promotions, checks, pins, and make/unmake.
Builds two probes (king-line fast path on and off) and checks them against
python-chess. Published perft totals are checked separately by legality_probe
selftest. The null-move FEN comparison is the regression for Black's fullmove
clock: the probe round-trips Forge's own FEN, so it cannot see a clock that
is wrong in the same way on both sides.

Usage (from anywhere):
  python3 forge-combo29/tools/legality_oracle.py
"""

import collections
import os
import random
import subprocess
import sys
import tempfile

import chess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INCLUDE = os.path.join(ROOT, "include")
SRC_BOARD = os.path.join(ROOT, "src", "board.cpp")
SRC_BB = os.path.join(ROOT, "src", "bitboard.cpp")
PROBE_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "legality_probe.cpp")

QUIET, CAPTURE, DOUBLE, KCASTLE, QCASTLE, EP, PROMO = 0, 1, 2, 4, 8, 16, 32
PROMO_PIECE = {chess.KNIGHT: 2, chess.BISHOP: 3, chess.ROOK: 4, chess.QUEEN: 5}

PERFT_ROOTS = [
    ("start", chess.STARTING_FEN, 2),
    ("kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 2),
    ("pos3", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 2),
    ("pos4", "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", 2),
    ("pos5", "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", 2),
    ("pos6", "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10", 2),
    ("promo", "n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - - 0 1", 2),
]

# name, fen. Each must be a python-chess valid position.
CASES = [
    ("castle", "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"),
    ("castle-black", "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1"),
    ("castle-in-check", "r3k2r/4r3/8/8/8/8/8/R3K2R w KQkq - 0 1"),
    ("castle-f1-attacked", "r3k2r/8/8/8/8/8/5r2/R3K2R w KQkq - 0 1"),
    ("castle-b1-attacked", "4k3/8/8/8/8/8/b7/R3K2R w KQ - 0 1"),
    ("castle-d1-attacked", "4k3/8/8/8/8/8/3r4/R3K2R w KQ - 0 1"),
    ("castle-g1-attacked", "4k3/8/8/8/8/6r1/8/R3K2R w KQ - 0 1"),
    ("castle-queenside-check", "3k4/8/8/8/8/8/8/R3K2R w KQ - 0 1"),
    ("castle-kingside-quiet", "4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1"),
    ("castle-hfile-blocked", "7k/7p/8/8/8/8/8/4K2R w K - 0 1"),
    ("pin-queen", "4k3/8/8/4r3/8/8/4Q3/4K3 w - - 0 1"),
    ("pin-knight", "4k3/8/8/4r3/8/8/4N3/4K3 w - - 0 1"),
    ("pin-rook", "4k3/8/8/4r3/8/8/4R3/4K3 w - - 0 1"),
    ("pin-pawn", "k7/8/8/8/8/2b5/1P6/K7 w - - 0 1"),
    ("pin-horizontal", "8/8/8/k1r1R2K/8/8/8/8 w - - 0 1"),
    ("ep-legal", "8/8/8/3pP3/8/8/4K3/k7 w - d6 0 1"),
    ("ep-pin-rank", "8/8/8/8/k2Pp2R/8/8/4K3 b - d3 0 1"),
    ("ep-pin-file", "4k3/8/8/8/3Pp3/8/8/4R1K1 b - d3 0 1"),
    ("ep-gives-check", "8/1k6/8/1Pp5/8/8/8/4K3 w - c6 0 1"),
    ("ep-discovered-check", "8/8/8/k2pP2R/8/8/8/4K3 w - d6 0 1"),
    ("ep-both-sides", "8/8/8/8/2pPp3/8/8/k3K3 b - d3 0 1"),
    ("ep-escapes-check", "8/8/8/4k3/3Pp3/8/8/4K3 b - d3 0 1"),
    ("ep-no-capturer", "8/8/8/8/3P4/8/8/k3K3 b - d3 0 1"),
    ("promo-file-check", "8/P7/8/8/8/8/8/k3K3 w - - 0 1"),
    ("promo-queen-check", "7k/4P3/8/8/8/8/8/4K3 w - - 0 1"),
    ("promo-discover", "3nk3/4P3/8/8/8/8/8/4R1K1 w - - 0 1"),
    ("discover-knight", "8/8/7k/8/8/8/3N4/2B1K3 w - - 0 1"),
    ("discover-bishop", "4k3/8/8/8/4B3/8/8/4R1K1 w - - 0 1"),
    ("double-check", "4r1k1/8/8/8/8/8/8/4K2r w - - 0 1"),
    ("capture-rook-promote", "r3k2r/1P6/8/8/8/8/8/R3K2R w KQkq - 0 1"),
    ("stalemate", "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"),
    ("checkmate", "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"),
]

# fen, substring required in Forge's reject reason.
REJECTS = [
    ("4k3/8/8/8/8/8/8/4R1K1 w - - 0 1", "side that moved left its king in check"),
    ("7k/8/8/8/8/8/8/4K2R w K - 0 1", "side that moved left its king in check"),
    ("8/8/8/8/8/8/8/2kK4 w - - 0 1", "kings may not be adjacent"),
    ("P7/8/8/8/8/8/8/k3K3 w - - 0 1", "pawn on promotion rank"),
    ("4k3/8/8/8/8/8/8/R3K1N1 w K - 0 1", "castling right without king and rook"),
    ("r3k2r/8/8/8/8/8/8/R3K2R w KQkqK - 0 1", "duplicate castling right"),
    ("8/8/8/8/8/8/8/k3K3 w - e3 0 1", "en-passant"),
    ("8/8/8/3P4/8/8/8/k3K3 b - d4 0 1", "en-passant"),
    ("8/PPPPPPPP/8/8/8/8/k6P/4K3 w - - 0 1", "impossible piece inventory"),
    ("8/8/8/8/8/8/8/k3K3 w KQkq - 0 1", "castling right without king and rook"),
]

DEEP_PERFT = [
    ("start", chess.STARTING_FEN, 6, 119060324),
    ("kiwipete", PERFT_ROOTS[1][1], 5, 193690690),
    ("pos3", PERFT_ROOTS[2][1], 6, 11030083),
    ("pos4", PERFT_ROOTS[3][1], 5, 15833292),
    ("pos6", PERFT_ROOTS[5][1], 4, 3894594),
]


class Probe:
    def __init__(self, path):
        self.proc = subprocess.Popen(
            [path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1
        )

    def call(self, line):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()
        rows = []
        while True:
            row = self.proc.stdout.readline()
            if row == "":
                raise RuntimeError("probe closed on: " + line)
            row = row.rstrip("\n")
            if row == "END":
                break
            rows.append(row)
        return rows

    def close(self):
        try:
            self.proc.stdin.write("quit\n")
            self.proc.stdin.flush()
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


def compile_probe(path, defines):
    cmd = [
        "g++", "-std=c++20", "-O2", "-DNDEBUG",
        "-I", INCLUDE, "-o", path, PROBE_SRC, SRC_BOARD, SRC_BB,
    ]
    for name, value in defines.items():
        cmd.append(f"-D{name}={value}")
    subprocess.check_call(cmd)


def fen_of(board):
    return board.fen(en_passant="fen")


def parse_audit(rows):
    state = None
    moves = []
    null_fen = None
    fails = []
    summary = None
    for row in rows:
        if row.startswith("FAIL "):
            fails.append(row[5:])
        elif row.startswith("S "):
            parts = row.split()
            field = {}
            it = iter(parts[1:])
            for key in it:
                field[key] = next(it)
            state = field
        elif row.startswith("M "):
            parts = row.split()
            # M uci legal N gives N flags N promo N child <fen...>
            child = " ".join(parts[11:])
            moves.append({
                "uci": parts[1],
                "legal": parts[3] == "1",
                "gives": parts[5] == "1",
                "flags": int(parts[7]),
                "promo": int(parts[9]),
                "child": child,
            })
        elif row.startswith("N "):
            null_fen = None if row == "N -" else row[2:]
        elif row.startswith("SUMMARY "):
            summary = int(row.split()[-1])
    return state, moves, null_fen, fails, summary


def expected_flags(board, move):
    if board.is_castling(move):
        return KCASTLE if board.is_kingside_castling(move) else QCASTLE
    flags = 0
    if move.promotion:
        flags |= PROMO
    if board.is_en_passant(move):
        flags |= EP | CAPTURE
    elif board.is_capture(move):
        flags |= CAPTURE
    elif move.promotion is None and board.piece_type_at(move.from_square) == chess.PAWN and chess.square_distance(move.from_square, move.to_square) == 2:
        flags |= DOUBLE
    return flags


def expected_promo(move):
    if move.promotion is None:
        return 0
    return PROMO_PIECE[move.promotion]


def compare_position(probe, board, label, errors):
    rows = probe.call("fen " + fen_of(board))
    fails = [row[5:] for row in rows if row.startswith("FAIL ")]
    if fails:
        errors.append(label + " setfen fail " + "; ".join(fails))
        return
    accept = [row for row in rows if row.startswith("ACCEPT ") or row.startswith("REJECT ")]
    if not accept or accept[0].startswith("REJECT"):
        reason = accept[0][7:] if accept else "no reply"
        errors.append(label + " rejected valid fen: " + reason + " :: " + fen_of(board))
        return
    got = accept[0][7:]
    if got != fen_of(board):
        errors.append(label + " fen normalized\n  py " + fen_of(board) + "\n  fg " + got)
        return
    state, moves, null_fen, fails, summary = parse_audit(probe.call("audit"))
    if fails or summary:
        errors.append(label + " invariant " + "; ".join(fails) + f" summary {summary}")
    if state is None:
        errors.append(label + " no state line")
        return
    if (state["check"] == "1") != board.is_check():
        errors.append(label + " check flag")
    if (state["mate"] == "1") != board.is_checkmate():
        errors.append(label + " mate flag")
    if (state["stale"] == "1") != board.is_stalemate():
        errors.append(label + " stalemate flag")
    has_move = any(True for _ in board.legal_moves)
    if (state["has"] == "1") != has_move:
        errors.append(label + " has_legal_move")
    ep = -1 if board.ep_square is None else board.ep_square
    if int(state["ep"]) != ep:
        errors.append(label + f" ep {state['ep']} != {ep}")
    if int(state["half"]) != board.halfmove_clock or int(state["full"]) != board.fullmove_number:
        errors.append(label + " clocks")
    py_checkers = sorted(chess.square_name(sq) for sq in board.checkers())
    fg_checkers = [] if state["checkers"] == "-" else sorted(state["checkers"].split(","))
    if fg_checkers != py_checkers:
        errors.append(label + f" checkers {fg_checkers} != {py_checkers}")

    py_moves = {move.uci(): move for move in board.legal_moves}
    fg_legal = {}
    for item in moves:
        uci = item["uci"]
        try:
            parsed = chess.Move.from_uci(uci)
        except ValueError:
            errors.append(label + " bad uci " + uci)
            continue
        pseudo = board.is_pseudo_legal(parsed)
        if not pseudo:
            errors.append(label + " forge pseudo not python pseudo " + uci)
            continue
        if item["legal"] != board.is_legal(parsed):
            errors.append(label + " legality " + uci)
        if item["legal"]:
            fg_legal[uci] = item
            if item["gives"] != board.gives_check(parsed):
                errors.append(label + " gives_check " + uci + f" forge {item['gives']}")
            if item["flags"] != expected_flags(board, parsed) or item["promo"] != expected_promo(parsed):
                errors.append(
                    label + f" flags {uci} forge {item['flags']}/{item['promo']} "
                    f"expect {expected_flags(board, parsed)}/{expected_promo(parsed)}"
                )
            pushed = board.copy(stack=False)
            pushed.push(parsed)
            if item["child"] != fen_of(pushed):
                errors.append(label + " child " + uci + "\n  py " + fen_of(pushed) + "\n  fg " + item["child"])
            if pushed.is_check() != item["gives"]:
                errors.append(label + " child check " + uci)
    if set(fg_legal) != set(py_moves):
        missing = sorted(set(py_moves) - set(fg_legal))
        extra = sorted(set(fg_legal) - set(py_moves))
        errors.append(label + f" move set missing {missing} extra {extra}")

    if not board.is_check():
        nulled = board.copy(stack=False)
        nulled.push(chess.Move.null())
        if null_fen != fen_of(nulled):
            errors.append(label + " null\n  py " + fen_of(nulled) + "\n  fg " + str(null_fen))
    elif null_fen is not None:
        errors.append(label + " null move while in check")


def positions():
    seen = set()
    ordered = []

    def add(board, label):
        fen = fen_of(board)
        if fen in seen:
            return
        if not board.is_valid():
            raise SystemExit("corpus built an invalid fen " + label + " " + fen)
        seen.add(fen)
        ordered.append((label, board.copy(stack=False)))

    for name, fen in CASES:
        add(chess.Board(fen), name)
    for name, fen, depth in PERFT_ROOTS:
        root = chess.Board(fen)
        add(root, name)
        stack = [(root, 0)]
        while stack:
            board, ply = stack.pop()
            if ply == depth:
                continue
            for move in board.legal_moves:
                board.push(move)
                add(board, f"{name}-d{ply + 1}-{move.uci()}")
                if ply + 1 < depth:
                    stack.append((board.copy(stack=True), ply + 1))
                board.pop()
    rng = random.Random(20261113)
    starts = [("start", chess.STARTING_FEN, 40, 12), ("kiwi", PERFT_ROOTS[1][1], 25, 6), ("promo", PERFT_ROOTS[6][1], 20, 6)]
    for name, fen, plies, games in starts:
        for game in range(games):
            board = chess.Board(fen)
            add(board, f"{name}-g{game}-0")
            for ply in range(plies):
                legal = list(board.legal_moves)
                if not legal:
                    break
                board.push(rng.choice(legal))
                add(board, f"{name}-g{game}-{ply + 1}")
    return ordered


def check_rejects(probe, errors):
    for fen, needle in REJECTS:
        rows = probe.call("fen " + fen)
        reject = [row for row in rows if row.startswith("REJECT ")]
        accept = [row for row in rows if row.startswith("ACCEPT ")]
        if accept or not reject:
            errors.append("expected reject " + fen + " got " + " | ".join(rows))
            continue
        if needle not in reject[0]:
            errors.append("reject reason " + reject[0] + " missing " + needle)


def deep_perft(probe, errors):
    for name, fen, depth, expect in DEEP_PERFT:
        probe.call("fen " + fen)
        rows = probe.call(f"perft {depth}")
        nodes = None
        for row in rows:
            if row.startswith("NODES "):
                nodes = int(row.split()[1])
            if row.startswith("FAIL "):
                errors.append(row)
        if nodes != expect:
            errors.append(f"deep perft {name} d{depth} {nodes} != {expect}")
        else:
            print(f"perft {name} d{depth} {nodes}", file=sys.stderr)


def main():
    # A private directory, mode 0700. A fixed name under /tmp can be replaced
    # before the compiled probe is executed.
    with tempfile.TemporaryDirectory(prefix="forge-legality-") as work:
        fast = os.path.join(work, "legality_kl1")
        slow = os.path.join(work, "legality_kl0")
        compile_probe(fast, {
            "FORGE_SPD_NO_ZERO_MOVELISTS": 2,
            "FORGE_SPD_PREFETCH_EARLY": 1,
            "FORGE_SPD_KING_LINES": 1,
        })
        compile_probe(slow, {
            "FORGE_SPD_NO_ZERO_MOVELISTS": 0,
            "FORGE_SPD_PREFETCH_EARLY": 0,
            "FORGE_SPD_KING_LINES": 0,
        })
        corpus = positions()
        print(f"positions {len(corpus)}", file=sys.stderr)
        fast_p = None
        slow_p = None
        errors = []
        kinds = collections.Counter()
        try:
            fast_p = Probe(fast)
            slow_p = Probe(slow)
            check_rejects(fast_p, errors)
            for index, (label, board) in enumerate(corpus):
                if index % 250 == 0:
                    print(f"compare {index}/{len(corpus)} {label}", file=sys.stderr)
                before = len(errors)
                compare_position(fast_p, board, "fast " + label, errors)
                compare_position(slow_p, board, "slow " + label, errors)
                if len(errors) == before:
                    kinds["ok"] += 1
                else:
                    kinds["bad"] += 1
            if not errors:
                deep_perft(fast_p, errors)
                rows = fast_p.call("selftest")
                text = "\n".join(rows)
                if "FAIL " in text or "ok 0" in text:
                    errors.append("selftest\n" + "\n".join(row for row in rows if row.startswith("FAIL") or row.startswith("PERFT") or row.startswith("TOTAL")))
        finally:
            if fast_p is not None:
                fast_p.close()
            if slow_p is not None:
                slow_p.close()
    print(f"ok {kinds['ok']} bad {kinds['bad']} errors {len(errors)}")
    for error in errors[:40]:
        print(error)
        print("---")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
