"""Fable 2026-11-23, server-day plan: the test of run/uciproc.py and run/engine_lines.py (version 2, second
edition after the reads of Astra `134620Z` and Neon `134912Z`: L13 to L20 are their reproductions).

    test_uciproc.py <engine exe> <folder with the engine's source (.cpp, .h, .hpp)> <serverday folder> <NEW work folder>

The serverday folder is an argument, so that a COPY with one planted change (or an earlier version) is tested the
same way. One engine thread, about a minute. Stand-in engines are small scripts this test writes into its work
folder; they are started through the driver's OWN start code (only the command is exchanged), so the driver's
pipes are the product's.

 L1  the table against the source: every `info string` text of the engine's source is in exactly one of the
     table's three lists, no list holds a text the source does not have, each is judged as its list says, and
     an allowed message that is bare or cut off is refused; the three `sgerror` forms of the source stop a game
 L2  the real engine, a clean session (uci, options, position, perft 3 = 8,902, eval): no line is refused
 L3  the real engine, each thing it does not take is refused: an unknown option, an invalid value, an invalid
     FEN, an illegal move, a perft depth of 11, a book that is not there, a root restricted to no legal move
 L4  a stand-in that prints 50 lines a second for ever: the wait ends at its limit (1.5 s), not later than 4 s
 L5  a silent stand-in: the wait ends at its limit; and with a cutoff of 1 s inside a limit of 60 s, at 1 s
 L6  stand-in lines: every refusing form, every form not expected on the day, a crash text, a line on the
     error output, an `sgerror`: each is refused; whole lines of each expected kind, as the engine printed them
     in the PC's clean runs: none is refused
 L7  300,000 bytes without a line end; L8 a byte outside ASCII; L9 the engine ends inside an answer; L10 the
     line bound of one wait; L11 a command with a line break or a character outside ASCII; L12 the end
 L13 a last line WITHOUT its line end from an engine that ended is an error, never a finished answer
 L14 the output closes while the process lives on: the wait still ends within its own time
 L15 a cutoff that has passed: command(), ready() and uci_options() send NOT ONE BYTE (the stand-in writes down
     every byte it receives) and the engine is usable afterwards
 L16 a NUL, a CR in the middle of a line, an escape, a DEL: refused when the engine writes one, never sent in a
     command, and refused by the table
 L17 after the line bound or a timeout the NEXT call fails at once and never reads the left-over lines; a limit
     that is not finite and a line bound of 0 are refused
 L19 `info string ERROR NNUE v3` followed by exit code 2 is reported as that refusal WITH the exit code; an
     `sgerror` with no end line is refused at once, not at the limit
 L20 the table on whole and on cut lines: every whole native line passes, every cut or altered one is refused
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
TIMEOUT = getattr(uciproc, "EngineTimeout", ())    # an earlier version has no such class: then nothing is caught


def check(name: str, ok, detail="") -> bool:
    results.append((name, bool(ok)))
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f": {str(detail)[:300]}" if detail != "" and not ok else ""), flush=True)
    return bool(ok)


def judged(line):
    """The table's word on a line; None when this tree has no table (then every table check fails)."""
    return engine_lines.why_not(line) if engine_lines is not None else None


# whole lines exactly as the frozen engine printed them in the PC's clean runs (the net's path exchanged)
NET = ("v3 {} hidden 768 king_buckets 8 mirrored output_buckets 8 standalone eval_scale 400 checksum 290bbb0b2e578ac "
       "max|w1| 559 max|b1| 432 max|w2| 127 kernel {}")
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -"
SGEND = f"sgend result 0 reason rule plies 8 run 0 searches 0 nodes 0 fen {START} 8 5 moves"
WHOLE = ["info string NNUE v3 loaded: " + NET.format("D:/nets/cand.fnn3", "avx512"),
         "info string NNUE v3 active: " + NET.format("/srv/day one/net v3/cand.fnn3", "avx2"),
         "info string eval hce 0 nnue 31 total 31", "info string eval hce 0 nnue -412 total -412 incheck 1",
         "info string bench depth 11 nodes 312866 time 163 nps 1919423",
         "sg 8 21 b1c3 r1bqkb1r/1ppp1ppp/p1n2n2/4p3/B3P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 2 5",
         "sg 9 -13 b7b5 r1bqkb1r/1ppp1ppp/p1n2n2/4p3/B3P3/2N2N2/PPPP1PPP/R1BQK2R b KQkq - 3 5",
         SGEND, "sgend result -1 reason mate plies 8 run 0 searches 0 nodes 0 fen "
         "rnb1kbnr/ppp2pp1/3pp2p/8/6Pq/1PN2P2/P1PPP2P/R1BQKBNR w KQkq - 1 5 moves",
         "sgend result 1 reason evallimit plies 10 run 0 searches 3 nodes 6021 fen 3B1r2/8/2k3R1/pp6/8/5P2/P7/1K1R4 b - - 2 43 moves f3d4 e5d4",
         "info depth 1 seldepth 1 score cp -15 nodes 23 nps 0 hashfull 0 time 0 pv d2d4",
         "bestmove e2e4", "bestmove e2e4 ponder e7e5", "bestmove e7e8q", "id name Chess Engine Forge 6.4.24 candidate",
         "option name Hash type spin default 32 min 1 max 2048", "e2e4: 20", "nodes 8902", "readyok", "uciok", ""]
