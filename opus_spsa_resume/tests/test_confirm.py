"""Tests of the independent confirmation pack (synthetic outcomes and generated PGNs only; no engine, no games).
usage: python -I -B test_confirm.py <scratch dir> [<results.json>]      exit 0 = all PASS
Synthetic outcomes come from models with a known true effect; nothing here measures Elo."""
import json
import math
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "confirm"))
import harness_util as h  # noqa: E402
import confirm_runner as cr  # noqa: E402

RUNNER = HERE.parent / "confirm" / "confirm_runner.py"
SELECT = HERE.parent / "confirm" / "select_candidate.py"
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append({"test": name, "pass": bool(ok), "detail": detail})
    print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}", flush=True)


def call(script, *args, crash=None):
    import os
    env = dict(os.environ)
    env.pop("OPUS3_CONFIRM_CRASH", None)
    if crash:
        env["OPUS3_CONFIRM_CRASH"] = crash
    p = subprocess.run([sys.executable, "-I", "-B", str(script)] + [str(a) for a in args], capture_output=True,
                       text=True, env=env, timeout=900)
    return p.returncode, p.stdout, p.stderr


# --- in-process statistics -------------------------------------------------------------------------------------------
PROTO_SPRT = {"nelo0": 0.0, "nelo1": 5.0, "alpha": 0.05, "beta": 0.05, "cap_games": 5000}


