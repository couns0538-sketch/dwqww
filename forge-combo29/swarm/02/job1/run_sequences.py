#!/usr/bin/env python3
"""S02 AREA 2 job 1 — run every sequence from seqs.jsonl through one engine process each,
record crashes / hangs / sanitizer lines / bestmove legality.

usage: run_sequences.py <exe> <seqs.jsonl> <outdir> [workers]

One engine process per sequence (fresh, so a crash cannot poison the next one). All input is written
to the child's stdin, stdin is then closed, output is read with a 25 s wall-clock deadline per
sequence; a process still alive at the deadline is a HANG: killed, counted, its raw output kept.

Board tracking (for the bestmove legality check) uses the behaviour this build is known to have:
  position startpos/fen [moves ...]  -> set the board; if python-chess rejects the FEN the previous
                                        board is kept; moves are applied only up to the first illegal one
  ucinewgame                        -> the engine resets to the start position (src/uci.cpp uci_loop)
Sanitizer lines are counted with the same pattern as the planted-fault proof, and every run clears
ASAN_OPTIONS / UBSAN_OPTIONS / TSAN_OPTIONS from the environment.
"""
import json
import os
import re
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import chess

TIMEOUT_S = 25.0
SAN_RE = re.compile(r"ERROR: AddressSanitizer|runtime error:|ERROR: LeakSanitizer|"
                    r"SUMMARY: (AddressSanitizer|UndefinedBehaviorSanitizer)|ERROR: UndefinedBehavior")
BESTMOVE_RE = re.compile(r"^bestmove\s+(\S+)(?:\s+ponder\s+(\S+))?\s*$")


def initial_board():
    return chess.Board()


def track_boards(lines):
    """Return a list of (line_index, board_after_processing_this_line) and the final board."""
    board = initial_board()
    seen = []  # (index, frozen board state (fen list of legal moves), note)
    for i, line in enumerate(lines):
        parts = line.split()
        if not parts:
            seen.append((i, board, None))
            continue
        cmd = parts[0]
        if cmd == "ucinewgame":
            board = initial_board()
            seen.append((i, board, "ucinewgame"))
        elif cmd == "position":
            new_board = board
            mv_start = None
            skip_line = False
            if len(parts) >= 2 and parts[1] == "startpos":
                new_board = chess.Board()
                mv_start = 2
            elif len(parts) >= 3 and parts[1] == "fen":
                # the fen is 6 fields; find the optional "moves"
                try:
                    cut = parts.index("moves")
                except ValueError:
                    cut = len(parts)
                fen = " ".join(parts[2:cut])
                try:
                    cand = chess.Board(fen)
                    ok = cand.is_valid()
                except Exception:
                    ok = False
                if ok:
                    new_board = cand
                    mv_start = cut + 1 if cut < len(parts) else None
                else:
                    # a refused FEN: the engine ignores the WHOLE line, its moves too
                    # (src/uci.cpp prints "invalid FEN: ..." and does not touch the board)
                    skip_line = True
            if skip_line:
                seen.append((i, board, "position-refused-fen"))
                continue
            if mv_start is not None and len(parts) > mv_start and parts[mv_start] == "moves":
                mv_start += 1
            if mv_start is not None:
                b = new_board.copy()
                for m in parts[mv_start:]:
                    try:
                        mv = chess.Move.from_uci(m)
                    except Exception:
                        break
                    if mv not in b.legal_moves:
                        break
                    b.push(mv)
                new_board = b
            seen.append((i, new_board, "position"))
            board = new_board
        else:
            seen.append((i, board, None))
    return seen, board


def check_bestmoves(lines, out_text):
    """Attribute the k-th `bestmove` in the output to the k-th `go` line, in order.

    Caveat, stated plainly: when a sequence has several `go` lines the engine answers them one at a
    time (stop_search joins the worker), so the k-th bestmove does belong to the k-th go. What is NOT
    modelled is a `go` sent while a search is already running: then the engine keeps the running search
    and the new `go` may never produce a bestmove, which shifts the pairing. Sequences where the count
    of bestmoves differs from the count of `go` lines are therefore listed separately, not counted
    either way.

    Returns (judged, illegal_list, notes)."""
    go_idx = [i for i, l in enumerate(lines) if l.split()[:1] == ["go"]]
    bestmoves = [m.group(1) for m in (BESTMOVE_RE.match(l) for l in out_text.splitlines()) if m]
    if not go_idx or not bestmoves:
        return 0, [], "no go/bestmove (go %d, bestmove %d)" % (len(go_idx), len(bestmoves)), 0, 0
    if len(go_idx) != len(bestmoves):
        return 0, [], "NOT PAIRED (go %d, bestmove %d)" % (len(go_idx), len(bestmoves)), 0, 0
    seen, final = track_boards(lines)
    illegal, notes = [], []
    zero_no_sm, zero_sm = 0, 0
    for gi, bm in zip(go_idx, bestmoves):
        board = seen[gi][1] if seen[gi][1] is not None else final
        go_tokens = lines[gi].split()
        has_sm = "searchmoves" in go_tokens
        if bm == "0000":
            if any(board.legal_moves):
                if has_sm:
                    zero_sm += 1
                else:
                    zero_no_sm += 1
                    notes.append("0000 but %d legal moves at line %d (go without searchmoves)"
                                 % (board.legal_moves.count(), gi))
            continue
        legal = {m.uci() for m in board.legal_moves}
        if bm not in legal:
            illegal.append({"go_line": gi, "bestmove": bm, "fen": board.fen(),
                            "legal": sorted(legal)[:12], "go": lines[gi]})
    return 1, illegal, "; ".join(notes) if notes else "paired %d" % len(go_idx), zero_no_sm, zero_sm


