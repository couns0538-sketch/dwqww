"""Fable 2026-11-23, server-day plan: the test of run/uciproc.py and run/engine_lines.py (version 2, third
edition: L13 to L20 are the reproductions of Astra `134620Z` and Neon `134912Z`, L21 to L24 and the search
and option lines of L2 and L20 those of Astra `142216Z` and Neon `143000Z`).

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
     error output, an `sgerror`: each is refused; whole lines of each expected kind (WHOLE: some verbatim from
     the PC's clean runs, some built to the source's print statements; see its comment): none is refused
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
 L20 the table on whole and on cut lines: every whole line passes, every cut or altered one is refused
 L21 every argument of a call is judged BEFORE its first byte: on the real engine a `go perft 1` with an
     unusable limit or cutoff sends nothing, so the next `go perft 2` answers 400 and never 20; on the stand-in
     no call with an unusable argument, text or length puts one byte on the pipe
 L22 a retired object is never given new work: after a timeout send(), command(), ready(), uci_options() and
     run() raise at once, quit() ends the process without writing; a write the system refuses retires it too
 L23 a line that arrived while nobody waited is never taken into the next answer; an engine that ended while
     nobody waited is reported by the next call at once
 L24 an `sgerror` after another unexpected line ends the wait at once (also when the caller judges the lines
     itself); an option line is read by its type
 L25 (fourth edition, Astra `144526Z`; with it L21 got three more unusable limits: a finite one beyond what a
     wait can serve, and whole numbers too large for a float) no failure after a command went out leaves the
     object usable: a transcript line that cannot be written (on the real engine, and on the stand-in at three
     places), an ending test that raises inside an answer
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


def check(name: str, ok, detail: object = "") -> bool:
    results.append((name, bool(ok)))
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f": {str(detail)[:300]}" if detail != "" and not ok else ""), flush=True)
    return bool(ok)


def judged(line):
    """The table's word on a line; None when this tree has no table (then every table check fails)."""
    return engine_lines.why_not(line) if engine_lines is not None else None