CUT = ["info string NNUE v3 loaded: ", "info string NNUE v3 active: ", "info string eval hce ", "info string bench depth ",
       "info string NNUE v3 loaded: x 9463528 bytes", "info string NNUE v3 active: 768 checksum 1",
       "info string NNUE v3 loaded: " + NET.format("D:/nets/cand.fnn3", "avx512")[:-12],
       "info string NNUE v3 loaded: " + NET.format("D:/nets/cand.fnn3", "sse2"),
       "info string eval hce 0 nnue 31", "info string eval hce 0 nnue 31 total", "info string eval hce 0 nnue 31 total 31 incheck 0",
       "info string bench depth 11", "info string bench depth 11 nodes 312866 time 163",
       "sgend result -0 reason rule plies 8 run 0 searches 0 nodes 0 fen " + START + " 8 5 moves",
       "sgend result 2 reason rule plies 8 run 0 searches 0 nodes 0 fen " + START + " 8 5 moves",
       "sgend result 0 reason fifty plies 8 run 0 searches 0 nodes 0 fen " + START + " 8 5 moves",
       "sgend result 0 reason rule plies 1 x", "sgend result 0 reason fifty plies 212 rows 180",
       SGEND[:-6], SGEND + " e2", "sg 17 -35 e2e4", "sg 17 -35 e2e4 " + START, "sg 17 e2e4 " + START + " 0 1",
       "bestmove", "bestmove e2", "bestmove 0000", "id name", "nodes", "e2e4:", "readyok ", " uciok"]

# ---------------------------------------------------------------- the stand-in
STANDIN = WORK / "standin.py"
STANDIN.write_text('''import os, sys, threading, time
threading.Timer(25.0, lambda: os._exit(9)).start()          # never outlives its test
mode = sys.argv[1]
say = open(sys.argv[2], encoding="utf-8").read().splitlines() if len(sys.argv) > 2 and sys.argv[2] != "-" else []
got = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != "-" else None
def put(b):                                                    # raw bytes, one LF as the line end
    sys.stdout.buffer.write(b); sys.stdout.buffer.flush()
for raw in sys.stdin.buffer:
    if got:
        with open(got, "ab") as g:                             # every byte that arrived, as it arrived
            g.write(raw)
    cmd = raw.strip().decode("latin-1")
    if cmd == "isready":
        for ln in say:
            if ln.startswith("ERR:"):
                sys.stderr.write(ln[4:] + "\\n"); sys.stderr.flush()
            else:
                print(ln, flush=True)
        print("readyok", flush=True)
    elif cmd == "uci":
        print("id name stand-in", flush=True); print("uciok", flush=True)
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
        put(b"info depth 1 caf\\xc3\\xa9\\n")
        print("bestmove e2e4", flush=True)
    elif cmd == "go" and mode == "exit7":                      # the engine ends in the middle of an answer
        print("info depth 1 score cp 0 nodes 1 pv e2e4", flush=True)
        os._exit(7)
    elif cmd == "go" and mode == "cutline":                    # the ending line WITHOUT its line end, then the end
        put(b"bestmove e2e4")
        os._exit(7)
    elif cmd == "go" and mode == "closed":                     # the output closes, the process lives on
        sys.stdout.flush()
        for fd in (1, 2):
            try:
                os.close(fd)
            except OSError:
                pass
        time.sleep(10)
    elif cmd == "go" and mode.startswith("ctl:"):              # one control byte in the middle of a line
        put(b"info depth 1 score cp 0 nodes 1 pv e2e4" + bytes.fromhex(mode[4:]) + b" e7e5\\n")
        put(b"bestmove e2e4\\n")
    elif cmd == "go" and mode == "ten":                        # ten lines and the end, at once
        put(b"".join(b"info depth %d score cp 0 nodes 1 pv e2e4\\n" % d for d in range(1, 11)) + b"bestmove e2e4\\n")
    elif cmd == "go" and mode == "slow":                       # the answer comes after one second
        time.sleep(1.0)
        put(b"bestmove e2e4\\n")
    elif cmd == "go" and mode == "err2":                       # the engine's own refusal of a net, then exit code 2
        put(b"info string ERROR NNUE v3: the file is not a v3 net\\n")
        os._exit(2)
    elif cmd == "go" and mode == "sgerr":                      # a game given up: no end line follows
        put(b"sgerror noscore ply 9 searches 1 nodes 0 fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\\n")
        time.sleep(20)
    elif cmd == "quit":
        os._exit(0)                                            # (the timer thread above would keep a plain end waiting)
os._exit(0)
''', encoding="utf-8", newline="\n")


