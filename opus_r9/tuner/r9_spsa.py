"""R9: SPSA tuner for Forge's R9Tune search parameters, driving fastchess on this PC (own code; the ideas and where
they come from are in opus_r9/IDEA_SOURCE.md).

usage:
  python -I -B run_pinned.py --mask 0x000F -- r9_spsa.py run <config.json> <run_dir> [--resume] [--max-pairs N]
                                                            [--max-hours H] [--until HH:MM]
  python -I -B r9_spsa.py status <run_dir>

Algorithm (simultaneous perturbation stochastic approximation, counted in game pairs as in Fishtest):
  per parameter i: c_i = c_end_i * N^gamma, a_i = r_end_i * c_end_i^2 * (A + N)^alpha, A = A_ratio * N, N = planned pairs
  batch b at pair count k: c_ki = c_i / (k + 1)^gamma, a_ki = a_i / (k + 1 + A)^alpha, delta_i = +-1 (seeded by k)
  plus = theta + c_k * delta, minus = theta - c_k * delta (clamped, rounded to the engine's integers)
  `pairs` game pairs (same opening, colours swapped) plus vs minus -> R = wins - losses of plus
  theta_i += a_ki / c_ki * R * delta_i (clamped), then k += pairs
State and evidence (append-only, nothing is ever overwritten): <run_dir>/config.json (copy of the config; a resume
must use the same one), iterations.jsonl (one record per finished batch: delta, c_k, a_k/c_k, the two value sets,
W/L/D, terminations, theta before/after, load, seconds), history.csv (theta after every batch), tuner.log, and
games/b<batch>_a<attempt>.pgn (+ fastchess .config.json, .out). --resume continues after the last complete record.
Load governor (PC rules): before every batch the system CPU load is sampled while no game of this tuner runs; the
batch runs with concurrency floor((cap_percent - load) * cpus / 100) clamped to [0, max_concurrency], and waits
(re-checking every wait_seconds) while that is 0 or free RAM is below min_free_gb. The STOP file <run_dir>/STOP ends
the run after the current batch."""
import csv
import json
import math
import os
import random
import re
import subprocess
import sys
import time
from pathlib import Path

import psutil

RESULT_RE = re.compile(r'^\[(White|Black|Result|Termination) "([^"]*)"\]', re.M)


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


class Run:
    def __init__(self, cfg, run_dir):
        self.cfg, self.dir = cfg, Path(run_dir)
        self.params = cfg["params"]
        self.names = [p["name"] for p in self.params]
        n = cfg["pairs_planned"]
        self.N, self.A = n, cfg.get("A_ratio", 0.1) * n
        self.alpha, self.gamma = cfg.get("alpha", 0.602), cfg.get("gamma", 0.101)
        self.c0 = [p["c_end"] * n ** self.gamma for p in self.params]
        self.a0 = [p.get("r_end", cfg.get("r_end", 0.002)) * p["c_end"] ** 2 * (self.A + n) ** self.alpha for p in self.params]
        self.log_f = open(self.dir / "tuner.log", "a", encoding="ascii", newline="\n")

    def log(self, msg):
        line = f"[{now()}] {msg}"
        print(line, flush=True)
        self.log_f.write(line + "\n")
        self.log_f.flush()

    def ck(self, k):
        return [c / (k + 1) ** self.gamma for c in self.c0]

    def ak(self, k):
        return [a / (k + 1 + self.A) ** self.alpha for a in self.a0]

    def delta(self, k):
        rng = random.Random(f"{self.cfg.get('seed', 1)}:{k}")  # str seeds are hashed deterministically
        return [rng.choice((-1, 1)) for _ in self.params]

    def clamp(self, i, v):
        p = self.params[i]
        return min(max(v, p["min"]), p["max"])

    def values(self, theta, ck, delta, sign):
        return {self.names[i]: int(round(self.clamp(i, theta[i] + sign * ck[i] * delta[i]))) for i in range(len(theta))}


def load_state(run):
    """Last complete record of iterations.jsonl -> (theta, k, batch, attempt counter base)."""
    path = run.dir / "iterations.jsonl"
    theta = [float(p["start"]) for p in run.params]
    k = batch = 0
    if path.exists():
        raw = path.read_bytes()
        if raw and not raw.endswith(b"\n"):  # torn last line of a killed run: start the next record on a new line
            with open(path, "ab") as f:
                f.write(b"\n")
            run.log("iterations.jsonl ended in a torn line (kept, skipped)")
        for line in raw.split(b"\n"):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            theta = [rec["theta_after"][n] for n in run.names]
            k, batch = rec["k_after"], rec["batch"] + 1
    return theta, k, batch


def cpu_load(seconds):
    return psutil.cpu_percent(interval=seconds)