# WHOLE: whole lines of the expected kinds, of two origins.
# VERBATIM from the PC's clean runs of the frozen engine (each found there by a search for the exact whole
# line): the two net lines (only the path exchanged, one with spaces, and in one of them the kernel's name),
# the bench line, the two `sg` rows, the `rule` end line, the first depth line, `bestmove e2e4`, the id line,
# the option lines of Hash, Ponder, OwnBook, Book File and Clear Hash, `readyok`, `uciok`.
# BUILT to the source's print statements (uci.cpp, search.cpp, nnue_v3.cpp): both eval lines' values (the
# clean runs hold `eval hce 0 nnue 87 total 87`) and the `incheck 1` form, the `mate` end line, the shortened
# `evallimit` end line, the three further search lines (two lines a position, a mate score with an empty move
# list, the move `0000` in a list), `bestmove` with a ponder move and with a promotion, the option `Some
# Margin` (a made-up name with negative numbers), `e2e4: 20` and `nodes 8902` (the clean runs hold these two
# shapes with other numbers). L2 below adds what no list can: every line of the REAL engine's option list and
# of two real searches (one and two lines a position) passes the table.
# In CUT on purpose, although the engine can print them: an empty line (no clean run prints one) and
# `bestmove 0000` (the answer to a search on a position without a legal move; the day's worker never asks for
# one: `go perft 1` for the opening, the ordinary start position at start-up, `sgend` or `sgerror` for a game;
# on the day it would mean that another position than the intended one was searched).
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
         "info depth 3 multipv 2 score cp 12 seldepth 4 nodes 512 nps 51200 hashfull 0 time 10 pv g1f3 d7d5 d2d4",
         "info depth 9 seldepth 14 score mate -3 nodes 70111 nps 1402220 hashfull 2 time 50 pv",
         "info depth 2 seldepth 2 score cp 0 nodes 40 nps 0 hashfull 0 time 0 pv 0000 e7e8q",
         "bestmove e2e4", "bestmove e2e4 ponder e7e5", "bestmove e7e8q", "id name Chess Engine Forge 6.4.24 candidate",
         "option name Hash type spin default 32 min 1 max 2048", "option name Ponder type check default false",
         "option name OwnBook type check default true", "option name Book File type string default <empty>",
         "option name Clear Hash type button", "option name Some Margin type spin default -12 min -400 max 400",
         "e2e4: 20", "nodes 8902", "uciok", "readyok"]
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
       "bestmove", "bestmove e2", "bestmove 0000", "id name", "nodes", "e2e4:", "readyok ", " uciok", "",
       # the search line and the option line, cut or altered (Astra's two, and their neighbours)
       "info depth 18 seldepth", "option name Hash type spinach", "info depth 1 score cp 0 nodes 1 pv e2e4",
       "info depth 1 seldepth 1 score cp -15 nodes 23 nps 0 hashfull 0 time 0",
       "info depth 1 seldepth 1 score cp -15 nodes 23 nps 0 hashfull 0 time 0 pv d2d",
       "info depth 1 seldepth 1 score cp -15 nodes 23 nps 0 hashfull 0 time 0 pv d2d4 ",
       "info depth 1 score cp -15 seldepth 1 nodes 23 nps 0 hashfull 0 time 0 pv d2d4",
       "info depth 3 multipv 2 seldepth 4 score cp 12 nodes 512 nps 51200 hashfull 0 time 10 pv g1f3",
       "info depth 1 seldepth 1 score cp nodes 23 nps 0 hashfull 0 time 0 pv d2d4",
       "info depth 1 seldepth 1 score win 3 nodes 23 nps 0 hashfull 0 time 0 pv d2d4",
       "option name Hash type spin default 32 min 1", "option name Hash type spin", "option name Ponder type check",
       "option name Ponder type check default maybe", "option name Book File type string default",
       "option name Clear Hash type buttons", "option name  type button", "option name Hash type combo default a var a var b"]

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
            print("info depth 1 seldepth 1 score cp 0 nodes 1 nps 0 hashfull 0 time 0 pv e2e4", flush=True)
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
        print("info depth 1 seldepth 1 score cp 0 nodes 1 nps 0 hashfull 0 time 0 pv e2e4", flush=True)
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
        put(b"info depth 1 seldepth 1 score cp 0 nodes 1 nps 0 hashfull 0 time 0 pv e2e4" + bytes.fromhex(mode[4:]) + b" e7e5\\n")
        put(b"bestmove e2e4\\n")
    elif cmd == "go" and mode == "ten":                        # ten lines and the end, at once
        put(b"".join(b"info depth %d seldepth 1 score cp 0 nodes 1 nps 0 hashfull 0 time 0 pv e2e4\\n" % d for d in range(1, 11)) + b"bestmove e2e4\\n")
    elif cmd == "go" and mode == "slow":                       # the answer comes after one second
        time.sleep(1.0)
        put(b"bestmove e2e4\\n")
    elif cmd == "go" and mode == "extra":                      # the answer, and one more line nobody asked for
        put(b"bestmove e2e4\\nbestmove e2e4\\n")
    elif cmd == "go" and mode == "badsg":                      # an unexpected line, THEN a game given up
        put(b"info string unknown option Foo\\n")
        put(b"sgerror noscore ply 12 searches 5 nodes 0 fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\\n")
        time.sleep(20)
    elif cmd == "go" and mode == "deaf":                       # the input closes, the process lives on for a while
        sys.stdin.close()
        try:
            os.close(0)
        except OSError:
            pass
        time.sleep(4)
        os._exit(0)
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
        f.write_text("".join(ln + "\n" for ln in lines), encoding="utf-8", newline="\n")   # no line for an empty list
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


class Tap:
    """A recorder on the PARENT's side of the engine's input: every byte the wrapper really wrote. What the
    stand-in writes down is what the CHILD read, and a child that is ended may not have read what was already in
    its pipe (Astra `145524Z`: 14 of 50 runs); "nothing more was sent" is therefore judged here, on the parent."""

    def __init__(self, f):
        self.f, self.data = f, b""

    def write(self, b):
        self.data += bytes(b)
        return self.f.write(b)

    def flush(self):
        return self.f.flush()

    def close(self):
        return self.f.close()


