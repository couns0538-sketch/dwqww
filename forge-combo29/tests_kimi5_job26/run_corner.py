#!/usr/bin/env python3
"""kimi5 job 26 step 2: one corner = one fresh engine process, 40 positions
(O[0:20] then G[0:20]), ucinewgame + isready before every search, go depth 9.
usage: run_corner.py <engine> <name|BASE> <value|-> <outdir>
Writes <outdir>/<tag>.input.log, <tag>.txt (raw), <tag>.meta, <tag>.row
"""
import subprocess, sys, os, re, hashlib, threading

engine, name, value, outdir = sys.argv[1:5]
tag = "base" if name == "BASE" else f"{name}_{'min' if value.endswith('!min') else 'max'}"
val = value.replace("!min", "").replace("!max", "")
os.makedirs(outdir, exist_ok=True)

PC20 = [l.split() for l in open(os.path.join(os.path.dirname(__file__), "pc20.opt")) if l.strip() and not l.startswith("#")]
POSITIONS = []
base_dir = os.path.dirname(__file__)
for f in ("O.epd", "G.epd"):
    POSITIONS += [l.strip() for l in open(os.path.join(base_dir, f))][:20]

cmds = []
for n, v in PC20:
    cmds.append(f"setoption name {n} value {v}")
cmds += ["setoption name Threads value 1", "setoption name Hash value 16"]
if name == "BASE":
    for n, v in [("QsSeeMargin", 40), ("CaptureFutilityMultiplier", 250), ("CaptureFutilityDepth", 6),
                 ("AspFailHighMaxReduce", 3), ("EvalSwingMax", 200)]:
        cmds.append(f"setoption name {n} value {v}")
else:
    cmds.append(f"setoption name {name} value {val}")

inp = open(f"{outdir}/{tag}.input.log", "w")
out = open(f"{outdir}/{tag}.txt", "w")
proc = subprocess.Popen([engine], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, text=True, bufsize=1)
for c in cmds:
    proc.stdin.write(c + "\n"); inp.write(c + "\n")
proc.stdin.write("uci\n"); inp.write("uci\n")
proc.stdin.flush()

idname = ""
# read until uciok
while True:
    line = proc.stdout.readline()
    if not line: break
    out.write(line)
    if line.startswith("id name"): idname = line.strip()
    if line.strip() == "uciok": break

searches = 0
nodes_sum = 0
bestmoves = []
hang = ""
dead = False
for i, fen in enumerate(POSITIONS):
    for c in (f"ucinewgame", "isready"):
        proc.stdin.write(c + "\n"); inp.write(c + "\n")
    proc.stdin.flush()
    # wait readyok (120 s guard)
    got = [False]
    def drain_ready():
        while True:
            line = proc.stdout.readline()
            if not line: return
            out.write(line)
            if line.strip() == "readyok":
                got[0] = True; return
    t = threading.Thread(target=drain_ready, daemon=True); t.start(); t.join(120)
    if not got[0]:
        hang = f"no readyok before search {i}"; dead = True; break
    proc.stdin.write(f"position fen {fen}\ngo depth 9\n"); inp.write(f"position fen {fen}\ngo depth 9\n")
    proc.stdin.flush()
    last_nodes = [None]
    got_bm = [False]
    def drain_go():
        while True:
            line = proc.stdout.readline()
            if not line: return
            out.write(line)
            m = re.search(r"^info depth \d+ .* nodes (\d+)", line)
            if m: last_nodes[0] = int(m.group(1))
            if line.startswith("bestmove"):
                bestmoves.append(line.strip())
                got_bm[0] = True; return
    t = threading.Thread(target=drain_go, daemon=True); t.start(); t.join(120)
    if not got_bm[0]:
        hang = f"no bestmove within 120 s at search {i} ({fen})"; dead = True; break
    searches += 1
    if last_nodes[0] is not None: nodes_sum += last_nodes[0]

if dead:
    try: proc.kill()
    except Exception: pass
else:
    try:
        proc.stdin.write("quit\n"); inp.write("quit\n"); proc.stdin.flush()
    except Exception: pass
try:
    rc = proc.wait(timeout=10)
except Exception:
    proc.kill(); rc = proc.wait()
inp.close(); out.close()

raw = open(f"{outdir}/{tag}.txt").read()
san = [l for l in raw.splitlines() if "runtime error" in l or "Sanitizer" in l or "AddressSanitizer" in l]
refusal = [l for l in raw.splitlines() if "unknown option" in l or "invalid value" in l or "ERROR" in l]
sha = hashlib.sha256(open(engine, "rb").read()).hexdigest()
with open(f"{outdir}/{tag}.meta", "w") as m:
    m.write(f"exe {engine}\nsha256 {sha}\n{idname}\ncorner {name} {val}\nsettings: see {tag}.input.log\n")
with open(f"{outdir}/{tag}.row", "w") as r:
    r.write(f"{tag}\tsearches={searches}\tbestmoves={len(bestmoves)}\texit={rc}\tsanitizer={len(san)}\t"
            f"refusal={len(refusal)}\tnodes_sum={nodes_sum}\thang={hang!r}\n")
    if san: r.write(f"first_sanitizer: {san[0]}\n")
    if refusal: r.write(f"first_refusal: {refusal[0]}\n")
print(f"{tag}: searches={searches} exit={rc} san={len(san)} nodes={nodes_sum} hang={hang!r}")
