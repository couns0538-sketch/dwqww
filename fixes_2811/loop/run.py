"""One command for the whole loop:

    datagen -> filter + quality stats -> train -> export + load check -> SPRT -> promote/reject -> repeat

Run:     pipeline\\run.cmd                 (resumes where it stopped)
Stop:    create an empty file pipeline\\STOP   (ends cleanly; delete the file before the next start)
Config:  pipeline\\config.toml             (re-read at the start of every round)
"""
from __future__ import annotations

import argparse
import math
import re
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nnloop import datagen_sftools, datagen_uci, filterqc, match, report, trainer  # noqa: E402
from nnloop.common import (DiskLow, SingleInstance, State, keep_awake, kill_children_on_exit,  # noqa: E402
                           load_config, log, now, past_deadline, run_stage, set_log_file, stop_requested)
from nnloop.datagen_uci import StopRequested  # noqa: E402
from nnloop.engine import check_engine_loads_net  # noqa: E402
from nnloop.filterqc import tools_convert  # noqa: E402


def window_less_than_best(d: dict, r: int, kept: int, window: int):
    """(best round, its kept positions) when the training window of round r (kept positions, after the cap) holds
    FEWER positions than the window the best net was trained on; None otherwise, or when that cannot be told.
    Reads the state dict only. 2026-11-16: [train] max_window_positions gave the candidates of rounds 14 to 16 ten
    rounds (151 million kept) against the best net's thirteen (166 million), and none of them gained."""
    best = d.get("best") or {}
    b = int(best.get("round") or 0)
    rounds = d.get("rounds") or {}
    if not 0 < b < r or str(b) not in rounds:
        return None
    b_drop = set(rounds[str(b)].get("window_dropped") or [])
    b_drop |= {int(x) for x in (rounds[str(b)].get("window_missing") or {})}   # rounds its training went without
    b_kept = 0
    for x in range(max(1, b - window + 1), b + 1):
        if x not in b_drop:
            q = (((rounds.get(str(x)) or {}).get("stages") or {}).get("filter") or {}).get("out") or {}
            b_kept += int(q.get("kept", 0) or 0)
    return (b, b_kept) if 0 < kept < b_kept else None


def training_window(d: dict, r: int, window: int, cap: int):
    """(rounds in round r's training window after the cap as (round, kept, filtered path), the rounds the cap left
    out, the kept positions that stay). Reads the state dict only. The cap counts the RECORDED kept positions of every
    round in range, whether its positions file is on disk or not: 2026-11-16 (Fable's job 6), a round packed by the
    disk relief that came back into the window was left out of the training without a word, because only rounds
    whose filtered.plain exists were counted. The caller brings such a round back or names it."""
    rounds = d.get("rounds") or {}
    per_round = []
    for rr in range(max(1, r - window + 1), r + 1):
        q = ((((rounds.get(str(rr)) or {}).get("stages") or {}).get("filter") or {}).get("out") or {})
        if q.get("filtered"):
            per_round.append((rr, int(q.get("kept", 0) or 0), q["filtered"]))
    kept = sum(n for _, n, _ in per_round)
    dropped = []
    while cap and kept > cap and len(per_round) > 1:
        rr, n, _ = per_round.pop(0)
        kept -= n
        dropped.append(rr)
    return per_round, dropped, kept


def pooled_gate(d: dict, r: int, k: int, z: float = 1.96, min_own: float = 0.0):
    """Pooled-gate rule (Opus 2026-11-20, job 1 (c) of FOR_THE_USER/opus 24h.txt; tables and replay in
    tmp/opus_scratch/opus24h/): (fires, info). It pools the pentanomials of the last k gates of rounds r, r - 1, ...
    that were played against the CURRENT best net with the same time control as round r's gate, back to the first
    gate against another net or an earlier pooled promotion against this one (so after a failed confirmation of a
    pooled promotion, k new gates are needed). It fires when all k exist, the pool's lower bound (z) is above 0 Elo
    and round r's own gate is at or above min_own. Why: a single gate (4,000 games, about +/- 6.5) cannot see the +3 to
    +4.5 by which the candidates of one best net were better for 8 and 29 rounds (rounds 31 to 38 and 39 to 67), so
    the loop stood still. The 250,000-node confirmation behind a promotion is unchanged. Reads the state dict only."""
    best = (d.get("best") or {}).get("net")
    rounds = d.get("rounds") or {}
    if k <= 0 or not best:
        return False, None

    def gate(rr):
        return (((rounds.get(str(rr)) or {}).get("stages") or {}).get("sprt") or {}).get("out") or {}

    own = gate(r)
    win = []
    for rr in range(r, 0, -1):
        g = gate(rr)
        p = g.get("ptnml")
        # W2: "complete" = a verdict or all planned games (since 16 Nov); round 112's gate was complete but killed
        # after its verdict (not "finished") and broke the chain. Records older than "complete" use "finished".
        if (not (g["complete"] if "complete" in g else g.get("finished")) or not g.get("base")
                or Path(str(g["base"])) != Path(str(best))
                or g.get("tc") != own.get("tc") or not isinstance(p, list) or len(p) != 5
                or (rr != r and (rounds.get(str(rr)) or {}).get("pooled_promote"))):
            break
        win.append((rr, [int(x) for x in p]))
        if len(win) == k:
            break

    def elo_ci(p):
        n = sum(p)
        sc = (0.0, 0.25, 0.5, 0.75, 1.0)
        s = sum(c * v for c, v in zip(p, sc)) / n
        se = (sum(c * (v - s) ** 2 for c, v in zip(p, sc)) / n / n) ** 0.5
        e = lambda x: 400.0 * math.log10(x / (1.0 - x)) if 0.0 < x < 1.0 else float("nan")  # noqa: E731
        return e(s), e(s - z * se), e(s + z * se)

    if not own.get("ptnml") or len(win) < 1:
        return False, None
    tot = [sum(c) for c in zip(*(p for _, p in win))]
    e, lo, hi = elo_ci(tot)
    own_e = elo_ci([int(x) for x in own["ptnml"]])[0]
    fires = len(win) == k and lo > 0 and own_e >= min_own
    info = {"rounds": [rr for rr, _ in win][::-1], "ptnml": tot, "elo": round(e, 2), "lo": round(lo, 2),
            "hi": round(hi, 2), "own_elo": round(own_e, 2), "k": k, "z": z, "min_own": min_own, "fires": fires}
    info["line"] = (f"round {r}: the last {len(win)} gates against the best net (rounds {info['rounds'][0]} to "
                    f"{info['rounds'][-1]}, {2 * sum(tot)} games) pool {e:+.2f} [{lo:+.2f}, {hi:+.2f}], this gate "
                    f"{own_e:+.2f}; rule: {k} gates, lower bound above 0, this gate at least {min_own:+g}: "
                    + ("FIRES, the candidate is promoted by the pooled gates (its confirmation follows)" if fires
                       else "does not fire"))
    return fires, info