def standin(mode, lines=None, got=None):
    """An Engine made by the driver's own start code, with only the command exchanged."""
    argv = [sys.executable, "-I", "-B", str(STANDIN), mode, "-", "-"]
    if lines is not None:
        f = WORK / f"say_{len(list(WORK.glob('say_*')))}.txt"
        f.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        argv[5] = str(f)
    if got is not None:
        argv[6] = str(got)
    real = subprocess.Popen

    def other(cmd, **kw):
        return real(argv, **kw)
    subprocess.Popen = other
    try:
        return uciproc.Engine(STANDIN)
    finally:
        subprocess.Popen = real


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


def timed(fn, give_up):
    secs, how, _ = outcome(fn, give_up)
    return secs, how


def refused(eng, what) -> str:
    """'' when the command went through, else the refusal's text."""
    try:
        what(eng)
        return ""
    except uciproc.EngineRefused as e:
        return str(e)


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


# ---------------------------------------------------------------- L1
sources = [f for d in (SRC, SRC.parent / "include") if d.is_dir() for pat in ("*.cpp", "*.h", "*.hpp") for f in sorted(d.rglob(pat))]
texts, sg = set(), set()
for f in sources:
    body = f.read_text(encoding="utf-8", errors="replace")
    texts |= set(re.findall(r'"info string ([^"]*)"', body))
    sg |= set(re.findall(r'"(sgerror [^"]*)"', body))
free = "" in texts
texts.discard("")
check("L1 the source has `info string` texts to judge (at least 20) and one free-text message", len(texts) >= 20 and free,
      (len(texts), free, len(sources)))
if engine_lines is None:
    check("L1 the table exists (run/engine_lines.py)", False, "no such file in this tree")
else:
    lists = {"allowed": engine_lines.INFO_ALLOWED, "refusing": engine_lines.INFO_REFUSING, "not on the day": engine_lines.INFO_NOT_ON_THE_DAY}
    where = {t: [k for k, v in lists.items() if any(t.startswith(e) for e in v)] for t in texts}
    bad = {t: w for t, w in where.items() if len(w) != 1}
    check("L1 every `info string` text of the source is in exactly one list", not bad, bad)
    stale = [e for v in lists.values() for e in v if not any(t.startswith(e) for t in texts)]
    check("L1 no list holds a text the source does not have", not stale, stale)
    wrong, bare = [], []
    for t, w in where.items():
        kind = w[0] if w else "refusing"
        got = engine_lines.why_not("info string " + t + "x")
        if kind == "allowed":            # the source's text alone is only the START of a message: never a whole one
            if got == "" or engine_lines.why_not("info string " + t) == "":
                bare.append(t)
            continue
        want = {"refusing": "the engine refused", "not on the day": "an engine message the day does not expect"}[kind]
        if not got.startswith(want):
            wrong.append((t, got[:50]))
    check("L1 each refusing text and each text not expected on the day is judged as its list says", not wrong, wrong)
    check("L1 an allowed message that is bare or cut off after its first words is refused", not bare, bare)
    check("L1 the free-text message and a new message are not expected",
          engine_lines.why_not("info string anything else") != "" and engine_lines.why_not("info string ") != "")
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
    except uciproc.EngineError:
        pass                                 # refused in another class (a game given up ends the object's use)
    finally:
        e.kill()
