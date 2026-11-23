"""Fable 2026-11-23, server-day plan: the test of run/uciproc.py and run/engine_lines.py (version 2).

    test_uciproc.py <engine exe> <folder with the engine's .cpp files> <serverday folder> <NEW work folder>

The serverday folder is an argument, so that a COPY with one planted change (or this morning's version 1) is
tested the same way. One engine thread, a few seconds. Stand-in engines are small scripts this test writes into
its work folder; they are started through the driver's OWN start code (only the command is exchanged), so the
driver's pipes are the product's.

 L1  the table against the source: every `info string` text of the engine's source is in exactly one of the
     table's three lists, no list holds a text the source does not have, and each is judged as its list says;
     the three `sgerror` forms of the source stop a game
 L2  the real engine, a clean session (uci, options, position, perft 3 = 8,902, eval): no line is refused
 L3  the real engine, each thing it does not take is refused: an unknown option, an invalid value, an invalid
     FEN, an illegal move, a perft depth of 11, a book that is not there, a root restricted to no legal move
 L4  a stand-in that prints 50 lines a second for ever: the wait ends at its limit (1.5 s), not later than 4 s
 L5  a silent stand-in: the wait ends at its limit; and with a cutoff of 1 s inside a limit of 60 s, at 1 s
 L6  stand-in lines: every refusing form, every form not expected on the day, a crash text, a line on the
     error output, an `sgerror`: each is refused; one line of each expected kind: none is refused
"""
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

if len(sys.argv) != 5:
    print(__doc__)
    sys.exit(2)
EXE, SRC, SD, WORK = (Path(a).resolve() for a in sys.argv[1:5])
if WORK.exists():
    print(f"STOP: {WORK} exists already (a NEW work folder)")
    sys.exit(2)
WORK.mkdir(parents=True)
sys.path.insert(0, str(SD / "run"))
import uciproc  # noqa: E402
try:
    import engine_lines  # noqa: E402
except ImportError:
    engine_lines = None

results = []


def check(name: str, ok, detail="") -> bool:
    results.append((name, bool(ok)))
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f": {str(detail)[:300]}" if detail != "" and not ok else ""), flush=True)
    return bool(ok)


# ---------------------------------------------------------------- the stand-in
STANDIN = WORK / "standin.py"
STANDIN.write_text('''import os, sys, threading, time
threading.Timer(25.0, lambda: os._exit(9)).start()          # never outlives its test
mode = sys.argv[1]
say = open(sys.argv[2], encoding="utf-8").read().splitlines() if len(sys.argv) > 2 else []
for cmd in sys.stdin:
    cmd = cmd.strip()
    if cmd == "isready":
        for ln in say:
            if ln.startswith("ERR:"):
                sys.stderr.write(ln[4:] + "\\n"); sys.stderr.flush()
            else:
                print(ln, flush=True)
        print("readyok", flush=True)
    elif cmd == "go" and mode == "flood":
        while True:
            print("info depth 1 score cp 0 nodes 1 pv e2e4", flush=True)
            time.sleep(0.02)
    elif cmd == "go" and mode == "silent":
        time.sleep(30)
    elif cmd == "go" and mode == "long":                       # 300,000 bytes and no line end
        sys.stdout.write("x" * 300000); sys.stdout.flush()
        time.sleep(30)
    elif cmd == "go" and mode == "bytes":                      # a byte outside ASCII
        sys.stdout.buffer.write(b"info depth 1 caf\\xc3\\xa9\\n"); sys.stdout.buffer.flush()
        print("bestmove e2e4", flush=True)
    elif cmd == "go" and mode == "exit7":                      # the engine ends in the middle of an answer
        print("info depth 1 score cp 0 nodes 1 pv e2e4", flush=True)
        os._exit(7)
    elif cmd == "quit":
        os._exit(0)                                            # (the timer thread above would keep a plain end waiting)
os._exit(0)
''', encoding="utf-8", newline="\n")


def standin(mode, lines=None):
    """An Engine made by the driver's own start code, with only the command exchanged."""
    argv = [sys.executable, "-I", "-B", str(STANDIN), mode]
    if lines is not None:
        f = WORK / f"say_{len(list(WORK.glob('say_*')))}.txt"
        f.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        argv.append(str(f))
    real = subprocess.Popen

    def other(cmd, **kw):
        return real(argv, **kw)
    subprocess.Popen = other
    try:
        return uciproc.Engine(STANDIN)
    finally:
        subprocess.Popen = real


