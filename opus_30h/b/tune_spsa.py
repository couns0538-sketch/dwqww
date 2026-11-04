"""tune_spsa.py - Opus 30-h job: SPSA tuner for Forge search constants exposed as UCI options, driving fastchess
(own code; port of R9's opus_r9/tuner/r9_spsa.py; ideas in opus_30h/IDEA_SOURCE.md).

usage:
  python -I -B tune_spsa.py run <config.json> <run_dir> [--resume] [--until "YYYY-MM-DD HH:MM"] [--max-pairs N]
                                [--total-pairs N] [--threads N] [--cpus 0,1]
  python -I -B tune_spsa.py stop <run_dir>        (the running tuner finishes its batch, then exits)
  python -I -B tune_spsa.py status <run_dir>
  (tune_spsa.ps1 is the re-runnable wrapper: it resumes an existing run dir, so a crash or reboot loses at most the
  batch that was playing.)

Config (JSON): engine, fastchess, book, book_format, tc, hash, pairs_planned, pairs_per_batch, alpha, gamma, A_ratio,
seed, threads, cpus, params_csv (name,start,min,max,c,a: c = perturbation at the end of the run, a = learning rate R at
the end, both per parameter, as c_end / r_end of R9), fixed_options (always passed to both engines).
Algorithm (simultaneous perturbation stochastic approximation, counted in game pairs):
  c_i = c_end_i * N^gamma, a_i = r_end_i * c_end_i^2 * (A + N)^alpha, A = A_ratio * N, N = pairs_planned
  batch at pair count k: c_ki = c_i / (k + 1)^gamma, a_ki = a_i / (k + 1 + A)^alpha, delta_i = +-1 (seeded by k)
  plus = theta + c_k * delta, minus = theta - c_k * delta (clamped to [min, max], rounded to integers)
  pairs_per_batch game pairs (same opening, colours swapped) plus vs minus -> R = wins - losses of plus
  theta_i += a_ki / c_ki * R * delta_i (clamped), then k += pairs.
State (append-only, never overwritten): run_dir/config.json (+ the params CSV copied in; a resume must use the same),
iterations.jsonl (one fsynced record per finished batch), history.csv (theta after every batch = the per-iteration
CSV), tuner.log, games/b<batch>_a<attempt>.{pgn,out,config.json}. --resume continues after the last complete record;
a torn last line (killed run) is kept and skipped.
CPU rules: the tuner pins itself (and so fastchess and every engine) to --cpus at Idle priority before it starts
anything. Before every batch it (1) waits while any fastchess.exe that is not its own has an affinity that overlaps
--cpus (a running gate), (2) samples the busy share of --cpus for 3 s while none of its games run and uses one game
slot per CPU of --cpus that is at most max_busy_percent (config, default 80) busy, never more than --threads (one game = one CPU: the two engines
alternate), (3) waits while free RAM < 6 GB, (4) stops when free space on C: < 30 GB or D: < 51 GB (the job's floors,
D: with 1 GB margin; resumable). Stops: --until, --max-pairs, --total-pairs, the disk floors, or the stop command (a
named event the tuner creates and holds; no STOP files). It never stops a game and never kills anything.
"""
import csv
import ctypes
import datetime as dt
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import psutil

RESULT_RE = re.compile(r'^\[(White|Black|Result|Termination) "([^"]*)"\]', re.M)
IDLE = 0x40
DISK_FLOORS_GB = {"C:\\": 30.0, "D:\\": 51.0}   # the job's stop rule (D: 50 GB + 1 GB margin)


def disk_low():
    """Text naming every drive below its floor, '' when all are above (a missing drive is skipped)."""
    out = []
    for drive, floor in DISK_FLOORS_GB.items():
        try:
            free = shutil.disk_usage(drive).free / 2 ** 30
        except OSError:
            continue
        if free < floor:
            out.append(f"{drive} {free:.1f} GB free < {floor:.0f}")
    return ", ".join(out)


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def event_name(run_dir):
    return "Local\\O30_Spsa_Stop_" + "".join(ch if ch.isalnum() else "_" for ch in os.path.abspath(run_dir))[-180:]


