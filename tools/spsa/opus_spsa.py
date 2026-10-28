#!/usr/bin/env python3
"""Forge offline SPSA tuner (R3-4): tunes integer UCI spin options with theta+ / theta- mini-matches in fastchess.

usage:
  opus_spsa.py --config CFG --workdir DIR                 run or resume a session (state.json, spsa_log.csv)
  opus_spsa.py --config CFG --workdir DIR --dry-run       short smoke session from the config's "dry_run" block
                                                          (very short TC, 2-3 params, 2-3 iterations, <= 2 threads)
                                                          in DIR/dry_run; resumable like a real session
  opus_spsa.py --config CFG --workdir DIR --plan          print the schedule and the next fastchess command only
  opus_spsa.py --workdir DIR --status                     current theta, rounded values, setoption lines
  opus_spsa.py --config CFG --workdir DIR --synthetic     the whole loop against a synthetic Elo landscape
options: --engine EXE --fastchess EXE --book FILE (override the config), --stop-after N (iterations in this run),
         [--dry-run] --status also accepts DIR/dry_run.
A session is resumed whenever DIR (or DIR/dry_run) holds a state.json; the config must not change in between
(its schedule/match fingerprint and the engine/book sha256 pins are checked). See tools/spsa/README.md.
Exit codes: 0 done (finished or --stop-after), 2 iteration failed (after retries), 3 low free RAM,
4 config/engine check failed, 130 interrupted (state stays at the last completed iteration).
Standard library only, Python 3.10+.
"""
from __future__ import annotations

import argparse
import copy
import csv
import datetime
import io
import json
import os
import shlex
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # the opus_spsa_* helpers (python -I drops it)

import opus_spsa_core as core  # noqa: E402
import opus_spsa_fastchess as fc  # noqa: E402
import opus_spsa_uci as uci  # noqa: E402

DEFAULTS = {
    "fastchess": "fastchess",
    "engine": None,
    "book": {"file": None, "format": "epd", "order": "random"},
    "tc": None,
    "nodes": None,
    "timemargin_ms": None,
    "threads": 1,
    "hash": 16,
    "concurrency": 1,
    "max_total_threads": None,
    "pairs_per_iteration": 4,
    "iterations": 1000,
    "seed": 1,
    "A_ratio": core.A_RATIO,
    "alpha": core.ALPHA,
    "gamma": core.GAMMA,
    "rounding": "deterministic",
    "r_end": 0.002,
    "engine_options": {"OwnBook": "false"},
    "strict": False,  # fastchess -strict stops on any warning, a single time forfeit included
    "extra_args": [],
    "priority": "idle",
    "iteration_timeout_s": 900,
    "retries": 1,
    "min_free_ram_gib": 0,
    "ram_wait_minutes": 30,
    "allow_start_offset": False,
    "params": [],
    "dry_run": {},
}
DRY_RUN_DEFAULTS = {"iterations": 3, "pairs_per_iteration": 1, "concurrency": 2, "tc": "0.5+0.005", "nodes": None,
                    "max_total_threads": 2, "param_count": 3}
EXIT_FAILED, EXIT_RAM, EXIT_CONFIG, EXIT_INTERRUPTED = 2, 3, 4, 130


class ConfigError(Exception):
    pass


class IterationFailed(Exception):
    pass


# ---------------------------------------------------------------------------------------------------------------
# Config

def load_config(path: str, overrides: dict) -> dict:
    """The effective config: defaults <- file <- command-line overrides; relative paths in the file are taken
    relative to the file's directory."""
    with open(path, "rb") as f:
        raw = json.loads(f.read().decode("utf-8"))
    cfg = copy.deepcopy(DEFAULTS)
    for key, value in raw.items():
        if key.startswith("_"):
            continue
        if key not in DEFAULTS:
            raise ConfigError(f"unknown config key {key!r}")
        if key == "book":
            cfg["book"].update(value)
        else:
            cfg[key] = value
    base = os.path.dirname(os.path.abspath(path))

    def resolve(p):
        return p if p is None or os.path.isabs(p) else os.path.normpath(os.path.join(base, p))
    cfg["engine"] = resolve(cfg["engine"])
    cfg["book"]["file"] = resolve(cfg["book"]["file"])
    if isinstance(cfg["fastchess"], str) and ("/" in cfg["fastchess"] or "\\" in cfg["fastchess"]):
        cfg["fastchess"] = resolve(cfg["fastchess"])
    for key, value in overrides.items():
        if value is None:
            continue
        if key == "book":
            cfg["book"]["file"] = os.path.abspath(value)
        else:
            cfg[key] = os.path.abspath(value) if key in ("engine", "fastchess") else value
    return cfg


