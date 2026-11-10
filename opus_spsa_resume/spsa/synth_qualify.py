"""synth_qualify.py - synthetic run-size qualification of a tuning config. No engine, no games, no Elo.

usage: python -I -B synth_qualify.py <config.json> <out_dir> [--reps N]
       python -I -B synth_qualify.py <config.json> <out_dir> --sweep [--reps N]

Derives SYNTHETIC copies of <config.json>. Each copy keeps everything the real run uses: schedule, bounds,
priors, pins, perturbation seed, N and batch size. Only four keys change: run_nonce, identity_check = "start"
(the pins are hashed once, not before every batch), a synthetic outcome model, and the comment.
Each copy runs to completion with opus3_spsa.py --mode synthetic. Re-running the script resumes or reuses
finished runs; a changed derived config is refused.

  landscape L2   quadratic, optimum 2 c_end from the start in every tuned coordinate, signs (+,-,-). The scale
                 is 2 c_end, so z = 1 per coordinate at the start. K = 1.25 puts the start 3.75 model units
                 below the optimum. Draw rate 0.75.
  landscape L2m  the mirror placement, signs (-,+,+). Same gap and draw rate.
  landscape L4   optimum 4 c_end away, scale 4 c_end. Same gap: a wider, flatter basin.
  null           a flat model with no signal. The final drift from the start is the noise floor of the procedure.
  resume         one L2 replicate run with two injected crashes (B3 mid-batch, then B5 after the update record),
                 each resumed. It always starts from an empty directory, both crashes must fire (exit 77), and its
                 ledger, RUN.json, HEAD.json and every checkpoint must equal the uninterrupted replicate byte for
                 byte.

  --sweep        run length and gain: N in {4000, 16000, 40000} pairs x r_end in {0.002, 0.005, 0.01}, landscape
                 L2 and null, --reps replicates each. Only pairs_planned and the tuned r_end differ from the real
                 config. Output: sweep_summary.json.

Model units use the logistic/400 scale of the harness's Synthetic backend. They describe the model only and
are NOT Elo of the engine. The output is summary.json in <out_dir>."""
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TUNER = HERE / "opus3_spsa.py"
sys.path.insert(0, str(HERE))
from opus3_spsa import Synthetic  # noqa: E402  (the harness's own model, so the metrics use the same strength)

GAP = 3.75
DRAW = 0.75
LANDSCAPES = {"L2": (2.0, (1, -1, -1)), "L2m": (2.0, (-1, 1, 1)), "L4": (4.0, (1, -1, -1))}
CHECKPOINTS_K = (500, 1000, 2000, 3000, 4000, 8000, 12000, 16000, 40000)


def tuned(cfg):
    return [p for p in cfg["params"] if p.get("enabled", True)]


def landscape_model(cfg, dist, signs, seed):
    ps = tuned(cfg)
    if len(signs) != len(ps):
        raise SystemExit(f"landscape signs {signs} do not match {len(ps)} tuned parameters")
    opt = {p["name"]: float(p["start"]) + s * dist * p["c_end"] for p, s in zip(ps, signs)}
    scale = {p["name"]: dist * p["c_end"] for p in ps}
    return {"kind": "quadratic", "K": GAP / len(ps), "draw": DRAW, "seed": seed, "opt": opt, "scale": scale}


def derive(base, base_name, nonce, synthetic):
    cfg = json.loads(json.dumps(base))
    cfg["run_nonce"] = nonce
    cfg["identity_check"] = "start"
    cfg["synthetic"] = synthetic
    cfg["comment"] = (f"SYNTHETIC QUALIFICATION copy of {base_name}, derived by spsa/synth_qualify.py: only run_nonce, "
                      "identity_check and synthetic differ. Outcomes come from a model; no games; no Elo.")
    return cfg


