"""Tests of the opus3_spsa harness: synthetic outcomes and saved/generated PGN replay only (no engine, no games).
usage: python -I -B test_spsa_harness.py <scratch dir> [<results.json>]     exit 0 = all PASS
Synthetic strengths are in synthetic units; nothing here is an Elo measurement."""
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "spsa"))
import harness_util as h  # noqa: E402
from ledger import canon, sha256_bytes  # noqa: E402

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append({"test": name, "pass": bool(ok), "detail": detail})
    print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}", flush=True)
    return ok


def fresh(base, name):
    d = Path(base) / name
    h.rmtree(d)
    d.mkdir(parents=True)
    return d


def ledger(run_dir):
    return [json.loads(x) for x in (Path(run_dir) / "ledger.jsonl").read_text(encoding="ascii").splitlines() if x]


def final_theta(run_dir):
    recs = ledger(run_dir)
    names = [r for r in recs if r["type"] == "init"][0]["names"]
    ups = [r for r in recs if r["type"] == "update"]
    return dict(zip(names, ups[-1]["update"]["theta_after"]))


# --- synthetic movement and constraints --------------------------------------------------------------------------
def t_movement(base):
    d = fresh(base, "movement")
    env = h.make_env(d / "env")
    cfg = h.make_config(env, pairs_planned=800)
    for p in cfg["params"]:
        p["r_end"] = 0.01
    c = h.write_config(d / "cfg.json", cfg)
    rc, out, err = h.cli("run", c, d / "run", "--mode", "synthetic")
    th = final_theta(d / "run")
    opt = cfg["synthetic"]["opt"]
    ok = rc == 0
    det = []
    for n, start in (("RazorBase", 150), ("RazorMultiplier", 350), ("QsFutilityMargin", 160)):
        moved = (th[n] - start) / (opt[n] - start)
        det.append(f"{n} {start}->{th[n]:.1f} (opt {opt[n]:.0f}, {100 * moved:.0f}% of the way)")
        ok &= moved >= 0.25
    check("synthetic: every parameter moves toward a known interior optimum (>=25% of the distance)", ok,
          "; ".join(det) + f"; rc {rc}")
    viol = [r for r in ledger(d / "run") if r["type"] == "plan" and r["plan"]["violations"]]
    check("synthetic: no plus/minus engine value violates a bound or C1/C3", not viol, f"{len(viol)} violating plans")


def t_null(base):
    d = fresh(base, "null_at_opt")
    env = h.make_env(d / "env")
    cfg = h.make_config(env, pairs_planned=800)
    cfg["synthetic"]["opt"] = {"RazorBase": 150.0, "RazorMultiplier": 350.0, "QsFutilityMargin": 160.0}
    for p in cfg["params"]:
        p["r_end"] = 0.01
    c = h.write_config(d / "cfg.json", cfg)
    rc, _, _ = h.cli("run", c, d / "run", "--mode", "synthetic")
    th = final_theta(d / "run")
    ok = rc == 0 and abs(th["RazorBase"] - 150) < 3 * 15 and abs(th["RazorMultiplier"] - 350) < 3 * 35 and \
        abs(th["QsFutilityMargin"] - 160) < 3 * 16
    check("synthetic: a run started at the optimum stays within 3 c_end", ok,
          ", ".join(f"{k} {v:.1f}" for k, v in th.items()))