def governor(run):
    """Concurrency allowed now (> 0), after waiting while the PC is too busy; None if the STOP file appeared."""
    g = run.cfg["governor"]
    ncpu = psutil.cpu_count(logical=True)
    waited = 0
    while True:
        if (run.dir / "STOP").exists():
            return None, None, None
        load = cpu_load(g.get("sample_seconds", 3))
        free_gb = psutil.virtual_memory().available / 2 ** 30
        slots = int(math.floor((g["cap_percent"] - load) * ncpu / 100.0 / g.get("cpus_per_game", 1.0)))
        slots = max(0, min(slots, g["max_concurrency"]))
        if slots > 0 and free_gb >= g["min_free_gb"]:
            if waited:
                run.log(f"governor: resuming after {waited} s of waiting (load {load:.0f}%, free RAM {free_gb:.1f} GB)")
            return slots, load, free_gb
        if waited % 600 == 0:
            run.log(f"governor: waiting (system load {load:.0f}% without this tuner, cap {g['cap_percent']}%, "
                    f"free RAM {free_gb:.1f} GB, min {g['min_free_gb']} GB)")
        time.sleep(g.get("wait_seconds", 60))
        waited += g.get("wait_seconds", 60)


def fastchess(run, plus, minus, pairs, conc, start, base):
    c = run.cfg
    def engine(name, vals):
        return ["-engine", f"name={name}", f"cmd={c['engine']}", "option.R9Tune=true"] + \
               [f"option.{k}={v}" for k, v in vals.items()]
    cmd = [c["fastchess"]] + engine("plus", plus) + engine("minus", minus) + [
        "-each", f"tc={c['tc']}", "timemargin=1000", "proto=uci", "option.Threads=1", f"option.Hash={c.get('hash', 16)}",
        "option.OwnBook=false",
        "-openings", f"file={c['book']}", f"format={c.get('book_format', 'pgn')}", "order=sequential", f"start={start}",
        "-games", "2", "-repeat", "-rounds", str(pairs), "-concurrency", str(conc), "-recover",
        "-pgnout", f"file={base}.pgn", "-config", f"outname={base}.config.json"]
    t0 = time.time()
    with open(f"{base}.out", "x", encoding="utf-8", newline="\n") as out:
        rc = subprocess.call(cmd, stdout=out, stderr=subprocess.STDOUT, cwd=str(run.dir / "games"))
    secs = time.time() - t0
    w = l = d = 0
    terms = {}
    text = Path(f"{base}.pgn").read_text(encoding="utf-8", errors="replace") if Path(f"{base}.pgn").exists() else ""
    games = text.split("[Event ")[1:]
    for g in games:
        tags = dict(RESULT_RE.findall(g))
        res, white = tags.get("Result"), tags.get("White")
        if res not in ("1-0", "0-1", "1/2-1/2"):
            continue
        terms[tags.get("Termination", "?")] = terms.get(tags.get("Termination", "?"), 0) + 1
        if res == "1/2-1/2":
            d += 1
        elif (res == "1-0") == (white == "plus"):
            w += 1
        else:
            l += 1
    return rc, w, l, d, terms, secs