def timed(fn, give_up):
    """(seconds, the exception's class name or 'returned' or 'STILL WAITING') of fn, given up after give_up s."""
    box = queue.Queue()

    def run():
        try:
            fn()
            box.put("returned")
        except Exception as e:  # noqa: BLE001
            box.put(type(e).__name__)
    t0 = time.monotonic()
    threading.Thread(target=run, daemon=True).start()
    try:
        how = box.get(timeout=give_up)
    except queue.Empty:
        how = "STILL WAITING"
    return time.monotonic() - t0, how


def refused(eng, what) -> str:
    """'' when the command went through, else the refusal's text."""
    try:
        what(eng)
        return ""
    except uciproc.EngineRefused as e:
        return str(e)


# ---------------------------------------------------------------- L1
texts = set()
for f in sorted(SRC.glob("*.cpp")):
    texts |= set(re.findall(r'"info string ([^"]*)"', f.read_text(encoding="utf-8", errors="replace")))
free = "" in texts
texts.discard("")
check("L1 the source has `info string` texts to judge (at least 20) and one free-text message", len(texts) >= 20 and free, (len(texts), free))
if engine_lines is None:
    check("L1 the table exists (run/engine_lines.py)", False, "no such file in this tree")
else:
    lists = {"allowed": engine_lines.INFO_ALLOWED, "refusing": engine_lines.INFO_REFUSING, "not on the day": engine_lines.INFO_NOT_ON_THE_DAY}
    where = {t: [k for k, v in lists.items() if any(t.startswith(e) for e in v)] for t in texts}
    bad = {t: w for t, w in where.items() if len(w) != 1}
    check("L1 every `info string` text of the source is in exactly one list", not bad, bad)
    stale = [e for v in lists.values() for e in v if not any(t.startswith(e) for t in texts)]
    check("L1 no list holds a text the source does not have", not stale, stale)
    wrong = []
    for t, w in where.items():
        got = engine_lines.why_not("info string " + t + "x")
        want = {"allowed": "", "refusing": "the engine refused", "not on the day": "an engine message the day does not expect"}[w[0] if w else "refusing"]
        if (got == "") != (want == "") or not got.startswith(want):
            wrong.append((t, got[:50]))
    check("L1 each text is judged as its list says", not wrong, wrong)
    check("L1 the free-text message and a new message are not expected",
          engine_lines.why_not("info string anything else") != "" and engine_lines.why_not("info string ") != "")
    sg = set()
    for f in sorted(SRC.glob("*.cpp")):
        sg |= set(re.findall(r'"(sgerror [^"]*)"', f.read_text(encoding="utf-8", errors="replace")))
    check("L1 the source's three `sgerror` forms each stop a game", len(sg) == 3 and all(engine_lines.why_not(s + "3") for s in sg), sorted(sg))

# ---------------------------------------------------------------- L2, L3: the real engine
eng = uciproc.Engine(EXE)
try:
    opts = eng.uci_options()
    check("L2 the engine lists its options (Hash among them)", "Hash" in opts and len(opts) > 20, len(opts))
    clean = refused(eng, lambda e: (e.command("setoption name Hash value 16"), e.command("ucinewgame"),
                                    e.command("position startpos moves e2e4 e7e5"), e.command("eval")))
    check("L2 a clean session: no line refused", clean == "", clean)
    try:
        perft = eng.command("position startpos") + eng.command("go perft 3", 60)
        check("L2 perft 3 from the start = 8,902, no line refused", "nodes 8902" in perft, perft[-3:])
    except uciproc.EngineError as e:
        check("L2 perft 3 from the start = 8,902, no line refused", False, e)
    cases = [("an unknown option", lambda e: e.command("setoption name NoSuchThing value 1"), "unknown option"),
             ("an invalid value", lambda e: e.command("setoption name Hash value many"), "invalid value"),
             ("an invalid FEN", lambda e: e.command("position fen 8/8/8/8/8/8/8/8 w - - 0 1"), "invalid FEN"),
             ("an illegal move", lambda e: e.command("position startpos moves e2e5"), "illegal move"),
             ("a perft depth of 11", lambda e: e.command("go perft 11"), "perft depth"),
             ("a book that is not there", lambda e: e.command("setoption name Book File value " + str(WORK / "no_such.book")), "cannot load book")]
    for name, what, part in cases:
        r = refused(eng, what)
        check(f"L3 {name} is refused", part in r, r or "went through")
        eng.command("position startpos", refuse=False)

    def no_root(e):
        e.command("position startpos")
        e.send("go depth 2 searchmoves e2e5")
        e.read_until(lambda s: s.startswith("bestmove"), 30, "a restricted search")
    try:
        r = refused(eng, no_root)
    except uciproc.EngineError as e:
        r = "NOT REFUSED BUT: " + str(e)
    check("L3 a root restricted to no legal move is refused", "searchmoves restriction" in r, r or "went through")