def run_tuner(args, crash=None):
    env = dict(os.environ)
    env.pop("OPUS3_CRASH_AT", None)
    if crash:
        env["OPUS3_CRASH_AT"] = crash
    p = subprocess.run([sys.executable, "-I", "-B", str(TUNER)] + [str(a) for a in args], capture_output=True,
                       text=True, env=env, timeout=7200)
    return p.returncode, p.stdout, p.stderr


def write_config(path, cfg):
    data = (json.dumps(cfg, indent=1) + "\n").encode("ascii")
    if path.exists() and path.read_bytes() != data:
        raise SystemExit(f"{path} exists with different content (refusing to reuse a changed derived config)")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(data)


def run_to_end(cfg_path, run_dir, crashes=()):
    """Run (or resume) a synthetic copy to completion. Returns the exit codes in order."""
    codes = []
    for crash in list(crashes) + [None]:
        resume = (run_dir / "RUN.json").exists()
        args = ["run", cfg_path, run_dir, "--mode", "synthetic"] + (["--resume"] if resume else [])
        rc, out, err = run_tuner(args, crash)
        codes.append(rc)
        if crash is None and rc != 0:
            raise SystemExit(f"{run_dir}: exit {rc}: {err[-600:]}")
        if crash is not None and rc not in (77, 0):
            raise SystemExit(f"{run_dir}: crash run exit {rc}: {err[-600:]}")
    rc, out, err = run_tuner(["verify", run_dir])
    if rc != 0:
        raise SystemExit(f"{run_dir}: verify exit {rc}: {err[-600:]}")
    codes.append(("verify", rc))
    return codes


def ledger_records(run_dir):
    return [json.loads(x) for x in (run_dir / "ledger.jsonl").read_text(encoding="ascii").splitlines() if x.strip()]


def metrics(cfg, run_dir):
    recs = ledger_records(run_dir)
    names = next(r for r in recs if r["type"] == "init")["names"]
    start = next(r for r in recs if r["type"] == "init")["theta"]
    comp = [r for r in recs if r["type"] == "complete"]
    if not comp:
        raise SystemExit(f"{run_dir}: run not complete")
    ups = [r["update"] for r in recs if r["type"] == "update"]
    plans = [r["plan"] for r in recs if r["type"] == "plan"]
    cend = {p["name"]: p["c_end"] for p in tuned(cfg)}
    model = Synthetic(cfg)
    m = cfg["synthetic"]

    def as_vals(theta):
        return dict(zip(names, theta))

    traj = {}
    for u in ups:
        if u["k_after"] in CHECKPOINTS_K:
            traj[str(u["k_after"])] = as_vals(u["theta_after"])
    final = comp[0]["theta"]
    out = {"pairs": comp[0]["k"], "batches": len(ups), "theta_start": as_vals(start), "theta_final": as_vals(final),
           "engine_values_final": comp[0]["values"],
           "drift_final_cend": {n: (final[i] - start[i]) / cend[n] for i, n in enumerate(names)},
           "updates_projected": sum(1 for u in ups if u.get("projected")),
           "updates_with_active_constraint": sum(1 for u in ups if u.get("active")),
           "plans_shrunk": sum(1 for p in plans if p.get("s", 1.0) < 1.0),
           "plans_capped": sum(1 for p in plans if any(p.get("capped") or [])),
           "plans_s_below_min": sum(1 for p in plans if p.get("s_below_min"))}
    if m.get("kind") == "quadratic":
        opt = [m["opt"][n] for n in names]
        s_opt = model.strength(dict(zip(names, opt)))
        gap0 = s_opt - model.strength(as_vals(start))
        out["gap_start_model_units"] = gap0
        out["gap_final_model_units"] = s_opt - model.strength(as_vals(final))
        out["gap_final_engine_ints_model_units"] = s_opt - model.strength(
            {n: comp[0]["values"][n] for n in names})
        out["gap_recovered_fraction"] = 1.0 - out["gap_final_model_units"] / gap0
        out["dist_to_opt_cend"] = {n: (final[i] - opt[i]) / cend[n] for i, n in enumerate(names)}
        out["gap_trajectory_model_units"] = {k: s_opt - model.strength(v) for k, v in traj.items()}
    return out


