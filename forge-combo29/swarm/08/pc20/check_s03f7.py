#!/usr/bin/env python3
"""check_s03f7.py OUT — my own check of seat 03's S-F7:

"Under the full PC20 option set the PC build's perft counts are unchanged (20,000/20,000 identical to base on set A,
 perft-4 sum 2,196,757,662), so CuckooRep/HistRework/TtPruneV2/CorrHistV2/MateAlphaGuard [do not change move
 generation]."

The claim: perft is IDENTICAL with the PC20 switches on and off. That is a strong, cheap, discriminating statement —
if any of those five options changed a perft count, it would mean an option reaching into move generation, which would
be a far more serious finding than a search-tuning difference.

My own positions (R seed 801 and 902 + G), perft 2 and 4 (4 is the expensive one; I use a smaller set), under:
  arm A: PC r15 with PC20 OFF (S14 only)
  arm B: PC r15 with PC20 ON
and, for the absolute check, compare B against the BASE build too.

CONTROL: the harness must be able to SEE a perft difference — so I also run one position whose FEN I deliberately
corrupt by moving a pawn, and require its perft to differ from the original. Without that, "identical" could be a
harness that returns a constant.

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
       ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true"), ("OwnBook", "false")]

r1 = [l.strip() for l in open("../job1/R_seed801.fens") if l.strip()][:20]
r2 = [l.strip() for l in open("../v3/../job1/R_seed801.fens") if l.strip()][20:30] if len(r1) >= 20 else []
g = [" ".join(l.strip().split()[:6]) for l in open("../job1/set_G.epd") if l.strip()][:10]
FENS = r1 + g


def perft(exe, fen, depth, extra):
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
    for k, v in S14 + extra + [("Threads", "1"), ("Hash", "16")]:
        send("setoption name %s value %s" % (k, v))
        sync()
    send("ucinewgame")
    sync()
    send("position fen " + fen)
    pre = sync()
    if any("invalid FEN" in l for l in pre):
        return None
    send("go perft %d" % depth)
    lines = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise EOFError
        lines.append(l.rstrip("\n"))
        if l.startswith("nodes "):
            break
    sync()
    send("quit")
    try:
        p.wait(timeout=30)
    except Exception:
        p.kill()
    return int([l for l in lines if l.startswith("nodes ")][-1].split()[1])


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## seat 03 S-F7 — do the PC20 switches change a PERFT count? (they must not)")
emit("")
emit("PC r15, Threads 1, Hash 16. Arm A = S14 only (PC20 off); arm B = S14 + the five PC20 switches + OwnBook false.")
emit("")
emit("| fen | perft4 base | perft4 PC off | perft4 PC ON | all equal? |")
emit("|---|---|---|---|---|")
same_off_base = same_on_off = tot = 0
for fen in FENS:
    b = perft(BASE, fen, 4, [])
    a = perft(PC, fen, 4, [])
    c = perft(PC, fen, 4, PC20_EXTRA)
    if None in (b, a, c):
        emit("| %s | (one arm refused) | | | |" % fen[:34])
        continue
    tot += 1
    same_off_base += (a == b)
    same_on_off += (c == a)
    emit("| %s | %s | %s | %s | %s |" % (fen[:34], f"{b:,}", f"{a:,}", f"{c:,}",
                                          "yes" if a == b == c else "**NO**"))

emit("")
emit("## THE CONTROL — the harness must be able to see a difference")
emit("")
# take one position and move a pawn one square in the FEN, which MUST change perft
base_fen = FENS[0]
b = chess.Board(base_fen)
p_orig = perft(PC, base_fen, 2, [])
altered = None
p_alt = p_orig
# keep trying moves until the ENGINE reports a different perft 2 — the control must be found, not assumed
for m in list(b.legal_moves):
    b.push(m)
    cand = b.fen()
    b.pop()
    v = perft(PC, cand, 2, [])
    if v is not None and v != p_orig:
        altered, p_alt = cand, v
        break
emit("")
emit("| position | perft 2 |")
emit("|---|---|")
emit("| original | %s |" % f"{p_orig:,}")
emit("| one move later (must differ) | %s |" % f"{p_alt:,}")
control_ok = p_orig != p_alt
emit("")
emit("| question | answer |")
emit("|---|---|")
emit("| the harness can see a perft difference (control) | **%s** |" % ("YES" if control_ok else "**NO — VOID**"))
emit("| PC-off equals BASE on every position | **%d of %d** |" % (same_off_base, tot))
emit("| **PC-ON equals PC-off on every position** | **%d of %d** |" % (same_on_off, tot))
emit("")
if not control_ok:
    emit("**VOID**: the control could not produce a different perft, so 'identical' below means nothing.")
elif same_on_off == tot and same_off_base == tot:
    emit("**CONFIRMS**: turning every PC20 switch on changes NO perft count on %d positions, and the PC build matches" % tot)
    emit("the base build with them off. So none of the five options reaches move generation — they are search-side")
    emit("only, which is what S-F7 asserts.")
else:
    emit("**NOT CONFIRMED**: %d of %d positions differ between switch-on and switch-off, which would mean an option"
         % (tot - same_on_off, tot))
    emit("reaches move generation. That would be a far more serious finding than a search-tuning difference.")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
