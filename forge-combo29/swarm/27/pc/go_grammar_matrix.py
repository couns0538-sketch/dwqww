#!/usr/bin/env python3
"""go_grammar_matrix.py <exe>

Map which MALFORMED `go` commands are accepted silently, and what each one actually does.

WHY. Four separate findings tonight share one shape: `bestmove 0000`, empty `info depth`, a refused FEN that
searches the previous position, and an ignored `go` token. In all four the protocol says nothing and in three
the output looks like success. Rather than collect them one at a time, this script reads the parser and then
tests EVERY failure mode it can produce, so the set is enumerated rather than discovered.

THE PARSER (src/uci.cpp, parse_limits). Each token is matched against a fixed list with `if/else if`. There is
**no else branch** - an unrecognised token falls through and is discarded with no message. Numbers are read by
`read_int()`, which returns **0** when `from_chars` fails, and `depth` is then `std::clamp(0, 1, 64)` = **1**.
`nodes`/`softnodes` only set `nodes_specified` if the parse SUCCEEDED, so a malformed count leaves **no limit at
all** rather than a zero limit.

So the predicted behaviours, each tested below:
   1. unknown token                       -> discarded, no message
   2. `depth <non-numeric>`               -> read_int 0 -> clamped to 1
   3. `depth` with no value               -> read_int 0 -> clamped to 1
   4. `nodes <non-numeric>`               -> nodes_specified stays false -> NO LIMIT (unbounded search)
   5. `nodes` with no value               -> same, NO LIMIT
   6. `movetime <non-numeric>`            -> read_clock of garbage -> 0 ms -> immediate stop
   7. `searchmoves <illegal moves>`       -> each dropped silently -> empty restriction
   8. `wtime`/`btime` for the side NOT to move -> stored in the other field, so no clock

CONTROLS:
  1. a well-formed `go depth 8` reaches depth 8 (the harness can produce a normal result)
  2. an unknown token changes NOTHING about a well-formed search (so a "no difference" verdict means silence,
     not a broken comparison)
  3. each test is a FRESH process, because a warm engine makes node counts incomparable
"""
import re
import subprocess
import sys
import time

TIMEOUT = 25.0


def probe(exe, go, fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", cap=TIMEOUT):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def s(x):
        p.stdin.write(x + "\n"); p.stdin.flush()

    def until(pred, tmo):
        t0 = time.monotonic(); out = []
        while time.monotonic() - t0 < tmo:
            ln = p.stdout.readline()
            if not ln:
                break
            y = ln.rstrip("\n"); out.append(y)
            if pred(y):
                return out, True
        return out, False

    try:
        s("uci")
        until(lambda x: x.strip() == "uciok", 20)
        s("setoption name Hash value 16"); s("setoption name Threads value 1")
        s("setoption name OwnBook value false")
        s("isready")
        until(lambda x: x.strip() == "readyok", 20)
        s("ucinewgame"); s("isready")
        until(lambda x: x.strip() == "readyok", 20)
        s("position fen " + fen)
        s("isready")
        pos, okp = until(lambda x: x.strip() == "readyok", 20)
        if not okp:
            return {"error": "no readyok"}
        s(go)
        t0 = time.monotonic()
        out, ok = until(lambda x: x.startswith("bestmove"), cap)
        el = time.monotonic() - t0
        infos = [l for l in out if l.startswith("info depth")]
        bm = [l for l in out if l.startswith("bestmove")]
        diag = [l for l in out if l.lower().startswith("info string")]
        depth = None
        nodes = None
        if infos:
            m = re.search(r"info depth (\d+)", infos[-1])
            depth = int(m.group(1)) if m else None
            m2 = re.search(r"nodes (\d+)", infos[-1])
            nodes = int(m2.group(1)) if m2 else None
        return {"bestmove": (bm[0].split()[1] if bm and len(bm[0].split()) > 1 else None),
                "depth": depth, "nodes": nodes, "n_info": len(infos),
                "secs": round(el, 2), "returned": ok, "diagnostics": diag}
    finally:
        try:
            p.stdin.write("stop\nquit\n"); p.stdin.flush(); p.wait(timeout=8)
        except Exception:
            p.kill()


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: go_grammar_matrix.py <exe>")
    exe = sys.argv[1]

    print("control 1: a well-formed `go depth 8` must reach depth 8")
    base = probe(exe, "go depth 8")
    c1 = base.get("depth") == 8
    print("   -> %s  %r" % ("PASS" if c1 else "FAIL", base))
    if not c1:
        print("harness cannot produce a normal result - aborting")
        raise SystemExit(2)

    print()
    print("control 2: an unknown token must not change a well-formed search")
    unknown = probe(exe, "go depth 8 zzzz 3")
    c2 = (unknown.get("depth"), unknown.get("nodes")) == (base.get("depth"), base.get("nodes"))
    print("   -> %s  depth %s nodes %s vs %s/%s"
          % ("PASS" if c2 else "FAIL", unknown.get("depth"), unknown.get("nodes"),
             base.get("depth"), base.get("nodes")))

    print()
    print("=== THE MATRIX: what each malformed command actually does (fresh process each) ===")
    print("  %-34s %-7s %-9s %-6s %-8s %s"
          % ("command", "depth", "nodes", "secs", "returned", "diagnostic"))
    cases = [
        ("go depth 8", "WELL-FORMED (reference)"),
        ("go depth 8 zzzz 3", "unknown token"),
        ("go depth abc", "depth non-numeric"),
        ("go depth", "depth with no value"),
        ("go depth 0", "depth zero"),
        ("go depth 999", "depth above the clamp"),
        ("go nodes abc", "nodes non-numeric"),
        ("go nodes", "nodes with no value"),
        ("go movetime abc", "movetime non-numeric"),
        ("go movetime 0", "movetime zero"),
        ("go searchmoves z9z9", "searchmoves illegal only"),
        ("go wtime abc", "wtime non-numeric (white to move)"),
        ("go btime 1000", "btime for the side NOT to move"),
    ]
    rows = []
    for go, why in cases:
        r = probe(exe, go, cap=8.0)
        d = r.get("diagnostics") or []
        print("  %-34s %-7s %-9s %-6s %-8s %s"
              % (go, r.get("depth"), r.get("nodes"), r.get("secs"),
                 r.get("returned"), (d[0][:34] if d else "NONE")))
        rows.append((go, why, r))

    print()
    print("=== READING ===")
    print("  A row whose 'diagnostic' is NONE was accepted silently.")
    print("  Compare its depth/nodes with the WELL-FORMED reference to see what it actually did.")
    silent = [r for go, why, r in rows if not (r.get("diagnostics") or []) and go != "go depth 8"]
    print()
    print("  %d of %d malformed commands produced NO diagnostic at all."
          % (len(silent), len(rows) - 1))


if __name__ == "__main__":
    main()
