#!/usr/bin/env python3
"""Job 1 part B0 controls.

(i)  print 20 cases with the python-chess checks that accepted them
(ii) a random legal move at C: how often it picks k'
(iii) planted faults must be rejected
"""

import json
import random
import sys

import chess

CASES = sys.argv[1]
FAULTS = sys.argv[2]
OUTDIR = sys.argv[3]

cases = json.load(open(CASES))["cases"]
faults = json.load(open(FAULTS))["cases"]

# ---------------------------------------------------------------- (i) 20 cases
with open(OUTDIR + "/B0i_20cases.txt", "w") as f:
    for c in cases[:20]:
        b = chess.Board(c["s0"])
        f.write(f"S0 {c['s0']}\n  moves {' '.join(c['moves'])}\n")
        for i, u in enumerate(c["moves"]):
            ok = chess.Move.from_uci(u) in b.legal_moves
            f.write(f"  ply {i+1} {u} legal={ok} turn={b.turn}")
            b.push_uci(u)
            f.write(f" -> after: checkmate={b.is_checkmate()} stalemate={b.is_stalemate()} "
                    f"halfmove={b.halfmove_clock}\n")
            if not ok:
                f.write("  !! ILLEGAL\n")
        f.write(f"  C: black to move={b.turn == chess.BLACK} in_check={b.is_check()} "
                f"legal_black_moves={b.legal_moves.count()}\n")
        reps = [m.uci() for m in b.legal_moves
                if (lambda a: (a.push(m), a.is_repetition(3))[1])(b.copy())]
        f.write(f"  third-repetition moves at C: {reps} (want {c['rep_move']})\n")
        others = []
        for m in b.legal_moves:
            a = b.copy()
            a.push(m)
            if not a.is_repetition(3):
                others.append((m.uci(), a.is_stalemate(), a.is_insufficient_material(),
                               a.is_checkmate(), a.is_game_over(claim_draw=True)))
        f.write(f"  other moves (uci, stalemate, insufficient, checkmate, game_over): {others}\n\n")

# ------------------------------------------------------ (ii) random player at C
rng = random.Random(4242)
hits, trials, expected = 0, 0, 0.0
for c in cases:
    b = chess.Board(c["s0"])
    for u in c["moves"]:
        b.push_uci(u)
    legal = list(b.legal_moves)
    expected += 1.0 / len(legal)
    for _ in range(20):
        trials += 1
        if rng.choice(legal).uci() == c["rep_move"]:
            hits += 1
with open(OUTDIR + "/B0ii_random_player.txt", "w") as f:
    f.write(f"cases {len(cases)}, 20 random picks each, trials {trials}, hits {hits}, "
            f"rate {hits/trials:.4f}\n")
    f.write(f"mean of 1/(legal moves at C) over the cases = {expected/len(cases):.4f}\n")
    f.write(f"expected hits for these {trials} draws = {20*expected:.1f} "
            f"(rate {20*expected/trials:.4f})\n")
    hist = {}
    for c in cases:
        hist[c["n_black_moves_at_c"]] = hist.get(c["n_black_moves_at_c"], 0) + 1
    f.write(f"distribution of legal black moves at C: {sorted(hist.items())}\n")

# ------------------------------------------------------ (iii) planted faults
# The generator refuses to emit a fault its checker accepts (it exits 2), so
# reaching this point with 500 faults means all 500 were rejected.  Re-run the
# checker here on the stored fault lists to show it in this file too.
sys.path.insert(0, "/agent/repos/dwqww/forge-combo29/tests_deepseek2_job1")
import gen_cases  # noqa: E402

rej1 = rej2 = 0
examples = []
for fcase in faults:
    s0 = chess.Board(fcase["s0"])
    m1 = [chess.Move.from_uci(u) for u in fcase["fault1_moves"]]
    ok1, r1, _ = gen_cases.check_case(s0, m1, need_len=False)
    if not ok1:
        rej1 += 1
    m2 = [chess.Move.from_uci(u) for u in fcase["fault2_moves"]] if fcase["fault2_moves"] else []
    if m2:
        ok2, r2, _ = gen_cases.check_case(s0, m2, need_len=False)
        if not ok2:
            rej2 += 1
    if len(examples) < 3:
        examples.append((fcase["s0"], fcase["fault1_moves"], r1,
                         fcase["fault2_moves"], fcase["fault2_reasons"]))
with open(OUTDIR + "/B0iii_planted_faults.txt", "w") as f:
    f.write(f"fault1 (one cycle less, 3 plies): {rej1}/{len(faults)} rejected\n")
    f.write(f"fault2 (full list + a legal non-repeating black move at C): {rej2}/"
            f"{sum(1 for x in faults if x['fault2_moves'])} rejected "
            f"({sum(1 for x in faults if not x['fault2_moves'])} cases had no alternative black move)\n")
    for e in examples:
        f.write("\nS0 " + e[0] + "\n  fault1 " + " ".join(e[1]) + "\n  reasons " + str(e[2]) + "\n")
        f.write("  fault2 " + " ".join(e[3]) + "\n  reasons " + str(e[4]) + "\n")
print("B0 written")
