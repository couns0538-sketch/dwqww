#!/usr/bin/env python3
"""S02 AREA 2 job 1 on the PC r15 build under PC20 (the same 2,000 sequences, the same v3 driver).

Differences from the base run, stated so the two are comparable:
  - PC20 is applied before every sequence: Threads 1, Hash 16, S14's 14 settings, then CuckooRep true,
    HistRework 2, TtPruneV2 true, CorrHistV2 true, MateAlphaGuard true, OwnBook false.
  - Threads 1 explicitly (seat 04: scores above Threads 1 are not reproducible).
  - the sequence lines are the SAME seqs.jsonl as the base run, so any difference is the build.

The driver is job1/run_sequences_v3.py imported as a module and its Engine class reused, so the harness is
identical to the one that produced the base numbers — a different driver would make the comparison worthless.

usage: run_pc.py <exe> <seqs.jsonl> <outdir> [workers]
"""
import json
import os
import sys
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVER = os.path.join(HERE, "..", "job1", "run_sequences_v3.py")
spec = importlib.util.spec_from_file_location("v3", DRIVER)
v3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v3)

from concurrent.futures import ThreadPoolExecutor

PC20 = [
    "setoption name Threads value 1",
    "setoption name Hash value 16",
    "setoption name LmrQuietBase value 93",
    "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13",
    "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643",
    "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8",
    "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24",
    "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212",
    "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2",
    "setoption name NonPawnCorrection value true",
    "setoption name CuckooRep value true",
    "setoption name HistRework value 2",
    "setoption name TtPruneV2 value true",
    "setoption name CorrHistV2 value true",
    "setoption name MateAlphaGuard value true",
    "setoption name OwnBook value false",
]


