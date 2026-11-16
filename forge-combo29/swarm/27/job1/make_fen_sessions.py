#!/usr/bin/env python3
"""make_fen_sessions.py - builds the UCI session files for the FEN stress used by job 1.

Two input sets, both written as text into the job folder first:
  sets/planted/  : one session with the control FEN that trips the PLANTED fault in the scratch
                   copy only (proof that the runner counts a sanitizer line).
  sets/real/     : the real stress. Every .uci session is
                     uci / isready / position fen <mutated FEN> / isready /
                     go depth <1..4> / <wait for bestmove via the engine's own output> / quit
                   The driver cannot "wait"; the session simply is the whole stdin and the engine
                   answers bestmove before it reads quit. To keep the pipe open until bestmove
                   the engine is fed the text with a trailing quit, and the engine reads it after
                   bestmove because bestmove is printed by the search thread at the end.
"""
import argparse
import json
import os
import random
import sys

BASE_FENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "4k3/8/8/8/8/8/8/4K3 w - - 0 1",
    "2K2r2/4P3/8/8/8/8/8/3k4 w - - 0 1",
]
FILES = "abcdefgh"
PIECES = "pnbrqkPNBRQK"


def mutate(fen: str, rng: random.Random):
    """One random mutation; returns (mutated_fen, description)."""
    fields = fen.split(" ")
    kind = rng.choice(["replace", "insert", "delete", "swap_fields", "drop_field"])
    if kind == "replace":
        idx = rng.randrange(len(fen))
        newc = rng.choice("12345678pnbrqkPNBRQKw-" + FILES)
        return fen[:idx] + newc + fen[idx + 1:], "replace pos %d '%s'->'%s'" % (idx, fen[idx], newc)
    if kind == "insert":
        idx = rng.randrange(len(fen) + 1)
        newc = rng.choice("12345678pnbrqkPNBRQK" + FILES)
        return fen[:idx] + newc + fen[idx:], "insert pos %d '%s'" % (idx, newc)
    if kind == "delete" and len(fen) > 1:
        idx = rng.randrange(len(fen))
        return fen[:idx] + fen[idx + 1:], "delete pos %d '%s'" % (idx, fen[idx])
    if kind == "swap_fields" and len(fields) >= 2:
        i, j = rng.sample(range(len(fields)), 2)
        fields[i], fields[j] = fields[j], fields[i]
        return " ".join(fields), "swap fields %d<->%d" % (i, j)
    # drop a field
    if len(fields) > 1:
        i = rng.randrange(len(fields))
        dropped = fields.pop(i)
        return " ".join(fields), "drop field %d ('%s')" % (i, dropped)
    return fen + " 9", "append junk field"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--seed", type=int, default=2701)
    ap.add_argument("--count", type=int, default=600)
    ap.add_argument("--per-session", type=int, default=100)
    ap.add_argument("--planted-only", action="store_true")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    real_dir = os.path.join(args.outdir, "real")
    plant_dir = os.path.join(args.outdir, "planted")
    os.makedirs(real_dir, exist_ok=True)
    os.makedirs(plant_dir, exist_ok=True)

    if not args.planted_only:
        rows = []
        for i in range(args.count):
            fen = rng.choice(BASE_FENS)
            mfen, desc = mutate(fen, rng)
            rows.append({"i": i, "base": fen, "mutated": mfen, "mutation": desc})
        with open(os.path.join(args.outdir, "mutations.jsonl"), "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        sess = 0
        for start in range(0, len(rows), args.per_session):
            chunk = rows[start:start + args.per_session]
            lines = ["uci", "isready"]
            for r in chunk:
                depth = rng.randint(1, 4)
                lines.append("position fen " + r["mutated"])
                lines.append("isready")
                lines.append("go depth %d" % depth)
            lines.append("quit")
            with open(os.path.join(real_dir, "sess_%03d.uci" % sess), "w") as f:
                f.write("\n".join(lines) + "\n")
            sess += 1
        print("wrote %d mutations in %d sessions to %s" % (len(rows), sess, real_dir))

    # planted proof session: a FEN starting with the planted trigger prefix
    trigger = "8/8/8/8/8/8/8/8 w - - 0 1"
    with open(os.path.join(plant_dir, "planted_trigger.uci"), "w") as f:
        f.write("uci\nisready\nposition fen %s\nisready\ngo depth 1\nquit\n" % trigger)
    # control: same shape of session, FEN that does not carry the trigger prefix
    with open(os.path.join(plant_dir, "planted_control.uci"), "w") as f:
        f.write("uci\nisready\nposition fen 4k3/8/8/8/8/8/8/4K3 w - - 0 1\nisready\ngo depth 1\nquit\n")
    print("wrote planted sessions to %s" % plant_dir)


if __name__ == "__main__":
    sys.exit(main())
