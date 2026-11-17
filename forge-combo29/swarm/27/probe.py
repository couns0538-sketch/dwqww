#!/usr/bin/env python3
"""probe.py — a safe-by-default UCI probe for AD-HOC use.

WHY THIS EXISTS. Every one of my three "guard I have to remember to run" failures happened in **ad-hoc probe
code**, not in committed harnesses:

  1. the settings script nobody called (S-W7/S-W8)                     - ad-hoc harness
  2. `grep -rl 'raise Missing'` never run on my own folder (S-C65)     - ad-hoc
  3. FEN validation, present in my main harnesses, absent in the probes that found S-C84 - ad-hoc

That is not an accident of attention. **A committed harness is written once and re-run; a probe is written in
30 seconds to answer one question and then thrown away.** The probe is exactly the code that has no time for
discipline, and it is also the code that most often produces a number I then believe.

**So the guard has to be in the API, not in the habit.** Importing this module means:

  * every FEN is validated with python-chess BEFORE it reaches the engine;
  * the reply is scanned for `invalid FEN` and the probe ABORTS rather than returning a substituted answer;
  * the option list is applied with its count asserted;
  * a search that produces no `info depth` line raises rather than returning an empty parse.

The second is the S-C84 defence specifically: the engine *tells you* it refused the FEN, and a probe that does
not read that line has no defence at all.

USAGE
    from probe import Engine
    with Engine(EXE, settings="PC20", depth=12) as e:
        r = e.search("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        print(r.depth, r.score, r.bestmove, r.nodes)

`e.search` returns a Result or raises. There is no path that returns a number from a position the engine did
not accept.
"""
import re
import subprocess
import sys
import time

import chess

S14 = ["LmrQuietBase 93", "LmrQuietDivisor 205", "LmrNoisyBase 13", "LmrNoisyDivisor 333",
       "LmrHistoryDivisor 5643", "NullMoveBase 5", "LmpBase 8", "HistoryPruneMultiplier 2220",
       "HistoryBonusQuadratic 24", "HistoryBonusLinear 54", "HistoryBonusMax 2212",
       "SingularDepth 6", "IirDepth 2", "NonPawnCorrection true"]
PC20X = ["CuckooRep true", "HistRework 2", "TtPruneV2 true", "CorrHistV2 true",
         "MateAlphaGuard true", "OwnBook false"]
SETTINGS = {
    "none": ["Hash 16", "Threads 1", "OwnBook false"],
    "S14": ["Hash 16", "Threads 1", "OwnBook false"] + S14,
    "PC20": ["Hash 16", "Threads 1"] + S14 + PC20X,
}
EXPECT = {"none": 3, "S14": 17, "PC20": 22}


class ProbeError(Exception):
    """Anything that means 'do not trust the number you were about to record'."""


class Result:
    __slots__ = ("depth", "seldepth", "score", "nodes", "bestmove", "pv", "n_info", "last", "secs")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))

    def __repr__(self):
        return "Result(depth=%s, score=%s, nodes=%s, bestmove=%s, pv=%d)" % (
            self.depth, self.score, self.nodes, self.bestmove, len(self.pv or []))


def validate_fen(fen):
    """Refuse anything python-chess calls invalid. This is the S-C59 rule, applied before the engine sees it."""
    fields = fen.split()
    if len(fields) < 4:
        raise ProbeError("FEN has %d fields, needs at least 4: %r" % (len(fields), fen))
    try:
        b = chess.Board(fen)
    except ValueError as e:
        raise ProbeError("python-chess refused %r: %s" % (fen, e))
    if not b.is_valid():
        raise ProbeError("python-chess: invalid position (%s): %r" % (b.status(), fen))
    return b


