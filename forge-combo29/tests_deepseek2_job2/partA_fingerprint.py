#!/usr/bin/env python3
"""Job 2 part A, final rule: IDENTIFY the evaluator by its fingerprint.

The two threshold rules failed for the same reason: comparison on a scale is
meaningless when one evaluator is a random test net with a huge scale, and rank
correlation is meaningless too (a random net's ranking is noise, so a correct
combination cannot be expected to correlate with it).

The rule used for the reported table is exact instead of statistical:

  1. Build a FINGERPRINT for each evaluator: the vector of the 30 depth-1
     scores produced when only that evaluator can be in use, separately for
     MultiPV 1 and MultiPV 3.
        HCE      : UseNNUE false (v3 off)
        SMALLNET : UseNNUE true, NNUEArch false
        V3       : UseNNUE true, NNUEArch true, net file set
  2. For each combination, take its 30 depth-1 scores and find which
     fingerprint it equals EXACTLY (all 30 positions, element by element).
  3. The combination is
        CONSISTENT      if the fingerprint it matches is the evaluator `eval`
                        names in that same run;
        INCONSISTENT    if it matches a different evaluator's fingerprint;
        UNIDENTIFIED    if it matches none (say so; do not call it consistent).

Why this has power: the three fingerprints are different on these positions
(shown in the report), and the match is exact, so a combination that names one
evaluator and runs another cannot slip through. The known-consistent controls
must land on their own fingerprint and the reviewer's case must land off its
named one.
"""

import itertools
import json
import queue
import subprocess
import sys
import threading
import time

ENGINE = sys.argv[1]
POSFILE = sys.argv[2]
NET = sys.argv[3]
OUT = sys.argv[4]
MAX_POS = 30


def run_combo(options, positions, timeout=30):
    p = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()

    def reader():
        for ln in p.stdout:
            q.put(ln.rstrip())
        q.put(None)

    threading.Thread(target=reader, daemon=True).start()

    def send(s):
        try:
            p.stdin.write(s + "\n")
            p.stdin.flush()
            return True
        except (BrokenPipeError, ValueError):
            return False

    def wait_for(pred, limit):
        t0 = time.time()
        got = []
        while time.time() - t0 < limit:
            try:
                ln = q.get(timeout=max(0.01, limit - (time.time() - t0)))
            except queue.Empty:
                break
            if ln is None:
                return got, "eof"
            got.append(ln)
            if pred(ln):
                return got, "ok"
        return got, "timeout"

    send("uci")
    wait_for(lambda l: l.strip() == "uciok", 10)
    for name, value in options:
        if not send(f"setoption name {name} value {value}"):
            p.kill()
            return {"alive": False, "exit": "closed", "rows": []}
    send("isready")
    got, why = wait_for(lambda l: l.strip() == "readyok" or "ERROR NNUE v3" in l, 15)
    if why != "ok" or not any(l.strip() == "readyok" for l in got):
        try:
            rc = p.wait(timeout=5)
        except Exception:
            p.kill()
            rc = "killed"
        return {"alive": False, "exit": rc, "rows": [], "banner": got[-1:]}

    rows = []
    for fen in positions:
        send(f"position fen {fen}")
        send("eval")
        got, _ = wait_for(lambda l: l.startswith("info string eval"), 10)
        elines = [l for l in got if l.startswith("info string eval")]
        send("go depth 1")
        got2, why2 = wait_for(lambda l: l.startswith("bestmove"), timeout)
        if why2 == "eof":
            return {"alive": False, "exit": "died mid-run", "rows": rows}
        infos = [l for l in got2 if l.startswith("info") and " score " in l]
        score = None
        if infos:
            t = infos[-1].split()
            i = t.index("score")
            score = t[i + 1] + " " + t[i + 2]
        rows.append({"fen": fen, "eval": elines[-1] if elines else None, "score": score})
    send("quit")
    try:
        rc = p.wait(timeout=10)
    except Exception:
        p.kill()
        rc = "killed"
    return {"alive": True, "exit": rc, "rows": rows}


