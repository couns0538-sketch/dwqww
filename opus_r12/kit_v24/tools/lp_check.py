#!/usr/bin/env python3
"""lp_check.py - node-identity checks for LTO+PGO (or any) Forge builds. Waits for real UCI output, no sleeps.

  run EXE OUT.json [--opt Name=Value]... [--depths "11 13 16 20 22"] [--fen-depth 13] [--fens FILE] [--perft 5] [--core 5]
      Fresh process. With no --opt NOTHING is set: every UCI option stays at its default (= OFF).
      Records: bench <d> totals, perft <n> for startpos and kiwipete, and per bench position
      (ucinewgame; position fen F; go depth D) the final 'info ... nodes' value and the bestmove.
      On Linux the engine runs under nice 19 + taskset -c CORE; on Windows it runs as is (set priority/affinity outside).
  compare PLAIN.json LP.json [--pins d11=312866,d13=...] [--perft-pins startpos=4865609,kiwipete=193690690] [--off OFF.json]
      Exit 0 only if every number and bestmove in LP equals PLAIN (and the pins, if given).
      --off: also say whether this option run differs from the OFF run (a run equal to OFF proves nothing).
"""
import json, os, re, subprocess, sys

KIWI = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"

def arg(args, name, default=None, multi=False):
    vals = [args[i + 1] for i, a in enumerate(args) if a == name and i + 1 < len(args)]
    return vals if multi else (vals[-1] if vals else default)

def run(args):
    exe, out = args[0], args[1]
    opts = arg(args, "--opt", multi=True)
    depths = [int(x) for x in arg(args, "--depths", "11 13 16 20 22").split()]
    fdepth = int(arg(args, "--fen-depth", "13"))
    fens_file = arg(args, "--fens", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "workload", "bench_fens.txt"))
    fens = [l.strip() for l in open(fens_file) if l.strip()]
    perft = int(arg(args, "--perft", "5"))
    core = arg(args, "--core", "5")
    cmd = [exe] if os.name == "nt" else ["nice", "-n", "19", "taskset", "-c", core, exe]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    log = open(out + ".uci.log", "w")
    def send(s):
        p.stdin.write(s + "\n"); p.stdin.flush(); log.write("> " + s + "\n")
    def wait(rx, keep=None):
        r = re.compile(rx); last = None
        for line in p.stdout:
            log.write(line); log.flush()
            if keep:
                m = keep.search(line)
                if m: last = m
            m = r.search(line)
            if m: return m, last
        raise SystemExit("engine exited before " + rx)
    send("uci"); wait(r"^uciok")
    for o in opts:
        n, v = o.split("=", 1)
        send(f"setoption name {n} value {v}")
    send("isready"); wait(r"^readyok")
    res = {"exe": exe, "opts": opts, "bench": {}, "perft": {}, "fen_depth": fdepth, "fens": []}
    for d in depths:
        send(f"bench {d}"); m, _ = wait(rf"bench depth {d} nodes (\d+)")
        res["bench"][f"d{d}"] = int(m.group(1)); print(f"bench d{d} {m.group(1)}", flush=True)
    for name, pos in (("startpos", "position startpos"), ("kiwipete", "position fen " + KIWI)):
        send(pos); send(f"go perft {perft}"); m, _ = wait(r"^nodes (\d+)")
        res["perft"][name] = int(m.group(1)); print(f"perft{perft} {name} {m.group(1)}", flush=True)
    info = re.compile(r"^info depth \d+ .* nodes (\d+) ")
    for i, f in enumerate(fens):
        send("ucinewgame"); send("isready"); wait(r"^readyok")
        send("position fen " + f); send(f"go depth {fdepth}")
        m, last = wait(r"^bestmove (\S+)", keep=info)
        nodes = int(last.group(1)) if last else -1
        res["fens"].append({"i": i, "fen": f, "nodes": nodes, "bestmove": m.group(1)})
        print(f"fen{i} d{fdepth} nodes {nodes} bestmove {m.group(1)}", flush=True)
    send("quit"); p.wait(timeout=60)
    json.dump(res, open(out, "w"), indent=1)

def parse_pins(s):
    return dict((k, int(v)) for k, v in (x.split("=") for x in s.split(","))) if s else {}

def compare(args):
    a, b = json.load(open(args[0])), json.load(open(args[1]))
    pins, ppins = parse_pins(arg(args, "--pins")), parse_pins(arg(args, "--perft-pins"))
    off = json.load(open(arg(args, "--off"))) if arg(args, "--off") else None
    ok = True
    print(f"opts: {a['opts'] or 'none (all UCI defaults = OFF)'}")
    print(f"{'item':<12} {'plain':>12} {'ltopgo':>12} {'pin':>12}  result")
    def row(k, x, y, pin=None):
        nonlocal ok
        good = x == y and (pin is None or x == pin); ok &= good
        print(f"{k:<12} {x!s:>12} {y!s:>12} {('' if pin is None else pin)!s:>12}  {'OK' if good else 'FAIL'}")
    for k in a["bench"]: row("bench " + k, a["bench"][k], b["bench"].get(k), pins.get(k))
    for k in a["perft"]: row("perft " + k, a["perft"][k], b["perft"].get(k), ppins.get(k))
    for fa, fb in zip(a["fens"], b["fens"]):
        row(f"fen{fa['i']} d{a['fen_depth']}", fa["nodes"], fb["nodes"])
        row(f"fen{fa['i']} best", fa["bestmove"], fb["bestmove"])
    if len(a["fens"]) != len(b["fens"]): ok = False; print("FEN count differs FAIL")
    if off is not None:
        same = off["bench"] == a["bench"] and [f["nodes"] for f in off["fens"]] == [f["nodes"] for f in a["fens"]]
        print("option run vs OFF: " + ("IDENTICAL to OFF (option not proven live at these depths)" if same else "differs from OFF (live)"))
    print("NODE IDENTITY: ALL OK" if ok else "NODE IDENTITY: MISMATCH")
    return 0 if ok else 1

if __name__ == "__main__":
    if len(sys.argv) < 4 or sys.argv[1] not in ("run", "compare"): sys.exit(__doc__)
    sys.exit(run(sys.argv[2:]) or 0 if sys.argv[1] == "run" else compare(sys.argv[2:]))
