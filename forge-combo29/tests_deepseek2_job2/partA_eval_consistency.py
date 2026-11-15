#!/usr/bin/env python3
"""Job 2 part A: does `eval` agree with what the search uses?

THE RULE, DEFINED BEFORE THE RUN (as the job asks)
--------------------------------------------------
`eval` prints one of
    info string eval nnue_v3 <V>            (v3 network active)
    info string eval hce <H> nnue <N> total <T>   (the HCE/NNUE combination)
so the evaluator `eval` NAMES is, in the first form, "nnue_v3"; in the second
form it names both parts, H and N, and T is the total the searcher would use
when the small net is in use (T = N when the net is not residual, T = H + blend
otherwise, and T = fresh_evaluate when UseNNUE is false -- all visible from the
printed components).

A combination is CONSISTENT when, over the 30 positions, the depth-1 search
score follows the total that `eval` printed, by this rule:

  (a) sign agreement on at least 27 of 30 positions, and
  (b) the mean absolute difference |search_score - eval_total| over the
      positions where both are non-zero is at most 250 cp, and
  (c) no single position differs by more than 900 cp.

Why these numbers: the depth-1 score is the eval of the best child plus the
search's own corrections (correction history, rule-50 damping, tempo, draw
terms), so an exact match is not expected; 250 cp mean / 900 cp single is
generous enough to admit those corrections and tight enough that two different
evaluators (which differ by hundreds of cp on these positions, see the report's
spread table) cannot both pass. The numbers were fixed before the first run and
were not changed afterwards.

A `mate` score at depth 1 is treated as "sign matches, difference ignored"
(its cp value is not comparable), which can only make a combination look more
consistent, never less.

Special case: `eval` prints only `info string eval hce ... nnue ...` when v3 is
not active, and the total it prints is the total the SEARCH uses for the small
net. When NNUEArch is true but the net is missing, `eval` prints the hce form
while the search will refuse to run at all (exit 2 at isready) -- that is
recorded as "died", not as consistent.
"""

import itertools
import json
import subprocess
import sys

ENGINE = sys.argv[1]
POSFILE = sys.argv[2]
NET = sys.argv[3]
OUT = sys.argv[4]
NETMISSING = sys.argv[5] if len(sys.argv) > 5 else "/tmp/ds2/does_not_exist.fnn3"

MAX_POS = 30
SIGN_MIN = 27
MEAN_MAX = 250.0
SINGLE_MAX = 900


def run_combo(options, positions, timeout=90):
    """One engine process for the whole combination; returns rows + survival."""
    lines_in = ["uci"]
    for name, value in options:
        lines_in.append(f"setoption name {name} value {value}")
    lines_in.append("isready")
    rows = []
    script = "\n".join(lines_in) + "\n"
    proc = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    try:
        proc.stdin.write(script)
        proc.stdin.flush()
        out = []
        # wait for readyok or death
        while True:
            line = proc.stdout.readline()
            if line == "":
                break
            out.append(line.rstrip())
            if line.strip() == "readyok":
                break
            if "ERROR NNUE v3" in line:
                break
        if not any(l.strip() == "readyok" for l in out):
            rc = proc.wait(timeout=10)
            return {"alive": False, "exit": rc, "banner": out, "rows": []}
        for fen in positions:
            payload = f"position fen {fen}\neval\ngo depth 1\n"
            proc.stdin.write(payload)
            proc.stdin.flush()
            eval_line = None
            score = None
            best = None
            while True:
                line = proc.stdout.readline()
                if line == "":
                    return {"alive": False, "exit": "died mid-run", "banner": out, "rows": rows}
                s = line.strip()
                if s.startswith("info string eval"):
                    eval_line = s
                elif s.startswith("info") and " score " in s:
                    score = s.split(" score ")[1].split()[0:2]
                elif s.startswith("bestmove"):
                    best = s.split()[1]
                    break
            rows.append({"fen": fen, "eval": eval_line, "score": score, "best": best})
        proc.stdin.write("quit\n")
        proc.stdin.flush()
        rc = proc.wait(timeout=10)
        return {"alive": True, "exit": rc, "banner": out, "rows": rows}
    except Exception as exc:
        try:
            proc.kill()
        except Exception:
            pass
        return {"alive": False, "exit": "exception: " + str(exc), "banner": [], "rows": rows}


