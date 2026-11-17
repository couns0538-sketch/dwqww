#!/usr/bin/env python3
"""probe.py -- one UCI question per position, with the FEN-refusal trap handled.

Rules implemented (from the coordinator's two corrections):
  * every FEN is validated by python-chess BEFORE it is sent;
  * the `position` reply AND the `go` output are BOTH scanned for `invalid FEN`,
    because the diagnostic moves between the two depending on whether an
    `isready` follows `position`;
  * `bestmove` is awaited with a timeout; `info depth` is never used as a
    completion signal;
  * nothing is parsed out of the search before the refusal check has passed.

Usage:
  probe.py --exe PATH --fen FEN --depth N [--options "Name=Value;..."] [--json]
  probe.py --exe PATH --fen-file F --depth N [--options ...] --out out.jsonl
"""
import argparse
import json
import re
import subprocess
import sys
import time

try:
    import chess
except ImportError:
    sys.stderr.write("python-chess is required: pip install python-chess\n")
    sys.exit(3)


def validate_fen(fen):
    """Return (ok, reason). A FEN python-chess rejects is never sent."""
    try:
        board = chess.Board(fen)
    except ValueError as exc:
        return False, "python-chess rejected: %s" % exc
    if not board.is_valid():
        return False, "python-chess: position not valid (status %d)" % board.status()
    return True, "ok"


def fen_facts(fen):
    b = chess.Board(fen)
    return {
        "side": "white" if b.turn else "black",
        "halfmove": b.halfmove_clock,
        "fullmove": b.fullmove_number,
        "legal_moves": b.legal_moves.count(),
        "in_check": b.is_check(),
        "board_is_valid": b.is_valid(),
    }


MATE_RE = re.compile(r"\bscore mate (-?\d+)")
CP_RE = re.compile(r"\bscore cp (-?\d+)")
DEPTH_RE = re.compile(r"\binfo depth (\d+)")
NODES_RE = re.compile(r"\bnodes (\d+)")


def score_of(line):
    m = MATE_RE.search(line)
    if m:
        return ("mate", int(m.group(1)))
    m = CP_RE.search(line)
    if m:
        return ("cp", int(m.group(1)))
    return (None, None)