finally:
    eng.kill()

# ---------------------------------------------------------------- L4, L5: the limits
fl = standin("flood")
try:
    fl.ready(10)
    fl.send("go")
    secs, how = timed(lambda: fl.read_until(lambda s: s.startswith("bestmove"), 1.5, "the flooding stand-in"), 6.0)
    check("L4 50 lines a second for ever: the wait ends at its limit (1.5 s; not later than 4 s)",
          how in ("EngineTimeout", "EngineError") and 1.4 <= secs <= 4.0, (round(secs, 2), how))
finally:
    fl.kill()
si = standin("silent")
try:
    si.ready(10)
    si.send("go")
    secs, how = timed(lambda: si.read_until(lambda s: s.startswith("bestmove"), 1.5, "the silent stand-in"), 6.0)
    check("L5 no line at all: the wait ends at its limit", how in ("EngineTimeout", "EngineError") and 1.4 <= secs <= 4.0, (round(secs, 2), how))
finally:
    si.kill()
si = standin("silent")
try:
    si.ready(10)
    si.send("go")

    def with_cutoff():
        si.read_until(lambda s: s.startswith("bestmove"), 60, "the silent stand-in", cutoff=time.monotonic() + 1.0)
    secs, how = timed(with_cutoff, 6.0)
    check("L5 a cutoff of 1 s inside a limit of 60 s ends the wait at 1 s", how == "EngineTimeout" and 0.9 <= secs <= 3.0, (round(secs, 2), how))
finally:
    si.kill()

# ---------------------------------------------------------------- L6: forms the real engine cannot be made to print
bad_lines = ["info string ERROR NNUE v3: checksum", "info string NNUE v3: no network loaded", "info string V3 VERIFY FAILED at ply 7",
             "info string book move e2e4", "info string loaded book x with 3 entries", "info string loaded nnue x",
             "info string softnodes nodes 2000", "info string TmNodeShare 3", "info string a message of a newer source",
             "Segmentation fault (core dumped)", "terminate called after throwing an instance of 'std::bad_alloc'",
             "ERR:something on the error output", "sgerror nomove ply 31", "sgerror badline go"]
missed = []
for ln in bad_lines:
    e = standin("say", [ln])
    try:
        if not refused(e, lambda x: x.ready(10)):
            missed.append(ln)
    finally:
        e.kill()
check(f"L6 each of {len(bad_lines)} lines that must stop the work is refused", not missed, missed)
good_lines = ["info string NNUE v3 loaded: x 9463528 bytes", "info string NNUE v3 active: 768 checksum 1", "info string eval hce 0 nnue 31 total 31",
              "info string bench depth 11", "sg 17 -35 e2e4 rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
              "sgend result 0 reason fifty plies 212 rows 180", "info depth 3 seldepth 4 score cp 12 nodes 99 pv e2e4",
              "bestmove e2e4 ponder e7e5", "bestmove e7e8q", "id name x", "option name Hash type spin default 32 min 1 max 2048",
              "e2e4: 20", "nodes 8902", ""]
e = standin("say", good_lines)
try:
    r = refused(e, lambda x: x.ready(10))
    check(f"L6 {len(good_lines)} lines of the expected kinds: none is refused", r == "", r)
finally:
    e.kill()