def summarize(rows):
    def mean(xs):
        return sum(xs) / len(xs)

    def sd(xs):
        mu = mean(xs)
        return (sum((x - mu) ** 2 for x in xs) / max(1, len(xs) - 1)) ** 0.5

    res = {"reps": len(rows)}
    names = list(rows[0]["drift_final_cend"])
    res["drift_final_cend_mean"] = {n: mean([r["drift_final_cend"][n] for r in rows]) for n in names}
    res["drift_final_cend_sd"] = {n: sd([r["drift_final_cend"][n] for r in rows]) for n in names}
    if "gap_final_model_units" in rows[0]:
        res["gap_start_model_units"] = rows[0]["gap_start_model_units"]
        res["gap_final_mean"] = mean([r["gap_final_model_units"] for r in rows])
        res["gap_final_min_max"] = [min(r["gap_final_model_units"] for r in rows),
                                    max(r["gap_final_model_units"] for r in rows)]
        res["gap_recovered_fraction_mean"] = mean([r["gap_recovered_fraction"] for r in rows])
        res["dist_to_opt_cend_mean"] = {n: mean([r["dist_to_opt_cend"][n] for r in rows]) for n in names}
        res["gap_trajectory_mean"] = {k: mean([r["gap_trajectory_model_units"][k] for r in rows])
                                      for k in rows[0]["gap_trajectory_model_units"]}
    return res


def run_files(run_dir):
    d = Path(run_dir)
    out = {n: (d / n).read_bytes() for n in ("ledger.jsonl", "HEAD.json", "RUN.json")}
    for p in sorted((d / "ckpt").glob("ckpt_*.json")):
        out["ckpt/" + p.name] = p.read_bytes()
    return out


SWEEP_N = (4000, 16000, 40000)
SWEEP_R_END = (0.002, 0.005, 0.01)