def t_interaction(base):
    """Cross term between RazorBase and QsFutilityMargin: the joint optimum (250, 120) differs from the coordinate-
    wise optimum of QsFutilityMargin with RazorBase held at 150 (120 - 60*rho/2 = 72). Joint SPSA must head for the
    joint optimum; tuning QsFutilityMargin alone ends near the coordinate-wise optimum."""
    rho = 1.6
    res = {}
    for label, enabled in (("joint", None), ("qs_only", {"QsFutilityMargin"})):
        d = fresh(base, f"interaction_{label}")
        env = h.make_env(d / "env")
        cfg = h.make_config(env, pairs_planned=1600)
        cfg["synthetic"]["cross"] = [["RazorBase", "QsFutilityMargin", rho]]
        for p in cfg["params"]:
            p["r_end"] = 0.01
            if enabled is not None and p["name"] in ("RazorBase", "RazorMultiplier"):
                p["enabled"] = False
        c = h.write_config(d / "cfg.json", cfg)
        rc, _, err = h.cli("run", c, d / "run", "--mode", "synthetic")
        res[label] = (rc, final_theta(d / "run"))
    joint, alone = res["joint"][1], res["qs_only"][1]
    cond = 120 - 60 * rho / 2
    ok = res["joint"][0] == 0 and res["qs_only"][0] == 0 and \
        abs(joint["QsFutilityMargin"] - 120) < abs(joint["QsFutilityMargin"] - cond) and \
        abs(alone["QsFutilityMargin"] - cond) < abs(alone["QsFutilityMargin"] - 120) and joint["RazorBase"] > 175
    check("synthetic interaction: joint tuning heads for the joint optimum, one-family tuning does not", ok,
          f"joint QsFutilityMargin {joint['QsFutilityMargin']:.1f} RazorBase {joint['RazorBase']:.1f} (joint opt 120/250); "
          f"QsFutilityMargin alone {alone['QsFutilityMargin']:.1f} (coordinate-wise opt {cond:.0f})")


def t_constrained(base):
    """Optimum outside C1 (QsFutilityMargin 380 > RazorBase 60 + RazorMultiplier 150): the run must stay feasible and
    end on the C1 boundary."""
    d = fresh(base, "constrained")
    env = h.make_env(d / "env")
    cfg = h.make_config(env, pairs_planned=1600)
    cfg["synthetic"]["opt"] = {"RazorBase": 60.0, "RazorMultiplier": 150.0, "QsFutilityMargin": 380.0}
    for p in cfg["params"]:
        p["r_end"] = 0.01
    c = h.write_config(d / "cfg.json", cfg)
    rc, out, _ = h.cli("run", c, d / "run", "--mode", "synthetic")
    recs = ledger(d / "run")
    plans = [r for r in recs if r["type"] == "plan"]
    ups = [r for r in recs if r["type"] == "update"]
    viol = [r["batch"] for r in plans if r["plan"]["violations"]]
    infeas = [r["batch"] for r in ups if not r["update"]["feasible"]]
    moved = sum(1 for r in plans if r["plan"]["theta_moved"])
    th = final_theta(d / "run")
    gap = th["RazorBase"] + th["RazorMultiplier"] - th["QsFutilityMargin"]
    active = ups[-1]["update"]["active"]
    ok = rc == 0 and not viol and not infeas and "C1" in active and gap >= -1e-6
    check("synthetic constrained optimum: every plus/minus/theta feasible, run ends on the C1 boundary", ok,
          f"violating plans {len(viol)}, infeasible updates {len(infeas)}, inner projections {moved}, "
          f"final RB+RM-QFM = {gap:.1f}, active {active}")


def t_levels(base):
    d = fresh(base, "levels")
    env = h.make_env(d / "env")
    cfg = h.make_config(env, pairs_planned=800)
    for p in cfg["params"]:
        p["r_end"] = 0.01
        if p["kind"] == "level":
            p["enabled"] = True
    for cst in cfg["constraints"]:
        cst["enabled"] = True
    cfg["synthetic"]["opt"].update({"QsSeeMargin": 140.0, "RazorDepth": 2.0})
    cfg["synthetic"]["scale"].update({"QsSeeMargin": 60.0, "RazorDepth": 0.7})
    cfg["constraints"][2]["coef"] = {"RazorBase": 1, "RazorMultiplier": 3}  # C3 with RazorDepth's highest level
    c = h.write_config(d / "cfg.json", cfg)
    rc, _, err = h.cli("run", c, d / "run", "--mode", "synthetic")
    plans = [r["plan"] for r in ledger(d / "run") if r["type"] == "plan"]
    vals_ok = all(p[s]["QsSeeMargin"] in (40, 140, 240) and p[s]["RazorDepth"] in (1, 2, 3) for p in plans
                  for s in ("plus", "minus"))
    viol = sum(1 for p in plans if p["violations"])
    eff = sum(p["eff"][3] for p in plans) if plans else 0
    check("synthetic levels: QsSeeMargin/RazorDepth only take their levels, C1-C3 hold, level coordinates carry updates",
          rc == 0 and vals_ok and viol == 0 and eff > 0, f"rc {rc}, plans {len(plans)}, violating {viol}, "
          f"batches with a QsSeeMargin level difference {eff}; {err[-200:]}")