def cmd_run(cfg_path, run_dir, resume, max_pairs, max_hours, until):
    cfg = json.loads(Path(cfg_path).read_text(encoding="utf-8"))
    d = Path(run_dir)
    if d.exists() and not resume:
        raise SystemExit(f"{d} exists: pass --resume to continue it")
    (d / "games").mkdir(parents=True, exist_ok=True)
    saved = d / "config.json"
    if saved.exists():
        if json.loads(saved.read_text(encoding="utf-8")) != cfg:
            raise SystemExit(f"{cfg_path} differs from the run's {saved}: a resumed run must keep its config")
    else:
        with open(saved, "x", encoding="utf-8", newline="\n") as f:
            json.dump(cfg, f, indent=1)
    run = Run(cfg, d)
    theta, k, batch = load_state(run)
    pairs = cfg["pairs_per_batch"]
    hist = d / "history.csv"
    new_hist = not hist.exists()
    hist_f = open(hist, "a", encoding="ascii", newline="")
    hw = csv.writer(hist_f)
    if new_hist:
        hw.writerow(["batch", "pairs_total", "games_total", "W", "L", "D", "R", "concurrency", "load_percent"] + run.names)
        hw.writerow([-1, 0, 0, 0, 0, 0, 0, 0, 0] + [f"{t:.3f}" for t in theta])
    t_start = time.time()
    deadline = None
    if until:
        hh, mm = (int(x) for x in until.split(":"))
        lt = time.localtime()
        deadline = time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, hh, mm, 0, 0, 0, -1))
        if deadline < time.time():
            deadline += 86400
    run.log(f"start: {len(theta)} parameters, pair count {k}, batch {batch}, planned pairs {run.N}, {pairs} pairs per "
            f"batch, tc {cfg['tc']}, engine {cfg['engine']}")
    n_openings = cfg.get("book_openings", 34700)
    done_pairs = 0
    while True:
        if max_pairs and done_pairs >= max_pairs:
            run.log(f"stop: --max-pairs {max_pairs} reached")
            break
        if max_hours and time.time() - t_start >= max_hours * 3600:
            run.log(f"stop: --max-hours {max_hours} reached")
            break
        if deadline and time.time() >= deadline:
            run.log(f"stop: --until {until} reached")
            break
        conc, load, free_gb = governor(run)
        if conc is None:
            run.log("stop: STOP file")
            break
        ck, ak, delta = run.ck(k), run.ak(k), run.delta(k)
        plus, minus = run.values(theta, ck, delta, +1), run.values(theta, ck, delta, -1)
        start = k % n_openings + 1
        attempt = fails = 0
        while True:
            attempt += 1
            base = str(d / "games" / f"b{batch:06d}_a{attempt}")
            if Path(base + ".out").exists():
                continue  # an attempt of a killed run: keep its files, use the next number
            rc, w, l, dr, terms, secs = fastchess(run, plus, minus, pairs, min(conc, 2 * pairs), start, base)
            if rc == 0 and w + l + dr == 2 * pairs:
                break
            fails += 1
            run.log(f"batch {batch} attempt {attempt}: fastchess exit {rc}, {w + l + dr} of {2 * pairs} games"
                    + (": retry" if fails < 3 else ""))
            if fails >= 3:
                run.log(f"ERROR: batch {batch} failed three times; stopping")
                sys.exit(3)
        r = w - l
        before = dict(zip(run.names, theta))
        g = [ak[i] / ck[i] for i in range(len(theta))]
        theta = [run.clamp(i, theta[i] + g[i] * r * delta[i]) for i in range(len(theta))]
        rec = {"batch": batch, "time": now(), "k_before": k, "k_after": k + pairs, "pairs": pairs, "opening_start": start,
               "concurrency": min(conc, 2 * pairs), "load_percent": load, "free_gb": round(free_gb, 1), "seconds": round(secs, 1),
               "delta": delta, "c_k": [round(x, 4) for x in ck], "a_over_c": [round(x, 6) for x in g], "plus": plus,
               "minus": minus, "W": w, "L": l, "D": dr, "R": r, "terminations": terms, "theta_before": before,
               "theta_after": dict(zip(run.names, theta))}
        with open(d / "iterations.jsonl", "a", encoding="ascii", newline="\n") as f:
            f.write(json.dumps(rec) + "\n")
            f.flush()
            os.fsync(f.fileno())
        k += pairs
        done_pairs += pairs
        hw.writerow([batch, k, 2 * k, w, l, dr, r, rec["concurrency"], load] + [f"{t:.3f}" for t in theta])
        hist_f.flush()
        bad = {t: n for t, n in terms.items() if t != "normal"}
        run.log(f"batch {batch}: pairs {k}, +{w} -{l} ={dr} (R {r:+d}) conc {rec['concurrency']} load {load:.0f}% "
                f"{secs:.0f} s{' terminations ' + str(bad) if bad else ''}; "
                + ", ".join(f"{n} {t:.1f}" for n, t in list(zip(run.names, theta))[:6]) + (" ..." if len(theta) > 6 else ""))
        batch += 1
    hist_f.close()
    run.log(f"end: pair count {k}, {done_pairs} pairs in this session")


def cmd_status(run_dir):
    d = Path(run_dir)
    recs = [json.loads(x) for x in (d / "iterations.jsonl").read_text(encoding="ascii").splitlines() if x.strip()]
    if not recs:
        print("no batches yet")
        return
    w = sum(r["W"] for r in recs)
    l = sum(r["L"] for r in recs)
    dr = sum(r["D"] for r in recs)
    print(f"{len(recs)} batches, {recs[-1]['k_after']} pairs, +{w} -{l} ={dr}, last {recs[-1]['time']}")
    for n, v in recs[-1]["theta_after"].items():
        print(f"  {n:26s} {recs[0]['theta_before'][n]:10.2f} -> {v:10.2f}")


if __name__ == "__main__":
    a = sys.argv
    if len(a) >= 3 and a[1] == "status":
        cmd_status(a[2])
    elif len(a) >= 4 and a[1] == "run":
        def opt(name, conv):
            return conv(a[a.index(name) + 1]) if name in a else None
        cmd_run(a[2], a[3], "--resume" in a, opt("--max-pairs", int), opt("--max-hours", float), opt("--until", str))
    else:
        raise SystemExit(__doc__)