def named_evaluator(eval_line):
    if not eval_line:
        return None
    return "V3" if "nnue_v3" in eval_line.split() else "SMALLNET_OR_HCE"


def main():
    positions = [p["fen"] for p in json.load(open(POSFILE))["positions"]][:MAX_POS]
    fingerprints = {}
    for mpv in ("1", "3"):
        canon = {
            "HCE": [("UseNNUE", "false"), ("MultiPV", mpv), ("Threads", "1")],
            "SMALLNET": [("UseNNUE", "true"), ("NNUEArch", "false"), ("MultiPV", mpv), ("Threads", "1")],
            "V3": [("UseNNUE", "true"), ("NNUEArch", "true"), ("NNUEArchFile", NET),
                   ("MultiPV", mpv), ("Threads", "1")],
        }
        for name, opts in canon.items():
            r = run_combo(opts, positions)
            vec = tuple(row["score"] for row in r["rows"])
            fingerprints[(mpv, name)] = {"vector": vec, "alive": r["alive"]}
            print(f"fingerprint {name} MultiPV {mpv}: alive={r['alive']} first={vec[:3]}", flush=True)

    combos = []
    for use, arch, archfile, dead, book, mpv, thr in itertools.product(
            ["true", "false"], ["true", "false"], ["set", "unset"],
            ["true", "false"], ["true", "false"], ["1", "3"], ["1", "2"]):
        if arch == "false" and archfile == "set":
            continue
        opts = [("UseNNUE", use), ("NNUEArch", arch)]
        if archfile == "set":
            opts.append(("NNUEArchFile", NET))
        opts += [("DeadMaterial", dead), ("OwnBook", book), ("MultiPV", mpv), ("Threads", thr)]
        combos.append({"opts": opts, "mpv": mpv,
                       "key": f"UseNNUE={use} NNUEArch={arch} file={archfile} "
                              f"DeadMaterial={dead} OwnBook={book} MultiPV={mpv} Threads={thr}"})

    results = []
    for i, c in enumerate(combos):
        r = run_combo(c["opts"], positions)
        rec = {"i": i, "key": c["key"], "alive": r["alive"], "exit": r["exit"],
               "banner": r.get("banner", []), "rows": r["rows"]}
        if not r["alive"] or not r["rows"]:
            rec.update({"matched": None, "named": None, "verdict": "died before any search"})
        else:
            vec = tuple(row["score"] for row in r["rows"])
            matched = [name for (mpv, name), fp in fingerprints.items()
                       if mpv == c["mpv"] and fp["vector"] == vec]
            named = ("V3" if all(named_evaluator(row["eval"]) == "V3" for row in r["rows"])
                     else "HCE_OR_SMALL")
            # which of HCE / SMALLNET the named HCE-form corresponds to: decided by
            # UseNNUE, which is what the search reads (search.cpp:1076)
            use_small = "UseNNUE=true" in c["key"]
            expected = "V3" if named == "V3" else ("SMALLNET" if use_small else "HCE")
            rec.update({"matched": matched, "named": named, "expected": expected,
                        "use_small_net": use_small})
            if not matched:
                rec["verdict"] = "UNIDENTIFIED"
            elif expected in matched:
                rec["verdict"] = "consistent"
            else:
                rec["verdict"] = "INCONSISTENT"
            rec["named_vs_matched"] = f"named {expected} / ran {','.join(matched)}"
        results.append(rec)
        if (i + 1) % 12 == 0:
            print(f"{i+1}/{len(combos)}", flush=True)

    json.dump({"fingerprints": {f"{k[0]}|{k[1]}": v["vector"] for k, v in fingerprints.items()},
               "results": results}, open(OUT, "w"), indent=1)
    for verdict in ("consistent", "INCONSISTENT", "UNIDENTIFIED", "died before any search"):
        n = sum(1 for r in results if r["verdict"] == verdict)
        print(f"{verdict}: {n}")


if __name__ == "__main__":
    main()
