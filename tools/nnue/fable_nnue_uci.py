#!/usr/bin/env python3
"""Drive a Forge engine over UCI for the NNUE v3 checks (job FB1).

  fable_nnue_uci.py <engine.exe> [--net <file.fnn3>] [--arch true|false] [--threads N] [--hash MB]
                    [--bench DEPTH ...] [--expect-exit N] [--setoption Name=Value ...]

Prints every engine line prefixed with '< ' and a summary line per bench:
  BENCH depth D nodes N time T nps X
With --expect-exit the exit status of the engine process must match (fail-loud checks).
"""
import argparse
import subprocess
import sys
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("engine")
    ap.add_argument("--net")
    ap.add_argument("--arch")
    ap.add_argument("--threads", type=int)
    ap.add_argument("--hash", type=int)
    ap.add_argument("--bench", type=int, nargs="*", default=[])
    ap.add_argument("--setoption", nargs="*", default=[])
    ap.add_argument("--expect-exit", type=int)
    ap.add_argument("--isready", action="store_true", help="send isready after the options (fail-loud check)")
    ap.add_argument("--fen", help="position for --go-depth (default: startpos)")
    ap.add_argument("--go-depth", type=int, help="search the position to this depth and wait for bestmove")
    ap.add_argument("--timeout", type=float, default=3600.0)
    args = ap.parse_args()

    cmds = ["uci"]
    if args.threads is not None:
        cmds.append(f"setoption name Threads value {args.threads}")
    if args.hash is not None:
        cmds.append(f"setoption name Hash value {args.hash}")
    for opt in args.setoption:
        name, value = opt.split("=", 1)
        cmds.append(f"setoption name {name} value {value}")
    if args.net is not None:
        cmds.append(f"setoption name NNUEArchFile value {args.net}")
    if args.arch is not None:
        cmds.append(f"setoption name NNUEArch value {args.arch}")
    if args.isready:
        cmds.append("isready")
    for depth in args.bench:
        cmds.append(f"bench {depth}")
    if args.go_depth is not None:
        cmds.append("position fen " + args.fen if args.fen else "position startpos")
        cmds.append(f"go depth {args.go_depth}")
    cmds.append("quit")

    proc = subprocess.Popen([args.engine], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    # A `go` must not be followed by `quit` before the search prints bestmove: send the commands up to `go`,
    # wait for bestmove, then quit.
    head = cmds[:-1]
    try:
        proc.stdin.write("\n".join(head) + "\n")
        proc.stdin.flush()
        if args.go_depth is None:
            proc.stdin.write("quit\n")
            proc.stdin.flush()
    except (BrokenPipeError, OSError):
        pass
    start = time.time()
    lines = []
    bestmove = None
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        line = line.rstrip("\r\n")
        lines.append(line)
        if not line.startswith("info depth"):
            print("< " + line, flush=True)
        if "bench depth" in line:
            parts = line.split()
            d = {parts[i]: parts[i + 1] for i in range(len(parts) - 1) if parts[i] in ("depth", "nodes", "time", "nps")}
            print(f"BENCH depth {d.get('depth')} nodes {d.get('nodes')} time {d.get('time')} nps {d.get('nps')}", flush=True)
        if line.startswith("bestmove"):
            bestmove = line.split()[1] if len(line.split()) > 1 else ""
            print(f"BESTMOVE {bestmove}", flush=True)
            try:
                proc.stdin.write("quit\n")
                proc.stdin.flush()
            except (BrokenPipeError, OSError):
                pass
        if time.time() - start > args.timeout:
            print("TIMEOUT", flush=True)
            break
    code = proc.wait(timeout=60)
    print(f"EXIT {code}", flush=True)
    if args.expect_exit is not None and code != args.expect_exit:
        print(f"FAIL: expected exit {args.expect_exit}, got {code}")
        sys.exit(1)
    if args.go_depth is not None and not bestmove:
        print("FAIL: no bestmove")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