# --- crash at every boundary -------------------------------------------------------------------------------------
BOUNDARIES = ["B0@0", "B1@0", "I6@0", "I7@0", "B2@3", "P6@3", "P7@3", "B3@3:1", "B3@3:3", "B4@3", "B5@3",
              "B6@3", "B7@3", "B8@3", "BC@10", "C6@10", "C7@10"]


def t_crash(base):
    d = fresh(base, "crash")
    env = h.make_env(d / "env")
    cfg = h.make_config(env, pairs_planned=40)
    c = h.write_config(d / "cfg.json", cfg)
    rc, _, _ = h.cli("run", c, d / "ref", "--mode", "synthetic")
    ref = h.run_files(d / "ref")
    check("crash reference: uninterrupted synthetic run of 10 batches", rc == 0 and len(ref) > 20,
          f"{len(ref)} state files")
    for b in BOUNDARIES:
        rd = d / ("run_" + b.replace("@", "_").replace(":", "_"))
        rc1, _, _ = h.cli("run", c, rd, "--mode", "synthetic", crash=b)
        rc2, _, err = h.cli("run", c, rd, "--mode", "synthetic", "--resume")
        rcv, _, _ = h.cli("verify", rd)
        same = h.run_files(rd) == ref if rc2 == 0 else False
        check(f"crash at {b}: crashed (77), resumed, state byte-identical to the uninterrupted run, verify OK",
              rc1 == 77 and rc2 == 0 and same and rcv == 0, f"rc {rc1}/{rc2}/{rcv} {err[-160:]}")
    rd = d / "run_double"
    a, _, _ = h.cli("run", c, rd, "--mode", "synthetic", crash="B3@2:2")
    b2, _, _ = h.cli("run", c, rd, "--mode", "synthetic", "--resume", crash="B6@5")
    c3, _, _ = h.cli("run", c, rd, "--mode", "synthetic", "--resume")
    check("double crash (B3@2:2 then B6@5): byte-identical after the second resume",
          (a, b2, c3) == (77, 77, 0) and h.run_files(rd) == ref, f"rc {a}/{b2}/{c3}")
    rd = d / "run_torn"
    h.cli("run", c, rd, "--mode", "synthetic", "--max-batches", "5")
    with open(rd / "ledger.jsonl", "ab") as f:
        f.write(b'{"v":1,"seq":51,"type":"pai')
    rc, out, _ = h.cli("run", c, rd, "--mode", "synthetic", "--resume")
    torn = list(rd.glob("ledger.torn.*.bin"))
    check("torn ledger tail (cut-off write): quarantined to ledger.torn.0.bin, run completes byte-identical",
          rc == 0 and len(torn) == 1 and h.run_files(rd) == ref, f"rc {rc}, torn files {len(torn)}")


# --- refusals ------------------------------------------------------------------------------------------------------
def partial(base, name, batches=4, **over):
    d = fresh(base, name)
    env = h.make_env(d / "env")
    cfg = h.make_config(env, pairs_planned=40, **over)
    c = h.write_config(d / "cfg.json", cfg)
    h.cli("run", c, d / "run", "--mode", "synthetic", "--max-batches", str(batches))
    return d, env, cfg, c


def rewrite_record(run_dir, idx, mutate):
    """Change ledger record idx and re-hash the chain from there on (a careful forger)."""
    recs = ledger(run_dir)
    mutate(recs[idx])
    prev = recs[idx - 1]["h"] if idx else "genesis"
    for r in recs[idx:]:
        r["prev"] = prev
        body = {k: v for k, v in r.items() if k != "h"}
        r["h"] = sha256_bytes(canon(body))
        prev = r["h"]
    (Path(run_dir) / "ledger.jsonl").write_bytes(b"".join(canon(r) + b"\n" for r in recs))