check(f"L6 each of {len(bad_lines)} lines that must stop the work is refused", not missed, missed)
e = standin("say", WHOLE)
try:
    r = refused(e, lambda x: x.ready(10))
    check(f"L6 {len(WHOLE)} whole lines of the expected kinds, as the engine printed them: none is refused", r == "", r)
finally:
    e.kill()

# ---------------------------------------------------------------- L7 to L12: bounded bytes, a clean end
(secs, how, text), _ = go_and_wait("long")
check("L7 300,000 bytes without a line end: an error that names the long line, within 5 s (not a wait to the limit)",
      how == "EngineError" and "more than" in text and secs <= 5.0, (round(secs, 2), how, text[:120]))
(secs, how, text), _ = go_and_wait("bytes")
check("L8 a byte outside ASCII: an error that says so (never a replaced character that passes)",
      how == "EngineError" and "outside" in text and "ASCII" in text, (round(secs, 2), how, text[:120]))
(secs, how, text), (secs2, how2, text2) = go_and_wait("exit7")
check("L9 the engine ends inside an answer: an error with its exit code 7", how == "EngineError" and "exit code 7" in text, (how, text[:120]))
check("L9 the NEXT wait on an ended engine fails at once (not after its 30 s)", how2 == "EngineError" and secs2 <= 2.0, (round(secs2, 2), how2))
(secs, how, text), _ = go_and_wait("flood", max_lines=20)
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

# ---------------------------------------------------------------- L13, L14: the end of the output
(secs, how, text), _ = go_and_wait("cutline")
check("L13 `bestmove e2e4` WITHOUT its line end from an engine that then ended: an error, never a finished answer",
      how == "EngineError" and "line end" in text, (round(secs, 2), how, text[:120]))
e = standin("closed")
try:
    e.ready(10)
    e.send("go")
    secs, how, text = outcome(lambda: e.read_until(lambda s: s.startswith("bestmove"), 0.5, "the stand-in",
                                                   cutoff=time.monotonic() + 0.3), 8.0)
    check("L14 the output closes and the process lives on: the wait ends within its own time (0.3 s; not later than 1.5 s)",
          how in ("EngineError", "EngineTimeout") and secs <= 1.5, (round(secs, 2), how, text[:120]))
finally:
    e.kill()

# ---------------------------------------------------------------- L15: a cutoff that has passed
got = WORK / "got_l15.bin"
e = standin("say", [], got=got)
hows = []
try:
    e.ready(10)
    past = time.monotonic() - 1.0
    for name, fn in (("command", lambda: e.command("go perft 1", cutoff=past)), ("ready", lambda: e.ready(cutoff=past)),
                     ("uci_options", lambda: e.uci_options(cutoff=past))):
        try:
            fn()
            hows.append(name + " returned")
        except TIMEOUT:
            hows.append("EngineTimeout")
        except Exception as x:  # noqa: BLE001
            hows.append(name + ": " + type(x).__name__)
    after = outcome(lambda: e.ready(10), 5.0)
    e.quit(5)
finally:
    e.kill()
arrived = got.read_bytes() if got.exists() else b"(no file)"
check("L15 a cutoff that has passed: command(), ready() and uci_options() each raise EngineTimeout", hows == ["EngineTimeout"] * 3, hows)
check("L15 ... and not one byte of them went to the engine (it received `isready`, `isready`, `quit` and nothing else)",
      arrived == b"isready\nisready\nquit\n", arrived[:200])
check("L15 ... and the engine answers the next command as before", after[1] == "returned", after)

# ---------------------------------------------------------------- L16: control bytes, both directions
leak = []
for hx in ("00", "0d", "1b", "7f"):
    (secs, how, text), _ = go_and_wait("ctl:" + hx)
    if not (how == "EngineError" and "printable" in text):
        leak.append((hx, how, text[:60]))
check("L16 a NUL, a CR in the middle, an escape, a DEL written by the engine: each is an error, never a line", not leak, leak)
got = WORK / "got_l16.bin"
e = standin("say", [], got=got)
went = []
try:
    e.ready(10)
    for c in ("\x00", "\r", "\x1b", "\x7f", "\t"):
        try:
            e.send("position startpos" + c + "injected")
            went.append(repr(c))
        except uciproc.EngineError:
            pass
    e.quit(5)