def make_params(cfg: dict) -> list[core.Param]:
    params = []
    for entry in cfg["params"]:
        try:
            params.append(core.Param(name=str(entry["name"]), start=float(entry["start"]), minimum=int(entry["min"]),
                                     maximum=int(entry["max"]), c_end=float(entry["c_end"]),
                                     r_end=float(entry.get("r_end", cfg["r_end"]))))
        except KeyError as exc:
            raise ConfigError(f"parameter {entry!r} lacks {exc}") from None
    return params


def validate(cfg: dict, params: list[core.Param]) -> list[str]:
    """Problems in a config (empty list = usable)."""
    problems = []
    if not params:
        problems.append("no params")
    names = [p.name for p in params]
    if len(set(names)) != len(names):
        problems.append("duplicate parameter names")
    for p in params:
        if not p.minimum <= p.start <= p.maximum:
            problems.append(f"{p.name}: start {p.start} outside [{p.minimum}, {p.maximum}]")
        if p.c_end <= 0 or p.r_end <= 0:
            problems.append(f"{p.name}: c_end and r_end must be > 0")
        if p.c_end > (p.maximum - p.minimum) / 2:
            problems.append(f"{p.name}: c_end {p.c_end} exceeds half the range")
        if cfg["rounding"] == "deterministic" and p.c_end < 0.5:
            problems.append(f"{p.name}: c_end {p.c_end} < 0.5 with deterministic rounding (theta+ and theta- "
                            f"could round to the same value); raise c_end or use rounding 'randomized'")
    if cfg["rounding"] not in core.ROUNDING_MODES:
        problems.append(f"rounding must be one of {core.ROUNDING_MODES}")
    for key in ("iterations", "pairs_per_iteration", "concurrency", "threads", "hash"):
        if not isinstance(cfg[key], int) or cfg[key] < 1:
            problems.append(f"{key} must be an integer >= 1")
    if not cfg["tc"] and not cfg["nodes"]:
        problems.append("set tc (e.g. '8+0.08') and/or nodes")
    if cfg["max_total_threads"] and cfg["concurrency"] * cfg["threads"] > cfg["max_total_threads"]:
        problems.append(f"concurrency {cfg['concurrency']} x threads {cfg['threads']} exceeds max_total_threads "
                        f"{cfg['max_total_threads']}")
    if cfg["priority"] not in fc.PRIORITIES:
        problems.append(f"priority must be one of {fc.PRIORITIES}")
    if not 0 < cfg["alpha"] <= 1 or not 0 < cfg["gamma"] <= 1 or cfg["A_ratio"] < 0:
        problems.append("need 0 < alpha <= 1, 0 < gamma <= 1, A_ratio >= 0")
    return problems


def apply_dry_run(cfg: dict) -> dict:
    """The smoke-session config: the "dry_run" block over DRY_RUN_DEFAULTS over the real config."""
    dr = dict(DRY_RUN_DEFAULTS)
    dr.update(cfg.get("dry_run") or {})
    out = copy.deepcopy(cfg)
    for key in ("iterations", "pairs_per_iteration", "concurrency", "tc", "nodes", "max_total_threads"):
        out[key] = dr[key]
    for key in ("timemargin_ms", "extra_args", "iteration_timeout_s", "strict"):
        if key in dr:
            out[key] = dr[key]
    wanted = dr.get("params") or [p["name"] for p in cfg["params"][:int(dr["param_count"])]]
    by_name = {p["name"]: p for p in cfg["params"]}
    missing = [n for n in wanted if n not in by_name]
    if missing:
        raise ConfigError(f"dry_run params not in params: {missing}")
    out["params"] = [by_name[n] for n in wanted]
    if dr.get("seed") is not None:
        out["seed"] = dr["seed"]
    out["dry_run"] = {}
    return out


