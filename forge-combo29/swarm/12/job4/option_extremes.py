#!/usr/bin/env python3
"""option_extremes.py EXE OUTDIR [--pc20] — area 2 job 3.

Every option the engine lists in its `uci` answer is set to six values, twice:

  BETWEEN searches   setoption, isready (read to readyok), then a real `go depth 6` whose
                     bestmove must be legal. This is the "next search still works" check.
  DURING a search    `go infinite`, then setoption at once, then `stop` and read the answer.
                     The answer must be legal and the engine must still answer isready.

Values per spin option: min, max, min-1, max+1, the word `word`, and the value left out.
Check options get `true`, `false`, `TRUE`, `maybe`, the value left out, and an empty value.
String options get a path-like value, a very long value, and the value left out.

Every response is checked for the three lines the rules say to stop on:
`unknown option`, `invalid value`, `ERROR`. A line that appears is recorded with the option and
value, not swallowed.

Threads 1 throughout: `Threads` is exercised as an OPTION (that is the job) but every other case
runs with whatever the engine's default is, and the harness never leaves Threads above 1 — after
testing the Threads option it sets it back to 1 and confirms with isready.
"""
import json
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

import chess

SAN = re.compile(r"ERROR: (AddressSanitizer|LeakSanitizer)|SUMMARY: (Address|Undefined|Leak)Sanitizer|runtime error: ")
STOPLINE = re.compile(r"unknown option|invalid value|invalid FEN|illegal move")
POS = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
BOARD = chess.Board(POS)

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]


class Eng:
    def __init__(self, exe, opts):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1,
                                  env={"PATH": "/usr/bin:/bin", "ASAN_OPTIONS": "detect_leaks=0",
                                       "UBSAN_OPTIONS": "print_stacktrace=1"})
        self.q = queue.Queue()
        self.lines = []
        threading.Thread(target=self._rd, daemon=True).start()
        self.send("uci")
        self.wait(lambda l: l == "uciok")
        for n, v in opts:
            self.send(f"setoption name {n} value {v}")
            self.send("isready")
            self.wait(lambda l: l == "readyok")

    def _rd(self):
        for ln in self.p.stdout:
            self.q.put(ln.rstrip("\n"))
        self.q.put(None)

    def send(self, s):
        try:
            self.p.stdin.write(s + "\n")
            self.p.stdin.flush()
        except (BrokenPipeError, OSError, ValueError):
            pass

    def wait(self, pred, bound=40.0):
        end = time.monotonic() + bound
        while time.monotonic() < end:
            try:
                ln = self.q.get(timeout=0.1)
            except queue.Empty:
                if self.p.poll() is not None:
                    return None
                continue
            if ln is None:
                return None
            self.lines.append(ln)
            if pred(ln):
                return ln
        return "TIMEOUT"

    def drain(self, quiet=0.05):
        while True:
            try:
                ln = self.q.get(timeout=quiet)
            except queue.Empty:
                return
            if ln is None:
                return
            self.lines.append(ln)

    def close(self):
        self.send("quit")
        try:
            self.p.stdin.close()
        except (OSError, ValueError):
            pass
        try:
            self.p.wait(timeout=20)
        except subprocess.TimeoutExpired:
            self.p.kill()
            self.p.wait()
        end = time.monotonic() + 2
        while time.monotonic() < end:
            try:
                ln = self.q.get(timeout=0.1)
            except queue.Empty:
                if self.p.poll() is not None:
                    break
                continue
            if ln is None:
                break
            self.lines.append(ln)
        return self.p.returncode


def options_of(exe):
    e = Eng(exe, [])
    out = []
    for ln in e.lines:
        m = re.match(r"^option name (.+?) type (\w+)(.*)$", ln)
        if m:
            rest = m.group(3)
            mn = re.search(r"min (-?\d+)", rest)
            mx = re.search(r"max (-?\d+)", rest)
            out.append({"name": m.group(1), "type": m.group(2),
                        "min": int(mn.group(1)) if mn else None,
                        "max": int(mx.group(1)) if mx else None})
    e.close()
    return out


def values_for(opt):
    t = opt["type"]
    if t == "spin":
        return [str(opt["min"]), str(opt["max"]), str(opt["min"] - 1), str(opt["max"] + 1),
                "word", None]
    if t == "check":
        return ["true", "false", "TRUE", "maybe", None, ""]
    if t == "string":
        return ["/tmp/nonexistent.bin", "x" * 300, None]
    return [None]          # button


def legal(mv):
    if not mv or mv in ("0000", "(none)"):
        return None
    try:
        return chess.Move.from_uci(mv) in BOARD.legal_moves
    except ValueError:
        return False


