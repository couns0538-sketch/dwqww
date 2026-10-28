#!/usr/bin/env python3
"""R3-6: summarise the FORGE_SMP_TRACE lines recorded by smp_ttd.py (trace build runs).

Per run (Threads >= 2):
  main_s        when the main thread returned (s since Searcher::search was entered)
  join_us       stop/join latency: helpers joined minus main returned
  helper_idle   sum over helpers of max(0, main return - helper return) / ((n-1) * main return):
                the share of helper wall time spent finished-and-waiting (helpers that completed the
                `go depth` limit before the main thread)
  finished      helpers that returned by themselves (completed the depth limit) / helpers
  ahead         share of helper iteration completions (depth >= 8) that came before the main thread
                completed the same depth (the helper led the main thread at that moment)
  lead          mean (helper depth - main thread's completed depth) at the helper's completions
  main_share    main thread nodes / all nodes; tt_hit, tt_cut: hits and cutoffs per probe
  main_cpu_s    main search thread CPU time (critical path); cpu_par = all threads' CPU / main return
  info_vs_exact nodes of the last info line / exact sum of the workers' nodes after the join
  *_vs_t1       geometric means over positions, relative to the position's `off` Threads=1 run (a
                deterministic search): main-thread nodes and CPU time to complete depth D (the helpers'
                benefit to the critical path; load-robust) and all workers' nodes (node inflation)
usage: trace_summary.py runs.jsonl [...] [--tsv out.tsv]
"""
import argparse
import json
import math
import statistics
from collections import defaultdict


def gmean(xs):
    xs = [x for x in xs if x > 0]
    return math.exp(sum(math.log(x) for x in xs) / len(xs)) if xs else float("nan")


def parse(trace):
    search, workers = None, {}
    for line in trace:
        f = line.split()
        if f[0] == "search":
            search = {f[i]: int(f[i + 1]) for i in range(1, len(f) - 1, 2)}
        elif f[0] == "worker":
            w = {}
            i = 2
            while i < len(f):
                if f[i] == "iters":
                    its = []
                    if i + 1 < len(f):
                        for item in f[i + 1].split(","):
                            d, us, n, res = item.split(":")
                            its.append((int(d), int(us), int(n), int(res)))
                    w["iters"] = its
                    break
                w[f[i]] = int(f[i + 1])
                i += 2
            w.setdefault("iters", [])
            workers[int(f[1])] = w
    return search, workers