def schedule_of(cfg: dict) -> core.Schedule:
    return core.Schedule.make(cfg["iterations"], cfg["A_ratio"], cfg["alpha"], cfg["gamma"])


def config_fingerprint(cfg: dict, params: list[core.Param]) -> str:
    """Everything that defines the session's numbers; a resumed session must have the same."""
    return core.fingerprint({
        "params": [[p.name, p.start, p.minimum, p.maximum, p.c_end, p.r_end] for p in params],
        "schedule": [cfg["iterations"], cfg["A_ratio"], cfg["alpha"], cfg["gamma"], cfg["rounding"], cfg["seed"]],
        "match": [cfg["pairs_per_iteration"], cfg["tc"], cfg["nodes"], cfg["threads"], cfg["hash"],
                  cfg["engine_options"], cfg["book"].get("format"), cfg["book"].get("order"), cfg["extra_args"]],
    })


# ---------------------------------------------------------------------------------------------------------------
# CSV log: one row per completed iteration, written after state.json (a missing last row is repaired on resume).

FIXED_COLUMNS = ["iteration", "utc", "seconds", "srand", "attempt", "games", "wins", "losses", "draws", "w_minus_l",
                 "ptnml_0", "ptnml_1", "ptnml_2", "ptnml_3", "ptnml_4", "time_losses", "abnormal"]
PARAM_COLUMNS = ["c_k", "a_k", "delta", "plus", "minus", "theta"]


def csv_header(params: list[core.Param]) -> list[str]:
    return FIXED_COLUMNS + [f"{p.name}.{c}" for p in params for c in PARAM_COLUMNS]


def csv_row(record: dict, params: list[core.Param]) -> list:
    row = [record["iteration"], record["utc"], f"{record['seconds']:.2f}", record["srand"], record["attempt"],
           record["games"], record["wins"], record["losses"], record["draws"], record["w_minus_l"],
           *record["ptnml"], record["time_losses"], record["abnormal"]]
    for p in params:
        e = record["params"][p.name]
        row += [f"{e['c_k']:.6g}", f"{e['a_k']:.6g}", e["delta"], e["plus"], e["minus"], f"{e['theta']:.6f}"]
    return row