def tapped(e) -> Tap:
    e.p.stdin = Tap(e.p.stdin)
    return e.p.stdin


def received(got, want: bytes, secs: float = 5.0) -> bool:
    """True once the stand-in's receipt file holds exactly `want`, waited for (bounded) BEFORE the stand-in is
    ended: the child had its chance to read what had gone out."""
    end = time.monotonic() + secs
    while True:
        if got.exists() and got.read_bytes() == want:
            return True
        if time.monotonic() >= end:
            return False
        time.sleep(0.02)


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

    def searched(lines_a_position):
        eng.command("setoption name OwnBook value false")
        eng.command(f"setoption name MultiPV value {lines_a_position}")
        eng.command("position startpos moves e2e4 e7e5 g1f3")
        eng.send("go depth 6")
        return eng.read_until(lambda s: s.startswith("bestmove"), 120, f"a search with {lines_a_position} lines a position")
    try:
        one, two = searched(1), searched(2)
        eng.command("setoption name MultiPV value 1")
        n1 = sum(ln.startswith("info depth ") and " multipv " not in ln for ln in one)
        n2 = sum(" multipv 2 " in ln for ln in two)
        check("L2 two real searches, one and two lines a position: every line passes the table (both forms of the search line seen)",
              n1 >= 3 and n2 >= 3, (n1, n2, one[:1], two[:1]))
    except uciproc.EngineError as e:
        check("L2 two real searches, one and two lines a position: every line passes the table (both forms of the search line seen)", False, e)
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
    check(f"L6 {len(WHOLE)} whole lines of the expected kinds (verbatim or built to the source's print statements): none is refused", r == "", r)
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
base = "info depth 1 seldepth 1 score cp 0 nodes 1 nps 0 hashfull 0 time 0 pv e2e4"
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
check(f"L20 each of {len(WHOLE)} whole lines passes the table", not not_whole, [(ln[:60], judged(ln)) for ln in not_whole][:4])
not_cut = [ln for ln in CUT if not judged(ln)]
check(f"L20 each of {len(CUT)} cut or altered lines is refused by the table", not not_cut, not_cut[:8])

# ---------------------------------------------------------------- L21: every argument is judged before the first byte
BAD_ARGS = (("a negative limit", {"secs": -1}), ("a cutoff that is not a number", {"cutoff": float("nan")}),
            ("an infinite limit", {"secs": float("inf")}), ("a limit that is a text", {"secs": "5"}),
            ("a limit that is True", {"secs": True}), ("a cutoff that is True", {"cutoff": True}),
            ("a finite limit beyond what a wait can serve", {"secs": threading.TIMEOUT_MAX + 1000}),
            ("a limit too large for a float", {"secs": 10 ** 400}), ("a cutoff too large for a float", {"cutoff": 10 ** 400}))
eng = uciproc.Engine(EXE)
native = []
try:
    eng.command("position startpos")
    for label, kw in BAD_ARGS:
        try:
            eng.command("go perft 1", **kw)
            how = "returned"
        except uciproc.EngineError as x:
            how = type(x).__name__
        except Exception as x:  # noqa: BLE001
            how = "another error: " + type(x).__name__
        try:
            nodes = [ln for ln in eng.command("go perft 2", 60) if ln.startswith("nodes ")]
        except uciproc.EngineError as x:
            nodes = ["ERROR " + str(x)[:80]]
        native.append((label, how, nodes))
finally:
    eng.kill()
check(f"L21 the REAL engine: `go perft 1` with each of {len(BAD_ARGS)} unusable limits or cutoffs raises EngineError, and the NEXT "
      "`go perft 2` answers `nodes 400` every time (never the 20 of a probe that went out after all)",
      len(native) == len(BAD_ARGS) and all(h == "EngineError" and n == ["nodes 400"] for _, h, n in native), native)
