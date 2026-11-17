#!/usr/bin/env python3
"""f3_halfmove_cap.py <exe> <outdir>

The halfmove clock is parsed as long long, then stored as std::uint16_t capped at 65535
(src/board.cpp:217, :351). Two consequences, both measured here:

  1. a FEN with any clock >= 65535 is ACCEPTED and the clock silently becomes 65535
  2. with the clock at 65535, every `halfmove_clock() >= 100` test fires, so the engine treats the
     position as an immediate fifty-move draw -- `go depth N` reports score cp 0 with nodes 0 and no
     search (the drawn-root path of my S-F1), and it will play any legal move.

A correct engine must refuse a clock above 100 (the rule cannot have been reached) or clamp to 100;
clamping to 65535 means "already drawn for 6 centuries", which is a silent wrong answer for any FEN a
tool feeds in. The CONTROL is the same position with clock 99, which must search normally.
"""
import json
import os
import subprocess
import sys

POSITIONS = [
    ("K+R vs K, white to move", "4k3/8/8/8/8/8/8/R3K3 w - - %d 1"),
    ("middlegame, black to move", "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R b KQkq - %d 8"),
]


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(self, s):
        self.p.stdin.write(s + "\n"); self.p.stdin.flush()

    def until(self, pred, timeout=120):
        import time
        t0 = time.monotonic(); out = []
        while time.monotonic() - t0 < timeout:
            ln = self.p.stdout.readline()
            if not ln:
                break
            s = ln.rstrip("\n"); out.append(s)
            if pred(s):
                return out, True
        return out, False

    def boot(self):
        self.send("uci"); self.until(lambda s: s.strip() == "uciok")
        self.send("isready"); self.until(lambda s: s.strip() == "readyok")

    def search(self, fen, depth=6):
        self.send("position fen " + fen)
        self.send("isready"); self.until(lambda s: s.strip() == "readyok")
        self.send("go depth %d" % depth)
        lines, ok = self.until(lambda s: s.startswith("bestmove"))
        if not ok:
            raise RuntimeError("no bestmove for %r (last %r)" % (fen, lines[-3:]))
        infos = [l for l in lines if l.startswith("info depth")]
        # GUARD (S-W1): zero info lines => no score/nodes. Raise rather than record a None row.
        if not infos:
            raise RuntimeError("no 'info depth' line for %r (row aborted)" % fen)
        last = infos[-1]
        import re
        n = re.search(r"nodes (\d+)", last)
        sc = re.search(r"score (cp|mate) (-?\d+)", last)
        d = re.search(r"depth (\d+)", last)
        bm = next(l for l in lines if l.startswith("bestmove")).split()[1]
        return {"fen": fen, "info_lines": len(infos), "last_info": last, "bestmove": bm,
                "nodes": int(n.group(1)) if n else None,
                "score": (sc.group(1), int(sc.group(2))) if sc else None,
                "depth": int(d.group(1)) if d else None}

    def refuses(self, fen):
        self.send("position fen " + fen)
        self.send("isready")
        lines, _ = self.until(lambda s: s.strip() == "readyok")
        return any("invalid FEN" in l for l in lines), lines

    def quit(self):
        try:
            self.send("quit"); self.p.wait(timeout=20)
        except Exception:
            self.p.kill()


def main():
    exe = os.path.realpath(sys.argv[1]); outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    rows = []
    e = Engine(exe); e.boot()
    for label, tpl in POSITIONS:
        for clock in (0, 99, 100, 101, 150, 65534, 65535, 65536, 99999):
            fen = tpl % clock
            refused, lines = e.refuses(fen)
            row = {"position": label, "clock": clock, "refused": refused}
            if refused:
                row["refusal"] = next((l for l in lines if "invalid" in l), "")
            else:
                row.update(e.search(fen, 6))
            rows.append(row)
    e.quit()

    with open(os.path.join(outdir, "table.txt"), "w") as f:
        f.write("| position | clock in FEN | refused | info lines | last info | bestmove |\n")
        f.write("|---|---|---|---|---|---|\n")
        for r in rows:
            f.write("| %s | %s | %s | %s | %s | %s |\n" % (
                r["position"], r["clock"], r["refused"], r.get("info_lines", "-"),
                (r.get("last_info", "") or "-")[:90], r.get("bestmove", "-")))
    with open(os.path.join(outdir, "result.json"), "w") as f:
        json.dump({"exe": exe,
                   "sha256": subprocess.run(["sha256sum", exe], capture_output=True,
                                            text=True).stdout.split()[0],
                   "date_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                              capture_output=True, text=True).stdout.strip(),
                   "rows": rows}, f, indent=2)

    accepted_over_100 = [r["clock"] for r in rows if not r["refused"] and r["clock"] > 100]
    drawn = [r for r in rows if not r["refused"] and r.get("nodes") == 0]
    print("clock values ABOVE 100 accepted:", sorted(set(accepted_over_100)))
    print("cases answered with 0 nodes (treated as already drawn):",
          [(r["position"][:12], r["clock"]) for r in drawn])
    print("control (clock 99) searched normally in all positions:",
          all(r.get("nodes") not in (0, None) for r in rows if r["clock"] == 99 and not r["refused"]))


if __name__ == "__main__":
    main()