def read_params(path):
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            p = {"name": row["name"].strip(), "start": float(row["start"]), "min": float(row["min"]),
                 "max": float(row["max"]), "c_end": float(row["c"]), "r_end": float(row["a"])}
            if not (p["min"] <= p["start"] <= p["max"]) or p["c_end"] <= 0 or p["r_end"] <= 0:
                raise SystemExit(f"bad parameter row {row}")
            out.append(p)
    if not out:
        raise SystemExit(f"no parameters in {path}")
    return out


class Run:
    def __init__(self, cfg, params, run_dir):
        self.cfg, self.dir, self.params = cfg, Path(run_dir), params
        self.names = [p["name"] for p in params]
        n = cfg["pairs_planned"]
        self.N, self.A = n, cfg.get("A_ratio", 0.1) * n
        self.alpha, self.gamma = cfg.get("alpha", 0.602), cfg.get("gamma", 0.101)
        self.c0 = [p["c_end"] * n ** self.gamma for p in params]
        self.a0 = [p["r_end"] * p["c_end"] ** 2 * (self.A + n) ** self.alpha for p in params]
        self.log_f = open(self.dir / "tuner.log", "a", encoding="ascii", errors="replace", newline="\n")

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
        rng = random.Random(f"{self.cfg.get('seed', 1)}:{k}")
        return [rng.choice((-1, 1)) for _ in self.params]

    def clamp(self, i, v):
        p = self.params[i]
        return min(max(v, p["min"]), p["max"])

    def values(self, theta, ck, delta, sign):
        return {self.names[i]: int(round(self.clamp(i, theta[i] + sign * ck[i] * delta[i]))) for i in range(len(theta))}


def load_state(run):
    path = run.dir / "iterations.jsonl"
    theta = [float(p["start"]) for p in run.params]
    k = batch = 0
    if path.exists():
        raw = path.read_bytes()
        if raw and not raw.endswith(b"\n"):
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


def pin_self(cpus):
    mask = sum(1 << c for c in cpus)
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.GetCurrentProcess.restype = ctypes.c_void_p
    h = ctypes.c_void_p(k32.GetCurrentProcess())
    if not k32.SetPriorityClass(h, IDLE) or not k32.SetProcessAffinityMask(h, ctypes.c_size_t(mask)):
        raise SystemExit("cannot set Idle priority / CPU mask (fail closed)")
    return mask


def foreign_gate_overlap(mask, mine):
    """fastchess.exe processes not started by this tuner whose affinity overlaps `mask`."""
    hits = []
    for p in psutil.process_iter(["name", "pid"]):
        try:
            if (p.info["name"] or "").lower() != "fastchess.exe" or p.pid in mine:
                continue
            aff = p.cpu_affinity()
            if sum(1 << c for c in aff) & mask:
                hits.append((p.pid, aff))
        except (psutil.Error, OSError):
            continue
    return hits


def slots_now(cpus, threads, max_busy):
    per = psutil.cpu_percent(interval=3.0, percpu=True)
    free = [c for c in cpus if c < len(per) and per[c] <= max_busy]
    return min(threads, len(free)), {c: per[c] for c in cpus if c < len(per)}


def fastchess(run, plus, minus, pairs, conc, start, base):
    c = run.cfg
    fixed = [f"option.{k}={v}" for k, v in c.get("fixed_options", {}).items()]

    def engine(name, vals):
        return ["-engine", f"name={name}", f"cmd={c['engine']}"] + fixed + [f"option.{k}={v}" for k, v in vals.items()]
    cmd = [c["fastchess"]] + engine("plus", plus) + engine("minus", minus) + [
        "-each", f"tc={c['tc']}", "timemargin=1000", "proto=uci", "option.Threads=1", f"option.Hash={c.get('hash', 16)}",
        "option.OwnBook=false",
        "-openings", f"file={c['book']}", f"format={c.get('book_format', 'epd')}", "order=sequential", f"start={start}",
        "-games", "2", "-repeat", "-rounds", str(pairs), "-concurrency", str(conc), "-recover",
        "-pgnout", f"file={base}.pgn", "-config", f"outname={base}.config.json"]
    t0 = time.time()
    with open(f"{base}.out", "x", encoding="utf-8", newline="\n") as out:
        proc = subprocess.Popen(cmd, stdout=out, stderr=subprocess.STDOUT, cwd=str(run.dir / "games"))
        run.my_pids.add(proc.pid)
        rc = proc.wait()
        run.my_pids.discard(proc.pid)
    secs = time.time() - t0
    w = l = d = 0
    terms = {}
    text = Path(f"{base}.pgn").read_text(encoding="utf-8", errors="replace") if Path(f"{base}.pgn").exists() else ""
    for g in text.split("[Event ")[1:]:
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