got = WORK / "got_l21.bin"
e = standin("say", [], got=got)
slipped = []
try:
    e.ready(10)
    run = getattr(e, "run", None)
    calls = []
    for label, kw in BAD_ARGS:
        calls += [(f"command with {label}", lambda kw=kw: e.command("go perft 1", **kw)),
                  (f"ready with {label}", lambda kw=kw: e.ready(**kw)),
                  (f"uci_options with {label}", lambda kw=kw: e.uci_options(**kw)),
                  (f"run with {label}", (lambda kw=kw: run("go perft 1", lambda s: True, **{"secs": 5, **kw})) if run else None)]
    calls += [("command with a number as its text", lambda: e.command(17)),
              ("command with a text of 65,636 characters", lambda: e.command("x" * 65636)),
              ("send with a text of 65,636 characters", lambda: e.send("x" * 65636)),
              ("send with a number as its text", lambda: e.send(17)),
              ("run with a line bound of 0", (lambda: run("go", lambda s: True, 5, max_lines=0)) if run else None),
              ("run with a line bound that is True", (lambda: run("go", lambda s: True, 5, max_lines=True)) if run else None),
              ("run with an ending test that cannot be called", (lambda: run("go", None, 5)) if run else None)]
    for name, fn in calls:
        if fn is None:
            slipped.append(name + ": no such call")
            continue
        try:
            fn()
            slipped.append(name + " returned")
        except uciproc.EngineError:
            pass
        except Exception as x:  # noqa: BLE001
            slipped.append(f"{name}: {type(x).__name__}")
    after = outcome(lambda: e.ready(10), 5.0)
    e.quit(5)
finally:
    e.kill()
arrived = got.read_bytes() if got.exists() else b"(no file)"
check(f"L21 the stand-in: each of {len(calls)} calls with an unusable argument raises EngineError, not one byte of them arrives "
      "(the engine received `isready`, `isready`, `quit` and nothing else), and the next command is answered",
      not slipped and arrived == b"isready\nisready\nquit\n" and after[1] == "returned", (slipped[:6], arrived[:120], after))

# ---------------------------------------------------------------- L22: a retired object is never given new work
got = WORK / "got_l22.bin"
e = standin("slow", got=got)
tap = tapped(e)
tries = []
try:
    e.ready(10)
    e.send("go")
    first = outcome(lambda: e.read_until(lambda s: s.startswith("bestmove"), 0.3, "a slow answer"), 8.0)
    run = getattr(e, "run", None)
    for name, fn in (("send", lambda: e.send("go perft 1")), ("command", lambda: e.command("go perft 1", 5)),
                     ("ready", lambda: e.ready(5)), ("uci_options", lambda: e.uci_options(5)),
                     ("run", (lambda: run("go perft 1", lambda s: s.startswith("nodes"), 5)) if run else None)):
        if fn is None:
            tries.append(name + ": no such call")
            continue
        s, how, _text = outcome(fn, 8.0)
        if how != "EngineError" or s > 1.0:
            tries.append((name, how, round(s, 2)))
    seen = received(got, b"isready\ngo\n")
    code = e.quit(5)
    time.sleep(0.3)
    ended = e.p.poll() is not None
finally:
    e.kill()
check("L22 after a timeout the object is retired: send(), command(), ready(), uci_options() and run() each raise at once, quit() "
      "ends the process without writing (it returns None), and the wrapper wrote `isready`, `go` and not one byte more (judged "
      "on the parent's own writes; the stand-in had read both)",
      first[1] == "EngineTimeout" and not tries and code is None and ended and tap.data == b"isready\ngo\n" and seen,
      (first[1], tries, code, ended, tap.data[:120], seen))
e = standin("deaf")
try:
    e.ready(10)
    e.send("go")                               # the stand-in closes its input and lives on
    time.sleep(0.5)
    how = []
    for _ in range(40):                        # a pipe takes what its buffer holds: write until the system refuses
        s, h, text = outcome(lambda: e.send("isready"), 5.0)
        if h != "returned":
            how = [h, text[:80]]
            break
    later = outcome(lambda: e.send("isready"), 5.0)
    gone = getattr(e, "gone", "")
