#!/usr/bin/env python3
"""
Step O2 (`InfoOnce`) Whole-Stream & Client-Rule Differential Oracle + Planted-Fault Verifier
============================================================================================
Over the full 60-game `Hash 32` self-play stream (`7,645` searches):
1. Verifies that with `InfoOnce` absent (default `false`), the entire stream output (`85,863` lines)
   equals the base build line for line (with only `nps` and `time` masked on `info depth` lines).
2. Verifies that with `InfoOnce` set to `true`, every single search prints strictly ONE line before
   `bestmove`, and its `bestmove`, `nodes`, and full masked `info` line equal byte-for-byte the line
   chosen by the PC client's rule from the `false` run.
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "job2"))
from selfplay_driver_v2 import (  # noqa: E402
    PC20_OPTIONS,
    MinimalBoardTracker,
    select_book_fens,
    send,
    wait_ready_collect,
)


def mask_info_line(line: str) -> str:
    if not line.startswith("info depth "):
        return line
    toks = line.split()
    out = []
    i = 0
    while i < len(toks):
        if toks[i] in ("nps", "time") and i + 1 < len(toks):
            out.append(toks[i])
            out.append("<MASK>")
            i += 2
        else:
            out.append(toks[i])
            i += 1
    return " ".join(out)


def is_exact_score_info(line: str) -> bool:
    if not line.startswith("info ") or " score " not in f" {line} ":
        return False
    toks = line.split()
    if "score" not in toks:
        return False
    idx = toks.index("score")
    if idx + 2 >= len(toks) or toks[idx + 1] not in ("cp", "mate"):
        return False
    after = toks[idx + 3 :]
    return "lowerbound" not in after and "upperbound" not in after


def is_bound_score_info(line: str) -> bool:
    if not line.startswith("info ") or " score " not in f" {line} ":
        return False
    toks = line.split()
    if "score" not in toks:
        return False
    idx = toks.index("score")
    if idx + 2 >= len(toks) or toks[idx + 1] not in ("cp", "mate"):
        return False
    after = toks[idx + 3 :]
    return "lowerbound" in after or "upperbound" in after


def pc_client_pick_info(pre_bestmove_lines: list[str]) -> str:
    exact = [ln for ln in pre_bestmove_lines if is_exact_score_info(ln)]
    if exact:
        return exact[-1]
    bound = [ln for ln in pre_bestmove_lines if is_bound_score_info(ln)]
    if bound:
        return bound[-1]
    raise RuntimeError(f"No score info line found in: {pre_bestmove_lines}")


def extract_nodes(info_ln: str) -> int:
    toks = info_ln.split()
    return int(toks[toks.index("nodes") + 1])


def collect_stream(binary: str, net768: str, fens: list[str], set_info_once: bool | None) -> tuple[list[str], list[tuple[list[str], str]]]:
    pc20_h32 = [(k, ("32" if k == "Hash" else v)) for k, v in PC20_OPTIONS]
    proc = subprocess.Popen(
        [binary],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None

    cfg = ["uci\n"] + [f"setoption name {k} value {v}\n" for k, v in pc20_h32]
    if set_info_once is not None:
        cfg.append(f"setoption name InfoOnce value {'true' if set_info_once else 'false'}\n")
    cfg += [
        f"setoption name NNUEArchFile value {net768}\n",
        "setoption name NNUEArch value true\n",
        "isready\n",
    ]
    send(proc, "".join(cfg))
    setup_lines = wait_ready_collect(proc, check_errors=True)

    whole_stream: list[str] = []
    per_search: list[tuple[list[str], str]] = []

    for root_fen in fens:
        send(proc, "ucinewgame\nisready\n")
        rdy = wait_ready_collect(proc, check_errors=True)
        whole_stream.extend(rdy)

        moves: list[str] = []
        tracker = MinimalBoardTracker()
        tracker.load_fen(root_fen)

        for _ply in range(300):
            if tracker.is_draw():
                break
            pos_str = f"position fen {root_fen}" + (" moves " + " ".join(moves) if moves else "")
            send(proc, f"{pos_str}\ngo softnodes 2000\n")

            pre: list[str] = []
            bm_line = ""
            while True:
                raw = proc.stdout.readline()
                if not raw:
                    proc.kill()
                    raise RuntimeError(f"EOF in {binary}")
                ln = raw.rstrip("\r\n")
                if ln.startswith("bestmove "):
                    bm_line = ln
                    whole_stream.append(ln)
                    break
                pre.append(ln)
                whole_stream.append(mask_info_line(ln))

            per_search.append((pre, bm_line))
            bm = bm_line.split()[1]
            if bm == "0000":
                break
            moves.append(bm)
            tracker.push_uci(bm)

    send(proc, "quit\n")
    proc.wait(timeout=5)
    return setup_lines, whole_stream, per_search


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--var", required=True)
    ap.add_argument("--net768", required=True)
    ap.add_argument("--pos250", required=True)
    ap.add_argument("--games", type=int, default=60)
    args = ap.parse_args()

    fens = select_book_fens(args.pos250, args.games)
    _, base_stream, base_searches = collect_stream(args.base, args.net768, fens, set_info_once=None)
    var_setup, var_absent_stream, _ = collect_stream(args.var, args.net768, fens, set_info_once=None)

    if not any("option name InfoOnce type check default false" in ln for ln in var_setup):
        print("O2_ORACLE FAIL: InfoOnce option not advertised in uci output", file=sys.stderr)
        return 1

    if base_stream != var_absent_stream:
        for idx, (a, b) in enumerate(zip(base_stream, var_absent_stream)):
            if a != b:
                print(
                    f"O2_ORACLE ABSENT STREAM MISMATCH at line {idx}:\n  base: {a}\n  var : {b}",
                    file=sys.stderr,
                )
                return 1
        print(
            f"O2_ORACLE ABSENT STREAM LENGTH MISMATCH: base={len(base_stream)} var={len(var_absent_stream)}",
            file=sys.stderr,
        )
        return 1

    _, _, var_true_searches = collect_stream(args.var, args.net768, fens, set_info_once=True)
    if len(base_searches) != len(var_true_searches):
        print(
            f"O2_ORACLE SEARCH COUNT MISMATCH: false={len(base_searches)} true={len(var_true_searches)}",
            file=sys.stderr,
        )
        return 1

    for s_idx, ((false_pre, false_bm), (true_pre, true_bm)) in enumerate(zip(base_searches, var_true_searches)):
        if len(true_pre) != 1:
            print(
                f"O2_ORACLE LINE COUNT MISMATCH at search {s_idx}: expected 1 line before bestmove, got {len(true_pre)}: {true_pre}",
                file=sys.stderr,
            )
            return 1
        picked_false = pc_client_pick_info(false_pre)
        got_true = true_pre[0]
        if false_bm != true_bm:
            print(
                f"O2_ORACLE BESTMOVE MISMATCH at search {s_idx}: false={false_bm!r} true={true_bm!r}",
                file=sys.stderr,
            )
            return 1
        if extract_nodes(picked_false) != extract_nodes(got_true):
            print(
                f"O2_ORACLE NODES MISMATCH at search {s_idx}:\n  picked_false: {picked_false}\n  got_true    : {got_true}",
                file=sys.stderr,
            )
            return 1
        if mask_info_line(picked_false) != mask_info_line(got_true):
            print(
                f"O2_ORACLE INFO LINE MISMATCH at search {s_idx}:\n  picked_false: {mask_info_line(picked_false)}\n  got_true    : {mask_info_line(got_true)}",
                file=sys.stderr,
            )
            return 1

    print(
        f"O2_STREAM_ORACLE PASS: games={args.games} searches_compared={len(base_searches)} "
        f"absent_stream_lines_equal={len(base_stream)}/{len(base_stream)} "
        f"true_single_line_exact={len(var_true_searches)}/{len(base_searches)} mismatches=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