def t_refusals(base):
    d, env, cfg, c = partial(base, "ref_identity")
    env["exe"].write_bytes(b"changed engine")
    rc, _, err = h.cli("run", c, d / "run", "--mode", "synthetic", "--resume")
    check("refuse a changed pinned exe on resume (exit 20)", rc == 20, err.strip()[-160:])

    d, env, cfg, c = partial(base, "ref_config")
    cfg["params"][0]["c_end"] = 16
    h.write_config(c, cfg)
    rc, _, err = h.cli("run", c, d / "run", "--mode", "synthetic", "--resume")
    check("refuse a changed config on resume (exit 11)", rc == 11, err.strip()[-160:])

    d, env, cfg, c = partial(base, "ref_mode")
    rc, _, err = h.cli("run", c, d / "run", "--mode", "replay", "--resume")
    check("refuse resuming in another mode (exit 11)", rc == 11, err.strip()[-160:])

    d, env, cfg, c = partial(base, "ref_ckpt")
    head = json.loads((d / "run" / "HEAD.json").read_text())
    p = d / "run" / "ckpt" / f"ckpt_{head['seq']:06d}.json"
    data = bytearray(p.read_bytes())
    data[data.index(b'"k":') + 4] ^= 1
    p.write_bytes(bytes(data))
    rc, _, err = h.cli("run", c, d / "run", "--mode", "synthetic", "--resume")
    check("refuse a corrupted HEAD checkpoint (exit 30)", rc == 30, err.strip()[-160:])

    d, env, cfg, c = partial(base, "ref_old_ckpt")
    p = d / "run" / "ckpt" / "ckpt_000002.json"
    p.write_bytes(p.read_bytes().replace(b'"k":4', b'"k":5'))
    rcv, _, err = h.cli("verify", d / "run")
    check("verify refuses a tampered older checkpoint (exit 30)", rcv == 30, err.strip()[-160:])

    d, env, cfg, c = partial(base, "ref_head_missing")
    (d / "run" / "HEAD.json").unlink()
    rc, _, err = h.cli("run", c, d / "run", "--mode", "synthetic", "--resume")
    check("refuse a missing HEAD while several checkpoints exist (exit 30)", rc == 30, err.strip()[-160:])

    d, env, cfg, c = partial(base, "ref_far_ckpt")
    (d / "run" / "ckpt" / "ckpt_000099.json").write_bytes((d / "run" / "ckpt" / "ckpt_000001.json").read_bytes())
    rc, _, err = h.cli("run", c, d / "run", "--mode", "synthetic", "--resume")
    check("refuse a checkpoint more than one step past HEAD (exit 30)", rc == 30, err.strip()[-160:])

    d, env, cfg, c = partial(base, "ref_ledger_mid")
    lines = (d / "run" / "ledger.jsonl").read_bytes().split(b"\n")
    lines[5] = lines[5].replace(b'"W":', b'"W" :')
    (d / "run" / "ledger.jsonl").write_bytes(b"\n".join(lines))
    rc, _, err = h.cli("run", c, d / "run", "--mode", "synthetic", "--resume")
    check("refuse a malformed record inside the ledger (exit 30)", rc == 30, err.strip()[-160:])

    d, env, cfg, c = partial(base, "ref_forged_score")
    idx = next(i for i, r in enumerate(ledger(d / "run")) if r["type"] == "pair")
    rewrite_record(d / "run", idx, lambda r: r.update(W=r["W"] + 1))
    rc, _, err = h.cli("run", c, d / "run", "--mode", "synthetic", "--resume")
    check("refuse a re-hashed pair record whose score does not match its games (exit 31)", rc == 31,
          err.strip()[-160:])

    d, env, cfg, c = partial(base, "ref_forged_update")
    idx = next(i for i, r in enumerate(ledger(d / "run")) if r["type"] == "update")
    rewrite_record(d / "run", idx, lambda r: r["update"]["theta_after"].__setitem__(0, 999.0))
    rc, _, err = h.cli("run", c, d / "run", "--mode", "synthetic", "--resume")
    check("refuse a re-hashed update that its pairs do not reproduce (exit 30)", rc == 30, err.strip()[-160:])

    d, env, cfg, c = partial(base, "ref_duplicate")
    recs = ledger(d / "run")
    h.cli("run", c, d / "run", "--mode", "synthetic", "--resume", crash="B3@4:2")
    recs = ledger(d / "run")
    dup = dict(recs[-1])
    dup.pop("h")
    dup["seq"], dup["prev"] = len(recs), recs[-1]["h"]
    dup["h"] = sha256_bytes(canon(dup))
    with open(d / "run" / "ledger.jsonl", "ab") as f:
        f.write(canon(dup) + b"\n")
    rc, _, err = h.cli("run", c, d / "run", "--mode", "synthetic", "--resume")
    check("refuse a pair recorded twice (duplicate result, exit 31)", rc == 31, err.strip()[-160:])

    d, env, cfg, c = partial(base, "ref_unknown_pair")
    h.cli("run", c, d / "run", "--mode", "synthetic", "--resume", crash="B3@4:1")
    recs = ledger(d / "run")
    bad = dict(recs[-1])
    bad.pop("h")
    bad["pair_id"] = bad["pair_id"].replace("/p000", "/p777")
    bad["seq"], bad["prev"] = len(recs), recs[-1]["h"]
    bad["h"] = sha256_bytes(canon(bad))
    with open(d / "run" / "ledger.jsonl", "ab") as f:
        f.write(canon(bad) + b"\n")
    rc, _, err = h.cli("run", c, d / "run", "--mode", "synthetic", "--resume")
    check("refuse a result for a pair that was never planned (exit 31)", rc == 31, err.strip()[-160:])

    d, env, cfg, c = partial(base, "ref_stale_ledger", run_nonce="1")
    other = fresh(base, "ref_stale_other")
    env2 = h.make_env(other / "env")
    cfg2 = h.make_config(env2, pairs_planned=40)
    cfg2["identity"] = cfg["identity"]
    cfg2["openings"] = cfg["openings"]
    c2 = h.write_config(other / "cfg.json", cfg2)
    h.cli("run", c2, other / "run", "--mode", "synthetic", "--max-batches", "4")
    with open(d / "run" / "ledger.jsonl", "ab") as f:
        f.write((other / "run" / "ledger.jsonl").read_bytes().split(b"\n")[6] + b"\n")
    rc, _, err = h.cli("run", c, d / "run", "--mode", "synthetic", "--resume")
    check("refuse a ledger record of another run (stale, exit 30/31)", rc in (30, 31), err.strip()[-160:])

    d = fresh(base, "ref_holdout")
    env = h.make_env(d / "env")
    cfg = h.make_config(env)
    cfg["openings"]["forbidden_sha256"].append(cfg["identity"]["openings"]["sha256"])
    c = h.write_config(d / "cfg.json", cfg)
    rc, _, err = h.cli("run", c, d / "run", "--mode", "synthetic")
    rc2, _, _ = h.cli("run", c, d / "run")
    check("refuse an openings file listed as holdout/screen (exit 41, also in dry-run)",
          rc == 41 and rc2 == 41 and not (d / "run").exists(), err.strip()[-160:])

    d = fresh(base, "ref_live")
    env = h.make_env(d / "env")
    cfg = h.make_config(env)
    c = h.write_config(d / "cfg.json", cfg)
    r1, _, e1 = h.cli("run", c, d / "run", "--mode", "live")
    r2, _, e2 = h.cli("run", c, d / "run", "--mode", "live", "--live")
    cfg["live"]["enabled"] = True
    h.write_config(c, cfg)
    r3, _, e3 = h.cli("run", c, d / "run", "--mode", "live", "--live")
    check("live mode refused without --live, without config.live.enabled, without LIVE_ACK (exit 40 x3)",
          (r1, r2, r3) == (40, 40, 40) and not (d / "run").exists(), f"{e3.strip()[-140:]}")