finally:
    e.kill()
check("L22 a write that the system refuses (the engine closed its input) retires the object: that send() raises EngineError, "
      "and the next one fails as a retired object without another write",
      how[:1] == ["EngineError"] and bool(gone) and later[1] == "EngineError" and "not used any further" in later[2], (how, gone[:60], later))

# ---------------------------------------------------------------- L23: no line is taken that nobody asked for
got = WORK / "got_l23.bin"
e = standin("extra", got=got)
tap = tapped(e)
try:
    e.ready(10)
    e.send("go")
    first = outcome(lambda: e.read_until(lambda s: s.startswith("bestmove"), 5, "an answer with one line too many"), 8.0)
    time.sleep(0.4)
    again = outcome(lambda: e.ready(5), 8.0)
    more = outcome(lambda: e.ready(5), 8.0)
finally:
    e.kill()
check("L23 a second `bestmove` after the answer: the next command is refused BEFORE it is sent, the object is retired, and the "
      "wrapper wrote `isready`, `go` and nothing else (judged on the parent's own writes)",
      first[1] == "returned" and again[1] == "EngineError" and "no command had asked for" in again[2] and more[1] == "EngineError"
      and tap.data == b"isready\ngo\n", (first[1], again[1], again[2][:100], more[1], tap.data[:120]))
e = standin("say", [])
try:
    e.ready(10)
    e.send("quit")
    time.sleep(0.5)
    s, how, text = outcome(lambda: e.ready(30), 8.0)
finally:
    e.kill()
check("L23 an engine that ended while nobody waited: the next call says so at once, with its exit code",
      how == "EngineError" and "exit code 0" in text and s <= 2.0, (round(s, 2), how, text[:120]))

# ---------------------------------------------------------------- L24: a game given up after another unexpected line; options by type
(secs, how, text), (secs2, how2, _t2) = go_and_wait("badsg")
check("L24 `info string unknown option Foo`, then `sgerror`, then nothing: refused within 2 s of the 10 s limit, the FIRST "
      "unexpected line named first, the object retired",
      how == "EngineRefused" and "unknown option Foo" in text and secs <= 2.0 and how2 == "EngineError" and secs2 <= 1.0,
      (round(secs, 2), how, text[:160], how2))
e = standin("badsg")
try:
    e.ready(10)
    e.send("go")
    s, how, text = outcome(lambda: e.read_until(lambda x: x.startswith("sgend"), 10, "a game", refuse=False), 8.0)
finally:
    e.kill()
check("L24 the same with refuse=False (the caller judges the lines itself): `sgerror` still ends the wait at once",
      how == "EngineRefused" and "sgerror" in text and s <= 2.0, (round(s, 2), how, text[:160]))
pat = getattr(uciproc, "_OPTION_LINE", None)
parsed = {}
if pat is not None:
    for ln in ("option name Book File type string default a b min c max d", "option name Hash type spin default 32 min 1 max 2048",
               "option name Ponder type check default false", "option name Clear Hash type button"):
        m = pat.fullmatch(ln)
        parsed[ln.split(" type ")[0][12:]] = {k: v for k, v in m.groupdict().items() if v is not None} if m else None
check("L24 an option line is read by its type: a text default with spaces and the words `min` and `max` inside stays ONE default "
      "and gives no `min`; a spin gives default, min and max; a button gives its name alone",
      parsed == {"Book File": {"name": "Book File", "string": "a b min c max d"},
                 "Hash": {"name": "Hash", "spin": "32", "min": "1", "max": "2048"},
                 "Ponder": {"name": "Ponder", "check": "false"},
                 "Clear Hash": {"name": "Clear Hash", "button": "button"}}, parsed)

