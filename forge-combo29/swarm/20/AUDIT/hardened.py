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

# Seat 19's sweep and my own S-C47 both turned on the same gap: a claimed behaviour cannot be re-checked if the file
# does not say WHICH BINARY produced it. This helper exists so every job can stamp its exe identity in one line.
import hashlib as _hashlib


def exe_identity(exe):
    """sha256 + `id name` for the executable, as a dict ready to dump into any job's meta/json."""
    h = _hashlib.sha256()
    try:
        with open(exe, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
    except OSError:
        return {"exe": exe, "sha256": None, "id_name": None}
    eng = Engine(exe) if "Engine" in globals() else None
    name = None
    if eng is not None:
        try:
            with eng.lock:
                for line in eng.lines:
                    if line.startswith("id name "):
                        name = line[len("id name "):]
                        break
        finally:
            eng.close()
    return {"exe": exe, "sha256": h.hexdigest(), "id_name": name}


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

    def isready(self, timeout=20.0):
        self.send("isready")
        _, ok = self.expect("readyok", timeout)
        if not ok:
            raise RuntimeError("no readyok — refusing to continue (19-F12 discipline)")

    def position(self, fen, ready_timeout=20.0):
        self.isready(ready_timeout)
        self.send(f"position fen {fen}")
        self.isready(ready_timeout)   # position has no answer; this isready is the readback

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


# --- regime guards (added after seat 30's extras-only bug, S-F65) -------------------------------------------------
# A settings list that is wrong-by-construction produces a plausible score and a legal move, so nothing downstream
# catches it. These assertions name what a regime MUST contain, so a config is checked where it is built.
REGIME_REQUIRED = {
    "S14": ["LmrQuietBase", "LmrQuietDivisor", "LmrNoisyBase", "LmrNoisyDivisor", "LmrHistoryDivisor",
            "NullMoveBase", "LmpBase", "HistoryPruneMultiplier", "HistoryBonusQuadratic", "HistoryBonusLinear",
            "HistoryBonusMax", "SingularDepth", "IirDepth", "NonPawnCorrection"],
    "PC20": ["CuckooRep", "HistRework", "TtPruneV2", "CorrHistV2", "MateAlphaGuard"],
    "base": ["Threads", "Hash"],
}


def assert_regime(opts, name):
    """Fail loudly if `opts` does not actually contain the settings that `name` claims.

    assert_regime(pc20_list, "PC20")  ->  raises if S14's 14 settings, the 5 extra switches or Threads/Hash are missing.
    This is the check that would have caught an extras-only "PC20" at the moment it was built.
    """
    have = {k for k, _ in opts}
    missing = []
    if name in ("S14", "PC20"):
        missing += [k for k in REGIME_REQUIRED["S14"] if k not in have]
    if name == "PC20":
        missing += [k for k in REGIME_REQUIRED["PC20"] if k not in have]
    missing += [k for k in REGIME_REQUIRED["base"] if k not in have]
    if missing:
        raise AssertionError(f"regime {name!r} is missing {missing} — this config does not mean what its name says")
    return True