class Engine:
    def __init__(self, exe, settings="PC20", depth=None, timeout=300):
        self.exe = exe
        self.settings_name = settings
        self.opts = SETTINGS[settings]
        self.expect = EXPECT[settings]
        self.depth = depth
        self.timeout = timeout
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)

    def _send(self, s):
        self.p.stdin.write(s + "\n"); self.p.stdin.flush()

    def _start_reader(self):
        """Start the single stdout reader thread for this engine session, once."""
        import queue
        import threading
        self._q = queue.Queue()
        q = self._q

        def reader():
            # explicit readline() delivers each line as it arrives; iterating the stream did not.
            try:
                while True:
                    ln = self.p.stdout.readline()
                    if not ln:
                        break
                    q.put(ln)
                q.put(None)
            except Exception:
                q.put(None)

        threading.Thread(target=reader, daemon=True).start()

    def _until(self, pred, tmo=None):
        """Read lines until `pred`, with a timeout THAT CAN ACTUALLY FIRE.

        The first version looped `while time.monotonic() - t0 < tmo: readline()`. That timeout is unreachable:
        `readline()` BLOCKS, so when the child has nothing to say the process sits there for ever and the
        deadline is never re-tested. It hung on the very first self-test control.

        A blocking-read timeout is a timeout in name only - the same class as a control that cannot fail. This
        version puts the read in a thread and waits on the deadline itself, so a silent child produces a
        timeout instead of a hang.
        """
        tmo = tmo if tmo is not None else self.timeout
        # ONE reader thread for the whole session. The first version started a NEW reader on every _until
        # call, so two threads competed for the same pipe: whichever was still alive from the previous call
        # could swallow the line the new call was waiting for. That is why the fake engine answered
        # `uciok` and then appeared to ignore `isready` - the second thread was stealing from the first.
        if getattr(self, "_q", None) is None:
            self._start_reader()
        q = self._q
        t0 = time.monotonic(); out = []
        while True:
            remaining = tmo - (time.monotonic() - t0)
            if remaining <= 0:
                return out, False
            try:
                ln = q.get(timeout=min(remaining, 1.0))
            except queue.Empty:
                if self.p.poll() is not None:
                    # child died: drain whatever is queued, then give up
                    while True:
                        try:
                            ln = q.get_nowait()
                        except queue.Empty:
                            break
                        if ln is None:
                            break
                        y = ln.rstrip("\n"); out.append(y)
                        if pred(y):
                            return out, True
                    return out, False
                continue
            if ln is None:
                return out, False
            y = ln.rstrip("\n"); out.append(y)
            if pred(y):
                return out, True

    def __enter__(self):
        self._send("uci")
        lines, ok = self._until(lambda x: x.strip() == "uciok", 30)
        if not ok:
            raise ProbeError("no uciok")
        adv = {m.group(1) for m in (re.match(r"option name (.+?) type ", l) for l in lines) if m}
        applied = 0
        for item in self.opts:
            name, _, val = item.rpartition(" ")
            if name not in adv:
                raise ProbeError("option %r is not advertised by this engine" % name)
            self._send("setoption name %s value %s" % (name, val))
            self._send("isready")
            l2, ok2 = self._until(lambda x: x.strip() == "readyok", 30)
            if not ok2:
                raise ProbeError("no readyok after %r" % item)
            for l in l2:
                if "unknown option" in l or "invalid value" in l:
                    raise ProbeError("bad option %r: %s" % (item, l))
            applied += 1
        if applied != self.expect:
            raise ProbeError("applied %d options, %r promises %d"
                             % (applied, self.settings_name, self.expect))
        self.n_applied = applied
        self._send("ucinewgame"); self._send("isready")
        self._until(lambda x: x.strip() == "readyok", 30)
        return self

    def __exit__(self, *exc):
        try:
            self._send("stop"); self._send("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()
        return False

    def search(self, fen, limit=None, validate=True):
        """Search one position. Raises ProbeError rather than returning a substituted answer."""
        if validate:
            validate_fen(fen)
        self._send("position fen " + fen)
        self._send("isready")
        pos_lines, ok = self._until(lambda x: x.strip() == "readyok", 30)
        if not ok:
            raise ProbeError("no readyok after position")
        # THE DIAGNOSTIC ARRIVES HERE, before readyok - not during the search. The first version scanned only
        # the `go` output and therefore MISSED it entirely on a real engine, returning a startpos result with
        # no error at all (control 5 failed and that is what found this). A harness that sends `isready`
        # between `position` and `go` - which is the normal defensive pattern - loses the only signal the
        # engine gives.
        for l in pos_lines:
            low = l.lower()
            if "invalid fen" in low or "illegal fen" in low:
                raise ProbeError("ENGINE REFUSED THE FEN (diagnosed before the search): %s\n"
                                 "  (S-C84: any answer would describe the PREVIOUS position)\n"
                                 "  fen sent: %r" % (l, fen))
        go = limit or ("go depth %d" % self.depth if self.depth else "go depth 10")
        self._send(go)
        t0 = time.monotonic()
        lines, ok = self._until(lambda x: x.startswith("bestmove"))
        secs = time.monotonic() - t0
        if not ok:
            raise ProbeError("no bestmove within %ds for %r" % (self.timeout, go))

        # THE S-C84 DEFENCE: the engine diagnoses a refused FEN and then searches the PREVIOUS position.
        # A probe that ignores this line records the wrong board's answer under this board's name.
        for l in lines:
            low = l.lower()
            if "invalid fen" in low or "illegal fen" in low:
                raise ProbeError("ENGINE REFUSED THE FEN and searched a different position: %s\n"
                                 "  (this is S-C84: the answer describes the PREVIOUS position)\n"
                                 "  fen sent: %r" % (l, fen))

        infos = [l for l in lines if l.startswith("info depth")]
        if not infos:
            raise ProbeError("no 'info depth' line for %r on %r" % (go, fen))
        last = infos[-1]
        d = re.search(r"info depth (\d+)", last)
        sd = re.search(r"seldepth (\d+)", last)
        sc = re.search(r"score (cp|mate) (-?\d+)", last)
        nd = re.search(r"nodes (\d+)", last)
        pv = []
        if " pv " in last:
            pv = last.split(" pv ", 1)[1].split()
        bm = next(l for l in lines if l.startswith("bestmove")).split()
        return Result(depth=int(d.group(1)) if d else None,
                      seldepth=int(sd.group(1)) if sd else None,
                      score=(sc.group(1), int(sc.group(2))) if sc else None,
                      nodes=int(nd.group(1)) if nd else None,
                      bestmove=bm[1] if len(bm) > 1 else None,
                      pv=pv, n_info=len(infos), last=last, secs=secs)


def _selftest(exe=None):
    """Prove the guards fire. Uses a FAKE engine for the reply guard so the test needs no real binary."""
    import os
    ok = True

    def chk(name, cond, detail=""):
        nonlocal ok
        print("  %-58s %s %s" % (name, "PASS" if cond else "FAIL", detail))
        if not cond:
            ok = False

    print("probe.py self-test:")

    try:
        validate_fen("8/8/8/8/8/8/1k6/K7 w - - 0 1")
        chk("1 illegal FEN refused before reaching the engine", False)
    except ProbeError:
        chk("1 illegal FEN refused before reaching the engine", True)

    try:
        validate_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        chk("2 a valid FEN passes", True)
    except ProbeError as e:
        chk("2 a valid FEN passes", False, str(e))

    # The fake engine is a COMMITTED FIXTURE, not a tempfile. The tempfile version could not be inspected
    # when it failed (it was deleted in `finally`), and it buffered stdout when piped, so the self-test waited
    # 30 s on "no uciok". A fixture you can run by hand is worth ten minutes of reading your own reader.
    fixture = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "fake_refusing_engine.py")
    if not os.path.exists(fixture):
        chk("3 invalid-FEN reply guard fires on a refused FEN", False, "fixture missing")
        return ok
    with Engine(fixture, settings="none", depth=1, timeout=15) as e:
        try:
            e.search("8/8/8/8/8/8/1k6/K7 w - - 0 1", validate=False)
            chk("3 invalid-FEN reply guard fires on a refused FEN", False, "it returned a result")
        except ProbeError as ex:
            chk("3 invalid-FEN reply guard fires on a refused FEN", "REFUSED" in str(ex))

    if exe:
        with Engine(exe, settings="PC20", depth=8) as e:
            r = e.search("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            chk("4 a real search returns a parseable result", r.bestmove is not None,
                "%r" % (r,))
        # control 5: a REAL engine is caught when the guard is disabled and the FEN is illegal
        with Engine(exe, settings="PC20", depth=4) as e:
            try:
                e.search("8/8/8/8/8/8/1k6/K7 w - - 0 1", validate=False)
                chk("5 REAL engine's refused-FEN reply is caught", False,
                    "(this engine may not refuse the FEN)")
            except ProbeError as ex:
                chk("5 REAL engine's refused-FEN reply is caught", "REFUSED" in str(ex))
    return ok


if __name__ == "__main__":
    sys.exit(0 if _selftest(sys.argv[1] if len(sys.argv) > 1 else None) else 1)
