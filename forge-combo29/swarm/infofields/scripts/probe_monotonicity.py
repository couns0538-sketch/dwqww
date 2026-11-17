"""Final consistency sweeps: monotonicity of `nodes` and `time` under threading.

`nodes` is `total_nodes()`: local_nodes_ plus every other worker's published
atomic, read without a barrier while helpers are still running. At Threads > 1
the sum is therefore only a lower bound at any instant, and nothing guarantees
the NEXT line is larger. This sweep looks for a decrease on the wire.

`time` is recomputed from `start_` at every emit, so it must be non-decreasing.

Both are repeated to give the reader a rate rather than a single anecdote.
"""

import json
import os

import uci

ENGINE = os.environ.get("FORGE_BIN", "/agent/repos/work-infofields/build/forge")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evidence")
SET = {"build": "g++ -DFORGE_MARCH=x86-64-v4 Release NDEBUG", "base_commit": "6b98f217",
       "own_book": False, "hash_mb": "default 32"}


def parse(lines):
    out = []
    for l in lines:
        f, pv = uci.parse_info(l)
        if f and "depth" in f:
            out.append({**f, "pv_moves": pv, "_line": l})
    return out


def main():
    result = {"by_threads": []}
    for threads in (1, 2, 4):
        node_drops, time_drops, runs = [], [], []
        for trial in range(4):
            e = uci.Engine(ENGINE)
            e.handshake()
            e.setoption("OwnBook", "false")
            e.setoption("Threads", str(threads))
            e.position()
            lines, bm = e.search("depth 16", timeout=300)
            e.quit()
            rows = parse(lines)
            ns = [int(r["nodes"]) for r in rows]
            ts = [int(r["time"]) for r in rows]
            for i in range(1, len(rows)):
                if ns[i] < ns[i - 1]:
                    node_drops.append({"trial": trial,
                                       "prev": rows[i - 1]["_line"],
                                       "cur": rows[i]["_line"],
                                       "prev_nodes": ns[i - 1], "cur_nodes": ns[i]})
                if ts[i] < ts[i - 1]:
                    time_drops.append({"trial": trial, "prev": rows[i - 1]["_line"],
                                       "cur": rows[i]["_line"]})
            runs.append({"trial": trial, "final_nodes": ns[-1], "final_time": ts[-1],
                         "n_lines": len(rows)})
        result["by_threads"].append({
            "threads": threads, "runs": runs,
            "node_drop_count": len(node_drops),
            "time_drop_count": len(time_drops),
            "node_drops": node_drops, "time_drops": time_drops,
            "final_node_range": [min(r["final_nodes"] for r in runs),
                                 max(r["final_nodes"] for r in runs)],
        })

    with open(os.path.join(OUT, "monotonicity.json"), "w") as fh:
        json.dump({"settings": SET, **result}, fh, indent=1, sort_keys=True)

    for r in result["by_threads"]:
        print("Threads %d: node drops %d, time drops %d, final nodes %s" % (
            r["threads"], r["node_drop_count"], r["time_drop_count"],
            r["final_node_range"]))
        for d in r["node_drops"][:3]:
            print("   nodes %d -> %d" % (d["prev_nodes"], d["cur_nodes"]))
            print("     prev:", d["prev"][:130])
            print("     cur :", d["cur"][:130])


if __name__ == "__main__":
    main()
