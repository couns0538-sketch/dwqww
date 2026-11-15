"""Part A of the Fable/Opus checks: the engine's move generator against known answers and against python-chess.
(Opus session, 2026-11-15; from Fable's job text HELPER_JOB2_glmflash.txt, part A.)

A1  Six positions with published perft counts (the start position, "Kiwipete", and positions 3 to 6 of the
    chessprogramming wiki), two depths each. The engine's answer must equal the published count.
A2  1,000 positions: 500 with seed 20261115 and 8 to 60 plies (the trial set), 500 with seed 20261116 and 20 to 120
    plies; topped up from seed 20261119 on until each kind (a legal en passant capture, a legal promotion, a legal
    castling move, side to move in check) occurs at least 20 times. For every position the engine's  go perft 3
    (total AND count per first move) is compared with python-chess; depth 4 on the first 100 if time allows.
Self-test: the comparison is run once on a deliberately altered copy of a real engine answer and must report the
difference (so a clean result means the comparison works).

    python perft_suite.py <engine exe> <results dir> [minutes for depth 4, default 25]
Exit code: 0 = no mismatch and every known answer right; 1 = a finding (see summary.txt); 2 = the check itself failed.
"""
from __future__ import annotations

import json
import os
import sys
import time

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import positions as pos  # noqa: E402
from uci import Engine, cut  # noqa: E402

KNOWN = [  # FEN, [(depth, published count), ...]
    ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", [(5, 4865609), (6, 119060324)]),
    ("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", [(4, 4085603), (5, 193690690)]),
    ("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", [(5, 674624), (6, 11030083)]),
    ("r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", [(4, 422333), (5, 15833292)]),
    ("rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", [(4, 2103487), (5, 89941194)]),
    ("r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10", [(4, 3894594), (5, 164075551)]),
]
KINDS = ("en_passant", "promotion", "castling", "check")
# FORGE_CI_SCALE (default 1) shrinks the position counts, for a quick trial of the script itself.
SCALE = float(os.environ.get("FORGE_CI_SCALE", "1"))


def n(x: int) -> int:
    return max(1, round(x * SCALE))


def py_perft(board: chess.Board, depth: int) -> int:
    if depth <= 0:
        return 1
    if depth == 1:
        return board.legal_moves.count()
    n = 0
    for m in board.legal_moves:
        board.push(m)
        n += py_perft(board, depth - 1)
        board.pop()
    return n


def py_divide(fen: str, depth: int) -> dict[str, int]:
    b = chess.Board(fen)
    out = {}
    for m in list(b.legal_moves):
        b.push(m)
        out[m.uci()] = py_perft(b, depth - 1)
        b.pop()
    return out


def engine_perft(eng: Engine, fen: str, depth: int, timeout: float) -> tuple[dict[str, int] | None, int | None, list[str]]:
    """go perft <depth>: lines 'move: count' then 'nodes <n>'. Returns (per move, total, raw lines)."""
    eng.send(f"position fen {fen}")
    eng.send(f"go perft {depth}")
    ok, lines = eng.wait_for("nodes", timeout)
    if not ok:
        return None, None, lines
    split: dict[str, int] = {}
    for ln in lines:
        if ":" in ln and not ln.startswith("info"):
            mv, _, cnt = ln.partition(":")
            try:
                split[mv.strip()] = int(cnt.strip())
            except ValueError:
                pass
    try:
        total = int(lines[-1].split()[1])
    except (IndexError, ValueError):
        total = None
    return split, total, lines


def compare(fen: str, depth: int, eng_split: dict[str, int] | None, eng_total: int | None,
            ref: dict[str, int]) -> list[str]:
    """Differences between the engine's answer and python-chess's, as lines; empty when they agree."""
    if eng_split is None or eng_total is None:
        return [f"{fen} | depth {depth} | the engine gave no answer"]
    out = []
    ref_total = sum(ref.values())
    if eng_total != ref_total:
        out.append(f"{fen} | depth {depth} | total: engine {eng_total}, python-chess {ref_total}")
    for mv in sorted(set(ref) | set(eng_split)):
        a, b = eng_split.get(mv), ref.get(mv)
        if a != b:
            out.append(f"{fen} | depth {depth} | move {mv}: engine {a}, python-chess {b}")
    if sum(eng_split.values()) != eng_total:
        out.append(f"{fen} | depth {depth} | the engine's own lines add up to {sum(eng_split.values())}, "
                   f"its total line says {eng_total}")
    return out