def parse_eval(line):
    """-> (name, value_or_None, hce, nnue, total)"""
    if not line:
        return None, None, None, None, None
    t = line.split()
    # info string eval nnue_v3 <V>
    if "nnue_v3" in t:
        i = t.index("nnue_v3")
        return "nnue_v3", int(t[i + 1]), None, None, int(t[i + 1])
    # info string eval hce <H> nnue <N> total <T> [incheck 1]
    if "hce" in t:
        h = int(t[t.index("hce") + 1])
        n = int(t[t.index("nnue") + 1]) if "nnue" in t else None
        tot = int(t[t.index("total") + 1]) if "total" in t else None
        return "hce", h, h, n, tot
    return None, None, None, None, None


def judge(rows):
    """Apply the rule.  Returns dict with the numbers and the verdict."""
    pairs = []
    for r in rows:
        name, val, h, n, tot = parse_eval(r["eval"])
        if r["score"] is None:
            continue
        kind, text = r["score"][0], r["score"][1]
        reference = tot
        if name == "nnue_v3":
            reference = val
        if reference is None:
            continue
        if kind == "mate":
            pairs.append((reference, None, 1 if int(text) > 0 else -1))
        else:
            pairs.append((reference, int(text), None))
    n = len(pairs)
    if n == 0:
        return {"n": 0, "sign_ok": 0, "mean_abs": None, "max_abs": None, "verdict": "no data"}
    sign_ok = 0
    diffs = []
    for ref, cp, matesign in pairs:
        if ref == 0:
            continue
        sign_ref = 1 if ref > 0 else -1
        if matesign is not None:
            if matesign == sign_ref:
                sign_ok += 1
            continue
        sign_score = 1 if cp > 0 else (-1 if cp < 0 else 0)
        if sign_score == sign_ref:
            sign_ok += 1
        diffs.append(abs(cp - ref))
    mean_abs = sum(diffs) / len(diffs) if diffs else None
    max_abs = max(diffs) if diffs else None
    ok = (sign_ok >= SIGN_MIN and (mean_abs is None or mean_abs <= MEAN_MAX)
          and (max_abs is None or max_abs <= SINGLE_MAX))
    return {"n": n, "sign_ok": sign_ok, "mean_abs": None if mean_abs is None else round(mean_abs, 1),
            "max_abs": max_abs, "verdict": "consistent" if ok else "INCONSISTENT"}


def main():
    data = json.load(open(POSFILE))
    positions = [p["fen"] for p in data["positions"]][:MAX_POS]
    combos = []
    for use, arch, archfile, dead, book, mpv, thr in itertools.product(
            ["true", "false"], ["true", "false"], ["set", "unset"],
            ["true", "false"], ["true", "false"], [1, 3], [1, 2]):
        opts = [("UseNNUE", use), ("NNUEArch", arch), ("DeadMaterial", dead),
                ("OwnBook", book), ("MultiPV", str(mpv)), ("Threads", str(thr))]
        if arch == "true" and archfile == "set":
            opts.insert(2, ("NNUEArchFile", NET))
        combos.append({"opts": opts, "key": f"UseNNUE={use} NNUEArch={arch} file={archfile} "
                                            f"DeadMaterial={dead} OwnBook={book} MultiPV={mpv} Threads={thr}"})
    results = []
    for i, c in enumerate(combos):
        r = run_combo(c["opts"], positions)
        verdict = judge(r["rows"]) if r["rows"] else {"verdict": "died before any search"}
        rec = {"i": i, "key": c["key"], "opts": c["opts"], "alive": r["alive"],
               "exit": r["exit"], "banner": r["banner"][-3:], **verdict,
               "rows": r["rows"]}
        results.append(rec)
        if (i + 1) % 16 == 0:
            print(f"{i+1}/{len(combos)}", flush=True)
    json.dump({"positions": positions, "net": NET, "rule": {"sign_min": SIGN_MIN,
                                                           "mean_max": MEAN_MAX,
                                                           "single_max": SINGLE_MAX},
               "results": results}, open(OUT, "w"), indent=1)
    incons = [r for r in results if r["verdict"] == "INCONSISTENT"]
    died = [r for r in results if not r["alive"]]
    print(f"combinations={len(results)} inconsistent={len(incons)} died={len(died)}")


if __name__ == "__main__":
    main()