def cmd_run(cfg_path, run_dir, resume, until, max_pairs, total_pairs, threads, cpus_arg):
    cfg = json.loads(Path(cfg_path).read_text(encoding="utf-8"))
    d = Path(run_dir)
    if d.exists() and not resume:
        raise SystemExit(f"{d} exists: pass --resume to continue it")
    (d / "games").mkdir(parents=True, exist_ok=True)
    saved, saved_params = d / "config.json", d / "params.csv"
    if saved.exists():
        old = json.loads(saved.read_text(encoding="utf-8"))
        keep = lambda c: {k: v for k, v in c.items() if k not in ("threads", "cpus")}
        if keep(old) != keep(cfg):
            raise SystemExit(f"{cfg_path} differs from the run's {saved}: a resumed run keeps its config "
                             "(only threads / cpus may change)")
        if Path(cfg["params_csv"]).read_bytes() != saved_params.read_bytes():
            raise SystemExit("the params CSV differs from the run's copy")
    else:
        with open(saved, "x", encoding="utf-8", newline="\n") as f:
            json.dump(cfg, f, indent=1)
        shutil.copyfile(cfg["params_csv"], saved_params)
    params = read_params(saved_params)
    threads = threads or cfg.get("threads", 2)
    cpus = [int(x) for x in (cpus_arg or cfg.get("cpus", "0,1")).split(",")]
    if threads > 8:
        raise SystemExit("--threads above the job cap of 8")
    mask = pin_self(cpus)
    k32 = ctypes.windll.kernel32
    ev = k32.CreateEventW(None, True, False, event_name(d))
    run = Run(cfg, params, d)
    run.my_pids = set()
    theta, k, batch = load_state(run)
    pairs = cfg["pairs_per_batch"]
    hist = d / "history.csv"
    new_hist = not hist.exists()
    hist_f = open(hist, "a", encoding="ascii", newline="")
    hw = csv.writer(hist_f)
    if new_hist:
        hw.writerow(["batch", "time", "pairs_total", "games_total", "W", "L", "D", "R", "concurrency"] + run.names)
        hw.writerow([-1, now(), 0, 0, 0, 0, 0, 0, 0] + [f"{t:.3f}" for t in theta])
    deadline = dt.datetime.strptime(until, "%Y-%m-%d %H:%M") if until else None
    run.log(f"start: {len(theta)} parameters, pair count {k}, batch {batch}, planned {run.N}, {pairs} pairs per batch, "
            f"tc {cfg['tc']}, engine {cfg['engine']}, cpus {cpus} (mask 0x{mask:X}, Idle), threads <= {threads}, "
            f"until {until}")
    n_openings = cfg.get("book_openings", 100000)
    max_busy = float(cfg.get("max_busy_percent", 80.0))
    last_wait_log = 0.0
    done = 0
    while True:
        if total_pairs and k >= total_pairs:
            run.log(f"stop: --total-pairs {total_pairs} reached"); break
        if max_pairs and done >= max_pairs:
            run.log(f"stop: --max-pairs {max_pairs} reached"); break
        if deadline and dt.datetime.now() >= deadline:
            run.log(f"stop: --until {until} reached"); break
        if k32.WaitForSingleObject(ev, 0) == 0:
            run.log("stop: stop requested"); break
        low = disk_low()
        if low:
            run.log(f"stop: disk floor ({low}); resume with tune_spsa.ps1 -RunDir {d} after space is back"); break
        gates = foreign_gate_overlap(mask, run.my_pids)
        if gates:
            run.log(f"waiting: a fastchess not started by this tuner uses these CPUs {gates}")
            time.sleep(60); continue
        if psutil.virtual_memory().available / 2 ** 30 < 6.0:
            run.log("waiting: free RAM below 6 GB"); time.sleep(60); continue
        conc, busy = slots_now(cpus, threads, max_busy)
        if conc == 0:
            if time.time() - last_wait_log >= 600:
                run.log(f"waiting: every CPU of {cpus} is more than {max_busy:.0f} % busy without this tuner ({busy})")
                last_wait_log = time.time()
            time.sleep(30); continue
        last_wait_log = 0.0
        ck, ak, delta = run.ck(k), run.ak(k), run.delta(k)
        plus, minus = run.values(theta, ck, delta, +1), run.values(theta, ck, delta, -1)
        start = k % n_openings + 1
        attempt = fails = 0
        while True:
            attempt += 1
            base = str(d / "games" / f"b{batch:06d}_a{attempt}")
            if Path(base + ".out").exists():
                continue
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
               "concurrency": min(conc, 2 * pairs), "busy_before": busy, "seconds": round(secs, 1), "delta": delta,
               "c_k": [round(x, 4) for x in ck], "a_over_c": [round(x, 6) for x in g], "plus": plus, "minus": minus,
               "W": w, "L": l, "D": dr, "R": r, "terminations": terms, "theta_before": before,
               "theta_after": dict(zip(run.names, theta))}
        with open(d / "iterations.jsonl", "a", encoding="ascii", newline="\n") as f:
            f.write(json.dumps(rec) + "\n")
            f.flush()
            os.fsync(f.fileno())
        k += pairs
        done += pairs
        hw.writerow([batch, rec["time"], k, 2 * k, w, l, dr, r, rec["concurrency"]] + [f"{t:.3f}" for t in theta])
        hist_f.flush()
        bad = {t: n for t, n in terms.items() if t != "normal"}
        run.log(f"batch {batch}: pairs {k}, +{w} -{l} ={dr} (R {r:+d}) conc {rec['concurrency']} {secs:.0f} s"
                f"{' terminations ' + str(bad) if bad else ''}; "
                + ", ".join(f"{n} {t:.1f}" for n, t in list(zip(run.names, theta))[:5]) + (" ..." if len(theta) > 5 else ""))
        batch += 1
    hist_f.close()
    run.log(f"end: pair count {k}, {done} pairs in this session")