def _csv_text(rows: list[list]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def last_csv_iteration(path: str) -> int | None:
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        lines = [line for line in f.read().decode("utf-8").split("\n") if line.strip()]
    if len(lines) <= 1:
        return None
    return int(lines[-1].split(",", 1)[0])


def append_csv(path: str, params: list[core.Param], record: dict) -> None:
    """Append record's row once (no-op if the CSV already ends at or after this iteration)."""
    last = last_csv_iteration(path)
    if last is not None and last >= record["iteration"]:
        return
    rows = [] if os.path.exists(path) and os.path.getsize(path) > 0 else [csv_header(params)]
    rows.append(csv_row(record, params))
    with open(path, "ab") as f:
        f.write(_csv_text(rows))
        f.flush()
        os.fsync(f.fileno())


# ---------------------------------------------------------------------------------------------------------------
# Session loop

def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Logger:
    def __init__(self, path: str | None, quiet: bool = False):
        self.path, self.quiet = path, quiet

    def __call__(self, message: str) -> None:
        line = f"{utc_now()} {message}"
        if not self.quiet:
            print(line, flush=True)
        if self.path:
            with open(self.path, "ab") as f:
                f.write((line + "\n").encode("utf-8"))


def open_session(workdir: str, cfg: dict, params: list[core.Param], pins: dict[str, str], log: Logger) -> dict:
    """Load state.json (resume) or start a new one; refuses a changed config or engine/book."""
    os.makedirs(workdir, exist_ok=True)
    state_path = os.path.join(workdir, "state.json")
    fp = config_fingerprint(cfg, params)
    if os.path.exists(state_path):
        state = core.load_json(state_path)
        if state.get("version") != core.STATE_VERSION or state.get("tool") != "opus_spsa":
            raise ConfigError(f"{state_path}: not an opus_spsa state (version {state.get('version')})")
        if state["fingerprint"] != fp:
            raise ConfigError(f"{state_path}: the config changed since the session started (fingerprint "
                              f"{state['fingerprint'][:12]} != {fp[:12]}); compare with config_used.json, or start "
                              f"a new workdir")
        for key, value in pins.items():
            if state["pins"].get(key) != value:
                raise ConfigError(f"{state_path}: {key} changed ({state['pins'].get(key)} -> {value})")
        if set(state["theta"]) != {p.name for p in params}:
            raise ConfigError(f"{state_path}: parameter set differs from the config")
        # Repair: the CSV row of the last completed iteration (state is written first).
        record = state.get("last_record")
        if record is not None:
            append_csv(os.path.join(workdir, "spsa_log.csv"), params, record)
        log(f"resume at iteration {state['next_iteration']}/{cfg['iterations']} from {state_path}")
        return state
    state = core.new_state(params, fp, pins)
    core.save_json_atomic(os.path.join(workdir, "config_used.json"), {"config": cfg, "fingerprint": fp,
                                                                       "pins": pins, "started": utc_now()})
    core.save_json_atomic(state_path, state)
    log(f"new session: {len(params)} params, {cfg['iterations']} iterations x {cfg['pairs_per_iteration']} pairs, "
        f"tc {cfg['tc']} nodes {cfg['nodes']}, concurrency {cfg['concurrency']}, fingerprint {fp[:12]}")
    return state


def wait_for_ram(cfg: dict, log: Logger) -> bool:
    """True when free RAM is at least min_free_ram_gib (waits up to ram_wait_minutes)."""
    need = float(cfg.get("min_free_ram_gib") or 0)
    if need <= 0:
        return True
    deadline = time.monotonic() + 60 * float(cfg.get("ram_wait_minutes") or 0)
    while True:
        free = fc.free_ram_gib()
        if free is None or free >= need:
            return True
        if time.monotonic() >= deadline:
            log(f"free RAM {free:.1f} GiB < {need} GiB: stopping (state saved)")
            return False
        log(f"free RAM {free:.1f} GiB < {need} GiB: waiting 60 s")
        time.sleep(60)


def run_session(cfg: dict, workdir: str, params: list[core.Param], match, pins: dict[str, str], log: Logger,
                stop_after: int | None = None) -> tuple[dict, int]:
    """Iterate from the saved state; `match(plus, minus, pairs, srand, k, attempt)` returns (MatchResult, info).
    Returns (state, exit code)."""
    schedule = schedule_of(cfg)
    state = open_session(workdir, cfg, params, pins, log)
    state_path = os.path.join(workdir, "state.json")
    csv_path = os.path.join(workdir, "spsa_log.csv")
    done_here = 0
    t_session = time.monotonic()
    while state["next_iteration"] < cfg["iterations"]:
        if stop_after is not None and done_here >= stop_after:
            log(f"stopped after {done_here} iteration(s) in this run (--stop-after); resume with the same command")
            state["status"] = "stopped"
            core.save_json_atomic(state_path, state)
            return state, 0
        if not wait_for_ram(cfg, log):
            state["status"] = "stopped: low RAM"
            core.save_json_atomic(state_path, state)
            return state, EXIT_RAM
        k = state["next_iteration"]
        theta = state["theta"]
        rng = core.iteration_rng(cfg["seed"], k)
        perts = core.perturb(theta, params, schedule, k, cfg["rounding"], rng)
        plus = {q.name: q.plus for q in perts}
        minus = {q.name: q.minus for q in perts}
        srand = core.iteration_srand(cfg["seed"], k)
        result = info = None
        failures = []
        for attempt in range(int(cfg["retries"]) + 1):
            try:
                result, info = match(plus, minus, cfg["pairs_per_iteration"], srand, k, attempt)
                core.check_result(result, cfg["pairs_per_iteration"])
                break
            except (IterationFailed, ValueError) as exc:
                failures.append(f"attempt {attempt}: {exc}")
                log(f"iteration {k} attempt {attempt} failed: {exc}")
                result = None
        if result is None:
            state["status"] = f"stopped: iteration {k} failed"
            state["last_failure"] = failures
            core.save_json_atomic(state_path, state)
            return state, EXIT_FAILED
        new_theta = core.update(theta, params, perts, result.w_minus_l)
        record = {
            "iteration": k, "utc": utc_now(), "seconds": float(info.get("seconds", 0.0)), "srand": srand,
            "attempt": info.get("attempt", 0), "games": result.games, "wins": result.wins, "losses": result.losses,
            "draws": result.draws, "w_minus_l": result.w_minus_l, "ptnml": list(result.ptnml),
            "time_losses": result.time_losses, "abnormal": result.abnormal,
            "terminations": dict(result.terminations),
            "params": {q.name: {"c_k": q.c_k, "a_k": q.a_k, "delta": q.delta, "plus": q.plus, "minus": q.minus,
                                "theta_before": theta[q.name], "theta": new_theta[q.name]} for q in perts},
        }
        state = core.advance_state(state, new_theta, result, record)
        core.save_json_atomic(state_path, state)
        append_csv(csv_path, params, record)
        done_here += 1
        per_it = (time.monotonic() - t_session) / done_here
        left = cfg["iterations"] - state["next_iteration"]
        moves = " ".join(f"{q.name} {theta[q.name]:.2f}->{new_theta[q.name]:.2f} ({q.plus}/{q.minus})"
                         for q in perts[:4])
        more = f" (+{len(perts) - 4} more)" if len(perts) > 4 else ""
        log(f"it {k + 1}/{cfg['iterations']} | W{result.wins} L{result.losses} D{result.draws} "
            f"ptnml {list(result.ptnml)} | {record['seconds']:.1f} s | ETA {left * per_it / 3600:.2f} h | "
            f"{moves}{more}")
    state["status"] = "finished"
    core.save_json_atomic(state_path, state)
    log("finished: " + ", ".join(f"{n}={v:.2f}" for n, v in state["theta"].items()))
    return state, 0


def fastchess_match(cfg: dict, workdir: str, log: Logger):
    """The match function of a real session: one fastchess run per attempt, in its own new directory."""
    games_dir = os.path.join(workdir, "games")
    os.makedirs(games_dir, exist_ok=True)

    def play(plus, minus, pairs, srand, k, attempt):
        n = attempt
        while os.path.exists(os.path.join(games_dir, f"iter_{k:06d}_a{n}")):
            n += 1  # an earlier (interrupted) attempt keeps its directory
        itdir = os.path.join(games_dir, f"iter_{k:06d}_a{n}")
        os.makedirs(itdir)
        argv = fc.build_command(cfg, plus, minus, srand, os.path.join(itdir, "games.pgn"))
        with open(os.path.join(itdir, "command.json"), "wb") as f:
            f.write((json.dumps(argv, indent=1) + "\n").encode("utf-8"))
        outcome = fc.run_child(argv, itdir, os.path.join(itdir, "fastchess.out"), cfg["iteration_timeout_s"],
                               cfg["priority"])
        if outcome.timed_out:
            raise IterationFailed(f"fastchess timed out after {cfg['iteration_timeout_s']} s ({itdir})")
        if outcome.returncode != 0:
            tail = " | ".join(outcome.output.strip().splitlines()[-3:])
            raise IterationFailed(f"fastchess exit code {outcome.returncode} ({itdir}): {tail}")
        result = fc.parse_output(outcome.output, pairs)
        if result.abnormal:
            raise IterationFailed(f"{result.abnormal} game(s) ended abnormally: {dict(result.terminations)}")
        return result, {"seconds": outcome.seconds, "attempt": n, "dir": itdir}
    return play


def synthetic_match(cfg: dict, params: list[core.Param]):
    """--synthetic: optimum = start + 2 c_end (inside the bounds), scale = 4 c_end, 10 Elo per scale^2."""
    optimum = {p.name: core.clamp(p.start + 2 * p.c_end, p.minimum, p.maximum) for p in params}
    scale = {p.name: 4 * p.c_end for p in params}
    game = core.SyntheticMatch(optimum, scale, depth=10.0, noise=True)

    def play(plus, minus, pairs, srand, k, attempt):
        return game(plus, minus, pairs, srand), {"seconds": 0.0, "attempt": attempt}
    return play, optimum


# ---------------------------------------------------------------------------------------------------------------
# Preflight, plan, status

def preflight(cfg: dict, params: list[core.Param], fresh: bool, log: Logger) -> dict[str, str]:
    """Files present, engine advertises and applies every tuned option; returns the sha256 pins."""
    problems = []
    if not cfg["engine"] or not os.path.isfile(cfg["engine"]):
        problems.append(f"engine not found: {cfg['engine']}")
    if not cfg["book"]["file"] or not os.path.isfile(cfg["book"]["file"]):
        problems.append(f"opening book not found: {cfg['book']['file']}")
    fastchess = cfg["fastchess"][0] if isinstance(cfg["fastchess"], list) else cfg["fastchess"]
    if ("/" in fastchess or "\\" in fastchess) and not os.path.isfile(fastchess):
        problems.append(f"fastchess not found: {fastchess}")
    if problems:
        raise ConfigError("; ".join(problems))
    flags = fc.IDLE_PRIORITY_CLASS if os.name == "nt" and cfg["priority"] == "idle" else 0
    try:
        options, applied = uci.prove_application(cfg["engine"], params, creationflags=flags)
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        raise ConfigError(f"engine check failed: {cfg['engine']}: {exc}") from None
    problems = uci.check_params(params, options, fresh, cfg["allow_start_offset"]) + applied
    for name in ["Threads", "Hash"] + list(cfg["engine_options"]):
        if name not in options:
            problems.append(f"engine option {name} not advertised")
    if problems:
        raise ConfigError("engine check failed:\n  " + "\n  ".join(problems))
    pins = {"engine_sha256": fc.sha256_file(cfg["engine"]), "book_sha256": fc.sha256_file(cfg["book"]["file"])}
    log(f"engine {cfg['engine']} sha256 {pins['engine_sha256'][:16]}: advertises and applies all {len(params)} "
        f"params; book sha256 {pins['book_sha256'][:16]}")
    return pins


def print_plan(cfg: dict, params: list[core.Param], workdir: str | None) -> None:
    schedule = schedule_of(cfg)
    n = cfg["iterations"]
    state_path = os.path.join(workdir, "state.json") if workdir else None
    state = core.load_json(state_path) if state_path and os.path.exists(state_path) else None
    k = state["next_iteration"] if state else 0
    theta = state["theta"] if state else {p.name: p.start for p in params}
    print(f"schedule: N = {n} iterations x {cfg['pairs_per_iteration']} pairs = {2 * n * cfg['pairs_per_iteration']} "
          f"games, A = {schedule.A:g}, alpha = {schedule.alpha}, gamma = {schedule.gamma}, "
          f"rounding {cfg['rounding']}, seed {cfg['seed']}")
    print(f"{'param':<22}{'start':>8}{'min':>7}{'max':>7}{'c_end':>7}{'r_end':>8}{'c_0':>10}{'a_0/c_0':>9}"
          f"{'a_end/c_end':>12}")
    for p in params:
        a0, c0 = schedule.gains(p, 0)
        a1, c1 = schedule.gains(p, n - 1)
        print(f"{p.name:<22}{p.start:>8g}{p.minimum:>7}{p.maximum:>7}{p.c_end:>7g}{p.r_end:>8g}{c0:>10.3f}"
              f"{a0 / c0:>9.4f}{a1 / c1:>12.4f}")
    print("(a_k/c_k = step of theta per unit of W-L in the mini-match)")
    if k >= n:
        print("session finished")
        return
    perts = core.perturb(theta, params, schedule, k, cfg["rounding"], core.iteration_rng(cfg["seed"], k))
    srand = core.iteration_srand(cfg["seed"], k)
    argv = fc.build_command(cfg, {q.name: q.plus for q in perts}, {q.name: q.minus for q in perts}, srand,
                            "<workdir>/games/iter_%06d_a0/games.pgn" % k)
    print(f"iteration {k}: srand {srand}")
    print(" ".join(shlex.quote(str(a)) for a in argv))


def print_status(workdir: str) -> int:
    state_path = os.path.join(workdir, "state.json")
    if not os.path.exists(state_path):
        print(f"no state.json in {workdir}")
        return EXIT_CONFIG
    state = core.load_json(state_path)
    used = core.load_json(os.path.join(workdir, "config_used.json"))
    cfg = used["config"]
    params = {p["name"]: p for p in cfg["params"]}
    t = state["totals"]
    print(f"{workdir}: {state['status']}, {state['next_iteration']}/{cfg['iterations']} iterations, "
          f"{t['games']} games (W {t['wins']} L {t['losses']} D {t['draws']}, ptnml {t['ptnml']}, "
          f"time losses {t['time_losses']})")
    print(f"{'param':<22}{'start':>8}{'theta':>11}{'rounded':>9}{'moved/c_end':>13}")
    for name, value in state["theta"].items():
        p = params[name]
        print(f"{name:<22}{p['start']:>8g}{value:>11.3f}{int(core.round_value(value, 'deterministic', None)):>9}"
              f"{(value - p['start']) / p['c_end']:>13.2f}")
    print("setoption lines:")
    for name, value in state["theta"].items():
        print(f"  setoption name {name} value {core.round_value(value, 'deterministic', None)}")
    print("fastchess: " + " ".join(f"option.{n}={core.round_value(v, 'deterministic', None)}"
                                   for n, v in state["theta"].items()))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config")
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--engine")
    ap.add_argument("--fastchess")
    ap.add_argument("--book")
    ap.add_argument("--dry-run", action="store_true", help="short smoke session from the config's dry_run block")
    ap.add_argument("--plan", action="store_true", help="print the schedule and the next fastchess command only")
    ap.add_argument("--status", action="store_true", help="print the session's current theta")
    ap.add_argument("--synthetic", action="store_true", help="play against a synthetic Elo landscape (no engine)")
    ap.add_argument("--stop-after", type=int, help="stop cleanly after N iterations in this run")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    workdir = os.path.abspath(a.workdir)
    if a.dry_run:
        workdir = os.path.join(workdir, "dry_run")
    if a.synthetic:
        workdir = os.path.join(workdir, "synthetic")
    if a.status:
        return print_status(workdir)
    if not a.config:
        ap.error("--config is required")
    try:
        cfg = load_config(a.config, {"engine": a.engine, "fastchess": a.fastchess, "book": a.book})
        if a.dry_run:
            cfg = apply_dry_run(cfg)
        params = make_params(cfg)
        problems = validate(cfg, params)
        if problems:
            raise ConfigError("config problems:\n  " + "\n  ".join(problems))
        if a.plan:
            print_plan(cfg, params, workdir)
            return 0
        os.makedirs(workdir, exist_ok=True)
        log = Logger(os.path.join(workdir, "session.log"), a.quiet)
        log(f"opus_spsa {'synthetic ' if a.synthetic else ''}{'dry run ' if a.dry_run else ''}session in {workdir} "
            f"(config {os.path.abspath(a.config)})")
        fresh = not os.path.exists(os.path.join(workdir, "state.json"))
        if a.synthetic:
            match, optimum = synthetic_match(cfg, params)
            log("synthetic optimum: " + ", ".join(f"{n}={v:g}" for n, v in optimum.items()))
            pins = {"engine_sha256": "synthetic", "book_sha256": "synthetic"}
        else:
            pins = preflight(cfg, params, fresh, log)
            match = fastchess_match(cfg, workdir, log)
        _, code = run_session(cfg, workdir, params, match, pins, log, a.stop_after)
        return code
    except ConfigError as exc:
        print(f"opus_spsa: {exc}", file=sys.stderr)
        return EXIT_CONFIG
    except KeyboardInterrupt:
        print("opus_spsa: interrupted; the state stays at the last completed iteration", file=sys.stderr)
        return EXIT_INTERRUPTED


if __name__ == "__main__":
    sys.exit(main())