def sim_confirm(true_nelo, seed, draw=0.6):
    """One sequential confirmation with outcomes from a known model; returns the verdict."""
    rng = random.Random(seed)
    sd_g = math.sqrt((1 - draw) / 4)
    mu = 0.5 + true_nelo * math.log(10) / 800 * sd_g
    pw, pl = mu - draw / 2, 1 - mu - draw / 2
    pen = [0, 0, 0, 0, 0]
    proto = {"sprt": PROTO_SPRT}
    for j in range(PROTO_SPRT["cap_games"] // 2):
        pts = 0.0
        for _ in range(2):
            x = rng.random()
            pts += 1.0 if x < pw else (0.0 if x < pw + pl else 0.5)
        pen[int(round(pts / 2 * 4))] += 1
        v = cr.decide(cr.gsprt(pen, 0.0, 5.0), proto, 2 * (j + 1))
        if v:
            return v
    return "cap, no decision (no claim)"


def t_controls():
    R = 300
    aa = [sim_confirm(0.0, f"aa:{i}") for i in range(R)]
    fp = sum(v == "H1 accepted" for v in aa) / R
    tol = 0.05 + 3 * math.sqrt(0.05 * 0.95 / R)
    check("negative control A/A (true nElo 0): H1 accepted at most alpha + 3 sigma", fp <= tol,
          f"{fp:.3f} of {R} runs (bound {tol:.3f}); H0 {sum(v == 'H0 accepted' for v in aa)}, "
          f"cap {sum(v.startswith('cap') for v in aa)} [SYNTHETIC]")
    pos = [sim_confirm(25.0, f"pos:{i}") for i in range(R)]
    pw = sum(v == "H1 accepted" for v in pos) / R
    check("positive control (true nElo 25; the 5000-game cap leaves little power below ~20): H1 accepted in >= 80%",
          pw >= 0.80, f"{pw:.3f} of {R} runs [SYNTHETIC]")
    # fake optimizer: K candidates of equal true strength; 'training' picks the luckiest; confirmation on fresh seeds
    K, n_train, apparent, accepted = 20, 200, [], 0
    for i in range(R):
        rng = random.Random(f"fake:{i}")
        best = max(sum(rng.choice((0.0, 0.25, 0.5, 0.5, 0.5, 0.75, 1.0)) for _ in range(n_train)) / n_train
                   for _ in range(K))
        apparent.append(best - 0.5)
        accepted += sim_confirm(0.0, f"fakeconf:{i}") == "H1 accepted"
    rate = accepted / R
    check("fake optimizer (best of 20 equal candidates looks good in training) fails confirmation: "
          "H1 at most alpha + 3 sigma", rate <= tol,
          f"mean apparent training edge +{sum(apparent) / R:.3f} pair score, confirmation H1 rate {rate:.3f} "
          f"(bound {tol:.3f}) [SYNTHETIC]")


# --- CLI-level -------------------------------------------------------------------------------------------------------
def setup(base, name, true_nelo=10.0, holdout_tag="G1"):
    d = Path(base) / name
    h.rmtree(d)
    d.mkdir(parents=True)
    env = h.make_env(d / "env")
    tcfg = h.make_config(env, pairs_planned=24)
    tc = h.write_config(d / "train_cfg.json", tcfg)
    rc, _, err = h.cli("run", tc, d / "train", "--mode", "synthetic")
    if rc != 0:
        raise RuntimeError(f"training run failed: {err[-300:]}")
    hold = d / "env" / f"holdout_{holdout_tag}.pgn"
    hold.write_text("".join(f'[Event "holdout {i}"]\n[Result "*"]\n\n1. d4 d5 {i} *\n\n' for i in range(40)),
                    encoding="ascii")
    proto = {"schema": "opus3-confirm-protocol/1", "name": "test",
             "holdout": {"name": holdout_tag, "pgn_sha256": h.sha(hold)},
             "training_partitions_sha256": [h.sha(env["train"])],
             "registry": str(d / "registry.jsonl"),
             "identity": {"fastchess": {"path": str(env["fastchess"]), "sha256": h.sha(env["fastchess"])},
                          "cand_exe": {"path": str(env["exe"]), "sha256": h.sha(env["exe"])},
                          "base_exe": {"path": str(env["exe"]), "sha256": h.sha(env["exe"])},
                          "holdout": {"path": str(hold), "sha256": h.sha(hold)}},
             "sprt": dict(PROTO_SPRT, cap_games=600), "match": {"tc": "10+0.1", "concurrency": 1},
             "synthetic": {"seed": "confirm-test", "true_nelo": true_nelo, "draw": 0.6},
             "checkpoint_every": 50, "live": {"enabled": False}}
    pp = d / "protocol.json"
    pp.write_text(json.dumps(proto, indent=1), encoding="ascii")
    cand = d / "candidate.json"
    rc, out, err = call(SELECT, d / "train", cand)
    if rc != 0:
        raise RuntimeError(f"select_candidate failed: {err[-300:]}")
    return d, pp, cand, proto, env


def ledger_bytes(rd):
    return (Path(rd) / "confirm_ledger.jsonl").read_bytes()


def t_cli(base):
    d, pp, cand, proto, env = setup(base, "cli_basic")
    rc, out, _ = call(RUNNER, "run", pp, cand, d / "dry")
    check("confirm dry-run (default) writes nothing and prints the fastchess command",
          rc == 0 and not (d / "dry").exists() and "fastchess" in json.loads(out)["fastchess_command"], f"rc {rc}")
    rc, out, err = call(RUNNER, "run", pp, cand, d / "run", "--mode", "synthetic")
    o = json.loads(out) if rc == 0 else {}
    check("confirm synthetic run (true nElo 10): sequential GSPRT reaches a recorded decision, labelled SYNTHETIC",
          rc == 0 and o.get("decision_recorded") and o.get("verdict") in ("H1 accepted", "H0 accepted",
                                                                          "cap, no decision (no claim)")
          and "SYNTHETIC" in o.get("label", ""), f"verdict {o.get('verdict')}, pairs {o.get('pairs')}, LLR {o.get('llr')} {err[-120:]}")
    rcv, vout, _ = call(RUNNER, "verify", d / "run")
    check("confirm verify OK on the finished run", rcv == 0, f"rc {rcv}")
    ref = ledger_bytes(d / "run")
    for spec in ("after_meta", "after_start", "after_pair@1", "after_pair@37", "ckpt_tmp@1", "ckpt_renamed@1",
                 "after_decision"):
        dd, pp2, cand2, _, _ = setup(base, "crash_" + spec.replace("@", "_"))
        r1, _, _ = call(RUNNER, "run", pp2, cand2, dd / "run", "--mode", "synthetic", crash=spec)
        r2, _, e2 = call(RUNNER, "run", pp2, cand2, dd / "run", "--mode", "synthetic", "--resume")
        r3, _, _ = call(RUNNER, "verify", dd / "run")
        # each setup dir has its own paths, so run ids, protocol/candidate hashes and the chain hashes differ;
        # everything else (pair indices, games, scores, decision) must be identical to the uninterrupted run
        a = [json.loads(x) for x in ledger_bytes(dd / "run").splitlines()]
        b = [json.loads(x) for x in ref.splitlines()]
        strip = lambda r: {k: v for k, v in r.items()
                           if k not in ("run_id", "h", "prev", "candidate_sha256", "protocol_sha256")}
        same = r2 == 0 and [strip(x) for x in a] == [strip(x) for x in b]
        check(f"confirm crash at {spec}: resumed run records the same pairs and decision exactly once, verify OK",
              r1 == 77 and same and r3 == 0, f"rc {r1}/{r2}/{r3} {e2[-120:]}")
    # holdout misuse
    rc, _, err = call(RUNNER, "run", pp, cand, d / "run_again", "--mode", "synthetic")
    check("refuse a second confirmation run on a used holdout group (exit 41)", rc == 41, err.strip()[-150:])
    c2 = json.loads(cand.read_text())
    c2["training_openings_sha256"] = [proto["holdout"]["pgn_sha256"]]
    body = {k: v for k, v in c2.items() if k != "spec_sha256"}
    c2["spec_sha256"] = cr.h(cr.cj(body))
    pk = d / "peeking_candidate.json"
    pk.write_text(json.dumps(c2), encoding="ascii")
    rc, _, err = call(RUNNER, "run", pp, pk, d / "peek", "--mode", "synthetic")
    check("refuse a peeking optimizer whose training read the holdout group (exit 41)", rc == 41, err.strip()[-150:])
    c3 = json.loads(cand.read_text())
    c3["values"]["RazorBase"] += 1
    t3 = d / "tampered_candidate.json"
    t3.write_text(json.dumps(c3), encoding="ascii")
    rc, _, err = call(RUNNER, "run", pp, t3, d / "tamper")
    check("refuse a candidate spec whose content does not match its spec_sha256 (exit 10)", rc == 10, err.strip()[-150:])
    # identity / protocol changes
    dd, pp4, cand4, proto4, env4 = setup(base, "changes")
    call(RUNNER, "run", pp4, cand4, dd / "run", "--mode", "synthetic", "--max-pairs", "5")
    env4["exe"].write_bytes(b"changed candidate exe")
    rc, _, err = call(RUNNER, "run", pp4, cand4, dd / "run", "--mode", "synthetic", "--resume")
    check("refuse a changed candidate/baseline exe (exit 20)", rc == 20, err.strip()[-150:])
    dd, pp5, cand5, proto5, _ = setup(base, "proto_change")
    call(RUNNER, "run", pp5, cand5, dd / "run", "--mode", "synthetic", "--max-pairs", "5")
    proto5["sprt"]["nelo1"] = 3.0
    pp5.write_text(json.dumps(proto5, indent=1), encoding="ascii")
    rc, _, err = call(RUNNER, "run", pp5, cand5, dd / "run", "--mode", "synthetic", "--resume")
    check("refuse resuming with a changed protocol (exit 11)", rc == 11, err.strip()[-150:])
    # forged duplicate / out-of-order pair
    dd, pp6, cand6, _, _ = setup(base, "dup")
    call(RUNNER, "run", pp6, cand6, dd / "run", "--mode", "synthetic", "--max-pairs", "5")
    lines = ledger_bytes(dd / "run").splitlines()
    last = json.loads(lines[-1])
    dup = dict(last)
    dup.pop("h")
    dup["n"], dup["prev"] = last["n"] + 1, last["h"]
    dup["h"] = cr.h(cr.cj(dup))
    with open(dd / "run" / "confirm_ledger.jsonl", "ab") as f:
        f.write(cr.cj(dup) + b"\n")
    rc, _, err = call(RUNNER, "run", pp6, cand6, dd / "run", "--mode", "synthetic", "--resume")
    check("refuse a duplicated pair result (exit 31)", rc == 31, err.strip()[-150:])
    dd, pp7, cand7, _, _ = setup(base, "ckpt_corrupt")
    call(RUNNER, "run", pp7, cand7, dd / "run", "--mode", "synthetic", "--max-pairs", "60")
    head = json.loads((dd / "run" / "HEAD.json").read_text())
    cp = dd / "run" / "ckpt" / f"c_{head['seq']:06d}.json"
    cp.write_bytes(cp.read_bytes().replace(b'"seq":', b'"seq" :'))
    rc, _, err = call(RUNNER, "run", pp7, cand7, dd / "run", "--mode", "synthetic", "--resume")
    check("refuse a corrupt checkpoint (exit 30)", rc == 30, err.strip()[-150:])
    # live guards
    dd, pp8, cand8, proto8, _ = setup(base, "live")
    r1, _, _ = call(RUNNER, "run", pp8, cand8, dd / "run", "--mode", "live")
    proto8["live"]["enabled"] = True
    pp8.write_text(json.dumps(proto8, indent=1), encoding="ascii")
    r2, _, e2 = call(RUNNER, "run", pp8, cand8, dd / "run", "--mode", "live", "--live")
    check("confirm live mode refused without --live / config / LIVE_ACK (exit 40 x2)", (r1, r2) == (40, 40),
          e2.strip()[-120:])


def pgn_game(rnd, white, black, result, fen=None, term="normal"):
    f = f'[FEN "{fen}"]\n[SetUp "1"]\n' if fen else ""
    return (f'[Event "Fastchess Tournament"]\n[Round "{rnd}"]\n[White "{white}"]\n[Black "{black}"]\n'
            f'[Result "{result}"]\n{f}[Termination "{term}"]\n\n1. e4 {result}\n\n')


def t_replay_audit(base):
    d, pp, cand, proto, env = setup(base, "replay")
    games = ""
    pattern = [("1-0", "1/2-1/2"), ("1/2-1/2", "1/2-1/2"), ("0-1", "1-0"), ("1/2-1/2", "0-1"), ("1-0", "1-0")]
    for j in range(1, 41):
        r1, r2 = pattern[j % 5]
        games += pgn_game(j, "cand", "base", r1) + pgn_game(j, "base", "cand", r2)
    pg = d / "confirm_games.pgn"
    pg.write_text(games, encoding="ascii")
    proto["replay"] = {"pgns": [{"path": str(pg), "sha256": h.sha(pg), "first_pair": 0}]}
    pp.write_text(json.dumps(proto, indent=1), encoding="ascii")
    rc, out, err = call(RUNNER, "run", pp, cand, d / "run", "--mode", "replay")
    o = json.loads(out) if rc == 0 else {}
    check("confirm replay of a saved confirmation PGN (40 pairs) recomputes pentanomial counts and LLR; "
          "40 < min_pairs 50, so no decision", rc == 0 and o.get("pairs") == 40 and sum(o.get("penta", [])) == 40
          and o.get("verdict", "").startswith("replay exhausted"), f"rc {rc} penta {o.get('penta')} "
          f"verdict {o.get('verdict')} {err[-120:]}")
    # degenerate sample: identical pair scores must give a finite LLR and no decision before min_pairs
    pen = [0, 0, 0, 40, 0]
    st = cr.gsprt(pen, 0.0, 5.0)
    v = cr.decide(st, {"sprt": dict(PROTO_SPRT)}, 80)
    check("degenerate sample (40 identical pair scores): finite LLR, no decision before min_pairs",
          math.isfinite(st["llr"]) and v is None, f"LLR {st['llr']:.2f}, verdict {v}")
    removed = pgn_game(7, "base", "cand", pattern[7 % 5][1])
    assert removed in games
    bad = games.replace(removed, "")
    d2, pp2, cand2, proto2, _ = setup(base, "replay_incomplete")
    pg2 = d2 / "confirm_games.pgn"
    pg2.write_text(bad, encoding="ascii")
    proto2["replay"] = {"pgns": [{"path": str(pg2), "sha256": h.sha(pg2), "first_pair": 0}]}
    pp2.write_text(json.dumps(proto2, indent=1), encoding="ascii")
    rc, _, err = call(RUNNER, "run", pp2, cand2, d2 / "run", "--mode", "replay")
    check("confirm replay refuses an incomplete pair (exit 31)", rc == 31, err.strip()[-150:])
    # audit of a QA-style PGN with FEN tags and one training position leaked in
    keys = d / "train.keys"
    leak_fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq -"
    keys.write_text(leak_fen + "\n", encoding="ascii")
    qa = ""
    for j in range(1, 21):
        fen = leak_fen + " 0 2" if j == 5 else f"8/8/8/8/8/8/8/K{j % 7}k5 w - - 0 1".replace("K0", "K")
        qa += pgn_game(j, "cand_opus3", "base_combo29", "1/2-1/2", fen) + \
            pgn_game(j, "base_combo29", "cand_opus3", "1-0" if j % 2 else "0-1", fen)
    qp = d / "qa_gate.pgn"
    qp.write_text(qa, encoding="ascii")
    proto["qa_gate"] = {"cand_name": "cand_opus3", "base_name": "base_combo29"}
    proto["training_keys_files"] = [{"path": str(keys), "sha256": h.sha(keys)}]
    pp.write_text(json.dumps(proto, indent=1), encoding="ascii")
    rc, out, err = call(RUNNER, "audit-pgn", pp, cand, qp)
    o = json.loads(out) if rc == 0 else {}
    check("audit-pgn (read-only) recomputes QA's SPRT data and finds the one leaked training position",
          rc == 0 and o.get("leaked_pairs") == 1 and o["all_pairs"]["pairs"] == 20 and
          o["pairs_without_training_positions"]["pairs"] == 19, f"rc {rc} leaked {o.get('leaked_pairs')} {err[-150:]}")


def t_select(base):
    d = Path(base) / "select_incomplete"
    h.rmtree(d)
    d.mkdir(parents=True)
    env = h.make_env(d / "env")
    tc = h.write_config(d / "cfg.json", h.make_config(env, pairs_planned=40))
    h.cli("run", tc, d / "train", "--mode", "synthetic", "--max-batches", "3")
    rc, _, err = call(SELECT, d / "train", d / "cand.json")
    check("select_candidate refuses an incomplete training run (fixed rule, exit 10)", rc == 10, err.strip()[-150:])


def main():
    base = Path(sys.argv[1])
    base.mkdir(parents=True, exist_ok=True)
    for t in (t_controls, lambda: t_cli(base), lambda: t_replay_audit(base), lambda: t_select(base)):
        try:
            t()
        except Exception as e:
            check(f"{getattr(t, '__name__', 'test')} raised", False, repr(e)[-300:])
    ok = all(r["pass"] for r in RESULTS)
    print(f"{sum(r['pass'] for r in RESULTS)}/{len(RESULTS)} PASS; " + ("CONFIRM TESTS OK" if ok else "CONFIRM TESTS FAILED"))
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(json.dumps({"results": RESULTS, "ok": ok}, indent=1), encoding="ascii")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
