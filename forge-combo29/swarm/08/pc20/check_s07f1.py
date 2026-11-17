#!/usr/bin/env python3
"""check_s07f1.py OUT — my own check of seat 07's 07-F1:

"`position` + `go depth N searchmoves <no legal root move>` on a board that HAS legal moves answers a fabricated
 per-depth report — one `info depth D ... score cp 0 nodes 0` line for EVERY depth up to the limit (64 of them with
 no depth limit) — then `bestmove 0000`."

Check on the PC build under PC20, Threads 1 (FABLE_TO_swarm_5 asks for finds to be re-run there). I test:
  1. does a searchmoves naming NO legal move produce the fabricated ladder, and how many info lines?
  2. is `bestmove 0000` returned although legal moves exist?
  3. does the engine ALSO print the diagnostic info string (their claim that it "says so")?
  4. CONTROL: legal searchmoves naming one real move must search normally (not the ladder) — otherwise the harness
     cannot tell a restricted search from a normal one.

The `searchmoves` name I use is a well-formed but illegal move (e2e5 from startpos) and a garbage token (a9a9),
so "no legal root move" is reached two ways.

ARGUMENT ORDER: OUT first.
"""
import subprocess
import sys

import chess

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

CASES = [
    ("searchmoves with no legal root move (e2e5)", "go depth 8 searchmoves e2e5"),
    ("searchmoves garbage (a9a9)", "go depth 8 searchmoves a9a9"),
    ("searchmoves with NO depth limit", "go searchmoves e2e5"),
    ("CONTROL: searchmoves naming a real move (e2e4)", "go depth 8 searchmoves e2e4"),
    ("CONTROL: no searchmoves at all", "go depth 8"),
]


def run(go):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def sync():
        send("isready")
        got = []
        while True:
            l = p.stdout.readline()
            if not l:
                raise EOFError
            got.append(l.rstrip("\n"))
            if l.startswith("readyok"):
                return got

    send("uci")
    while not p.stdout.readline().startswith("uciok"):
        pass
    for k, v in PC20:
        send("setoption name %s value %s" % (k, v))
        sync()
    send("ucinewgame")
    sync()
    send("position fen " + START)
    sync()
    import threading
    lines = []
    done = threading.Event()

    def rd():
        while True:
            l = p.stdout.readline()
            if not l:
                return
            lines.append(l.rstrip("\n"))
            if l.startswith("bestmove"):
                done.set()
                return

    send(go)
    threading.Thread(target=rd, daemon=True).start()
    finished = done.wait(180.0)
    if not finished:
        p.kill()
        return {"timeout": True, "lines": lines}
    sync()
    send("quit")
    try:
        p.wait(timeout=30)
    except Exception:
        p.kill()
    infos = [l for l in lines if l.startswith("info depth")]
    strings = [l for l in lines if l.startswith("info string")]
    bm = [l for l in lines if l.startswith("bestmove")][-1].split()[1]
    zero_nodes = sum(1 for l in infos if " nodes 0 " in l or l.endswith(" nodes 0"))
    return {"n_info": len(infos), "zero_nodes": zero_nodes, "strings": strings, "bm": bm,
            "depths": [l.split()[2] for l in infos][:6]}


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## seat 07's 07-F1 on the PC build under PC20, Threads 1 — startpos (20 legal moves)")
emit("")
emit("| case | info depth lines | of those `nodes 0` | bestmove | info string |")
emit("|---|---|---|---|---|")
res = {}
for label, go in CASES:
    r = run(go)
    if r.get("timeout"):
        emit("| %s | TIMEOUT after 180 s (%d info lines) | | | |" % (label, len(r["lines"])))
        continue
    res[label] = r
    emit("| %s | **%d** | %d | **%s** | %s |" %
         (label, r["n_info"], r["zero_nodes"], r["bm"],
          "; ".join(x.replace("|", "/")[:60] for x in r["strings"]) or "-"))

emit("")
emit("## The claim, tested link by link")
emit("")
emit("| link | measured |")
emit("|---|---|")
illegal = res.get("searchmoves with no legal root move (e2e5)")
ctrl = res.get("CONTROL: searchmoves naming a real move (e2e4)")
if illegal and ctrl:
    emit("| `bestmove 0000` on a board WITH legal moves | **%s** (bestmove %s) |" %
         ("YES" if illegal["bm"] == "0000" else "NO", illegal["bm"]))
    emit("| fabricated per-depth report | **%d info depth lines, %d with `nodes 0`** for a depth-8 limit |" %
         (illegal["n_info"], illegal["zero_nodes"]))
    emit("| the engine also prints a diagnostic | **%s** |" %
         ("YES: " + illegal["strings"][0].replace("|", "/") if illegal["strings"] else "NO"))
    emit("| CONTROL: a legal searchmoves does NOT do this | **%s** (%d info lines, bestmove %s) |" %
         ("PASS" if ctrl["bm"] != "0000" and ctrl["zero_nodes"] == 0 else "FAIL", ctrl["n_info"], ctrl["bm"]))
    emit("| CONTROL: an unrestricted search | **%s** |" %
         ("PASS" if (res.get("CONTROL: no searchmoves at all") or {}).get("zero_nodes", 1) == 0 else "FAIL"))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
