#!/usr/bin/env python3
"""UCI-level checks of the Syzygy options (job C1).

  uci_tb_smoke.py <forge exe> <tablebase dir (3-4 or 3-4-5 piece set)> [threads]

- `uci` advertises SyzygyPath, SyzygyProbeDepth, Syzygy50MoveRule;
- SyzygyPath with a missing folder, an empty value and the real folder report
  the expected "info string Syzygy..." lines and never crash;
- a won KQvK root reports the tablebase win score, a drawn KRvKR root 0;
- a root with castling rights (not probed) and endgames above the table size
  search normally; with `threads` > 1 these run multi-threaded (TSan job);
- every search ends with exactly one legal-looking bestmove.
Exit status 0 = all checks passed.
"""
import subprocess
import sys
import threading
import queue

TB_WIN_SHOWN = 32000 - 128 - 2  # TbWin - 1


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
        self.q = queue.Queue()
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        for line in self.p.stdout:
            self.q.put(line.rstrip("\n"))
        self.q.put(None)

    def send(self, cmd):
        self.p.stdin.write(cmd + "\n")
        self.p.stdin.flush()

    def until(self, prefix, timeout=300):
        lines = []
        while True:
            line = self.q.get(timeout=timeout)
            if line is None:
                raise RuntimeError("engine exited; last lines: %s" % lines[-5:])
            lines.append(line)
            if line.startswith(prefix):
                return lines

    def sync(self):
        self.send("isready")
        return self.until("readyok")

    def close(self):
        self.send("quit")
        self.p.wait(timeout=60)
        return self.p.returncode


failures = 0


def check(ok, what):
    global failures
    print(("PASS " if ok else "FAIL ") + what)
    if not ok:
        failures += 1


def last_score(lines):
    score = None
    for line in lines:
        parts = line.split()
        if parts[:1] == ["info"] and "score" in parts:
            i = parts.index("score")
            score = (parts[i + 1], int(parts[i + 2]))
    return score


def search(e, fen, go):
    e.send("position fen " + fen)
    e.send(go)
    lines = e.until("bestmove")
    best = lines[-1].split()[1]
    return lines, best


def main():
    exe, tb = sys.argv[1], sys.argv[2]
    threads = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    e = Engine(exe)
    e.send("uci")
    lines = e.until("uciok")
    for opt in ("option name SyzygyPath type string default <empty>",
                "option name SyzygyProbeDepth type spin default 1 min 1 max 10",
                "option name Syzygy50MoveRule type check default true"):
        check(opt in lines, "advertised: " + opt)
    e.send("setoption name Threads value %d" % threads)
    e.send("setoption name SyzygyPath value /no/such/folder/for/forge")
    lines = e.sync()
    check(any("info string Syzygy: 0 WDL and 0 DTZ tables, up to 0 pieces" in l for l in lines), "missing folder reported")
    e.send("setoption name SyzygyPath value")
    lines = e.sync()
    check(any("info string Syzygy tablebases off" in l for l in lines), "empty value switches tables off")
    e.send("setoption name SyzygyPath value " + tb)
    lines = e.sync()
    loaded = [l for l in lines if l.startswith("info string Syzygy:")]
    check(len(loaded) == 1 and " 0 WDL" not in loaded[0], "tables loaded: " + (loaded[0] if loaded else "none"))
    e.send("ucinewgame")
    e.sync()

    lines, best = search(e, "4k3/8/8/8/8/8/8/4K2Q w - - 0 1", "go depth 10")
    check(last_score(lines) == ("cp", TB_WIN_SHOWN) and best != "0000", "KQvK root reports the TB win, best %s" % best)
    lines, best = search(e, "4k3/8/8/8/8/8/r7/4K2R w - - 0 1", "go depth 10")
    check(last_score(lines) == ("cp", 0) and best != "0000", "KRvKR root reports the draw, best %s" % best)
    lines, best = search(e, "4k3/8/8/8/8/8/8/4K2R w K - 0 1", "go depth 10")
    check(best != "0000" and last_score(lines) is not None, "castling root searched normally, best %s score %s" % (best, last_score(lines)))
    for fen in ("8/4k3/8/8/2K5/8/1P4R1/r7 w - - 0 1", "4k3/8/8/8/3r4/8/3Q4/3RK2n w - - 0 1",
                "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1", "8/8/8/2k5/3pP3/8/8/4K3 b - e3 0 1"):
        lines, best = search(e, fen, "go depth 12")
        check(best != "0000", "searched %s -> %s" % (fen, best))
    e.send("setoption name SyzygyProbeDepth value 5")
    e.send("setoption name Syzygy50MoveRule value false")
    lines, best = search(e, "4k3/8/8/8/3r4/8/3Q4/3RK2n w - - 0 1", "go movetime 300")
    check(best != "0000", "SyzygyProbeDepth 5 / Syzygy50MoveRule false: searched -> %s" % best)
    e.send("setoption name SyzygyPath value <empty>")
    lines = e.sync()
    check(any("info string Syzygy tablebases off" in l for l in lines), "<empty> switches tables off")
    lines, best = search(e, "4k3/8/8/8/8/8/8/4K2Q w - - 0 1", "go depth 8")
    sc = last_score(lines)
    check(best != "0000" and sc is not None and sc[1] != TB_WIN_SHOWN, "tables off: plain search score %s" % (sc,))
    rc = e.close()
    check(rc == 0, "engine exit code %s" % rc)
    print("uci_tb_smoke: %d failures" % failures)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
