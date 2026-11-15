#!/usr/bin/env python3
"""Job 2 part A, second attempt: a rule with measured power.

WHY THIS REPLACES THE FIRST RULE
The first rule (absolute |search_score - eval_total|) had NO power: it called all
96 surviving combinations inconsistent, including the two that must be
consistent. Cause: the three evaluators are on different scales. `eval nnue_v3`
prints the reference network output, and a random test net has a huge scale, so
its values are in the thousands while the search's score at depth 1 is not.

THE RULE USED, fixed before the run that matters
A combination is CONSISTENT when, over the 30 positions, the depth-1 search
score has the same RANK ORDER as the total `eval` prints, measured as
Spearman's rho with at least rho >= 0.40, and with a positive sign agreement on
at least 20 of 30 positions.

Rank order is used because it is invariant under the evaluator's scale: an
evaluator with a different scale or a different tempo term still ranks the
positions the same way if it is the evaluator the search is actually using.
Both thresholds were fixed before this run; the report states the measured
margin between the controls and the failures.

Controls the rule must satisfy:
  * all defaults (UseNNUE true, NNUEArch false) -> consistent
  * NNUEArch true with the file set, nothing else -> consistent
  * UseNNUE false with NNUEArch true (the reviewer's case) -> INCONSISTENT
"""

import itertools
import json
import math
import subprocess
import sys
import threading
import queue

ENGINE = sys.argv[1]
POSFILE = sys.argv[2]
NET = sys.argv[3]
OUT = sys.argv[4]

MAX_POS = 30
RHO_MIN = 0.40
SIGN_MIN = 20


def spearman(a, b):
    n = len(a)

    def ranks(v):
        order = sorted(range(n), key=lambda i: v[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    ra, rb = ranks(a), ranks(b)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((ra[i] - ma) * (rb[i] - mb) for i in range(n))
    da = math.sqrt(sum((x - ma) ** 2 for x in ra))
    db = math.sqrt(sum((x - mb) ** 2 for x in rb))
    if da == 0 or db == 0:
        return 0.0
    return cov / (da * db)


def eval_number(line):
    if not line:
        return None
    t = line.split()
    if "nnue_v3" in t:
        return int(t[t.index("nnue_v3") + 1])
    if "total" in t:
        return int(t[t.index("total") + 1])
    return None


def run_combo(options, positions):
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

    def wait_for(pred, timeout):
        import time
        t0 = time.time()
        got = []
        while time.time() - t0 < timeout:
            try:
                ln = q.get(timeout=max(0.01, timeout - (time.time() - t0)))
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
            return {"alive": False, "exit": "closed", "rows": [], "banner": []}
    send("isready")
    got, why = wait_for(lambda l: l.strip() == "readyok" or "ERROR NNUE v3" in l, 15)
    if why != "ok" or not any(l.strip() == "readyok" for l in got):
        try:
            rc = p.wait(timeout=5)
        except Exception:
            p.kill()
            rc = "killed"
        return {"alive": False, "exit": rc, "rows": [], "banner": got[-2:]}

    rows = []
    for fen in positions:
        send(f"position fen {fen}")
        send("eval")
        got, why = wait_for(lambda l: l.startswith("info string eval"), 10)
        eline = [l for l in got if l.startswith("info string eval")]
        send("go depth 1")
        got2, why2 = wait_for(lambda l: l.startswith("bestmove"), 30)
        if why2 == "eof":
            return {"alive": False, "exit": "died mid-run", "rows": rows, "banner": []}
        infos = [l for l in got2 if l.startswith("info") and " score " in l]
        score = None
        if infos:
            t = infos[-1].split()
            i = t.index("score")
            score = (t[i + 1], t[i + 2])
        rows.append({"fen": fen, "eval": eline[-1] if eline else None, "score": score})
    send("quit")
    try:
        rc = p.wait(timeout=10)
    except Exception:
        p.kill()
        rc = "killed"
    return {"alive": True, "exit": rc, "rows": rows, "banner": []}


def judge(rows):
    pairs = []
    for r in rows:
        e = eval_number(r["eval"])
        if e is None or r["score"] is None:
            continue
        if r["score"][0] == "mate":
            continue
        pairs.append((e, int(r["score"][1])))
    if len(pairs) < 10:
        return {"n": len(pairs), "rho": None, "sign": None, "verdict": "too few comparable"}
    a = [p[0] for p in pairs]
    b = [p[1] for p in pairs]
    rho = spearman(a, b)
    sign = sum(1 for x, y in pairs if (x > 0) == (y > 0) or x == 0 or y == 0)
    ok = rho >= RHO_MIN and sign >= SIGN_MIN
    return {"n": len(pairs), "rho": round(rho, 3), "sign": sign,
            "verdict": "consistent" if ok else "INCONSISTENT"}


def main():
    data = json.load(open(POSFILE))
    positions = [p["fen"] for p in data["positions"]][:MAX_POS]
    combos = []
    for use, arch, archfile, dead, book, mpv, thr in itertools.product(
            ["true", "false"], ["true", "false"], ["set", "unset"],
            ["true", "false"], ["true", "false"], ["1", "3"], ["1", "2"]):
        if arch == "false" and archfile == "set":
            continue                      # the file without the arch flag is a separate case
        opts = [("UseNNUE", use), ("NNUEArch", arch)]
        if archfile == "set":
            opts.append(("NNUEArchFile", NET))
        opts += [("DeadMaterial", dead), ("OwnBook", book), ("MultiPV", mpv), ("Threads", thr)]
        combos.append({"opts": opts,
                       "key": f"UseNNUE={use} NNUEArch={arch} file={archfile} "
                              f"DeadMaterial={dead} OwnBook={book} MultiPV={mpv} Threads={thr}"})
    results = []
    for i, c in enumerate(combos):
        r = run_combo(c["opts"], positions)
        v = judge(r["rows"]) if r["rows"] else {"verdict": "died before any search"}
        results.append({"i": i, "key": c["key"], "opts": c["opts"], "alive": r["alive"],
                        "exit": r["exit"], "banner": r["banner"], "rows": r["rows"], **v})
        if (i + 1) % 12 == 0:
            print(f"{i+1}/{len(combos)}", flush=True)
    json.dump({"positions": positions, "rule": {"rho_min": RHO_MIN, "sign_min": SIGN_MIN},
               "results": results}, open(OUT, "w"), indent=1)
    incons = [r for r in results if r.get("verdict") == "INCONSISTENT"]
    died = [r for r in results if not r["alive"]]
    print(f"combos={len(results)} inconsistent={len(incons)} died={len(died)}")


if __name__ == "__main__":
    main()