def t_dryrun(base):
    d = fresh(base, "dryrun")
    env = h.make_env(d / "env")
    c = h.write_config(d / "cfg.json", h.make_config(env))
    import opus3_spsa as m

    def boom(*a, **k):
        raise AssertionError("dry-run started a process")
    saved = (m.subprocess.call, m.subprocess.Popen, m.subprocess.run)
    m.subprocess.call = m.subprocess.Popen = m.subprocess.run = boom
    try:
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = m.main(["opus3_spsa.py", "run", str(c), str(d / "run")])
        out = json.loads(buf.getvalue())
    finally:
        m.subprocess.call, m.subprocess.Popen, m.subprocess.run = saved
    check("dry-run (the default mode) starts no process and writes nothing; prints the fastchess command",
          rc == 0 and not (d / "run").exists() and "fastchess" in out["fastchess_command"] and
          out["started_processes"] == 0, f"rc {rc}, batch {out.get('batch')}")


# --- replay ------------------------------------------------------------------------------------------------------
def pgn_game(rnd, white, black, result, term="normal"):
    return (f'[Event "Fastchess Tournament"]\n[Site "?"]\n[Round "{rnd}"]\n[White "{white}"]\n[Black "{black}"]\n'
            f'[Result "{result}"]\n[Termination "{term}"]\n\n1. e4 e5 {result}\n\n')


