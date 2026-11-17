"""JOB 1 + JOB 2: does a fixed `go nodes N` answer depend on the machine's environment?

Every variant here is something a harness author would consider irrelevant to the
search: the working directory, the locale, the timezone, which core the process runs
on, its nice level, its stack/file limits and its virtual-memory limit. A variant that
moves the node count or the bestmove is a hidden dependency, and a fixed-budget
measurement taken under it is not reproducible on another machine.

The budget is `go nodes 50000` (a fixed-count search) and `go depth 12`, both at
Threads 1 and Hash 16. Each variant is compared against the reference cell for the
same position; the comparison key is (nodes, bestmove, score, depth).
"""

import json
import os
import subprocess
import sys
import tempfile

import chess

import ucih
from matrix import BASE_EXE, PC_EXE, cell_key, summarize

OPTIONS = [("Hash", 16), ("Threads", 1)]
BUDGETS = ["go nodes 50000", "go depth 12"]


def load_fens():
    valid, invalid = ucih.validate_fens("/tmp/O.fens")
    assert not invalid, invalid[:3]
    return valid


def variants(tmpdir, fens):
    """name -> kwargs accepted by ucih.Engine (prefix / cwd / env)."""
    other_cwd = os.path.join(tmpdir, "elsewhere")
    os.makedirs(other_cwd, exist_ok=True)
    base_env = dict(os.environ)

    lang_env = dict(base_env)
    lang_env.update({"LANG": "tr_TR.UTF-8", "LC_ALL": "tr_TR.UTF-8",
                     "LC_NUMERIC": "de_DE.UTF-8", "TZ": "Pacific/Kiritimati"})

    shuffled_env = dict(base_env)
    # Same values, different insertion order: catches any getenv-order dependency.
    shuffled_env = {k: shuffled_env[k] for k in sorted(shuffled_env, reverse=True)}
    shuffled_env["TZ"] = "Asia/Kathmandu"

    return {
        # reference: the obvious invocation
        "ref": dict(),
        # same binary, different working directory
        "cwd_tmp": dict(cwd=other_cwd),
        "cwd_root": dict(cwd="/"),
        # locale and timezone
        "locale_tz": dict(env=lang_env),
        "env_order_tz": dict(env=shuffled_env),
        # CPU affinity: pin to one core, then to a different one
        "cpu0": dict(prefix=["taskset", "-c", "0"]),
        "cpu1": dict(prefix=["taskset", "-c", "1"]),
        "cpu2": dict(prefix=["taskset", "-c", "2"]),
        # scheduling priority
        "nice19": dict(prefix=["nice", "-n", "19"]),
        # resource limits
        "ulimit_v_2g": dict(prefix=["bash", "-c", 'ulimit -v 2097152; exec "$0"']),
        "ulimit_s_8m": dict(prefix=["bash", "-c", 'ulimit -s 8192; exec "$0"']),
        "ulimit_n_256": dict(prefix=["bash", "-c", 'ulimit -n 256; exec "$0"']),
        # memory pressure: a hard cap far below the Hash allocation
        "ulimit_v_64m": dict(prefix=["bash", "-c", 'ulimit -v 65536; exec "$0"']),
    }


def run_variant(spec, fens, budget):
    cells = []
    for fen in fens:
        try:
            res = ucih.Engine(
                BASE_EXE,
                cwd=spec.get("cwd"),
                env=spec.get("env"),
                timeout=300,
                prefix=spec.get("prefix"),
            )
            try:
                res.uci()
                for name, value in OPTIONS:
                    res.setoption(name, value)
                res.position_fen(fen)
                out = res.go(budget)
            finally:
                res.close()
            cells.append(summarize(out))
        except Exception as exc:  # noqa: BLE001 - a crash is a result here
            cells.append({"error": "%s: %s" % (type(exc).__name__, exc)})
    return cells


def main():
    fens = load_fens()
    sample = fens[:40]
    with tempfile.TemporaryDirectory() as tmpdir:
        specs = variants(tmpdir, sample)
        report = {}
        for budget in BUDGETS:
            ref = run_variant(specs["ref"], sample, budget)
            ref_keys = [tuple(c.get(k) for k in ("nodes", "bestmove", "score", "depth"))
                        for c in ref]
            entry = {"reference": ref, "variants": {}}
            for name, spec in specs.items():
                if name == "ref":
                    continue
                got = run_variant(spec, sample, budget)
                keys = [tuple(c.get(k) for k in ("nodes", "bestmove", "score", "depth"))
                        if "error" not in c else ("ERROR", c["error"])
                        for c in got]
                diff = [i for i in range(len(sample)) if keys[i] != ref_keys[i]]
                entry["variants"][name] = {
                    "cells": got,
                    "differing": sorted(diff),
                    "n_differing": len(diff),
                    "n": len(sample),
                }
            report[budget] = entry

    out = "/agent/repos/dwqww/forge-combo29/swarm/69/job1/env_matrix.json"
    with open(out, "w") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)

    print("=== fixed-budget environment matrix (base build, Threads 1, Hash 16) ===")
    for budget in BUDGETS:
        entry = report[budget]
        print("\nbudget: %s" % budget)
        print("%-16s %s" % ("variant", "differing / n"))
        for name in sorted(entry["variants"]):
            v = entry["variants"][name]
            print("%-16s %d / %d %s" % (name, v["n_differing"], v["n"],
                                        v["differing"][:5] if v["differing"] else ""))
    print("\nraw:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