def note(state: State, msg: str) -> None:
    state.d.setdefault("history", []).append(f"{now()} {msg}")
    state.save()
    log(msg)


def loop_model_names(cfg: dict) -> set[str]:
    """The file names the loop's trainers give a candidate's model (nnloop/trainer.py, tag "cand"): "cand.pt"
    (nnue_pytorch backend) and "cand" + [train] model_suffix (command backend, default ".pt")."""
    return {"cand.pt", "cand" + str(cfg["train"].get("model_suffix", ".pt") or ".pt")}


def drop_replaced_model(cfg: dict, old_model, keep, why: str) -> None:
    """Deletes the model file of a replaced best net, but ONLY when it is one of the loop's own candidate files:
    <[paths] runs>/rNNNN/train/<a name from loop_model_names>, judged on the path with every link resolved, and
    not the file of the net that stays best (keep). Anything else is kept, and one log line says why.
    (2026-11-15, review F2: the confirmation of round 10 deleted the hand-adopted copy
    runs/forge/adopted/v3_h512_r1to8_e40_kd.pt; a best net whose model is an experiment's, a teacher's or a copy
    by hand must never lose that file.)"""
    if not old_model:
        return
    try:
        p = Path(old_model).resolve()
        runs = Path(cfg["paths"]["runs"]).resolve()
        keep_p = Path(keep).resolve() if keep else None
    except (OSError, RuntimeError, ValueError) as e:
        log(f"kept the model file of the replaced best net {old_model} ({why}): its path could not be resolved "
            f"({type(e).__name__}: {e})")
        return
    names = {n.lower() for n in loop_model_names(cfg)}
    own = (p.name.lower() in names and p.parent.name.lower() == "train"
           and re.fullmatch(r"r\d{4,}", p.parent.parent.name.lower()) is not None
           and p.parent.parent.parent == runs)
    if not own:
        log(f"kept the model file of the replaced best net {old_model} ({why}): it is not one of the loop's own "
            f"candidate files ({runs}\\rNNNN\\train\\{' or '.join(sorted(loop_model_names(cfg)))}; resolved: {p})")
        return
    if keep_p is not None and p == keep_p:
        log(f"kept the model file of the replaced best net {old_model} ({why}): it is the model of the net that "
            f"stays best ({keep})")
        return
    p.unlink(missing_ok=True)
    log(f"deleted the model file of the replaced best net ({why}): {p}")


def wait_for_experiment_training(t: dict) -> None:
    """One whole-rounds reader at a time (the PC ran out of memory on 2026-11-14 21:13 when two ran at once).

    The Opus session's experiment trainings hold the folder C:/nnue-lab/tmp/exp_gpu.lock while they run. The
    loop's training waits until that folder is gone, at most [train] wait_for_experiments_min minutes
    (default 60; 0 = do not wait). A folder older than 3 hours counts as left over and is ignored.
    """
    lock = Path(str(t.get("experiment_lock", "C:/nnue-lab/tmp/exp_gpu.lock")))
    limit = float(t.get("wait_for_experiments_min", 60)) * 60
    t0 = time.time()
    told = False
    while limit > 0 and lock.exists():
        try:
            age = time.time() - lock.stat().st_mtime
        except OSError:
            break
        if age > 3 * 3600 or time.time() - t0 > limit:
            log(f"training: {lock} is still there ({age / 60:.0f} minutes old) after {(time.time() - t0) / 60:.0f} "
                f"minutes of waiting; going on")
            break
        if not told:
            log(f"training waits: an experiment training holds {lock}; one job that reads all rounds at a time")
            told = True
        time.sleep(20)
    if told and not lock.exists():
        log(f"training: the experiment training is done after {(time.time() - t0) / 60:.1f} minutes; starting")


def net_hidden(net) -> int | None:
    """Hidden width of a Forge .inc net (its header line says "HiddenSize == N"); None for other net files."""
    try:
        with open(net, "r", encoding="ascii", errors="replace") as fh:
            head = fh.read(4096)
        import re
        m = re.search(r"HiddenSize == (\d+)", head)
        return int(m.group(1)) if m else None
    except (OSError, TypeError):
        return None


def val_path(cfg: dict, runs: Path) -> Path:
    plain = cfg["filter"].get("output", "binpack") == "plain"
    return runs / "val" / ("val.plain" if plain else "val.binpack")