def main() -> int:
    exe, res = sys.argv[1], sys.argv[2]
    d4_minutes = float(sys.argv[3]) if len(sys.argv) > 3 else 25.0
    os.makedirs(res, exist_ok=True)
    t_start = time.time()
    summary: list[str] = []
    findings: list[str] = []
    eng = Engine(exe, os.path.join(res, "engine_stderr.txt"))
    if not eng.start_uci({"OwnBook": "false"}):
        print("the engine did not answer uci/isready")
        return 2

    # ---- A1: known answers ---------------------------------------------------------------------------------
    summary.append("A1. Known answers (published perft counts)")
    a1_ok = True
    for fen, pairs in KNOWN:
        for depth, want in pairs:
            t = time.time()
            _, got, _ = engine_perft(eng, fen, depth, timeout=900)
            line = f"  {fen} | perft {depth} | engine {got} | published {want} | {time.time() - t:.1f} s"
            if got != want:
                a1_ok = False
                findings.append("A1 " + line.strip())
                line += "   <-- DIFFERENT"
            summary.append(line)
    summary.append(f"  A1 result: {'all 12 right' if a1_ok else 'DIFFERENCES, see above'}")

    # ---- A2: positions -----------------------------------------------------------------------------------------
    t_gen = time.time()
    set1, n1 = pos.generate(20261115, 8, 60, n(500))
    set2, n2 = pos.generate(20261116, 20, 120, n(500))
    fens = set1 + set2
    counts = {k: 0 for k in KINDS}
    feats = []
    for f in fens:
        ft = pos.features(f)
        feats.append(ft)
        for k in KINDS:
            counts[k] += ft[k]
    extra, seed = [], 20261119
    while any(counts[k] < n(20) for k in KINDS) and seed < 20261119 + 40:
        need = [k for k in KINDS if counts[k] < n(20)]
        cand, _ = pos.generate(seed, 8, 160, 500)
        for f in cand:
            ft = pos.features(f)
            if any(ft[k] for k in need) and f not in fens and f not in extra:
                extra.append(f)
                for k in KINDS:
                    counts[k] += ft[k]
                need = [k for k in KINDS if counts[k] < n(20)]
                if not need:
                    break
        seed += 1
    fens_all = fens + extra
    with open(os.path.join(res, "positions_A2.txt"), "w", encoding="ascii", newline="\n") as fh:
        fh.write("\n".join(fens_all) + "\n")
    summary.append("")
    summary.append(f"A2. {len(fens_all)} positions: {len(set1)} (seed 20261115, plies 8-60, {n1} playouts), {len(set2)} (seed 20261116, "
                   f"plies 20-120, {n2} playouts), {len(extra)} added (seeds 20261119 on) so that every kind occurs at "
                   f"least {n(20)} times; made in {time.time() - t_gen:.0f} s")
    summary.append("  kinds: " + ", ".join(f"{k} {counts[k]}" for k in KINDS)
                   + ("" if all(counts[k] >= n(20) for k in KINDS) else f"   <-- a kind is below {n(20)} (not enough found)"))

    # self-test of the comparison: a real answer, one count altered, must be reported
    fen0 = fens_all[0]
    s0, t0_, _ = engine_perft(eng, fen0, 2, timeout=120)
    if s0:
        mv = sorted(s0)[0]
        planted = dict(s0)
        planted[mv] += 1
        caught = compare(fen0, 2, planted, (t0_ or 0) + 1, py_divide(fen0, 2))
        clean = compare(fen0, 2, s0, t0_, py_divide(fen0, 2))
        selftest = bool(caught) and not clean
    else:
        selftest = False
    summary.append(f"  self-test of the comparison (one count altered by one must be reported): "
                   f"{'PASS' if selftest else 'FAIL'}")

    mism: list[str] = []
    t3 = time.time()
    for i, f in enumerate(fens_all):
        split, total, _ = engine_perft(eng, f, 3, timeout=120)
        mism += compare(f, 3, split, total, py_divide(f, 3))
    summary.append(f"  depth 3: {len(fens_all)} positions compared in {time.time() - t3:.0f} s, "
                   f"{len(mism)} difference lines")
    t4, n4 = time.time(), 0
    for f in fens_all[:n(100)]:
        if time.time() - t4 > d4_minutes * 60:
            break
        split, total, _ = engine_perft(eng, f, 4, timeout=300)
        mism += compare(f, 4, split, total, py_divide(f, 4))
        n4 += 1
    summary.append(f"  depth 4: {n4} of the first 100 positions compared in {time.time() - t4:.0f} s "
                   f"(limit {d4_minutes:.0f} minutes)")
    findings += ["A2 " + m for m in mism]
    with open(os.path.join(res, "mismatches.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(mism) + ("\n" if mism else "none\n"))

    rc, secs = eng.quit()
    summary.append("")
    summary.append(f"engine exit code after quit: {rc} ({secs:.1f} s); stderr bytes: {os.path.getsize(eng.stderr_path)}")
    summary.append(f"total time: {(time.time() - t_start) / 60:.1f} minutes")
    summary.append("")
    summary.append("FINDINGS: " + ("none" if not findings and selftest else str(len(findings)) + (" (and the self-test failed)" if not selftest else "")))
    summary += ["  " + cut(f, 300) for f in findings[:200]]
    with open(os.path.join(res, "summary.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(summary) + "\n")
    with open(os.path.join(res, "transcript.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(eng.transcript) + "\n")
    with open(os.path.join(res, "results.json"), "w", encoding="utf-8") as fh:
        json.dump({"a1_all_right": a1_ok, "positions": len(fens_all), "kinds": counts, "selftest": selftest,
                   "difference_lines": len(mism), "depth4_positions": n4, "findings": len(findings)}, fh, indent=1)
    print("\n".join(summary))
    if not selftest:
        return 2
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
