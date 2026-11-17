"""`hashfull`: per-mille of WHAT?

UCI: "the number of hash table entries under consideration, in permill
(0-1000)". The accepted meaning is occupancy of the table: how full it is, so a
GUI can advise raising Hash.

The implementation counts only entries whose generation equals the CURRENT
search generation:

    int TransparentTable::hashfull() const {
        for (...) if (entry.occupied() && entry.generation() == generation_) ++count;
        return count * 1000 / (4 * sample);
    }

`Searcher::search` calls `shared_.tt.new_search()` once per search, bumping the
generation. So every entry written by an EARLIER search is invisible to this
count even though the entries are still in the table and still being probed.

Test, with two independent proofs (brief rule 2):

  A. Reported occupancy: the first info line of search 2 must read ~0 no matter
     how full search 1 left the table.
  B. The table really is still warm: search 2 must do FAR less work than the
     same search from a cold table. If both hold, the number is provably wrong
     about the table it describes.

Control: the same pair with an explicit cold table (`setoption Hash` to its own
value clears the table -- a known trap, used here deliberately) so B is shown to
be measuring warmth and not something else.
"""

import json
import os
import re

import uci

ENGINE = os.environ.get("FORGE_BIN", "/agent/repos/work-infofields/build/forge")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evidence")
SET = {"build": "g++ -DFORGE_MARCH=x86-64-v4 Release NDEBUG", "base_commit": "6b98f217",
       "threads": 1, "hash_mb": 32, "own_book": False, "fen": "startpos",
       "depth": 18}


def parse(lines):
    out = []
    for l in lines:
        f, pv = uci.parse_info(l)
        if f and "depth" in f:
            out.append({**f, "pv_moves": pv, "_line": l})
    return out


def engine():
    e = uci.Engine(ENGINE)
    e.handshake()
    e.setoption("OwnBook", "false")
    return e


def search(e, depth):
    e.position()
    lines, bm = e.search("depth %d" % depth, timeout=300)
    rows = parse(lines)
    return {"first": rows[0], "last": rows[-1],
            "first_hashfull": int(rows[0]["hashfull"]),
            "last_hashfull": int(rows[-1]["hashfull"]),
            "last_nodes": int(rows[-1]["nodes"])}


def main():
    depth = SET["depth"]
    e = engine()
    warm1 = search(e, depth)
    warm2 = search(e, depth)          # table already warm from warm1
    warm3 = search(e, depth)
    # control: force a cold table, then search again
    e.setoption("Hash", "32")         # same value: clears the table (known trap)
    cold = search(e, depth)
    e.quit()

    out = {
        "depth": depth,
        "run1_cold_table": warm1,
        "run2_warm_table": warm2,
        "run3_warm_table": warm3,
        "run4_after_forced_clear": cold,
        "proof_a_hashfull_reads_zero_on_warm_table": warm2["first_hashfull"] == 0,
        "proof_b_warm_is_cheaper": {
            "run1_nodes": warm1["last_nodes"], "run2_nodes": warm2["last_nodes"],
            "run3_nodes": warm3["last_nodes"], "run4_nodes_cold": cold["last_nodes"],
            "run2_is_much_cheaper_than_cold": warm2["last_nodes"] < 0.6 * cold["last_nodes"],
            "run3_is_much_cheaper_than_cold": warm3["last_nodes"] < 0.6 * cold["last_nodes"],
        },
        "hashfull_never_reports_the_warm_table": (
            warm2["first_hashfull"] == 0 and warm3["first_hashfull"] == 0),
    }

    with open(os.path.join(OUT, "hashfull_generation.json"), "w") as fh:
        json.dump({"settings": SET, **out}, fh, indent=1, sort_keys=True)

    def show(name, r):
        print("%-26s first hashfull=%-4d last hashfull=%-4d final nodes=%-8d" % (
            name, r["first_hashfull"], r["last_hashfull"], r["last_nodes"]))

    show("run1 (cold table)", warm1)
    show("run2 (warm from run1)", warm2)
    show("run3 (warm from run2)", warm3)
    show("run4 (after forced clear)", cold)
    print()
    print("proof A, hashfull reads 0 on a warm table:", out["proof_a_hashfull_reads_zero_on_warm_table"])
    print("proof B, warm run2 is <60%% of cold nodes:",
          out["proof_b_warm_is_cheaper"]["run2_is_much_cheaper_than_cold"])
    print("proof B, warm run3 is <60%% of cold nodes:",
          out["proof_b_warm_is_cheaper"]["run3_is_much_cheaper_than_cold"])
    print()
    print("run1 final line:", warm1["last"]["_line"][:150])
    print("run2 first line:", warm2["first"]["_line"][:150])


if __name__ == "__main__":
    main()