def make_val_set(cfg: dict, state: State, r: int, runs: Path, backend: str, best_net):
    g = cfg["datagen"]
    val = val_path(cfg, runs)
    if val.exists() or int(cfg["train"].get("validation_size", 0)) <= 0 or int(g.get("val_positions", 0)) <= 0:
        return str(val) if val.exists() else None
    raw = runs / "val" / "raw"
    n = int(g["val_positions"])
    if backend == "sf_tools":
        datagen_sftools.generate(cfg, r, raw, n, tag="val")
        parts = sorted(raw.glob("chunk_*_n*.binpack"))
        with open(val.with_name("tmp_val.binpack"), "wb") as o:
            for p in parts:
                o.write(p.read_bytes())
        val.with_name("tmp_val.binpack").replace(val)
    else:
        datagen_uci.generate(cfg, r, best_net, raw, n)
        cat = runs / "val" / "tmp_val_all.plain"
        with open(cat, "wb") as o:
            for p in sorted(raw.glob("*.plain")):
                o.write(p.read_bytes())
        if val.suffix == ".plain":
            cat.replace(val)
        else:
            tools_convert(cfg, cat, val, runs / "val" / "convert.log", validate=True)
            cat.unlink(missing_ok=True)
    return str(val)


def confirm_sprt_settings(s_cfg: dict) -> dict | None:
    """[sprt] confirm_sprt (Opus 2026-11-15, job 10; Fable's decision of 17:00): with true the confirmation match is an
    SPRT with the bounds below, at most confirm_games games, and the fixed LOS rule decides only when no bound was
    crossed. Defaults = rule C08 (survey/confirm_early_stop.md: 10.6 % false pass at 0 Elo against 9.8 % for the
    fixed match, 78.9 % pass at +10 against 80.5 %, about 1,100 to 1,250 games instead of 2,000; no verdict of the six
    past confirmations changes). false or no line = the fixed-length match as before. Returns the bounds or None."""
    if not s_cfg.get("confirm_sprt", False):
        return None
    return {"elo0": float(s_cfg.get("confirm_sprt_elo0", 0.0)), "elo1": float(s_cfg.get("confirm_sprt_elo1", 17.2)),
            "alpha": float(s_cfg.get("confirm_sprt_alpha", 0.08)), "beta": float(s_cfg.get("confirm_sprt_beta", 0.14))}


def confirm_match_cfg(mcfg: dict, c_sprt: dict | None, games: int) -> dict:
    """The match config of the confirmation: the gate's own [sprt] settings with the confirmation's SPRT bounds and
    its game cap in place of the gate's (a copy; the loop's config is not changed)."""
    if c_sprt is None:
        return mcfg
    out = dict(mcfg)
    out["sprt"] = {**mcfg["sprt"], **c_sprt, "max_games": int(games)}
    return out


