#!/usr/bin/env python3
"""P2: identity of the option-off build with the unpatched engine.

For each of the first N lines of the UHO book: `ucinewgame`, `position fen`,
`go depth D`, and take best move, score and node count.  One engine process
serves all positions (with `ucinewgame` between them so no search leaks into
the next), which is faster than a process per position; the same script is used
for both builds, so the comparison is like for like.

Outputs, for one engine, a file with one line per position plus a sha256 over
the whole file, and the smallest node count seen.  The smallest node count is
reported on purpose: an identity proof over empty or trivially equal data must
not be able to pass by accident, so the report shows that real work was done.

Usage: python3 p2_identity.py <exe> <book> <positions> <depth> <outfile>
"""
import hashlib
import subprocess
import sys
import time

START = time.time()


def main():
    if len(sys.argv) != 6:
        print(__doc__)
        return 2
    exe, book, n_pos, depth, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]

    fens = []
    with open(book) as fh:
        for line in fh:
            parts = line.split()
            if len(parts) >= 6 and parts[1] in ("w", "b"):
                fens.append(" ".join(parts[:6]))
            if len(fens) >= n_pos:
                break
    print(f"read {len(fens)} positions from {book}")

    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True, bufsize=1)
    proc.stdin.write("uci\nisready\n")
    proc.stdin.flush()

    lines = []
    min_nodes = None
    for i, fen in enumerate(fens):
        proc.stdin.write(f"ucinewgame\nisready\nposition fen {fen}\ngo depth {depth}\n")
        proc.stdin.flush()
        best = None
        score = None
        nodes = None
        while True:
            reply = proc.stdout.readline()
            if not reply:
                raise RuntimeError("engine died")
            if reply.startswith("bestmove"):
                best = reply.split()[1] if len(reply.split()) > 1 else "none"
                break
            if reply.startswith("info") and " score " in reply and " pv " in reply:
                # keep the LAST score line, i.e. the final iteration
                toks = reply.split()
                sc = " ".join(toks[toks.index("score"):toks.index("score") + 3])
                score = sc
                if " nodes " in reply:
                    nodes = int(toks[toks.index("nodes") + 1])
        lines.append(f"{i} {fen} best={best} {score} nodes={nodes}")
        if nodes is not None:
            min_nodes = nodes if min_nodes is None else min(min_nodes, nodes)
        if (i + 1) % 250 == 0:
            print(f"  {i + 1} positions, {time.time() - START:.0f}s")

    proc.stdin.write("quit\n")
    proc.stdin.flush()
    proc.wait(timeout=30)

    with open(out, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    digest = hashlib.sha256(("\n".join(lines) + "\n").encode()).hexdigest()
    print(f"wrote {out}")
    print(f"positions={len(lines)} depth={depth} min_nodes={min_nodes}")
    print(f"sha256={digest}")
    with open(out + ".sha256", "w") as fh:
        fh.write(f"{digest}  {out}\npositions={len(lines)} depth={depth} min_nodes={min_nodes}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