def run_one(exe, rec, outdir):
    """Same shape as v3.run_one, but every sequence starts from the PC20 options."""
    sid, lines = rec["id"], rec["lines"]
    o = {"id": sid, "crashed": False, "hung": False, "sanitizer_lines": 0, "sanitizer_first": [],
         "illegal": [], "bestmoves": [], "missing_bestmove": [], "readyok_missing": 0,
         "uciok_missing": 0, "zero_no_sm": 0, "zero_sm": 0, "n_go": 0, "n_bestmove": 0,
         "no_info_bestmoves": 0, "driver_stopped_go": 0, "info_depth_total": 0,
         "book_answers": 0, "option_refused": [], "steps": []}
    import time
    eng = v3.Engine(exe)
    t0 = time.monotonic()
    try:
        if not eng.send("uci") or eng.wait_for("uciok", 0) < 0:
            o["uciok_missing"] += 1
        # PC20 before anything else; a refusal is a hard error for this run
        for s in PC20:
            eng.send(s)
        eng.send("isready")
        if eng.wait_for("readyok", 0) < 0:
            o["readyok_missing"] += 1
        for line in eng.lines:
            if "unknown option" in line or "invalid value" in line:
                o["option_refused"].append(line)
        if o["option_refused"]:
            o["bad"] = True
            return o
        o["steps"].append({"setup": "PC20 applied"})

        # now the sequence itself, driven exactly as v3 does
        for i, line in enumerate(lines):
            parts = line.split()
            cmd = parts[0] if parts else ""
            start = eng.mark()
            if not eng.send(line):
                o["crashed"] = True
                break
            if cmd == "uci":
                if eng.wait_for("uciok", start) < 0:
                    o["uciok_missing"] += 1
            elif cmd == "isready":
                if eng.wait_for("readyok", start) < 0:
                    o["readyok_missing"] += 1
            elif cmd == "go":
                o["n_go"] += 1
                side_white = v3.board_after(lines, i).turn
                if v3.is_unbounded(parts, side_white):
                    time.sleep(v3.STOP_AFTER_MS / 1000.0)
                    eng.send("stop")
                    o["driver_stopped_go"] += 1
                at = eng.wait_for("bestmove", start)
                if at < 0:
                    o["missing_bestmove"].append({"i": i, "go": line})
                    continue
                o["n_bestmove"] += 1
                with eng.lock:
                    bm_line, seg = eng.lines[at], eng.lines[start:at]
                info = [l for l in seg if l.startswith("info depth")]
                book = [l for l in seg if "book move" in l]
                o["info_depth_total"] += len(info)
                if book:
                    o["book_answers"] += 1
                elif not info:
                    o["no_info_bestmoves"] += 1
                m = v3.BESTMOVE_RE.match(bm_line)
                bm = m.group(1) if m else "?"
                board = v3.board_after(lines, i)
                legal = {mv.uci() for mv in board.legal_moves}
                if bm == "0000" and legal:
                    if "searchmoves" in parts:
                        o["zero_sm"] += 1
                    else:
                        o["zero_no_sm"] += 1
                        o["illegal"].append({"i": i, "bestmove": bm, "kind": "0000 with legal moves"})
                elif bm != "0000" and bm not in legal:
                    o["illegal"].append({"i": i, "bestmove": bm, "fen": board.fen(),
                                         "legal_sample": sorted(legal)[:12]})
                o["bestmoves"].append({"i": i, "bestmove": bm, "go": line, "info_depth": len(info)})
            else:
                time.sleep(0.002)
        eng.send("quit")
        try:
            eng.proc.wait(timeout=5)
        except Exception:
            eng.kill()
            o["hung"] = True
    finally:
        if eng.proc.poll() is None:
            eng.kill()
            o["hung"] = True
        with eng.lock:
            text = list(eng.lines)
        san = [l for l in text if v3.SAN_RE.search(l)]
        o["sanitizer_lines"] = len(san)
        o["sanitizer_first"] = san[:2]
        o["wall_s"] = round(time.monotonic() - t0, 3)
        o["bad"] = bool(o["crashed"] or o["hung"] or san or o["illegal"] or o["missing_bestmove"]
                        or o["readyok_missing"] or o["uciok_missing"] or o["zero_no_sm"]
                        or o["option_refused"])
        if o["bad"]:
            d = os.path.join(outdir, "bad")
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "seq%04d.txt" % sid), "w") as fh:
                for l in lines:
                    fh.write(repr(l) + "\n")
                fh.write("# verdict\n%s\n" % json.dumps({k: o[k] for k in
                         ("crashed", "hung", "sanitizer_lines", "illegal", "missing_bestmove",
                          "option_refused")}))
                for l in text:
                    fh.write(l + "\n")
    return o


def main():
    exe, seqs, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    os.makedirs(outdir, exist_ok=True)
    recs = [json.loads(l) for l in open(seqs)]
    import subprocess
    with open(os.path.join(outdir, "meta.txt"), "w") as fh:
        fh.write("exe %s\n" % exe)
        fh.write("sha256 %s\n" % subprocess.run(["sha256sum", exe], capture_output=True,
                                               text=True).stdout.split()[0])
        fh.write("nm __asan_ %s\n" % subprocess.run("nm -C %s | grep -c __asan_" % exe, shell=True,
                                                    capture_output=True, text=True).stdout.strip())
        fh.write("nm __ubsan_ %s\n" % subprocess.run("nm -C %s | grep -c __ubsan_" % exe, shell=True,
                                                     capture_output=True, text=True).stdout.strip())
        fh.write("settings PC20, Threads 1\n")
        fh.write("options sent: %s\n" % " | ".join(PC20))
        fh.write("driver: job1/run_sequences_v3.py imported (identical harness to the base run)\n")
        fh.write("sequences: %s (%d)\n" % (seqs, len(recs)))
        fh.write("started_utc %s\n" % __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ",
                                                                 __import__("time").gmtime()))
    res = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for r in pool.map(lambda rec: run_one(exe, rec, outdir), recs):
            res.append(r)
    with open(os.path.join(outdir, "results.jsonl"), "w") as fh:
        for r in res:
            fh.write(json.dumps(r) + "\n")
    print("done %d sequences" % len(res))


if __name__ == "__main__":
    main()