# ---------------------------------------------------------------- L7 to L12: bounded bytes, a clean end
def outcome(fn, give_up):
    """(seconds, the exception's class name or 'returned' or 'STILL WAITING', its text) of fn."""
    box = queue.Queue()

    def run():
        try:
            fn()
            box.put(("returned", ""))
        except Exception as e:  # noqa: BLE001
            box.put((type(e).__name__, str(e)))
    t0 = time.monotonic()
    threading.Thread(target=run, daemon=True).start()
    try:
        how, text = box.get(timeout=give_up)
    except queue.Empty:
        how, text = "STILL WAITING", ""
    return time.monotonic() - t0, how, text


def go_and_wait(mode, secs=10.0, **kw):
    e = standin(mode)
    try:
        e.ready(10)
        e.send("go")
        first = outcome(lambda: e.read_until(lambda s: s.startswith("bestmove"), secs, "the stand-in", **kw), 8.0)
        again = outcome(lambda: e.read_until(lambda s: s.startswith("bestmove"), 30.0, "the stand-in again"), 4.0)
        return first, again
    finally:
        e.kill()


(secs, how, text), _ = go_and_wait("long")
check("L7 300,000 bytes without a line end: an error that names the long line, within 5 s (not a wait to the limit)",
      how == "EngineError" and "more than" in text and secs <= 5.0, (round(secs, 2), how, text[:120]))
(secs, how, text), _ = go_and_wait("bytes")
check("L8 a byte outside ASCII: an error that says so (never a replaced character that passes)",
      how == "EngineError" and "outside ASCII" in text, (round(secs, 2), how, text[:120]))
(secs, how, text), (secs2, how2, text2) = go_and_wait("exit7")
check("L9 the engine ends inside an answer: an error with its exit code 7", how == "EngineError" and "exit code 7" in text, (how, text[:120]))
check("L9 the NEXT wait on an ended engine fails at once (not after its 30 s)", how2 == "EngineError" and secs2 <= 2.0, (round(secs2, 2), how2))
try:
    (secs, how, text), _ = go_and_wait("flood", max_lines=20)
except TypeError as e:
    secs, how, text = 0.0, "TypeError", str(e)
check("L10 more lines than one wait allows (20): an error that says so, long before the 10 s limit",
      how == "EngineError" and "lines and no end" in text and secs <= 4.0, (round(secs, 2), how, text[:120]))
e = standin("say", [])
try:
    try:
        e.send("setoption name Hash value 16\nquit")
        sent_two = "went through"
    except uciproc.EngineError as x:
        sent_two = "refused: " + str(x)
    check("L11 a command with a line break inside is never sent", sent_two.startswith("refused"), sent_two)
    try:
        e.send("setoption name NNUEArchFile value café.fnn3")
        sent_odd = "went through"
    except uciproc.EngineError as x:
        sent_odd = "refused: " + str(x)
    except Exception as x:  # noqa: BLE001
        sent_odd = "another error: " + type(x).__name__
    check("L11 a command with a character outside ASCII is never sent", sent_odd.startswith("refused"), sent_odd)
finally:
    e.kill()
before = threading.active_count()
e = standin("say", [])
e.ready(10)
code = e.quit(10)
time.sleep(0.3)
check("L12 after quit(): exit code 0, both pipes closed, the reader thread ended",
      code == 0 and e.p.stdin.closed and e.p.stdout.closed and threading.active_count() <= before,
      (code, e.p.stdin.closed, e.p.stdout.closed, threading.active_count(), before))
before = threading.active_count()
e = standin("silent")
e.ready(10)
e.send("go")
e.kill()
time.sleep(0.3)
check("L12 after kill() in the middle of a search: both pipes closed, the reader thread ended",
      e.p.stdin.closed and e.p.stdout.closed and threading.active_count() <= before,
      (e.p.stdin.closed, e.p.stdout.closed, threading.active_count(), before))
try:
    uciproc.Engine(WORK / "no_such_engine")
    missing = "started"
except uciproc.EngineError as x:
    missing = "EngineError: " + str(x)
except Exception as x:  # noqa: BLE001
    missing = "another error: " + type(x).__name__
check("L12 an engine file that is not there: an EngineError, not a traceback of another kind", missing.startswith("EngineError"), missing)

bad = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(bad)} of {len(results)} checks pass")
print("ALL " + str(len(results)) + " CHECKS PASS" if not bad else "FAILED: " + "; ".join(bad))
sys.exit(1 if bad else 0)