finally:
    e.kill()
arrived = got.read_bytes() if got.exists() else b"(no file)"
check("L16 a command with a NUL, a CR, an escape, a DEL or a tab inside is never sent (the engine received `isready` and `quit` only)",
      not went and arrived == b"isready\nquit\n", (went, arrived[:120]))
base = "info depth 1 score cp 0 nodes 1 pv e2e4"
check("L16 the table refuses a line with a control character and passes the same line without it",
      judged(base + " e7e5") == "" and all(judged(base + c + " e7e5") for c in ("\x00", "\r", "\x1b", "\x7f", "\t")),
      [repr(c) for c in ("\x00", "\r", "\x1b", "\x7f", "\t") if not judged(base + c + " e7e5")])

# ---------------------------------------------------------------- L17: no left-over line is ever read as an answer
e = standin("ten")
try:
    e.ready(10)
    e.send("go")
    first = outcome(lambda: e.read_until(lambda s: s.startswith("bestmove"), 10, "ten lines", max_lines=3), 8.0)
    time.sleep(0.5)
    again = outcome(lambda: e.ready(5), 8.0)
    check("L17 after the line bound (3 of 11 lines read): the NEXT call fails at once and reads no left-over line",
          first[1] == "EngineError" and again[1] == "EngineError" and again[0] <= 1.0, (first[1], round(again[0], 2), again[1], again[2][:80]))
finally:
    e.kill()
e = standin("slow")
try:
    e.ready(10)
    e.send("go")
    first = outcome(lambda: e.read_until(lambda s: s.startswith("bestmove"), 0.3, "a slow answer"), 8.0)
    time.sleep(1.2)                      # the late `bestmove` has arrived by now
    again = outcome(lambda: e.ready(5), 8.0)
    check("L17 after a timeout: the NEXT call fails at once and never takes the late answer for its own",
          first[1] == "EngineTimeout" and again[1] == "EngineError" and again[0] <= 1.0, (first[1], round(again[0], 2), again[1], again[2][:80]))
finally:
    e.kill()
odd = []
for label, secs_, kw in (("an infinite limit", float("inf"), {}), ("a limit that is not a number", float("nan"), {}),
                         ("a cutoff that is not a number", 1.0, {"cutoff": float("nan")}), ("a line bound of 0", 1.0, {"max_lines": 0})):
    e = standin("say", [])
    try:
        e.ready(10)
        s, how, text = outcome(lambda e=e, secs_=secs_, kw=kw: e.read_until(lambda x: x == "readyok", secs_, "a wait", **kw), 3.0)
        if how != "EngineError" or s > 1.0:
            odd.append((label, how, round(s, 2)))
    finally:
        e.kill()
check("L17 a limit that is not finite, a cutoff that is not a number and a line bound of 0 are refused at once", not odd, odd)

# ---------------------------------------------------------------- L19: the engine's own two ways of giving up
(secs, how, text), _ = go_and_wait("err2")
check("L19 `info string ERROR NNUE v3` and then exit code 2: the refusal is reported, with the exit code",
      how == "EngineRefused" and "ERROR NNUE v3" in text and "exit code 2" in text, (how, text[:160]))
(secs, how, text), (secs2, how2, _t) = go_and_wait("sgerr")
check("L19 `sgerror` and no end line: refused at once (within 2 s, not at the 10 s limit)",
      how == "EngineRefused" and "sgerror" in text and secs <= 2.0, (round(secs, 2), how, text[:120]))
check("L19 ... and that engine object is not used again", how2 == "EngineError" and secs2 <= 1.0, (round(secs2, 2), how2))

# ---------------------------------------------------------------- L20: the table on whole and on cut lines
not_whole = [ln for ln in WHOLE if judged(ln) != ""]
check(f"L20 each of {len(WHOLE)} whole native lines passes the table", not not_whole, [(ln[:60], judged(ln)) for ln in not_whole][:4])
not_cut = [ln for ln in CUT if not judged(ln)]
check(f"L20 each of {len(CUT)} cut or altered lines is refused by the table", not not_cut, not_cut[:8])

bad = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(bad)} of {len(results)} checks pass")
print("ALL " + str(len(results)) + " CHECKS PASS" if not bad else "FAILED: " + "; ".join(bad))
sys.exit(1 if bad else 0)