def replay_setup(base, name, pgns, pairs_per_batch=4, planned=None, run_id_override=None):
    d = fresh(base, name)
    env = h.make_env(d / "env")
    cfg = h.make_config(env, pairs_planned=planned or pairs_per_batch * len(pgns), pairs_per_batch=pairs_per_batch)
    sys.path.insert(0, str(HERE.parent / "spsa"))
    import opus3_spsa as m
    run_id = run_id_override or m.run_id_of(cfg)
    rep = d / "replay"
    rep.mkdir()
    ents = []
    for b, text in enumerate(pgns):
        p = rep / f"batch{b:03d}.pgn"
        p.write_bytes(text if isinstance(text, bytes) else text.encode("ascii"))
        ents.append({"batch": b, "pgn": p.name, "sha256": h.sha(p)})
    man = {"schema": "opus3-replay/1", "run_id": run_id, "core_config_sha256": m.core_config_sha(cfg),
           "plus_name": "plus", "minus_name": "minus", "batches": ents}
    mp = rep / "manifest.json"
    mp.write_text(json.dumps(man, indent=1), encoding="ascii")
    cfg["replay"] = {"manifest": str(mp), "manifest_sha256": h.sha(mp)}
    c = h.write_config(d / "cfg.json", cfg)
    return d, c, cfg


def t_replay(base):
    smoke = (HERE / "fixtures" / "pgn" / "r9_fastchess_smoke_2games.pgn").read_bytes()
    d, c, cfg = replay_setup(base, "replay_r9_smoke", [smoke], pairs_per_batch=1)
    rc, out, err = h.cli("run", c, d / "run", "--mode", "replay")
    pr = [r for r in ledger(d / "run") if r["type"] == "pair"]
    ok = rc == 0 and len(pr) == 1 and (pr[0]["W"], pr[0]["L"], pr[0]["D"]) == (0, 0, 2) and \
        pr[0]["source"]["pgn_sha256"] == sha256_bytes(smoke)
    check("replay of R9's saved fastchess smoke PGN (2 games = 1 pair, both drawn)", ok, f"rc {rc} {err[-160:]}")

    # synthetic -> PGN -> replay must give the same trajectory (same pairs, colours and results)
    s = fresh(base, "replay_equiv_src")
    env = h.make_env(s / "env")
    scfg = h.make_config(env, pairs_planned=24)
    sc = h.write_config(s / "cfg.json", scfg)
    h.cli("run", sc, s / "run", "--mode", "synthetic")
    recs = ledger(s / "run")
    pgns = []
    for b in range(6):
        text = ""
        for r in [r for r in recs if r["type"] == "pair" and r["batch"] == b]:
            for g in r["games"]:
                w, bl = ("plus", "minus") if g["white"] == "plus" else ("minus", "plus")
                text += pgn_game(r["j"] + 1, w, bl, g["result"])
        pgns.append(text)
    d, c, cfg = replay_setup(base, "replay_equiv", pgns, planned=24)
    # same params/seed/openings as the synthetic run; only identity paths differ
    rc, out, err = h.cli("run", c, d / "run", "--mode", "replay")
    a = [r["update"]["theta_after"] for r in recs if r["type"] == "update"]
    b2 = [r["update"]["theta_after"] for r in ledger(d / "run") if r["type"] == "update"]
    check("replay of PGNs written from a synthetic run reproduces its theta trajectory exactly",
          rc == 0 and a == b2 and len(a) == 6, f"rc {rc}, {len(b2)} updates {err[-120:]}")

    good = "".join(pgn_game(j, *(("plus", "minus") if g == 0 else ("minus", "plus")), "1/2-1/2")
                   for j in range(1, 5) for g in range(2))
    cases = {
        "incomplete pair (round 2 has one game)": good.replace(pgn_game(2, "minus", "plus", "1/2-1/2"), ""),
        "duplicate result (round 1 has three games)": good + pgn_game(1, "plus", "minus", "1-0"),
        "foreign engine name": good.replace('[White "plus"]', '[White "other"]', 1),
        "unfinished game (result *)": good.replace('[Result "1/2-1/2"]', '[Result "*"]', 1),
        "round outside the planned pairs": good + pgn_game(9, "plus", "minus", "1-0") + pgn_game(9, "minus", "plus", "1-0"),
    }
    for label, text in cases.items():
        d, c, cfg = replay_setup(base, "replay_bad_" + str(abs(hash(label)) % 10000), [text], planned=4)
        rc, _, err = h.cli("run", c, d / "run", "--mode", "replay")
        check(f"replay refuses {label} (exit 31)", rc == 31, err.strip()[-150:])
    d, c, cfg = replay_setup(base, "replay_stale", [good], planned=4, run_id_override="other:0:000000000000")
    rc, _, err = h.cli("run", c, d / "run", "--mode", "replay")
    check("replay refuses a manifest of another run (stale, exit 31)", rc == 31, err.strip()[-150:])
    d, c, cfg = replay_setup(base, "replay_truncated", [good], planned=4)
    p = d / "replay" / "batch000.pgn"
    p.write_bytes(p.read_bytes()[:-40])
    rc, _, err = h.cli("run", c, d / "run", "--mode", "replay")
    check("replay refuses a truncated PGN (sha256 differs from the manifest, exit 20)", rc == 20, err.strip()[-150:])