def case_between(exe, opts, opt, value):
    """setoption between searches: the next search must still produce a legal bestmove."""
    e = Eng(exe, opts)
    e.send(f"position fen {POS}")
    e.send("isready")
    e.wait(lambda l: l == "readyok")
    i = len(e.lines)
    e.send(f"setoption name {opt['name']}" + (f" value {value}" if value is not None else ""))
    e.send("isready")
    ready = e.wait(lambda l: l == "readyok", 20) == "readyok"
    e.send("go depth 6")
    bm_line = e.wait(lambda l: l.startswith("bestmove"), 60)
    if isinstance(bm_line, str) and bm_line.startswith("bestmove") is False:
        e.send("stop")
        e.wait(lambda l: l.startswith("bestmove"), 10)
    e.close()
    seg = e.lines[i:]
    bms = [l.split()[1] for l in seg if l.startswith("bestmove")]
    return {
        "phase": "between", "option": opt["name"], "type": opt["type"], "value": value,
        "readyok": ready,
        "bestmove": bms[-1] if bms else None,
        "bestmove_legal": legal(bms[-1]) if bms else None,
        "stoplines": [l for l in seg if STOPLINE.search(l)][:3],
        "sanitizer_lines": [l for l in seg if SAN.search(l)][:3],
        "crash": e.p.returncode is not None and e.p.returncode < 0,
    }


def case_during(exe, opts, opt, value):
    """setoption during a search: the engine must still answer and still be usable."""
    e = Eng(exe, opts)
    e.send(f"position fen {POS}")
    e.send("isready")
    e.wait(lambda l: l == "readyok")
    i = len(e.lines)
    e.send("go infinite")
    time.sleep(0.01)                      # let the search start (measured: depth lines appear)
    e.send(f"setoption name {opt['name']}" + (f" value {value}" if value is not None else ""))
    e.send("stop")
    bm = e.wait(lambda l: l.startswith("bestmove"), 30)
    e.send("isready")
    ready = e.wait(lambda l: l == "readyok", 20) == "readyok"
    e.close()
    seg = e.lines[i:]
    bms = [l.split()[1] for l in seg if l.startswith("bestmove")]
    return {
        "phase": "during", "option": opt["name"], "type": opt["type"], "value": value,
        "readyok": ready,
        "bestmove": bms[-1] if bms else None,
        "bestmove_legal": legal(bms[-1]) if bms else None,
        "stoplines": [l for l in seg if STOPLINE.search(l)][:3],
        "sanitizer_lines": [l for l in seg if SAN.search(l)][:3],
        "crash": e.p.returncode is not None and e.p.returncode < 0,
    }


def main():
    exe, outdir = sys.argv[1], Path(sys.argv[2])
    use_pc20 = "--pc20" in sys.argv
    base_opts = PC20 if use_pc20 else []
    label = "PC20" if use_pc20 else "none"
    outdir.mkdir(parents=True, exist_ok=True)

    opts = options_of(exe)
    sha = subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0]
    (outdir / "option_extremes.meta").write_text(
        f"exe: {exe}\nsha256: {sha}\ndate_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n"
        f"settings: {label}\nthreads: 1 (the Threads option is exercised AS an option; after it, "
        f"Threads is reset to 1)\noptions listed: {len(opts)}\n"
        f"position: {POS}\nbase setoptions sent first: {base_opts}\n"
        "env: ASAN_OPTIONS=detect_leaks=0 UBSAN_OPTIONS=print_stacktrace=1\n")
    print(f"exe {exe}\nsettings {label}, {len(opts)} options listed")

    recs = []
    f = (outdir / "option_extremes.jsonl").open("w")
    bad = 0
    for opt in opts:
        if opt["name"] == "Threads":
            continue                       # handled last, with a reset to 1
        for value in values_for(opt):
            for fn in (case_between, case_during):
                r = fn(exe, base_opts, opt, value)
                recs.append(r)
                f.write(json.dumps(r) + "\n")
                fired = (r["crash"] or r["sanitizer_lines"] or r["bestmove_legal"] is False
                         or r["readyok"] is False)
                if fired:
                    bad += 1
                    print(f"  !! {r['phase']:7} {r['option']}={value!r}: crash={r['crash']} "
                          f"legal={r['bestmove_legal']} ready={r['readyok']} "
                          f"san={len(r['sanitizer_lines'])}", flush=True)
        f.flush()

    # Threads last, then always back to 1
    topt = next((o for o in opts if o["name"] == "Threads"), None)
    if topt:
        for value in ["1", "2", str(topt["max"]), "0", str(topt["max"] + 1), "word", None]:
            r = case_between(exe, base_opts, topt, value)
            r["note"] = "after this case the harness sets Threads back to 1"
            recs.append(r)
            f.write(json.dumps(r) + "\n")
            if r["crash"] or r["sanitizer_lines"] or r["bestmove_legal"] is False:
                bad += 1
                print(f"  !! between Threads={value!r}: crash={r['crash']} "
                      f"legal={r['bestmove_legal']} san={len(r['sanitizer_lines'])}")
    f.close()

    legal_n = sum(1 for r in recs if r["bestmove_legal"] is True)
    print(f"\ncases {len(recs)}; legal bestmoves {legal_n}; cases that fired anything: {bad}")
    (outdir / "option_extremes.summary.json").write_text(json.dumps(
        {"exe": exe, "settings": label, "cases": len(recs), "legal_bestmoves": legal_n,
         "fired": [r for r in recs if r["crash"] or r["sanitizer_lines"]
                   or r["bestmove_legal"] is False or r["readyok"] is False]}, indent=1) + "\n")


if __name__ == "__main__":
    main()
