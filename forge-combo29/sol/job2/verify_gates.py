#!/usr/bin/env python3
"""Check the uninstrumented/counting identity and the three counter controls."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

EXPECTED = {
    "O": (200, 8315168, [21812, 26844, 35173], "fd609b7b1a8dd179", "14583c86b5f56cb6"),
    "G": (353, 17611204, [31779, 46086, 84457], "60b6916f01395e99", "0846f027e7e9b77e"),
}
CNT_PREFIX = "info string CNT "


def rows(folder, name):
    path = folder / f"{name}.jsonl"
    meta = json.loads(path.with_suffix(".jsonl.meta").read_text())
    assert meta["status"] == "complete", meta
    return [json.loads(line) for line in path.read_text().splitlines()]


def cnt(row):
    assert row["cnt"].startswith(CNT_PREFIX), row
    return json.loads(row["cnt"].removeprefix(CNT_PREFIX))


def digest(values):
    return sha256("".join(f"{v}\n" for v in values).encode()).hexdigest()[:16]


def identities(folder):
    for dataset, want in EXPECTED.items():
        plain = rows(folder, f"identity-plain-{dataset}")
        instrumented = rows(folder, f"identity-count-{dataset}")
        assert len(plain) == len(instrumented) == want[0]
        for p, c in zip(plain, instrumented):
            assert all(p[k] == c[k] for k in ("fen", "nodes", "bestmove", "depth")), (dataset, p["index"])
            counted = cnt(c)
            assert sum(counted["main_nodes"]) + sum(counted["q_nodes"]) == c["nodes"], (dataset, c["index"])
        nodes = [r["nodes"] for r in plain]
        moves = [r["bestmove"] for r in plain]
        actual = (len(nodes), sum(nodes), nodes[:3], digest(nodes), digest(moves))
        assert actual == want, (dataset, actual, want)
        print(f"{dataset}: {actual[0]}/{want[0]} exact, nodes {actual[1]}, first three {actual[2]}, node SHA {actual[3]}, move SHA {actual[4]}")


def controls(folder):
    names = ("pc20", "rfp-off", "eval-swing", "null-min10")
    counters = {}
    for name in names:
        samples = rows(folder, f"control-{name}")
        assert len(samples) == 20, name
        counts = [cnt(row) for row in samples]
        assert all(sum(c["main_nodes"]) + sum(c["q_nodes"]) == 20000 for c in counts), name
        counters[name] = {event: [sum(c[event][d] for c in counts) for d in range(32)] for event in counts[0]}
    base = counters["pc20"]
    no_rfp = counters["rfp-off"]["rfp_taken"]
    swing = counters["eval-swing"]["eval_swing_taken"]
    nulls = counters["null-min10"]["null_move_tested"]
    print(f"RfpDepth=0: {sum(no_rfp)} taken at all depths; PC20 {sum(base['rfp_taken'])}")
    print(f"EvalSwingMult=16: {sum(swing)} updates; PC20 {sum(base['eval_swing_taken'])}")
    print(f"NullMoveMinDepth=10: {sum(nulls[:10])} tries below depth 10; {sum(nulls[10:])} at depth 10+; PC20 {sum(base['null_move_tested'][:10])} below 10")
    assert sum(no_rfp) == 0 and sum(base["rfp_taken"]) > 0
    assert sum(swing) > 0 and sum(base["eval_swing_taken"]) == 0
    assert sum(nulls[:10]) == 0 and sum(base["null_move_tested"][:10]) > 0


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("stage", choices=("identities", "controls"))
parser.add_argument("raw", type=Path)
args = parser.parse_args()
{"identities": identities, "controls": controls}[args.stage](args.raw)