def run_one(exe, fen, depth, options, extra_go="", timeout=120.0, movetime=None):
    """One fresh process, one position, one go. Returns a result dict."""
    res = {
        "fen": fen,
        "depth": depth,
        "options": options,
        "refused": False,
        "refusal_where": None,
        "refusal_line": None,
        "timed_out": False,
        "bestmove": None,
        "last_info": None,
        "last_score": None,
        "last_depth": None,
        "last_nodes": None,
        "info_lines": 0,
        "rc": None,
        "stderr": "",
    }
    ok, why = validate_fen(fen)
    res["fen_valid_python_chess"] = ok
    res["fen_check"] = why
    if not ok:
        res["skipped"] = True
        return res

    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    def send(line):
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(pred, deadline):
        """Read lines until pred(line) or the deadline; returns (lines, hit)."""
        out = []
        while time.monotonic() < deadline:
            line = proc.stdout.readline()
            if line == "":
                return out, False
            line = line.rstrip("\n")
            out.append(line)
            if pred(line):
                return out, True
        return out, False

    try:
        send("uci")
        seen_uci, _ = read_until(lambda l: l.strip() == "uciok", time.monotonic() + timeout)
        for name, value in options:
            if value is None:
                send("setoption name %s" % name)
            else:
                send("setoption name %s value %s" % (name, value))
        send("isready")
        opt_lines, _ = read_until(lambda l: l.strip() == "readyok", time.monotonic() + timeout)
        res["option_errors"] = [
            l for l in opt_lines
            if "unknown option" in l or "invalid value" in l
        ]

        send("ucinewgame")
        send("isready")
        read_until(lambda l: l.strip() == "readyok", time.monotonic() + timeout)

        # --- the position reply window -------------------------------------
        send("position fen " + fen)
        send("isready")
        pos_lines, got_ready = read_until(
            lambda l: l.strip() == "readyok", time.monotonic() + timeout)
        res["position_reply"] = pos_lines
        for line in pos_lines:
            if "invalid FEN" in line:
                res["refused"] = True
                res["refusal_where"] = "position reply"
                res["refusal_line"] = line
                break

        if res["refused"]:
            send("quit")
            proc.wait(timeout=10)
            res["rc"] = proc.returncode
            return res

        # --- the go window --------------------------------------------------
        if movetime is not None:
            send("go movetime %d %s" % (movetime, extra_go))
        else:
            send("go depth %d %s" % (depth, extra_go))
        go_lines, got_best = read_until(
            lambda l: l.startswith("bestmove"), time.monotonic() + timeout)
        res["timed_out"] = not got_best

        # The refusal can land here instead, ahead of the first info depth.
        first_info = None
        for idx, line in enumerate(go_lines):
            if "invalid FEN" in line:
                res["refused"] = True
                res["refusal_where"] = "go output"
                res["refusal_line"] = line
                res["go_index_of_refusal"] = idx
            if first_info is None and DEPTH_RE.search(line):
                first_info = idx
        res["go_index_of_first_info_depth"] = first_info

        if res["refused"]:
            send("quit")
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
            res["rc"] = proc.returncode
            return res

        for line in go_lines:
            if DEPTH_RE.search(line):
                res["info_lines"] += 1
                res["last_info"] = line
                res["last_depth"] = int(DEPTH_RE.search(line).group(1))
                kind, val = score_of(line)
                res["last_score"] = [kind, val]
                nm = NODES_RE.search(line)
                if nm:
                    res["last_nodes"] = int(nm.group(1))
            if line.startswith("bestmove"):
                res["bestmove"] = line.split()[1]

        send("quit")
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        res["rc"] = proc.returncode
        res["stderr"] = proc.stderr.read()[:2000]
    finally:
        if proc.poll() is None:
            proc.kill()
    return res


def parse_options(spec):
    out = []
    if not spec:
        return out
    for part in spec.split(";"):
        part = part.strip()
        if not part:
            continue
        if "=" in part:
            name, value = part.split("=", 1)
            out.append((name.strip(), value.strip()))
        else:
            out.append((part, None))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--fen")
    ap.add_argument("--fen-file")
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--movetime", type=int)
    ap.add_argument("--options", default="")
    ap.add_argument("--extra-go", default="")
    ap.add_argument("--timeout", type=float, default=120.0)
    ap.add_argument("--out")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    options = parse_options(args.options)

    if args.fen_file:
        fens = [l.strip() for l in open(args.fen_file) if l.strip() and not l.startswith("#")]
    else:
        fens = [args.fen]

    results = []
    sink = open(args.out, "w") if args.out else None
    for fen in fens:
        r = run_one(args.exe, fen, args.depth, options,
                    extra_go=args.extra_go, timeout=args.timeout,
                    movetime=args.movetime)
        r["facts"] = fen_facts(fen) if r.get("fen_valid_python_chess") else None
        results.append(r)
        if sink:
            sink.write(json.dumps(r) + "\n")
            sink.flush()
            print("%s d%d -> %s %s nodes=%s refused=%s%s" % (
                fen, args.depth,
                r["last_score"][0], r["last_score"][1],
                r["last_nodes"], r["refused"],
                " (%s)" % r["refusal_where"] if r["refused"] else ""))
        elif args.json:
            print(json.dumps(r, indent=2))
        else:
            print("%s d%d -> %s %s nodes=%s refused=%s%s" % (
                fen, args.depth,
                r["last_score"][0], r["last_score"][1],
                r["last_nodes"], r["refused"],
                " (%s)" % r["refusal_where"] if r["refused"] else ""))
    if sink:
        sink.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