def run_one(exe, rec, outdir):
    sid = rec["id"]
    lines = rec["lines"]
    payload = ("\n".join(lines) + "\n").encode()
    env = dict(os.environ)
    for k in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
        env.pop(k, None)
    t0 = time.monotonic()
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env=env, start_new_session=True)
    hung = False
    try:
        out, _ = proc.communicate(payload, timeout=TIMEOUT_S)
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        hung = True
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except Exception:
            pass
        try:
            out, _ = proc.communicate(timeout=10)
        except Exception:
            out = b""
        rc = "KILLED_TIMEOUT"
    wall = time.monotonic() - t0
    text = out.decode("utf-8", "replace")
    san_lines = [l for l in text.splitlines() if SAN_RE.search(l)]
    n_isready = sum(1 for l in lines if l.strip() == "isready")
    n_readyok = sum(1 for l in text.splitlines() if l.strip() == "readyok")
    n_uci = sum(1 for l in lines if l.strip() == "uci")
    n_uciok = sum(1 for l in text.splitlines() if l.strip() == "uciok")
    checked, illegal, note, zero_no_sm, zero_sm = check_bestmoves(lines, text)
    rec_out = {
        "id": sid, "rc": rc if rc != "KILLED_TIMEOUT" else rc,
        "crashed": (not hung) and isinstance(rc, int) and rc != 0,
        "hung": hung, "wall_s": round(wall, 3),
        "sanitizer_lines": len(san_lines), "sanitizer_first": san_lines[:2],
        "isready_sent": n_isready, "readyok_seen": n_readyok,
        "uci_sent": n_uci, "uciok_seen": n_uciok,
        "readyok_missing": max(0, n_isready - n_readyok),
        "uciok_missing": max(0, n_uci - n_uciok),
        "bestmove_checked": checked, "illegal_bestmoves": illegal, "check_note": note,
        "unpaired": note.startswith("NOT PAIRED"),
        "zero_no_searchmoves": zero_no_sm, "zero_with_searchmoves": zero_sm,
        "n_go": sum(1 for l in lines if l.split()[:1] == ["go"]),
        "n_bestmove": len([l for l in text.splitlines() if l.startswith("bestmove")]),
    }
    bad = (rec_out["crashed"] or hung or san_lines or illegal or rec_out["readyok_missing"]
           or rec_out["uciok_missing"] or rec_out["zero_no_searchmoves"])
    if bad:
        path = os.path.join(outdir, "bad", "seq%04d.txt" % sid)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write("# lines sent\n")
            for l in lines:
                fh.write(repr(l) + "\n")
            fh.write("# exit %r hung %s wall %r\n" % (rc, hung, round(wall, 3)))
            fh.write("# output\n")
            fh.write(text)
    return rec_out


def main():
    exe, seqs_path, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    os.makedirs(outdir, exist_ok=True)
    recs = [json.loads(l) for l in open(seqs_path)]
    with open(os.path.join(outdir, "meta.txt"), "w") as fh:
        fh.write("exe %s\n" % exe)
        fh.write("sha256 %s\n" % subprocess.run(["sha256sum", exe], capture_output=True,
                                               text=True).stdout.split()[0])
        nm = subprocess.run("nm -C %s | grep -c __asan_" % exe, shell=True, capture_output=True,
                            text=True).stdout.strip()
        nmu = subprocess.run("nm -C %s | grep -c __ubsan_" % exe, shell=True, capture_output=True,
                             text=True).stdout.strip()
        fh.write("nm -C grep -c __asan_ %s\n" % nm)
        fh.write("nm -C grep -c __ubsan_ %s\n" % nmu)
        fh.write("timeout_per_sequence_s %s\nworkers %d\n" % (TIMEOUT_S, workers))
        fh.write("started_utc %s\n" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        idout = subprocess.run([exe], input=b"uci\nquit\n", capture_output=True, env={
            k: v for k, v in os.environ.items() if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS")})
        for line in idout.stdout.decode("utf-8", "replace").splitlines():
            if line.startswith("id name") or line.startswith("option"):
                fh.write("sent: (nothing)  answer: %s\n" % line)
        fh.write("option lines above were the uci answer of this exe\n")
    results = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for r in pool.map(lambda rec: run_one(exe, rec, outdir), recs):
            results.append(r)
    with open(os.path.join(outdir, "results.jsonl"), "w") as fh:
        for r in results:
            fh.write(json.dumps(r) + "\n")
    print("done %d sequences" % len(results))


if __name__ == "__main__":
    main()
