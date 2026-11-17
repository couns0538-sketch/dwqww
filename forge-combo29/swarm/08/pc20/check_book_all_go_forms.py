#!/usr/bin/env python3
"""check_book_all_go_forms.py OUT — close my own 08-F12 gap across ALL `go` forms.

08-F12 and 08-C24 establish the book fires on `game_search` forms (`wtime`/`btime`, `movetime`) and never on
`go depth`. I flagged that I had not tested `go nodes` or `go infinite`. This closes it: every `go` form the engine
accepts, on the same three opening positions, with OwnBook true, and the book line counted.

Expected per the gating rule: book on `wtime`/`btime` and `movetime`; no book on `depth`, `nodes`, `infinite`.
A `go infinite` needs a `stop` to end — that is sent with a deadline, and the presence of a book answer is
determined by whether the engine prints `info string book move` and returns immediately rather than searching.

ARGUMENT ORDER: OUT first.
"""
import subprocess
import sys
import threading
import time

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true")]
OPENINGS = ["", "e2e4", "e2e4 e7e5"]
FORMS = [("go depth 12", "depth", False),
         ("go nodes 5000", "nodes", False),
         ("go infinite", "infinite", True),
         ("go wtime 6000 btime 6000", "wtime", False),
         ("go movetime 100", "movetime", False)]


def run(moves, go, need_stop):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def sync():
        send("isready")
        while True:
            l = p.stdout.readline()
            if not l:
                raise EOFError
            if l.startswith("readyok"):
                return

    send("uci")
    while not p.stdout.readline().startswith("uciok"):
        pass
    for k, v in PC20 + [("Threads", "1"), ("Hash", "16"), ("OwnBook", "true")]:
        send("setoption name %s value %s" % (k, v))
        sync()
    send("ucinewgame")
    sync()
    send(("position startpos moves " + moves) if moves else "position startpos")
    sync()
    lines = []
    done = threading.Event()

    def rd():
        while True:
            l = p.stdout.readline()
            if not l:
                break
            lines.append(l.rstrip("\n"))
            if l.startswith("bestmove"):
                break
        done.set()

    send(go)
    threading.Thread(target=rd, daemon=True).start()
    if need_stop:
        # an infinite search must be stopped; if the book answers it, bestmove arrives first
        got = done.wait(1.5)
        if not got:
            send("stop")
    done.wait(30.0)
    sync()
    send("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    book = [l for l in lines if "book move" in l]
    return {"book": bool(book), "n_info": sum(1 for l in lines if l.startswith("info depth")),
            "n_bf": len(book)}


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## Every `go` form vs the book — closing the 08-F12 gap (OwnBook true, PC r15 PC20, Threads 1)")
emit("")
emit("| `go` form | startpos | 1.e4 | 1.e4 e5 | book lines | gating rule says |")
emit("|---|---|---|---|---|---|")
results = {}
for go, kind, need_stop in FORMS:
    marks = []
    n = 0
    for moves in OPENINGS:
        r = run(moves, go, need_stop)
        marks.append("BOOK" if r["book"] else "no search-book" if r["n_info"] else "no")
        n += r["book"]
    results[kind] = n
    expect = "BOOK" if kind in ("wtime", "movetime") else "no book"
    emit("| %s | %s | %s | %s | **%d of 3** | %s |" % (go, marks[0], marks[1], marks[2], n, expect))

emit("")
emit("## Verdict")
emit("")
emit("| form | book lines | as the gating rule predicts? |")
emit("|---|---|---|")
for go, kind, _ in FORMS:
    expect_book = kind in ("wtime", "movetime")
    got = results[kind]
    ok = (got == 3) if expect_book else (got == 0)
    emit("| %s | %d of 3 | **%s** |" % (kind, got, "YES" if ok else "**NO**"))
emit("")
allok = all(((results[k] == 3) if k in ("wtime", "movetime") else (results[k] == 0))
            for _, k, _ in FORMS)
if allok:
    emit("**The book fires on exactly the two `game_search` forms and on none of the other three** — so 08-F12's")
    emit("warning covers all five forms the engine accepts, and a `go depth`/`nodes`/`infinite` harness can never")
    emit("hit the book hazard. That closes the gap I named in 08-C24.")
else:
    emit("**NOT as predicted** — see the table; a form other than wtime/movetime fired the book, which would be a")
    emit("correction to the gating rule and to my 08-F12.")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
