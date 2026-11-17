"""How much does the cluster mapping actually change between two table sizes?

The engine indexes by multiply-high: cluster = (key * cluster_count) >> 64. Any
change in cluster_count remaps essentially every key, because the index is a
continuous function of a fractional multiplier.

This measures it on real traffic: run one search at each size, dump every occupied
slot's full key, and count how many keys map to a DIFFERENT cluster at the other
size. The number matters because a key that moves to a different cluster is
competing for a different set of three neighbours -- so the replacement policy
evicts a different entry, even when both tables are nearly empty.

Reported beside it: the fraction of keys that share their cluster with a
different key at each size (the actual collision pressure).
"""

import json
import subprocess
import sys

BUDGET = 2000000


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


def run(binary, fen, hash_mb):
    """Return (answer, keys, clusters)."""
    process = subprocess.Popen([binary], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               text=True, bufsize=1)
    process.stdin.write(f"uci\n")
    process.stdin.flush()
    while True:
        line = process.stdout.readline()
        if line.strip() == "uciok":
            break
    for command in (f"setoption name Hash value {hash_mb}",
                    "setoption name Threads value 1",
                    "setoption name OwnBook value false",
                    "isready"):
        process.stdin.write(command + "\n")
    process.stdin.flush()
    while True:
        if process.stdout.readline().strip() == "readyok":
            break

    keys = []
    clusters = 0
    bestmove = None
    score = None

    process.stdin.write(f"position fen {fen}\n")
    process.stdin.write(f"go nodes {BUDGET}\n")
    process.stdin.flush()
    while True:
        line = process.stdout.readline()
        if not line:
            break
        stripped = line.strip()
        if stripped.startswith("bestmove"):
            bestmove = stripped.split()[1]
        elif "score cp" in stripped:
            score = int(stripped.split("score cp")[1].split()[0])
        elif stripped.startswith("score mate") or "score mate" in stripped:
            score = 10000
        if bestmove is not None:
            break

    process.stdin.write("ttkeys\nisready\n")
    process.stdin.flush()
    while True:
        line = process.stdout.readline()
        if not line:
            break
        stripped = line.strip()
        if stripped.startswith("keysbegin"):
            clusters = int(stripped.split()[1])
            continue
        if stripped == "keysend":
            # drain to readyok
            while True:
                tail = process.stdout.readline()
                if not tail or tail.strip() == "readyok":
                    break
            break
        if stripped.isdigit():
            keys.append(int(stripped))

    process.stdin.write("quit\n")
    process.stdin.flush()
    process.wait(timeout=30)
    return bestmove, score, keys, clusters


def main():
    binary = sys.argv[1]
    out_path = sys.argv[2]
    position_file = sys.argv[3]
    fens = load_positions(position_file, 8)

    sizes = [64, 65, 256]
    results = {}
    for fen in fens:
        for size in sizes:
            bestmove, score, keys, clusters = run(binary, fen, size)
            results[(fen, size)] = {
                "bestmove": bestmove,
                "score": score,
                "keys": keys,
                "clusters": clusters,
            }
            print(f"  done hash={size} keys={len(keys)} clusters={clusters} for {fen[:24]}",
                  flush=True)

    rows = []
    print("\n## Cluster remap and collision pressure\n")
    print("| size pair | budget | keys moved cluster | keys sharing cluster |")
    print("|---|---|---|---|")

    for fen in fens:
        for a_size, b_size in ((64, 65), (64, 256)):
            a = results[(fen, a_size)]
            b = results[(fen, b_size)]
            common = set(a["keys"]) & set(b["keys"])
            if not common:
                continue

            def cluster_of(key, count):
                return (key * count) >> 64

            moved = sum(1 for key in common
                        if cluster_of(key, a["clusters"]) != cluster_of(key, b["clusters"]))
            # Collision pressure inside the smaller table: keys sharing a cluster.
            buckets = {}
            for key in a["keys"]:
                buckets.setdefault(cluster_of(key, a["clusters"]), []).append(key)
            sharing = sum(len(v) - 1 for v in buckets.values() if len(v) > 1)
            rows.append({
                "fen": fen,
                "pair": f"{a_size}-{b_size}",
                "common_keys": len(common),
                "moved_cluster": moved,
                "moved_fraction": moved / len(common),
                "keys_sharing_cluster": sharing,
                "sharing_fraction": sharing / len(a["keys"]) if a["keys"] else 0,
                "differed": (a["bestmove"] != b["bestmove"] or a["score"] != b["score"]),
            })
            print(f"| {a_size} vs {b_size} | {BUDGET} | "
                  f"{moved}/{len(common)} ({moved/len(common)*100:.1f}%) | "
                  f"{sharing}/{len(a['keys'])} ({sharing/len(a['keys'])*100:.1f}%) |")

    with open(out_path, "w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")

    # Summary over cells
    print("\n## Summary, means over cells\n")
    print("| pair | mean keys moved cluster | mean keys sharing cluster | cells differing |")
    print("|---|---|---|---|")
    for pair in ("64-65", "64-256"):
        subset = [r for r in rows if r["pair"] == pair]
        if not subset:
            continue
        moved = sum(r["moved_fraction"] for r in subset) / len(subset)
        sharing = sum(r["sharing_fraction"] for r in subset) / len(subset)
        differed = sum(1 for r in subset if r["differed"])
        print(f"| {pair} | {moved*100:.1f}% | {sharing*100:.1f}% | {differed}/{len(subset)} |")


if __name__ == "__main__":
    main()