def run_metrics(r):
    search, workers = parse(r["trace"])
    if not search or 0 not in workers:
        return None
    n = len(workers)
    main = workers[0]
    main_done = search["main_done_us"]
    out = {"pos": r["pos"], "config": r["config"], "threads": r["threads"], "depth": r["depth"],
           "main_s": main_done / 1e6, "join_us": search["join_latency_us"],
           "main_cpu_s": main.get("cpu_us", -1) / 1e6, "wall_s": r["wall_s"]}
    total_nodes = sum(w["nodes"] for w in workers.values())
    out["main_share"] = main["nodes"] / total_nodes if total_nodes else float("nan")
    out["main_nodes"] = main["nodes"]
    out["nodes_total"] = total_nodes
    out["nodes_info"] = r["nodes"]
    # The last info line is printed when the main thread completes the depth, before the helpers stop.
    out["info_vs_exact"] = r["nodes"] / total_nodes if total_nodes else float("nan")
    probes = sum(w["tt_probes"] for w in workers.values())
    out["tt_hit"] = sum(w["tt_hits"] for w in workers.values()) / probes if probes else float("nan")
    out["tt_cut"] = sum(w["tt_cutoffs"] for w in workers.values()) / probes if probes else float("nan")
    out["main_tt_hit"] = main["tt_hits"] / main["tt_probes"] if main["tt_probes"] else float("nan")
    out["cpu_par"] = sum(max(0, w.get("cpu_us", 0)) for w in workers.values()) / main_done if main_done else 0
    main_done_at = {d: us for d, us, _, _ in main["iters"]}
    if n > 1:
        idle = 0
        finished = 0
        ahead, total, leads = 0, 0, []
        for i, w in workers.items():
            if i == 0:
                continue
            idle += max(0, main_done - w["exit_us"])
            if w["aborted_depth"] == 0:
                finished += 1
            for d, us, _, _ in w["iters"]:
                if d < 8:
                    continue
                total += 1
                if us < main_done_at.get(d, 1 << 62):
                    ahead += 1
                md = max([dd for dd, t in main_done_at.items() if t <= us], default=0)
                leads.append(d - md)
        out["helper_idle"] = idle / ((n - 1) * main_done) if main_done else 0
        out["finished"] = finished / (n - 1)
        out["ahead"] = ahead / total if total else float("nan")
        out["lead"] = statistics.mean(leads) if leads else float("nan")
        ratios = [w.get("cpu_us", 0) / main["cpu_us"] for i, w in workers.items() if i and main.get("cpu_us", 0) > 0]
        if ratios:
            out["helper_cpu_vs_main"] = statistics.mean(ratios)
    out["researches_main"] = sum(res for *_, res in main["iters"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--tsv")
    a = ap.parse_args()
    rows = []
    for p in a.runs:
        for line in open(p, encoding="utf-8"):
            r = json.loads(line)
            m = run_metrics(r)
            if m:
                rows.append(m)
    # Threads=1 reference per position (deterministic search): main-thread nodes and CPU of the
    # off run; ratios < 1 mean the helpers saved the main thread work on its way to depth D.
    t1 = {m["pos"]: m for m in rows if m["threads"] == 1 and m["config"] == "off"}
    for m in rows:
        ref = t1.get(m["pos"])
        if ref:
            m["main_nodes_vs_t1"] = m["main_nodes"] / ref["main_nodes"]
            if ref["main_cpu_s"] > 0 and m["main_cpu_s"] > 0:
                m["main_cpu_vs_t1"] = m["main_cpu_s"] / ref["main_cpu_s"]
            m["total_nodes_vs_t1"] = m["nodes_total"] / ref["main_nodes"]
    groups = defaultdict(list)
    for m in rows:
        groups[(m["config"], m["threads"])].append(m)
    keys = ["main_s", "join_us", "helper_idle", "finished", "ahead", "lead", "main_share", "tt_hit", "tt_cut",
            "main_cpu_s", "cpu_par", "helper_cpu_vs_main", "info_vs_exact", "main_nodes_vs_t1", "main_cpu_vs_t1",
            "total_nodes_vs_t1"]
    print("| config | T | runs | " + " | ".join(keys) + " |")
    print("|" + "---|" * (len(keys) + 3))
    for (cfg, t), ms in sorted(groups.items()):
        vals = []
        for k in keys:
            xs = [m[k] for m in ms if k in m and m[k] == m[k]]
            if not xs:
                vals.append("-")
            elif k == "join_us":
                vals.append(f"med {statistics.median(xs):.0f} max {max(xs):.0f}")
            elif k in ("helper_idle", "finished", "ahead", "main_share", "tt_hit", "tt_cut", "info_vs_exact"):
                vals.append(f"{statistics.mean(xs) * 100:.1f}%")
            elif k.endswith("_vs_t1"):
                vals.append(f"{gmean(xs):.3f}")
            else:
                vals.append(f"{statistics.mean(xs):.3f}")
        print(f"| {cfg} | {t} | {len(ms)} | " + " | ".join(vals) + " |")
    if a.tsv:
        cols = ["pos", "config", "threads", "depth", "wall_s", "main_s", "main_cpu_s", "join_us", "helper_idle",
                "finished", "ahead", "lead", "main_share", "main_nodes", "nodes_total", "nodes_info", "info_vs_exact",
                "main_nodes_vs_t1", "main_cpu_vs_t1", "total_nodes_vs_t1", "tt_hit", "tt_cut", "main_tt_hit",
                "cpu_par", "helper_cpu_vs_main", "researches_main"]
        with open(a.tsv, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\t".join(cols) + "\n")
            for m in rows:
                fh.write("\t".join(f"{m[c]:.4f}" if isinstance(m.get(c), float) else str(m.get(c, "")) for c in cols)
                         + "\n")
        print(f"per-run TSV: {a.tsv}")


if __name__ == "__main__":
    main()