def confirm_decision(cres: dict, s_cfg: dict, c_sprt: dict | None) -> tuple[bool, str]:
    """(passed, how) of a confirmation match: the SPRT's verdict when it gave one, else the fixed LOS rule on a match
    that reached its end; a match that did not is not passed."""
    los = cres.get("los_pct")
    by_los = los is not None and los >= float(s_cfg.get("confirm_min_los", 95.0))
    # Agent review finding 2, statistics review finding 1 (2026-11-15): the LOS rule decides only a match that reached
    # its end (all confirm_games games, exit code 0, fastchess's own end). The loop's call (need_complete=True) plays
    # such a match again before it gets here; this is the second line for a result stored as done before that change.
    why = match.incomplete_reason(cres, 2 * max(1, int(s_cfg.get("confirm_games", 0) or 0) // 2))
    if why is not None:
        return False, f"the match did not reach its end ({why}): not decided by the LOS rule, so not passed"
    if c_sprt is None:
        return by_los, f"fixed rule (LOS {los}%)"
    v = cres.get("verdict")
    if v == "H1":
        return True, f"SPRT H1 after {cres.get('games')} games"
    if v == "H0":
        return False, f"SPRT H0 after {cres.get('games')} games"
    return by_los, f"no SPRT bound after {cres.get('games')} games: fixed rule (LOS {los}%)"


def match_cfg(cfg: dict) -> dict:
    """The config for the loop's matches between two nets. With [sprt] default_settings = true (2026-11-15) the
    tuned search values (engine.tuned_options_file) are left out for BOTH sides, so the match is played with the
    engine's default settings. Why: the values were found by self-play of ONE net (the round 2 net) and fit that
    net. Measured on 2026-11-15 with the same two nets, 2,000 games each at 50,000 nodes: at default settings
    b_full beat the round 2 net by +29.2 +/- 10.3; with the tuned values on both sides they were level. A match
    with the tuned values therefore measures a candidate with settings fitted to its opponent. Self-play keeps
    the tuned values (they belong to the net that plays it)."""
    if not cfg["sprt"].get("default_settings"):
        return cfg
    names = set(cfg["engine"].get("tuned_option_names") or [])
    if not names:
        return cfg
    out = dict(cfg)
    out["engine"] = dict(cfg["engine"],
                         uci_options={k: v for k, v in cfg["engine"].get("uci_options", {}).items() if k not in names})
    return out


def do_round(cfg: dict, state: State, r: int) -> None:
    runs = Path(cfg["paths"]["runs"])
    rd = runs / f"r{r:04d}"
    g, t = cfg["datagen"], cfg["train"]

    def stage(name, fn):
        # The STOP file also ends the run BETWEEN two stages (2026-11-14 23:15; before, only at the start of a
        # round and during self-play): a stage that has not begun is not started. So a stop asked for during the
        # training ends the run before the match, and the match is not begun only to be thrown away. A stage
        # that is already done is still skipped as always, and the same command resumes at the stage not begun.
        if state.stage(r, name).get("status") != "done" and stop_requested(cfg):
            raise StopRequested(f"STOP file found before stage {name}")
        out = run_stage(state, r, name, fn, cfg)
        report.update(cfg, state.d)
        return out

    def play_yardsticks():
        """The strength matches on the clock ([anchor], [[anchor_extra]]) for the best confirmed net; each net and
        reference once. Called at the start of a round, after a possible confirmation match and before self-play (so a
        new best net is measured at once, since 2026-11-15 09:15), and at the end of every round."""
        # Outside yardstick ([anchor] in the config): each confirmed net plays one fixed-length match against
        # a reference engine, once. It decides nothing, so a failure here is logged and the round still counts.
        a_cfg = cfg.get("anchor") or {}
        if a_cfg.get("enabled"):
            try:
                from nnloop.engine import file_sha12
                done = state.d.setdefault("anchors", {})
                todo = []
                b = state.d["best"]
                b = b["prev"] if (b and b.get("confirm_pending") and b.get("prev")) else b
                if b and b.get("net"):
                    todo.append((f"the best confirmed net (round {b.get('round')})", b["net"]))      # first: the answer wanted most
                if a_cfg.get("include_initial", True) and cfg["engine"].get("initial_net"):
                    todo.append(("the initial net", cfg["engine"]["initial_net"]))
                # Results are kept per net AND reference. The first reference ("sf_elo3100", the development Stockfish of
                # 2026-11-10 at UCI_Elo 3100) was recorded under the net's id alone; any other name gets "<net id>:<name>",
                # so a net measured against the old reference is measured once more against a new one.
                ref_id = str(a_cfg.get("name", "") or "")
                # Agent review finding 9 (2026-11-15): with no CPU temperature reading every yardstick waited
                # temperature_wait_seconds (5 minutes, CPU idle) before it was put off. Once one of this call is put
                # off for that (ares "no_reading"), the others are put off at once and named in ONE note at the end.
                no_reading, put_off = False, []
                for label, net in todo:
                    key = file_sha12(net) if ref_id in ("", "sf_elo3100") else f"{file_sha12(net)}:{ref_id}"
                    if key in done:
                        continue
                    if no_reading:
                        put_off.append(f"yardstick match for {label}")
                        continue
                    tag = "anchor_" + key.replace(":", "_")
                    ares = stage(tag, lambda net=net, tag=tag: match.run_anchor(
                        cfg, net, rd / tag, seed=200000 + r, loop_stop=True))
                    if ares.get("skipped"):
                        # no room for a fair clock match now (other programs, or heat): not recorded, so the end
                        # of the next round tries again
                        note(state, f"yardstick match for {label} put off to the next round: {ares['skipped']}")
                        no_reading = no_reading or bool(ares.get("no_reading"))
                        continue
                    done[key] = {"label": label, "net": str(net), "round": r, "reference": ares.get("reference"),
                                 "reference_options": ares.get("reference_options"), "tc": ares.get("tc"),
                                 **{k: ares.get(k) for k in ("games", "wins", "losses", "draws", "elo", "elo_err",
                                                            "score_pct", "time_forfeits_by_engine")}}
                    state.save()
                    note(state, f"yardstick match, {label} against {ares.get('reference')} at {ares.get('tc')}: "
                                f"{ares.get('games')} games, W-L-D {ares.get('wins')}-{ares.get('losses')}-{ares.get('draws')}, "
                                f"Elo {ares.get('elo')} +/- {ares.get('elo_err')}, "
                                f"time forfeits {ares.get('time_forfeits_by_engine') or 0}")
                # Rated references ([[anchor_extra]] in the config, 2026-11-15): old official Stockfish releases with a
                # published rating. Only the best confirmed net plays them, once each, under the yardstick's rules
                # (played only when the PC has room and is cool; put off to the next round otherwise).
                for extra in (cfg.get("anchor_extra") or []):
                    if not extra.get("enabled", True) or not (b and b.get("net")):
                        continue
                    # every_rounds = N (2026-11-15 15:30): this reference is played only in rounds whose number is
                    # a multiple of N. The two old releases cost about 19 minutes of a round; the [anchor] block
                    # (Stockfish 19 at 3100, the pairing the owner asked for) is still played for every confirmed net.
                    every = int(extra.get("every_rounds", 1) or 1)
                    if every > 1 and r % every != 0:
                        continue
                    net, label = b["net"], f"the best confirmed net (round {b.get('round')})"
                    name = str(extra.get("name", "reference"))
                    key = f"{file_sha12(net)}:{name}"
                    if key in done:
                        continue
                    if no_reading:
                        put_off.append(f"rated match against {name}")
                        continue
                    tag = f"anchor_{file_sha12(net)}_{name}"
                    ares = stage(tag, lambda net=net, extra=extra, tag=tag: match.run_anchor(
                        cfg, net, rd / tag, seed=210000 + r, anchor=extra, loop_stop=True))
                    if ares.get("skipped"):
                        note(state, f"rated match for {label} against {name} put off to the next round: {ares['skipped']}")
                        no_reading = no_reading or bool(ares.get("no_reading"))
                        continue
                    done[key] = {"label": label, "net": str(net), "round": r, "reference": name,
                                 "reference_rating": extra.get("rating"), "reference_rating_source": extra.get("rating_source"),
                                 "reference_options": ares.get("reference_options"), "tc": ares.get("tc"),
                                 **{k: ares.get(k) for k in ("games", "wins", "losses", "draws", "elo", "elo_err",
                                                            "score_pct", "time_forfeits_by_engine")}}
                    state.save()
                    est = ""
                    if extra.get("rating") is not None and ares.get("elo") is not None:
                        est = (f"; on that list's scale about {round(float(extra['rating']) + float(ares['elo']))} "
                               f"(published {extra['rating']} + difference; other clock and openings, so a rough figure)")
                    note(state, f"rated match, {label} against {name} ({extra.get('rating_source', 'published rating')}: "
                                f"{extra.get('rating')}) at {ares.get('tc')}: {ares.get('games')} games, W-L-D "
                                f"{ares.get('wins')}-{ares.get('losses')}-{ares.get('draws')}, Elo {ares.get('elo')} +/- "
                                f"{ares.get('elo_err')}, time forfeits {ares.get('time_forfeits_by_engine') or 0}{est}")
                if put_off:
                    note(state, f"also put off to the next round, without waiting, as there is no CPU temperature "
                                f"reading (see above): {', '.join(put_off)}")
            except StopRequested:
                raise   # a stop is a stop: the round is resumed here later (2026-11-15: it was swallowed once)
            except Exception as e:  # noqa: BLE001
                note(state, f"yardstick match failed, the round goes on: {type(e).__name__}: {str(e)[:300]}")

    # starting net given in the config (an engine that already has a net)
    if state.d["best"] is None and cfg["engine"].get("initial_net"):
        state.d["best"] = {"net": cfg["engine"]["initial_net"], "model": t.get("initial_model") or None,
                           "round": 0, "label": "initial net from config"}
        state.save()

    best = state.d["best"]

    # A promotion can ask for a second, independent match before the net is used further
    # (sprt.confirm_games > 0). It is played at the start of the next round of this profile.
    if best and best.get("confirm_pending") and best.get("prev"):
        s_cfg = cfg["sprt"]
        games = int(s_cfg.get("confirm_games", 0))
        if games > 0:
            c_sprt = confirm_sprt_settings(s_cfg)        # None = the fixed-length match (job 10)
            cres = stage("confirm_best", lambda: match.run_sprt(
                confirm_match_cfg(match_cfg(cfg), c_sprt, games), best["net"], best["prev"]["net"], rd / "confirm",
                seed=100000 + r, cand_name="new_best", base_name="previous_best",
                fixed_games=(0 if c_sprt else games),
                nodes_override=(0 if best.get("clock_confirm") else
                                (int(s_cfg["confirm_nodes"]) if s_cfg.get("confirm_nodes") else None)),
                need_complete=True))      # finding 2: a cut-off confirmation is played again, never decided by LOS
            los = cres.get("los_pct")
            ok, how = confirm_decision(cres, s_cfg, c_sprt)
            summary = (f"{cres.get('games')} games, W-L-D {cres.get('wins')}-{cres.get('losses')}-{cres.get('draws')}, "
                       f"Elo {cres.get('elo')} +/- {cres.get('elo_err')}, LOS {los}% ({cres.get('tc')}); {how}")
            # SHADOW of the early-stop rule C08 (Opus 2026-11-15; placed by Fable 16:00): one line on what the rule
            # computed from the game records would have decided and after how many games. Since 17:16 the rule itself
            # decides ([sprt] confirm_sprt, confirm_decision above); the line stays as a cross-check of fastchess's
            # own verdict.
            try:
                from nnloop import confirm_shadow
                note(state, confirm_shadow.summary_line(cres.get("log"), float(s_cfg.get("confirm_min_los", 95.0))))
            except Exception as e:  # noqa: BLE001 -- a shadow must never stop the loop
                note(state, f"confirmation SHADOW (rule C08): not computed ({e})")
            if ok:
                old_model = best["prev"].get("model")
                if old_model and old_model != best.get("model") and not cfg["limits"].get("keep_models", False):
                    drop_replaced_model(cfg, old_model, best.get("model"),
                                        f"the net of round {best.get('round')} is confirmed")
                best["confirm_pending"] = False
                best["confirmed"] = {k: cres.get(k) for k in ("games", "wins", "losses", "draws", "elo", "elo_err",
                                                               "los_pct", "tc")}
                best["label"] = str(best.get("label", "")).replace(", confirmation match pending", "") + \
                    f"; confirmed by a second match ({summary})"
                state.save()
                note(state, f"confirmation PASSED for the net of round {best['round']}: {summary}")
            else:
                failed = dict(best)
                state.d["best"] = best["prev"]
                state.d.setdefault("reverted", []).append(
                    {"net": failed.get("net"), "round": failed.get("round"),
                     "confirm": {k: cres.get(k) for k in ("games", "wins", "losses", "draws", "elo", "elo_err",
                                                           "los_pct", "tc")}})
                state.save()
                note(state, f"confirmation FAILED for the net of round {failed.get('round')}: {summary}; "
                            f"the previous net is best again")
            report.update(cfg, state.d)
            best = state.d["best"]

    backend = g.get("backend_round1") if (r == 1 and g.get("backend_round1")) else g["backend"]
    target = int(g.get("positions_round1", g["positions"])) if r == 1 else int(g["positions"])
    raw_dir = rd / "data" / "raw"

    def s_datagen():
        net = best["net"] if best else None
        make_val_set(cfg, state, r, runs, backend, net)
        if backend == "sf_tools":
            return datagen_sftools.generate(cfg, r, raw_dir, target)
        if backend == "uci_selfplay":
            return datagen_uci.generate(cfg, r, net, raw_dir, target)
        raise ValueError(f"unknown datagen backend {backend!r}")

    # Strength matches still owed for the best confirmed net are played now, before self-play: a net that has just
    # been confirmed is measured at once, and a restart between stages resumes here ([anchor] at_round_start).
    if (cfg.get("anchor") or {}).get("at_round_start", True) and state.stage(r, "datagen").get("status") != "done":
        play_yardsticks()

    stage("datagen", s_datagen)
    qc = stage("filter", lambda: filterqc.filter_round(cfg, raw_dir, rd / "data"))

    val = val_path(cfg, runs)
    val_set = str(val) if val.exists() else None

    if state.d["best"] is None:
        def s_baseline():
            out = trainer.train(cfg, [qc["filtered"]], None, None, runs / "baseline",
                                epochs=1, lr=1e-12, tag="untrained")
            check_engine_loads_net(cfg, out["net"])
            # the untrained net is only a baseline to play against: drop its 3 GB checkpoint and model
            for ck in (runs / "baseline").glob("training_logs/version_*/checkpoints/*.ckpt"):
                ck.unlink(missing_ok=True)
            Path(out["model"]).unlink(missing_ok=True)
            return out
        base = stage("baseline", s_baseline)
        state.d["best"] = {"net": base["net"], "model": None, "round": 0, "label": "untrained net"}
        state.save()
    best = state.d["best"]

    window = int(t.get("window_rounds", 1000))
    # [train] max_window_positions (2026-11-15, 0 or unset = no limit): the trainers hold the whole window on the
    # graphics card (about 90 bytes a position: 20 GB hold a little over 200 million). When the window has more,
    # the OLDEST rounds are left out until it fits, at least the newest round stays, and the round's note says so.
    # Since 2026-11-16 (training_window) the cap counts every round's recorded positions, file on disk or not.
    cap = int(t.get("max_window_positions", 0) or 0)
    per_round, dropped, kept = training_window(state.d, r, window, cap)
    if dropped and state.round(r).get("window_dropped") != dropped:
        state.round(r)["window_dropped"] = dropped
        state.save()
        note(state, f"round {r}: the training window is limited to {cap} positions (max_window_positions); "
                    f"left out the oldest rounds {dropped}, {kept} positions stay")
    # A round inside the window whose positions file is not on disk (packed by the disk relief) is brought back
    # before the training (nnloop/diskrelief.py restore_plain: unpacked, compared, only then named filtered.plain);
    # one note per round. If it cannot be brought back (nothing to unpack from, or the disk would go under
    # [limits] min_free_gb), a WARNING note names it and the positions missing, and the training goes on without
    # it: never a silent skip, and the comparison with the best net below sees the smaller count.
    datasets, reserve_gb = [], 0.0
    for rr, n, f in per_round:
        if Path(f).exists():
            datasets.append(f)
            continue
        try:
            from nnloop import diskrelief
            from nnloop.common import free_gb
            res = diskrelief.restore_plain(Path(f).parent, lambda: free_gb(runs),
                                           float(cfg["limits"].get("min_free_gb", 0) or 0) + reserve_gb)
            if not Path(f).exists():
                raise RuntimeError(f"{f} is still missing after the restore")
        except Exception as e:  # noqa: BLE001
            kept -= n
            missing = state.round(r).setdefault("window_missing", {})
            if missing.get(str(rr)) != n:
                missing[str(rr)] = n
                state.save()
                note(state, f"round {r}: WARNING: round {rr} is in the training window but its positions file "
                            f"{f} is missing and could not be brought back ({type(e).__name__}: {str(e)[:240]}); "
                            f"the training goes on WITHOUT its {n} positions ({kept} stay)")
            continue
        reserve_gb += res["bytes"] * diskrelief.CACHE_PER_PLAIN / 2**30   # its cache comes when the trainer runs
        datasets.append(f)
        if (state.round(r).get("window_missing") or {}).pop(str(rr), None) is not None:
            state.save()                     # missing at an earlier start of this stage, brought back now
        note(state, f"round {r}: round {rr} is back in the training window: its positions file was packed by the "
                    f"disk relief and is unpacked again ({res['bytes'] / 1e9:.2f} GB, compared with the packed "
                    f"copy{'; the packed copy could not be removed and stays beside it' if res['packed_left'] else ''})")
    # A candidate must not be trained on less data than the net it has to beat (2026-11-16). Log only: one loud
    # note per round, nothing is changed, and a fault in this look never stops a round.
    try:
        less = window_less_than_best(state.d, r, kept, window)
        if less and state.round(r).get("window_less_than_best") != [kept, less[1]]:
            state.round(r)["window_less_than_best"] = [kept, less[1]]
            state.save()
            note(state, f"round {r}: WARNING: this round's net is trained on {kept} kept positions, FEWER than the "
                        f"{less[1]} of the best net (round {less[0]}) it has to beat. A net with less data rarely "
                        f"wins: raise [train] max_window_positions (or the window) if the card has room.")
    except Exception as e:  # noqa: BLE001
        note(state, f"round {r}: the window comparison with the best net was skipped ({type(e).__name__}: {e})")
    # Disk relief (owner, 2026-11-15: "when selfplay gets too large for disk space filter the positions that frees
    # space"): when free space is under [limits] relief_below_gb, rounds that are no longer in the training window
    # lose their rebuildable training cache and get their positions file packed (nnloop/diskrelief.py; no position
    # is lost). Oldest first, only until the space is back.
    relief_below = float(cfg["limits"].get("relief_below_gb", 0) or 0)
    if relief_below and dropped:
        from nnloop.common import free_gb
        if free_gb(runs) < relief_below:
            from nnloop import diskrelief
            diskrelief.relieve([(rr, runs / f"r{rr:04d}" / "data") for rr in dropped], relief_below + 5.0,
                               lambda: free_gb(runs), lambda text: note(state, text))
    # Step 3 (owner, 2026-11-16 about 18:05 and 18:10): when C: is still short, the packed positions of rounds
    # outside the window move to the lab's own folder on another disk, never below 30 GB free there
    # (nnloop/diskrelief.py overflow_step; [limits] overflow_dirs / overflow_below_gb). A fault never stops a round.
    if dropped:
        try:
            from nnloop import diskrelief
            diskrelief.overflow_step(cfg, runs, dropped, lambda text: note(state, text))
        except Exception as e:  # noqa: BLE001
            note(state, f"round {r}: disk relief step 3 skipped ({type(e).__name__}: {str(e)[:200]})")
    init = best.get("model") if (t.get("init", "best") == "best" and best.get("model")
                                 and Path(best["model"]).exists()) else None
    lr = float(t.get("lr_continue", t["lr"])) if init else float(t["lr"])
    epochs = trainer.plan_epochs(t, kept)

    # A wider net ([train] widen_to): once the training window holds widen_min_positions, the candidate is the
    # best net widened (it computes the same at first) and trained with widen_epochs / widen_lr. Tried at most
    # widen_max_attempts times. A net of another width runs at another speed, so its matches are played on the
    # clock (sprt.tc), not at fixed nodes.
    widen_to = int(t.get("widen_to", 0) or 0)
    best_h = net_hidden(best.get("net"))
    tries = int(state.d.get("widen_attempts", 0))
    if (widen_to and best_h and best_h < widen_to and kept >= int(t.get("widen_min_positions", 100_000_000))
            and (tries < int(t.get("widen_max_attempts", 3)) or state.round(r).get("widened"))):
        if not state.round(r).get("widened"):
            state.round(r)["widened"] = True
            state.d["widen_attempts"] = tries + 1
            state.save()
            note(state, f"round {r}: {kept} positions in the training window; the candidate is the best net widened "
                        f"from {best_h} to {widen_to} hidden units (attempt {tries + 1})")
        t["env"] = {**(t.get("env") or {}), "FORGE_WIDEN_TO": str(widen_to)}
        epochs = int(t.get("widen_epochs", epochs))
        lr = float(t.get("widen_lr", lr))

    # [train] keep_noisy (2026-11-14, from the Opus session's arm b: +15.4 +/- 5.9 Elo over 6,000 games against the
    # same recipe without it): the trainer also learns from positions whose best move is a capture or a promotion.
    # Positions in check stay out. The candidate still has to pass both matches.
    if t.get("keep_noisy"):
        t["env"] = {**(t.get("env") or {}), "FORGE_KEEP_NOISY": "1"}
        if not state.round(r).get("keep_noisy"):
            state.round(r)["keep_noisy"] = True
            state.save()
            note(state, f"round {r}: training keeps positions whose best move is a capture or promotion (keep_noisy)")

    # [train] standalone / from_scratch / hidden (2026-11-14, off unless set): a net that the engine uses WITHOUT the
    # hand-written evaluation (net file flag FORGE_NNUE_RESIDUAL 0). from_scratch = true trains a new net of `hidden`
    # units in every round instead of continuing the best one. Switch these on only when the loop's best net is itself
    # a stand-alone net of the same width: only then are candidate and best equally fast and a fixed-node match fair.
    if t.get("standalone"):
        t["env"] = {**(t.get("env") or {}), "FORGE_STANDALONE": "1"}
    if t.get("from_scratch"):
        t["env"] = {**(t.get("env") or {}), "FORGE_FROM_SCRATCH": "1"}
        init = None
    if t.get("hidden"):
        t["env"] = {**(t.get("env") or {}), "FORGE_HIDDEN": str(int(t["hidden"]))}
    # [train] out_buckets (2026-11-14): a net started from scratch gets this many output blocks, chosen by the
    # number of pieces (needs an engine source with output buckets: forge/r5 or later). 1 or unset = none.
    if int(t.get("out_buckets", 1) or 1) > 1:
        t["env"] = {**(t.get("env") or {}), "FORGE_OUT_BUCKETS": str(int(t["out_buckets"]))}
    # [train] ft_backend (2026-11-14): "triton" = the first layer by the Triton kernels (pipeline/ft_triton), about
    # 3 times faster at the loop's recipe and equal to the old path up to float rounding. The trainer tests the
    # kernels against the old path before every training and falls back to it by itself. Unset or "dense" = as before.
    if str(t.get("ft_backend", "") or "") in ("triton", "triton1"):
        t["env"] = {**(t.get("env") or {}), "FORGE_FT_BACKEND": str(t["ft_backend"])}

    def s_train():
        wait_for_experiment_training(t)
        # [datagen] early_selfplay: round r + 1's self-play runs on the processor while the card trains round r
        with datagen_uci.EarlySelfplay(cfg, r + 1, best.get("net"), runs / f"r{r + 1:04d}" / "data" / "raw",
                                       int(g["positions"]), rd / "train" / "train.log"):
            return trainer.train(cfg, datasets, val_set, init, rd / "train", epochs=epochs, lr=lr,
                                 init_net=best.get("net"))

    tr = stage("train", s_train)
    stage("check", lambda: check_engine_loads_net(cfg, tr["net"]))
    cand_h = net_hidden(tr["net"])
    other_width = bool(best_h and cand_h and cand_h != best_h)
    cfg_m = match_cfg(cfg)
    if other_width:
        cfg_m = dict(cfg_m)
        cfg_m["sprt"] = dict(cfg["sprt"], nodes=0, max_games=int(cfg["sprt"].get("max_games_clock", 2000)))
    sp = stage("sprt", lambda: match.run_sprt(cfg_m, tr["net"], best["net"], rd / "sprt", seed=r))

    def s_promote():
        if (state.d.get("best") or {}).get("round") == r and state.d["best"].get("net") == tr["net"]:
            return {"decision": "promote", "best": state.d["best"]}     # resumed after this stage's own save below
        decision = sp["decision"]
        pk = int(cfg["sprt"].get("pooled_gate_k", 0) or 0)       # 0 (the default) = the rule is off
        pooled = None
        if decision != "promote" and pk > 0:
            fires, pooled = pooled_gate(state.d, r, pk, float(cfg["sprt"].get("pooled_gate_z", 1.96)),
                                        float(cfg["sprt"].get("pooled_gate_min_own", 0.0)))
            if pooled:
                note(state, "POOLED GATE: " + pooled["line"])
            if fires:
                decision = "promote"
                state.round(r)["pooled_promote"] = {k: v for k, v in pooled.items() if k != "line"}
            else:
                pooled = None
        if decision == "promote":
            old_model = best.get("model")
            confirm = int(cfg["sprt"].get("confirm_games", 0)) > 0
            prev = {k: best.get(k) for k in ("net", "model", "round", "label")}
            state.d["best"] = {"net": tr["net"], "model": tr["model"], "round": r,
                               "label": f"promoted in round {r}: {sp.get('wins')}-{sp.get('losses')}-{sp.get('draws')} "
                                        f"(W-L-D) against the previous best"
                                        + (f" (by the POOLED gates of rounds {pooled['rounds'][0]} to "
                                           f"{pooled['rounds'][-1]}: {pooled['elo']:+.2f} [{pooled['lo']:+.2f}, "
                                           f"{pooled['hi']:+.2f}])" if pooled else "")
                                        + (", confirmation match pending" if confirm else ""),
                               "confirm_pending": confirm, "prev": prev if confirm else None,
                               "clock_confirm": other_width}
            # while a confirmation is pending the previous model is kept, so a failed one can go back to it
            if (not confirm and old_model and old_model != tr["model"]
                    and not cfg["limits"].get("keep_models", False)):
                drop_replaced_model(cfg, old_model, tr["model"], f"round {r} promoted without a confirmation match")
        else:
            if not cfg["limits"].get("keep_models", False):
                Path(tr["model"]).unlink(missing_ok=True)
        if not cfg["limits"].get("keep_checkpoints", False):
            for ck in (rd / "train").glob("training_logs/version_*/checkpoints/*.ckpt"):
                ck.unlink(missing_ok=True)
        state.round(r)["decision"] = decision
        state.save()
        return {"decision": decision, "best": state.d["best"]}

    stage("promote", s_promote)

    play_yardsticks()

    state.round(r)["finished"] = now()
    state.save()
    tl, vl = tr.get("train_loss_last"), tr.get("val_loss_last")
    note(state, f"round {r} finished: {state.round(r).get('decision')}; "
                f"SPRT {sp.get('games')} games, W-L-D {sp.get('wins')}-{sp.get('losses')}-{sp.get('draws')}, "
                f"Elo {sp.get('elo')} +/- {sp.get('elo_err')}; "
                f"train loss {'-' if tl is None else format(tl, '.5f')}, hold-out loss {'-' if vl is None else format(vl, '.5f')}; "
                f"best is now from round {state.d['best']['round']}")
    report.update(cfg, state.d)


def report_in_error_path(cfg: dict, state: State) -> None:
    """REPORT.md update after a stop or a failure. A report write that raises here (REPORT.md locked by an editor)
    would end run.py before its exit code and failure count are settled (skill test of 23 Nov 2026, F6): it only logs."""
    try:
        report.update(cfg, state.d)
    except Exception as e:  # noqa: BLE001
        log(f"WARNING: REPORT.md not updated after the stop or failure: {type(e).__name__}: {str(e)[:300]}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(Path(__file__).resolve().parent / "config.toml"))
    ap.add_argument("--rounds", type=int, default=0, help="stop after this many rounds in this run (0 = no limit)")
    args = ap.parse_args()

    cfg = load_config(args.config)
    runs = Path(cfg["paths"]["runs"])
    runs.mkdir(parents=True, exist_ok=True)
    set_log_file(runs / "pipeline.log")
    _lock = SingleInstance(runs / "pipeline.lock")
    kill_children_on_exit()
    keep_awake()
    state = State(runs / "state.json")
    log(f"pipeline start: config {args.config}, runs {runs}, next round {state.current_round()}")
    done = 0
    while True:
        cfg = load_config(args.config)  # re-read so settings can change between rounds
        r = state.current_round()
        if stop_requested(cfg):
            log("STOP file present: not starting. Delete pipeline\\STOP and run again to resume.")
            break
        if past_deadline(cfg):
            log(f"deadline {cfg['limits'].get('deadline')} reached: not starting round {r}")
            break
        max_rounds = int(cfg["limits"].get("max_rounds", 0))
        if (max_rounds and r > max_rounds) or (args.rounds and done >= args.rounds):
            log("round limit reached")
            break
        try:
            log(f"===== round {r} =====")
            do_round(cfg, state, r)
            done += 1
        except StopRequested as e:
            note(state, f"stopped on request in round {r}: {e}")
            report_in_error_path(cfg, state)
            break
        except DiskLow as e:
            note(state, f"STOPPED, disk low in round {r}: {e}")
            report_in_error_path(cfg, state)
            return 3
        except Exception as e:
            note(state, f"ERROR in round {r}: {type(e).__name__}: {str(e)[:500]}")
            log(traceback.format_exc())
            fails = state.d.get("consecutive_failures", 0) + 1
            state.d["consecutive_failures"] = fails
            state.save()
            report_in_error_path(cfg, state)
            if fails >= int(cfg["limits"].get("max_consecutive_failures", 3)):
                log("too many failures in a row; stopping so the cause can be fixed")
                return 2
            time.sleep(30)
            continue
        state.d["consecutive_failures"] = 0
        state.save()
    log(f"pipeline exit ({done} round(s) finished in this run)")
    return 0 if done > 0 else 10  # 10 = nothing was run (deadline, STOP or round limit)


if __name__ == "__main__":
    raise SystemExit(main())
