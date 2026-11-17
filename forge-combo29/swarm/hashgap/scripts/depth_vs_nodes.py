"""The test that separates "the table loses a good entry" from "the tree is
chaotic under a node budget".

A `go nodes N` search stops mid-iteration at exactly N nodes. Two table sizes
visit slightly different trees, so they stop at slightly different points in the
tree, and a different subtree may be the last one searched. That is a property of
node-limited search, not of any lost entry.

If that is what is happening, then:

* equal-NODE searches should differ often, and
* equal-DEPTH searches should agree, because a completed depth iteration is a
  fixed point of the search rather than a stopping point inside one.

This runs both and reports them side by side. No arm is enabled: both rows are
the shipped search, so the only difference between the rows is the stopping rule.
"""

import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor

HASHES = [1, 16, 64, 256]
DEPTHS = [14, 16, 18, 20]
NODES = [500000, 1000000, 2000000]
POSITION_COUNT = 16


def load_positions(path, count):
    fens = []
    with open(path) as handle:
        for line in handle:
            line = line.strip()
            if line and not line.startswith("#"):
                fens.append(line)
                if len(fens) >= count:
                    break
    return fens


def run_one(job):
    binary, fen, hash_mb, go = job
    import ucih

    try:
        cell = ucih.one_cell(binary, fen, go, hash_mb)
    except Exception as exc:  # noqa: BLE001
        return {"fen": fen, "hash": hash_mb, "go": go, "error": repr(exc)}
    trace = cell["trace"] or {}
    return {
        "fen": fen,
        "hash": hash_mb,
        "go": go,
        "bestmove": cell["bestmove"],
        "score": cell["score"],
        "depth": cell["depth"],
        "nodes": trace.get("nodes"),
    }


def main():
    binary = sys.argv[1]
    out_path = sys.argv[2]
    position_file = sys.argv[3]

    fens = load_positions(position_file, POSITION_COUNT)
    go_commands = [f"go nodes {n}" for n in NODES] + [f"go depth {d}" for d in DEPTHS]
    jobs = [(binary, fen, hash_mb, go)
            for go in go_commands for fen in fens for hash_mb in HASHES]
    print(f"{len(jobs)} cells", flush=True)

    rows = []
    started = time.monotonic()
    with ProcessPoolExecutor(max_workers=4) as pool:
        for i, row in enumerate(pool.map(run_one, jobs, chunksize=1), 1):
            rows.append(row)
            if i % 100 == 0:
                print(f"  {i}/{len(jobs)} {time.monotonic() - started:.0f}s", flush=True)

    with open(out_path, "w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")

    errors = [r for r in rows if "error" in r]
    print(f"wrote {len(rows)} rows, {len(errors)} refused")

    by_key = {(r["fen"], r["hash"], r["go"]): r for r in rows if "error" not in r}

    print("\n## Equal-nodes vs equal-depth: do sizes agree?\n")
    print("| stopping rule | Hash 1 | Hash 16 | Hash 256 | mean nodes (h16) | mean depth (h16) |")
    print("|---|---|---|---|---|---|")
    for go in go_commands:
        cells = []
        for hash_mb in HASHES:
            if hash_mb == 64:
                continue
            differed = 0
            counted = 0
            for fen in fens:
                base = by_key.get((fen, 64, go))
                other = by_key.get((fen, hash_mb, go))
                if base is None or other is None:
                    continue
                counted += 1
                if (other["bestmove"] != base["bestmove"]
                        or other["score"] != base["score"]):
                    differed += 1
            cells.append(f"**{differed}/{counted}**")
        nodes16 = [by_key[(f, 16, go)]["nodes"] for f in fens if (f, 16, go) in by_key]
        depth16 = [by_key[(f, 16, go)]["depth"] for f in fens if (f, 16, go) in by_key]
        mean_nodes = sum(nodes16) / len(nodes16) if nodes16 else 0
        mean_depth = sum(depth16) / len(depth16) if depth16 else 0
        print(f"| `{go}` | " + " | ".join(cells) +
              f" | {mean_nodes:.0f} | {mean_depth:.1f} |")


if __name__ == "__main__":
    main()
