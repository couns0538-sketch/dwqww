#!/usr/bin/env python3
"""check_s12f14.py OUT — my own check of seat 12's S-F14, WITH A CONTROL SET.

Their claim:
"the ONE-PLY-DOWN draw short-circuit is STILL OPEN on the PC build: `6k1/8/5PPP/8/8/8/8/R6K b - - 99 40`
 (black's only two moves both allow Ra8#) answers `cp 0` in 36 nodes on PC r15, whereas [hm 97/98 differ]."

The claim is that one ply DOWN from the root the fifty-move test still fires, because `Worker::is_draw` returns 0 at
any node with halfmove >= 100, while the ROOT repair (FABLE 5's FORGE_FIX_ROOT_DRAWN) only fixes the root.

Check:
  - the board at halfmove 99 must answer cp 0 in a small node count on the PC build (their claim);
  - the SAME board at halfmove 97 and 98 must NOT be cp 0 — that is the discriminating control, and it is exactly
    what makes the hm-99 result a defect rather than a correct draw;
  - the board at halfmove 0 must score a win for White, proving the position is genuinely won (the plant: if the
    harness cannot see a win on the same board, the cp 0 values mean nothing).

ARGUMENT ORDER: OUT first.
"""
import subprocess
import sys

import chess

OUT = sys.argv[1]
PC = "/home/ubuntu/builds/pc/forge"
BASE = "/home/ubuntu/builds/release/forge"
S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
       ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
       ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
       ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
       ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false")]
TMPL = "6k1/8/5PPP/8/8/8/8/R6K b - - %d 40"
COUNTERS = [0, 96, 97, 98, 99, 100]
DEPTH = 6


def run(exe, fen, depth=DEPTH):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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
    for k, v in S14 + [("Threads", "1"), ("Hash", "16")]:
        send("setoption name %s value %s" % (k, v))
        sync()
    send("ucinewgame")
    sync()
    send("position fen " + fen)
    pre = sync()
    if any("invalid FEN" in l for l in pre):
        return {"err": "refused"}
    send("go depth %d" % depth)
    lines = []
    while True:
        l = p.stdout.readline()
        if not l:
            break
        lines.append(l.rstrip("\n"))
        if l.startswith("bestmove"):
            break
    sync()
    send("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    nodes = None
    score = None
    maxd = 0
    for l in lines:
        if l.startswith("info depth"):
            t = l.split()
            try:
                maxd = max(maxd, int(t[2]))
                if "score" in t and "nodes" in t:
                    si = t.index("score")
                    score = "%s %s" % (t[si + 1], t[si + 2])
                    nodes = int(t[t.index("nodes") + 1])
            except (IndexError, ValueError):
                pass
    return {"nodes": nodes, "score": score, "bm": lines[-1].split()[1], "maxd": maxd}


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## seat 12 S-F14 — is the one-ply-down draw short-circuit still open on the PC build?")
emit("")
emit("Board `%s` at several halfmove counters, `go depth %d`, Threads 1, Hash 16." % (TMPL % 99, DEPTH))
emit("")
emit("| build | halfmove | score | nodes | depth | bestmove |")
emit("|---|---|---|---|---|---|")
rows = {}
for label, exe in (("PC r15/PC20", PC), ("base/S14", BASE)):
    for c in COUNTERS:
        r = run(exe, TMPL % c)
        rows[(label, c)] = r
        emit("| %s | %d | **%s** | %s | %s | %s |" %
             (label, c, r.get("score"), f"{r['nodes']:,}" if r.get("nodes") is not None else "-",
              r.get("maxd"), r.get("bm")))

emit("")
emit("## The claim, and the discriminating controls")
emit("")
emit("| question | answer |")
emit("|---|---|")
pc99 = rows[("PC r15/PC20", 99)]
pc0 = rows[("PC r15/PC20", 0)]
emit("| PC at halfmove 99 gives cp 0 in a small node count (their claim) | **%s in %s nodes** (they said cp 0 in 36) |" %
     (pc99.get("score"), f"{pc99['nodes']:,}" if pc99.get("nodes") is not None else "-"))
emit("| PC at halfmove 0 scores a WIN (the plant: the position really is won) | **%s** |" % pc0.get("score"))
low = [rows[("PC r15/PC20", c)].get("score") for c in (96, 97, 98)]
emit("| PC at halfmove 96/97/98 does NOT give cp 0 (the discriminator) | **%s** |" % ", ".join(str(x) for x in low))
win_ok = bool(pc0.get("score")
              and (pc0["score"].startswith("mate") or
                   (pc0["score"].startswith("cp") and int(pc0["score"].split()[1]) > 100)))
zero99 = bool(pc99.get("score") and pc99["score"].startswith("cp") and int(pc99["score"].split()[1]) == 0)
discrim = all(s and not (s.startswith("cp") and int(s.split()[1]) == 0) for s in low)
emit("")
if win_ok and zero99 and discrim:
    emit("**CONFIRMS**: the board is genuinely won (halfmove 0 scores %s), the PC build still returns **cp 0 at "
         "halfmove 99** in %s nodes, and halfmoves 96-98 do NOT return cp 0 — so the short-circuit is firing one ply "
         "down rather than at the root." % (pc0["score"], f"{pc99['nodes']:,}"))
else:
    emit("**NOT CONFIRMED as stated** — see the table. plant_win=%s zero99=%s discriminator=%s"
         % (win_ok, zero99, discrim))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