def sweep(base, base_path, out, reps):
    """Run-size / gain sweep on landscape L2 and the null model. Each cell is the real config with only
    pairs_planned (and with it A, c0, a0) and every tuned parameter's r_end changed. A run directory is deleted
    after its metrics are extracted (it regenerates byte-identically from the kept config.json)."""
    import shutil
    res = {"schema": "opus3-synthqual-sweep/1", "label": "SYNTHETIC: model outcomes, no games, no Elo",
           "base_config_name": base_path.name, "landscape": "L2", "draw": DRAW, "gap_start": GAP, "cells": {}}
    for n in SWEEP_N:
        for r_end in SWEEP_R_END:
            v = json.loads(json.dumps(base))
            v["pairs_planned"] = n
            for p in v["params"]:
                if p.get("enabled", True):
                    p["r_end"] = r_end
            rows = {"L2": [], "null": []}
            for r in range(1, reps + 1):
                for group, model in (("L2", landscape_model(v, *LANDSCAPES["L2"], f"sweep-L2-{r}")),
                                     ("null", {"kind": "flat", "draw": DRAW, "seed": f"sweep-null-{r}"})):
                    tag = f"sweep_N{n}_r{r_end}_{group}_r{r}"
                    cfg = derive(v, base_path.name, f"synthqual-{tag}", model)
                    d = out / "sweep" / tag
                    write_config(d / "config.json", cfg)
                    mp = d / "metrics.json"
                    if mp.exists():
                        row = json.loads(mp.read_text(encoding="ascii"))
                    else:
                        run_to_end(d / "config.json", d / "run")
                        row = metrics(cfg, d / "run")
                        mp.write_text(json.dumps(row, indent=1) + "\n", encoding="ascii")
                        shutil.rmtree(d / "run")
                    rows[group].append(row)
            cell = {"pairs": n, "games": 2 * n, "r_end": r_end, "L2": summarize(rows["L2"]),
                    "null": summarize(rows["null"])}
            res["cells"][f"N{n}_r{r_end}"] = cell
            print(f"N={n} r_end={r_end}: L2 recovered {cell['L2']['gap_recovered_fraction_mean']:.3f}, "
                  f"null drift sd {cell['null']['drift_final_cend_sd']}", flush=True)
    (out / "sweep_summary.json").write_text(json.dumps(res, indent=1) + "\n", encoding="ascii")
    return 0


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    base_path, out = Path(argv[1]).resolve(), Path(argv[2]).resolve()
    reps = int(argv[argv.index("--reps") + 1]) if "--reps" in argv else 4
    base = json.loads(base_path.read_text(encoding="utf-8-sig"))
    if base.get("synthetic") or base.get("identity_check"):
        raise SystemExit("give the real config (no synthetic block, default identity_check)")
    out.mkdir(parents=True, exist_ok=True)
    if "--sweep" in argv:
        return sweep(base, base_path, out, reps)
    results = {"schema": "opus3-synthqual/1", "label": "SYNTHETIC: model outcomes, no games, no Elo",
               "base_config": str(base_path), "base_config_name": base_path.name,
               "model_units": "logistic/400 scale of the harness Synthetic backend (model only, not engine Elo)",
               "draw": DRAW, "gap_start": GAP, "runs": {}, "groups": {}}
    jobs = []
    for name, (dist, signs) in LANDSCAPES.items():
        for r in range(1, reps + 1):
            jobs.append((name, f"{name}_r{r}", landscape_model(base, dist, signs, f"synthqual-{name}-{r}")))
    for r in range(1, reps + 1):
        jobs.append(("null", f"null_r{r}", {"kind": "flat", "draw": DRAW, "seed": f"synthqual-null-{r}"}))
    for group, tag, model in jobs:
        cfg = derive(base, base_path.name, f"synthqual-{tag}", model)
        d = out / tag
        write_config(d / "config.json", cfg)
        codes = run_to_end(d / "config.json", d / "run")
        row = metrics(cfg, d / "run")
        row["exit_codes"] = codes
        results["runs"][tag] = row
        print(f"{tag}: gap_final={row.get('gap_final_model_units', 'n/a')} drift={row['drift_final_cend']}",
              flush=True)
    for group in list(LANDSCAPES) + ["null"]:
        rows = [v for k, v in results["runs"].items() if k.startswith(group + "_r")]
        results["groups"][group] = summarize(rows)
    # resume equivalence on the real schedule: the L2_r1 copy, crashed twice, must equal the uninterrupted run
    cfg = derive(base, base_path.name, "synthqual-L2_r1", landscape_model(base, *LANDSCAPES["L2"], "synthqual-L2-1"))
    d = out / "resume_L2_r1"
    write_config(d / "config.json", cfg)
    if (d / "config.json").read_bytes() != (out / "L2_r1" / "config.json").read_bytes():
        raise SystemExit("resume copy differs from L2_r1's config")
    crashes = ("B3@300:2", "B5@700")
    if (d / "run").exists():  # the check must exercise both crashes: always start from an empty run directory
        import shutil
        shutil.rmtree(d / "run")
    codes = run_to_end(d / "config.json", d / "run", crashes)
    a, b = run_files(out / "L2_r1" / "run"), run_files(d / "run")
    diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    crashed = codes[:len(crashes)] == [77] * len(crashes) and codes[len(crashes)] == 0
    results["resume_check"] = {"crashes": list(crashes), "exit_codes": codes, "both_crashes_fired": crashed,
                               "files_compared": len(a), "files_differing": diff,
                               "identical": crashed and not diff and len(a) == len(b)}
    print(f"resume_check: identical={results['resume_check']['identical']} files={len(a)} codes={codes}", flush=True)
    (out / "summary.json").write_text(json.dumps(results, indent=1) + "\n", encoding="ascii")
    print(json.dumps({"groups": results["groups"], "resume_check": results["resume_check"]}, indent=1))
    return 0 if results["resume_check"]["identical"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