# ---------------------------------------------------------------- L25: no failure after a command went out leaves the object usable
class FullDisk:
    """A transcript whose n-th line cannot be written, as on a full disk. Every other line is kept, so the
    object must be retired by that ONE failure and not by a transcript that stays broken."""

    def __init__(self, fail_at):
        self.n, self.fail_at, self.kept = 0, fail_at, []

    def write(self, text):
        self.n += 1
        if self.n == self.fail_at:
            raise OSError(28, "No space left on device")
        self.kept.append(text)


def tried(fn):
    try:
        return "returned", fn()
    except Exception as x:  # noqa: BLE001
        return type(x).__name__, str(x)


eng = uciproc.Engine(EXE, log=FullDisk(4))     # 1 `>>> isready`, 2 `readyok`, 3 `>>> position ...`, 4 `>>> isready`
try:
    eng.ready(30)
    first = tried(lambda: eng.command("position startpos moves e2e4 e7e5", 30))
    retired = bool(getattr(eng, "gone", ""))
    t0 = time.monotonic()
    nxt = tried(lambda: eng.command("go perft 1", 30))
    took = time.monotonic() - t0
finally:
    eng.kill()
check("L25 the REAL engine, the transcript's fourth line cannot be written (the end mark of `position startpos moves e2e4 "
      "e7e5`): the call raises EngineLogError, the object is retired, and the next `go perft 1` raises at once and answers "
      "nothing (on the bytes before it answered `nodes 29`: the failed call had moved the board)",
      first[0] == "EngineLogError" and retired and nxt[0] == "EngineError" and took <= 1.0,
      (first[0], str(first[1])[:100], retired, nxt[0], str(nxt[1])[:100], round(took, 2)))
slips = []
for at, want in ((3, b"isready\n"), (4, b"isready\nposition startpos\n"), (5, b"isready\nposition startpos\nisready\n")):
    got = WORK / f"got_l25_{at}.bin"
    e = standin("say", [], got=got)
    tap = tapped(e)
    e.log = FullDisk(at)
    try:
        e.ready(10)
        first = tried(lambda: e.command("position startpos", 10))
        nxt = tried(lambda: e.command("go perft 1", 10))
        one_more = tried(lambda: e.send("stop"))
        wrote = tap.data                     # the PARENT's writes so far: nothing of the three failed calls beyond `want`
        seen = received(got, want)           # the child reads what had gone out, waited for BEFORE it is ended
        code = e.quit(5)
    finally:
        e.kill()
    if not (first[0] == "EngineLogError" and nxt[0] == "EngineError" and one_more[0] == "EngineError" and code is None
            and wrote == want and tap.data == want and seen):
        slips.append((at, first[0], nxt[0], one_more[0], code, wrote[:80], tap.data[:80], seen))
check("L25 the stand-in, the transcript failing at its third, fourth and fifth line (before a command, between the command and "
      "its end mark, inside the answer): each time EngineLogError, every later call refused, and the wrapper wrote exactly "
      "what had gone out before the failure and not one byte more (judged on the parent's own writes, also after quit(); the "
      "stand-in's receipt of exactly those bytes is waited for before it is ended)", not slips, slips)
e = standin("ten")
tap = tapped(e)
try:
    e.ready(10)
    run = getattr(e, "run", None)
    first = tried(lambda: run("go", lambda s: 1 // 0, 5)) if run else ("no such call", "")
    nxt = tried(lambda: e.ready(5))
    e.quit(5)
finally:
    e.kill()
check("L25 an ending test that raises inside an answer: an EngineError that names it (not the test's own error passed "
      "through), the object retired, nothing written afterwards (the parent's own writes are `isready`, `go`)",
      first[0] == "EngineError" and "ZeroDivisionError" in str(first[1]) and nxt[0] == "EngineError" and tap.data == b"isready\ngo\n",
      (first[0], str(first[1])[:100], nxt[0], tap.data[:80]))

bad = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(bad)} of {len(results)} checks pass")
print("ALL " + str(len(results)) + " CHECKS PASS" if not bad else "FAILED: " + "; ".join(bad))
sys.exit(1 if bad else 0)