def cmd_stop(run_dir):
    h = ctypes.windll.kernel32.OpenEventW(0x0002 | 0x00100000, False, event_name(Path(run_dir)))
    if not h:
        raise SystemExit("no running tuner holds the stop event of " + run_dir)
    ctypes.windll.kernel32.SetEvent(h)
    print("stop requested: the tuner exits after the batch that is playing")


def cmd_status(run_dir):
    d = Path(run_dir)
    p = d / "iterations.jsonl"
    recs = [json.loads(x) for x in p.read_text(encoding="ascii").splitlines() if x.strip()] if p.exists() else []
    if not recs:
        print("no batches yet")
        return
    w = sum(r["W"] for r in recs)
    l = sum(r["L"] for r in recs)
    dr = sum(r["D"] for r in recs)
    print(f"{len(recs)} batches, {recs[-1]['k_after']} pairs, +{w} -{l} ={dr}, last {recs[-1]['time']}")
    for n, v in recs[-1]["theta_after"].items():
        print(f"  {n:26s} {recs[0]['theta_before'][n]:10.2f} -> {v:10.2f}")


def main():
    a = sys.argv
    if len(a) >= 3 and a[1] == "status":
        cmd_status(a[2])
    elif len(a) >= 3 and a[1] == "stop":
        cmd_stop(a[2])
    elif len(a) >= 4 and a[1] == "run":
        def opt(name, conv):
            return conv(a[a.index(name) + 1]) if name in a else None
        cmd_run(a[2], a[3], "--resume" in a, opt("--until", str), opt("--max-pairs", int), opt("--total-pairs", int),
                opt("--threads", int), opt("--cpus", str))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
