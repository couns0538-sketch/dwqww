#!/usr/bin/env python3
"""hardened.py — seat 20's SINGLE engine driver after the 19-F12 broadcast.

Rules this driver enforces, so no result of mine can be a fabricated bestmove:
  * every command is written, then stdout is read until the ANSWER to that command appears
    (`readyok` for isready, `uciok` for uci, `bestmove` for go, nothing needed for setoption/position);
  * `quit` is written ONLY after the last `bestmove` has been read;
  * stdin is never closed while a search is running;
  * a search with no `bestmove` within the timeout is reported as a HANG, never as an answer;
  * a search that answers `bestmove` with NO `info depth` line is flagged UNSEARCHED in the result, so the
    fabricated-answer case can never be mistaken for a search result.

usage (as a module):
    from hardened import run_search
    r = run_search(exe, fen, "go depth 12", opts=[("LmpBase", 8)])
    r["score"], r["nodes"], r["pv"], r["unsearched"]
"""
import re
import subprocess
import threading
import time

DEFAULT_TIMEOUT = 180.0


class Engine:
    def __init__(self, exe, opts=(), uci_name=True):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.lines = []
        self.lock = threading.Lock()
        self.dead = False
        self.t = threading.Thread(target=self._rd, daemon=True)
        self.t.start()
        self.send("uci")
        self.expect("uciok", 20.0)
        self.send("setoption name OwnBook value false")
        for k, v in opts:
            self.send(f"setoption name {k} value {v}")
        self.isready()

    def _rd(self):
        try:
            for l in self.p.stdout:
                with self.lock:
                    self.lines.append(l.rstrip("\n"))
        except Exception:
            pass

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def mark(self):
        with self.lock:
            return len(self.lines)

    def since(self, k):
        with self.lock:
            return self.lines[k:]

    def expect(self, token, timeout):
        """read stdout until a line starting with `token`; returns (all_new_lines, found)"""
        k = self.mark()
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            for l in self.since(k):
                if l.startswith(token):
                    return self.since(k), True
            time.sleep(0.002)
        return self.since(k), False

    def isready(self):
        self.send("isready")
        _, ok = self.expect("readyok", 20.0)
        if not ok:
            raise RuntimeError("no readyok — refusing to continue (19-F12 discipline)")

    def position(self, fen):
        self.isready()
        self.send(f"position fen {fen}")
        self.isready()          # position has no answer; this isready is the readback

    def move_list(self, start_fen, moves):
        self.isready()
        self.send(f"position fen {start_fen} moves {' '.join(moves)}")
        self.isready()

    def search(self, go, timeout=DEFAULT_TIMEOUT):
        """write go, READ UNTIL bestmove, then return. quit is never sent mid-search."""
        self.isready()
        k = self.mark()
        t0 = time.monotonic()
        self.send(go)
        while time.monotonic() - t0 < timeout:
            new = self.since(k)
            if any(x.startswith("bestmove") for x in new):
                break
            time.sleep(0.002)
        else:
            return {"hang": True, "score": None, "nodes": 0, "pv": [], "bestmove": None,
                    "unsearched": True, "info_depth_lines": 0}
        new = self.since(k)
        depths = [x for x in new if x.startswith("info depth")]
        best = [x for x in new if x.startswith("bestmove")][-1].split()
        last = depths[-1] if depths else ""
        m = re.search(r"score (\S+)(?: (\S+))?", last)
        score = None
        if m:
            score = f"{m.group(1)} {m.group(2)}" if m.group(2) and not m.group(2).startswith(("nodes", "nps")) \
                else m.group(1)
        n = re.search(r"nodes (\d+)", last)
        pv = last.split(" pv ", 1)[1].split() if " pv " in last else []
        return {"hang": False, "score": score,
                "nodes": int(n.group(1)) if n else 0,
                "pv": pv, "bestmove": best[1] if len(best) > 1 else None,
                "unsearched": len(depths) == 0,
                "info_depth_lines": len(depths),
                "last_info": last, "wall": time.monotonic() - t0}

    def close(self):
        """quit ONLY after the last bestmove has been read — the caller guarantees that by using search()."""
        try:
            self.send("quit")
            self.p.wait(timeout=15)
        except Exception:
            self.p.kill()


def run_search(exe, fen, go, opts=(), timeout=DEFAULT_TIMEOUT):
    e = Engine(exe, opts)
    try:
        e.position(fen)
        r = e.search(go, timeout)
    finally:
        e.close()
    r["fen"], r["go"] = fen, go
    return r