# --- rollback and export -------------------------------------------------------------------------------------------
def t_rollback(base):
    d, env, cfg, c = partial(base, "rollback", batches=6)
    obj = json.loads((d / "run" / "ckpt" / "ckpt_000005.json").read_text())
    rc, out, err = h.cli("rollback", d / "run", "--to-ckpt", "5")
    rcv, vout, _ = h.cli("verify", d / "run")
    st = json.loads(vout)["state"] if rcv == 0 else {}
    ok = rc == 0 and rcv == 0 and list(st.get("theta", {}).values()) == obj["theta"] and st.get("k") == obj["k"]
    check("rollback --to-ckpt 5 restores theta and k of checkpoint 5 as a new logged checkpoint; verify OK", ok,
          f"rc {rc}/{rcv} {err[-120:]}")
    rc2, _, _ = h.cli("run", c, d / "run", "--mode", "synthetic", "--resume", "--max-batches", "2")
    rcv2, _, _ = h.cli("verify", d / "run")
    check("a rolled-back run resumes and still verifies", rc2 == 0 and rcv2 == 0, f"rc {rc2}/{rcv2}")
    before = sorted(p.name for p in d.rglob("*"))
    rc3, out3, _ = h.cli("rollback", c, "--baseline")
    after = sorted(p.name for p in d.rglob("*"))
    base_line = json.loads(out3)
    check("rollback --baseline prints the lock values and writes nothing",
          rc3 == 0 and before == after and base_line["baseline_values"]["RazorBase"] == 150, out3.strip()[-160:])
    rc4, out4, _ = h.cli("export", d / "run", "--out", d / "export")
    cand = json.loads((d / "export" / "candidate.json").read_text()) if rc4 == 0 else {}
    check("export writes history.csv and candidate.json from the ledger", rc4 == 0 and "values" in cand and
          (d / "export" / "history.csv").exists(), f"rc {rc4}")


def main():
    base = Path(sys.argv[1])
    base.mkdir(parents=True, exist_ok=True)
    for t in (t_movement, t_null, t_interaction, t_constrained, t_levels, t_crash, t_refusals, t_dryrun, t_replay,
              t_rollback):
        try:
            t(base)
        except Exception as e:  # a crashing test is a failing test
            check(f"{t.__name__} raised", False, repr(e)[-300:])
    ok = all(r["pass"] for r in RESULTS)
    print(f"{sum(r['pass'] for r in RESULTS)}/{len(RESULTS)} PASS; " + ("HARNESS TESTS OK" if ok else "HARNESS TESTS FAILED"))
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(json.dumps({"results": RESULTS, "ok": ok}, indent=1), encoding="ascii")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
