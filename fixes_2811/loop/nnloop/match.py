"""SPRT match between two nets with fastchess. Nothing else heavy may run at the same time."""
from __future__ import annotations

import re
import time
from pathlib import Path

from .common import ENDED_AFTER_RESULT, atomic_write_json, child_env, log, now, run_logged, tail_text
from .engine import check_options, engine_for_net
from .heat import MatchHeatGuard, clock_concurrency, cpu_temp, others_busy_threads

_ANSI = re.compile(r"\x1b\[[0-9;]*m")
# After its SPRT verdict fastchess prints no game and no result block more (61 of the 61 verdict matches of rounds 2 to
# 134) and "Finished match" (60 of 61); round 112's gate printed its verdict and never exited (killed at 9,000 s).
VERDICT_EXIT_GRACE_S = 120.0


class MatchIncomplete(RuntimeError):
    """A match that did not reach its own end (2026-11-15, agent review findings 1 and 2). Its games decide nothing. The
    error leaves the loop's stage unfinished, so the round is tried again after 30 s and the stage is played again from
    the start (run_stage; three failed rounds in a row stop the loop, as for every other failing stage)."""


def _log_heat(guard: MatchHeatGuard) -> None:
    h = guard.summary()
    if h.get("cpu_max_c") is None:
        return
    extra = ""
    if h.get("changes"):
        extra = (f"; it ran on as few as {h['threads_fewest']} of {h['threads_total']} threads "
                 f"({h['changes']} changes, about {h['seconds_lost']} s lost)")
    elif h.get("seconds_at_limit"):
        extra = f"; about {h['seconds_at_limit']} s at the limit or above"
    log(f"match heat: hottest CPU reading {h['cpu_max_c']:.0f} C{extra}")


def _sha256(path) -> str | None:
    import hashlib

    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(1 << 20), b""):
                h.update(block)
        return h.hexdigest()
    except (OSError, TypeError):
        return None


def _engine_args(spec, name: str) -> list[str]:
    # 2026-11-16: every fastchess command of the loop and of the hand tools is built here, so the engine is asked
    # once, before the match, whether it takes every option (nnloop.engine.check_options; raises OptionRefused).
    check_options(spec)
    args = ["-engine", f"cmd={spec.exe}", f"name={name}"]
    if spec.cwd:
        args.append(f"dir={spec.cwd}")
    for k, v in spec.options.items():
        if isinstance(v, bool):
            v = "true" if v else "false"
        args.append(f"option.{k}={v}")
    return args


def parse_fastchess(text: str) -> dict:
    text = _ANSI.sub("", text)
    out: dict = {}

    def last(pattern):
        m = None
        for m in re.finditer(pattern, text):
            pass
        return m

    num = r"(-?[\d.]+|-?inf|-?nan)"
    m = last(r"Elo:\s*" + num + r"\s*\+/-\s*" + num + r"(?:,\s*nElo:\s*" + num + r"\s*\+/-\s*" + num + r")?")
    if m:
        out["elo"], out["elo_err"] = m.group(1), m.group(2)
        if m.group(3):
            out["nelo"], out["nelo_err"] = m.group(3), m.group(4)
    m = last(r"Games:\s*(\d+),\s*Wins:\s*(\d+),\s*Losses:\s*(\d+),\s*Draws:\s*(\d+)(?:,\s*Points:\s*([\d.]+)\s*\(([\d.]+)\s*%\))?")
    if m:
        out.update(games=int(m.group(1)), wins=int(m.group(2)), losses=int(m.group(3)), draws=int(m.group(4)))
        if m.group(6):
            out["score_pct"] = float(m.group(6))
    m = last(r"Ptnml\(0-2\):\s*\[([\d,\s]+)\]")
    if m:
        out["ptnml"] = [int(x) for x in m.group(1).split(",")]
    m = last(r"LLR:\s*(-?[\d.]+)\s*(?:\([^)]*\)\s*)?\((-?[\d.]+),\s*(-?[\d.]+)\)\s*\[(-?[\d.]+),\s*(-?[\d.]+)\]")
    if m:
        out.update(llr=float(m.group(1)), llr_lower=float(m.group(2)), llr_upper=float(m.group(3)),
                   elo0=float(m.group(4)), elo1=float(m.group(5)))
    m = last(r"LOS:\s*([\d.]+)\s*%")
    if m:
        out["los_pct"] = float(m.group(1))
    low = text.lower()
    if re.search(r"h1 (was|is) accepted", low):
        out["verdict"] = "H1"
    elif re.search(r"h0 (was|is) accepted", low):
        out["verdict"] = "H0"
    else:
        out["verdict"] = "none"
    # Statistics review finding 9 (2026-11-15): the verdict text counts only when the printed LLR is past its printed
    # bound (rounding keeps the order; every real H1 / H0 of the loop shows it: 2.96 >= 2.94, 2.39 >= 2.37,
    # -2.98 <= -2.94). This fastchess can print "H1" for an LLR between the bounds at the cap (roundrobin.cpp:152-162,
    # not reached today); such a text is now no verdict.
    if out["verdict"] != "none" and not ("llr" in out and (out["llr"] >= out["llr_upper"] if out["verdict"] == "H1"
                                                           else out["llr"] <= out["llr_lower"])):
        out["verdict_text_ignored"] = out["verdict"]
        out["verdict"] = "none"
    # Agent review finding 2: fastchess prints "Finished match" when it ends by its own rule (bound, cap); a killed one
    # does not (the loop's and the hand tools' real logs). Only text after run_logged's last "=====" line counts (its
    # header, or its "KILLED after timeout" line).
    out["finished"] = text.rfind("Finished match") > text.rfind(chr(10) + "===== ")
    # time forfeits by engine: "Finished game 7 (cand vs best): 0-1 {White loses on time}" (first name is White)
    forfeits: dict[str, int] = {}
    for m in re.finditer(r"Finished game \d+ \((\S+) vs (\S+)\): \S+ \{(White|Black) loses on time", text):
        loser = m.group(1) if m.group(3) == "White" else m.group(2)
        forfeits[loser] = forfeits.get(loser, 0) + 1
    out["time_forfeits_by_engine"] = forfeits
    out["time_losses"] = max(sum(forfeits.values()), len(re.findall(r"loses on time|lost on time", low)))
    out["disconnects"] = len(re.findall(r"disconnect|stalls|crash", low))
    out["illegal_moves"] = len(re.findall(r"illegal move", low))
    return out


def incomplete_reason(res: dict, planned: int) -> str | None:
    """Why the match of `res` (a run_sprt result) did NOT end by its own rule, or None when it did: an SPRT verdict
    (its LLR past the bound, parse_fastchess), or all `planned` games with fastchess's own end (agent review finding 2,
    statistics review finding 1, 2026-11-15). On this PC every normal end of a loop match, at a bound or at the cap,
    had exit code 0 and the line "Finished match"; matches cut off by a kill had exit code 1 or 4294967295 and no such
    line; run_logged's own time limit returns -9 (header of pipeline/experiments/loopfix2_los_incomplete.patch.txt).
    A key missing in a result stored before this change (exit_code, finished) counts as not known, not as a fault."""
    if res.get("verdict") in ("H0", "H1"):
        return None
    heat = res.get("heat") or {}
    if res.get("timed_out"):
        return f"killed at its time limit (exit {res.get('exit_code')})"
    if heat.get("stopped_for_heat") or heat.get("stopped_without_reading"):
        return "stopped by the heat guard"
    if res.get("exit_code") not in (0, None):
        return f"fastchess ended with exit code {res.get('exit_code')}"
    if res.get("finished") is False:
        return "fastchess did not print its closing line 'Finished match'"
    if int(res.get("games") or 0) < int(planned):
        return f"{res.get('games')} of {planned} games"
    return None


def _new_stamp(out_dir: Path) -> str:
    # target 63 (23 Nov): the names carry no date and run_logged APPENDS, so a run at the same second of another
    # day wrote into an earlier run's log and was scored by its verdict; a stamp in use here gets a suffix
    base = stamp = time.strftime("%H%M%S")
    k = 1
    while any(out_dir.glob(f"*_{stamp}.*")):
        k += 1
        stamp = f"{base}_{k}"
    return stamp


def run_sprt(cfg: dict, cand_net: str, base_net: str | None, out_dir: Path, seed: int,
             cand_name: str = "cand", base_name: str = "best", fixed_games: int = 0,
             nodes_override: int | None = None, need_complete: bool = False) -> dict:
    """SPRT match, or (fixed_games > 0) a match of exactly that many games with no early stop.

    need_complete (the confirmation, 2026-11-15): a match that ends with no SPRT verdict and did not reach its end
    (incomplete_reason) raises MatchIncomplete, so the stage is played again; the LOS rule never sees it. The gate
    keeps its declared stop rule ("... or N games, or M minutes"): a time limit there is "reject_inconclusive"."""
    s = dict(cfg["sprt"])
    if nodes_override is not None:
        s["nodes"] = nodes_override
    if fixed_games > 0:
        s["max_games"] = fixed_games
    out_dir.mkdir(parents=True, exist_ok=True)
    cand = engine_for_net(cfg, cand_net)
    base = engine_for_net(cfg, base_net)
    stamp = _new_stamp(out_dir)
    flog = out_dir / f"fastchess_{stamp}.out"
    max_games = int(s["max_games"])
    cmd = [s["fastchess"], *_engine_args(cand, cand_name), *_engine_args(base, base_name), "-each", "proto=uci"]
    nodes = int(s.get("nodes", 0) or 0)
    if nodes > 0:
        # fixed nodes per move, no clock: the result does not depend on machine load or timing
        cmd.append(f"nodes={nodes}")
    else:
        cmd.append(f"tc={s['tc']}")
        if s.get("timemargin_ms"):
            cmd.append(f"timemargin={int(s['timemargin_ms'])}")
    cmd += ["-openings", f"file={s['book']}", f"format={s.get('book_format', 'epd')}", "order=random",
            "-srand", str(seed),
            "-rounds", str(max(1, max_games // 2)), "-games", "2", "-repeat",
            "-concurrency", str(int(s["concurrency"])),
            *([] if fixed_games > 0 else
              ["-sprt", f"elo0={s['elo0']}", f"elo1={s['elo1']}", f"alpha={s['alpha']}", f"beta={s['beta']}",
               f"model={s.get('model', 'normalized')}"]),
            "-recover", "-ratinginterval", str(int(s.get("ratinginterval", 20))),
            "-pgnout", f"file={out_dir / f'games_{stamp}.pgn'}", "min=true",
            "-autosaveinterval", "0",
            "-log", f"file={out_dir / f'fastchess_{stamp}.log'}", "level=warn"]
    if s.get("resign_score"):
        cmd += ["-resign", f"movecount={int(s.get('resign_movecount', 3))}", f"score={int(s['resign_score'])}",
                "twosided=true"]
    if s.get("draw_movenumber"):
        cmd += ["-draw", f"movenumber={int(s['draw_movenumber'])}", f"movecount={int(s.get('draw_movecount', 8))}",
                f"score={int(s.get('draw_score', 10))}"]
    if s.get("maxmoves"):
        cmd += ["-maxmoves", str(int(s["maxmoves"]))]
    cmd += [str(a) for a in s.get("extra_args", [])]
    # written before the first game: what is tested, against what, under which rules
    decl = {"written": now(), "candidate": {"name": cand_name, "exe": cand.exe, "exe_sha256": _sha256(cand.exe),
                                            "net": str(cand_net), "net_sha256": _sha256(cand_net), "options": cand.options},
            "opponent": {"name": base_name, "exe": base.exe, "exe_sha256": _sha256(base.exe),
                         "net": str(base_net), "net_sha256": _sha256(base_net), "options": base.options},
            "max_games": max_games, "openings": s["book"], "opening_order": "random", "seed": seed,
            "clock": (f"{nodes} nodes per move, no clock" if nodes > 0 else s["tc"]),
            "timemargin_ms": (None if nodes > 0 else s.get("timemargin_ms")), "concurrency": int(s["concurrency"]),
            "stop_rule": (f"exactly {max_games} games, no early stop (confirmation match)" if fixed_games > 0 else
                          f"SPRT elo0={s['elo0']} elo1={s['elo1']} alpha={s['alpha']} beta={s['beta']} "
                          f"model={s.get('model', 'normalized')}, or {max_games} games, or {s.get('max_minutes', 90)} minutes"),
            "adjudication": {"resign_score": s.get("resign_score", 0), "draw_movenumber": s.get("draw_movenumber", 0),
                             "maxmoves": s.get("maxmoves", 0)},
            "tool": "fastchess (official release binary)", "kind": "screening match of the training loop, not a gate result",
            "command": cmd}
    atomic_write_json(out_dir / f"declaration_{stamp}.json", decl)
    limit_txt = f"{nodes} nodes/move" if nodes > 0 else f"tc {s['tc']}"
    log(f"sprt: {cand_name} vs {base_name}, {limit_txt}, concurrency {s['concurrency']}, "
        f"bounds [{s['elo0']}, {s['elo1']}] {s.get('model', 'normalized')}, max {max_games} games")
    t0 = time.time()
    # heat limit (nnloop/heat.py): a fixed-nodes match gets fewer processor threads when the CPU is at its limit;
    # a clock match is only watched
    guard = MatchHeatGuard(cfg, f"the match {cand_name} vs {base_name}", clock=(nodes <= 0))
    verdict_seen: list[float] = []

    def verdict_in_and_no_exit() -> bool:     # W2: fastchess printed its verdict and hung (round 112's gate)
        own = tail_text(flog, 400000).rsplit("\n===== ", 1)[-1]   # this run only: the log is named by HHMMSS alone
        if parse_fastchess(own)["verdict"] not in ("H0", "H1"):
            return False
        verdict_seen[:] = verdict_seen or [time.time()]
        return time.time() - verdict_seen[0] >= VERDICT_EXIT_GRACE_S

    rc = run_logged(cmd, flog, cwd=str(out_dir), env=child_env(cfg),
                    timeout=float(s.get("max_minutes", 90)) * 60, guard=guard, done=verdict_in_and_no_exit)
    res = parse_fastchess(tail_text(flog, 400000))
    res.update(exit_code=rc, seconds=round(time.time() - t0, 1), cand=str(cand_net), base=str(base_net),
               tc=(f"nodes={nodes}" if nodes > 0 else s["tc"]), concurrency=int(s["concurrency"]), log=str(flog),
               timed_out=(rc == -9), heat=guard.summary())
    if rc == ENDED_AFTER_RESULT:
        res.update(finished=True, ended_after_verdict=True)   # fastchess's verdict ended it; only the exit hung
        ended = [x for x in tail_text(flog, 4000).splitlines() if ":: ENDED" in x][-1:]
        clean = bool(ended) and " 0 still alive" in ended[0] and "process list failed" not in ended[0]
        log(f"sprt: fastchess had not exited {VERDICT_EXIT_GRACE_S:.0f} s after its verdict ({res['verdict']}, "
            f"{res.get('games')} games); {'ended with its engines' if clean else 'ended'}, the result is kept")
        if not clean:   # Fable's C2, 23 Nov: an unproven clean-up is said once, the verdict is still kept
            log("WARNING: the clean-up after that gate is not proven, engines may be left running: "
                + (ended[0].split(" :: ", 1)[-1] if ended else "no ENDED line in its log"))
    _log_heat(guard)
    if guard.aborted:
        # Agent review finding 1 (2026-11-15): a match on the clock (nodes = 0) that the heat guard STOPPED (a minute at
        # the limit, or no temperature reading) ended for the heat, not by its SPRT, its cap or its time limit. Before,
        # its partial log was scored as if it had ended: the gate threw the net away ("reject_inconclusive"), and a
        # confirmation fell back to the LOS rule on a few games (3-0 is LOS 95.8 %). Now nothing of it counts: a note
        # beside its files says so, the CPU gets the yardstick's cool-down (to heat_add_worker_c, at most
        # [sprt] cool_wait_seconds = 600 s), and MatchIncomplete leaves the stage unfinished: it is played again.
        blind = bool(getattr(guard, "aborted_blind", False))
        why = "no temperature reading" if blind else f"CPU up to {guard.cpu_max} C"
        (out_dir / f"STOPPED_FOR_HEAT_{stamp}.txt").write_text(
            f"{now()}: stopped by the heat guard ({why}) after {res.get('games', 0)} games; the games of this attempt "
            f"(games_{stamp}.pgn) are not counted, the match is played again from the start" + chr(10), encoding="utf-8")
        lim = cfg.get("limits") or {}
        t_ok = float(lim.get("heat_add_worker_c", float(lim.get("cpu_temp_pause_c", 92)) - 2.0))
        log(f"sprt: STOPPED by the heat guard ({why}) after {res.get('games', 0)} games; not counted; cooling down, "
            f"then the stage is played again")
        waited, t = 0, cpu_temp(cfg)
        while t is not None and t > t_ok and waited < float(s.get("cool_wait_seconds", 600)):
            time.sleep(20)
            waited += 20
            t = cpu_temp(cfg)
        now_txt = "no reading" if t is None else f"{t:.0f} C"
        raise MatchIncomplete(f"the match {cand_name} vs {base_name} was stopped by the heat guard ({why}) after "
                              f"{res.get('games', 0)} games; not counted, played again from the start (CPU now "
                              f"{now_txt} after {waited} s of cooling down)")
    if "games" not in res or res.get("games", 0) == 0:
        raise RuntimeError(f"fastchess produced no games (exit {rc}); output tail:\n{tail_text(flog, 3000)}")
    planned = 2 * max(1, max_games // 2)          # -rounds max_games // 2, -games 2
    why = incomplete_reason(res, planned)
    res.update(games_planned=planned, complete=(why is None))
    if need_complete and why is not None:
        raise MatchIncomplete(f"the match {cand_name} vs {base_name} did not reach its end ({why}); not counted, "
                              f"played again from the start")
    v = res["verdict"]
    if fixed_games > 0:
        res["fixed_games"] = fixed_games
        res["decision"] = "fixed_length_match"
    else:
        res["decision"] = "promote" if v == "H1" else ("reject" if v == "H0" else "reject_inconclusive")
    log(f"sprt: {res.get('games')} games, W-L-D {res.get('wins')}-{res.get('losses')}-{res.get('draws')}, "
        f"Elo {res.get('elo')} +/- {res.get('elo_err')}, LLR {res.get('llr')}, verdict {v} -> {res['decision']}, "
        f"time forfeits {res['time_forfeits_by_engine'] or 0}")
    return res


def run_anchor(cfg: dict, net: str, out_dir: Path, seed: int, anchor: dict | None = None,
               loop_stop: bool = False) -> dict:
    """Fixed-length match of the engine with `net` against the reference engine of the [anchor] block.

    The reference (official Stockfish with UCI_LimitStrength) is an outside yardstick. The result says
    where the net stands against that yardstick at this time control on this PC. It is not a rating and
    not a gate: nothing is promoted or rejected by it.

    anchor (2026-11-15): another reference than the [anchor] block, as a table with the same keys (missing keys
    are taken from [anchor]). Used for the rated references ([[anchor_extra]]: old official Stockfish releases
    with a published rating) and by pipeline/tools/rated_match.py.

    loop_stop (2026-11-15, agent review finding 8): True when the loop calls (run.py play_yardsticks). The STOP file
    is then looked at after every 20-s sleep of the waits below and before every attempt, and ends the run with
    StopRequested (the stage stays "running" and is played at the next start). A match that has begun is not
    interrupted. Hand tools (rated_match.py, yardstick.py) leave it False: the STOP file of a stopped loop is still
    there while a match is played by hand.
    """
    from .common import stop_requested
    from .datagen_uci import StopRequested
    from .engine import EngineSpec

    def stop_check(what: str) -> None:
        if loop_stop and stop_requested(cfg):
            raise StopRequested(f"STOP file found while the yardstick {what}")

    a = {**(cfg.get("anchor") or {}), **anchor} if anchor else cfg["anchor"]
    s = cfg["sprt"]
    out_dir.mkdir(parents=True, exist_ok=True)
    cand = engine_for_net(cfg, net)
    ref = EngineSpec(a["cmd"], dict(a.get("uci_options", {})), a.get("cwd") or None)
    cand_name = str(cfg["engine"].get("name", "engine"))
    ref_name = str(a.get("name", "reference"))
    games = int(a.get("games", 400))
    tc = str(a.get("tc", s["tc"]))
    conc_set = conc = int(a.get("concurrency", s["concurrency"]))
    # A clock match is only worth its result when every engine has a whole processor thread and the CPU is not
    # at its heat limit (a hot CPU runs slower). So (2026-11-15): look how many threads other programs use now
    # and play fewer games at once; with no room, or a CPU that stays hot, do not play now. The caller then
    # tries again at the end of the next round. [anchor] share_cpu = false gives the old behaviour.
    others = None
    # [anchor] busy_files (2026-11-15): files that exist while a job runs that makes a clock match unfair or hot
    # (Opus's trainings on the graphics card: tmp/exp_gpu.lock). Wait for them to go, at most busy_wait_seconds;
    # still there: not played now.
    busy = [Path(str(f)) for f in (a.get("busy_files") or [])]
    for f in list(busy):
        try:
            age = time.time() - f.stat().st_mtime
        except OSError:   # not there (or gone this instant)
            continue
        if age > 3 * 3600:   # left by a killed job or a reset; the same rule as the training's wait in run.py
            log(f"yardstick: {f} is {age / 3600:.1f} hours old, left over by a killed job: not waited for")
            busy.remove(f)
    waited_busy = 0
    while any(f.exists() for f in busy) and waited_busy < float(a.get("busy_wait_seconds", 1800)):
        if waited_busy == 0:
            log(f"yardstick: waiting for {', '.join(f.name for f in busy if f.exists())} to go (another job has the "
                f"graphics card) before a clock match")
        time.sleep(20)
        waited_busy += 20
        stop_check("waited for a busy file to go")
    if any(f.exists() for f in busy):
        why = f"{', '.join(f.name for f in busy if f.exists())} still there after {waited_busy} s (another job has the graphics card)"
        log(f"yardstick: not played now ({why})")
        return {"skipped": why}
    if a.get("share_cpu", True):
        import os
        n_threads = int(os.cpu_count() or 1)
        others = others_busy_threads(float(a.get("share_measure_seconds", 10)))
        conc = clock_concurrency(conc_set, others, n_threads, int(a.get("min_concurrency", 4)))
        if conc <= 0:
            why = (f"other programs use {others:.1f} of {n_threads} processor threads; a match on the clock "
                   f"would not be fair now")
            log(f"yardstick: not played now ({why})")
            return {"skipped": why}
        lim = cfg.get("limits") or {}
        t_ok = float(lim.get("heat_add_worker_c", float(lim.get("cpu_temp_pause_c", 92)) - 2.0))
        waited = 0
        t = cpu_temp(cfg)
        # No temperature reading (2026-11-15: HWiNFO was not logging after a restart of the PC): the heat guard could
        # not stop a clock match that runs too hot, so the match is not played now and is tried again at the end of
        # the next round. [anchor] need_temperature = false gives the old behaviour (play unwatched).
        if t is None and bool(a.get("need_temperature", True)):
            waited_t, wait_t = 0, float(a.get("temperature_wait_seconds", 300))
            while t is None and waited_t < wait_t:
                if waited_t == 0:
                    log(f"yardstick: no CPU temperature reading (is HWiNFO logging?); waiting up to {wait_t / 60:g} "
                        f"minutes for one before a clock match")
                time.sleep(20)
                waited_t += 20
                stop_check("waited for a temperature reading")
                t = cpu_temp(cfg)
            if t is None:
                why = ("there is no CPU temperature reading (HWiNFO is not logging), so the heat guard could not "
                       "watch a match on the clock")
                log(f"yardstick: not played now ({why})")
                # no_reading: run.py play_yardsticks then puts the other yardsticks of the same call off at once
                # (agent review finding 9)
                return {"skipped": why, "no_reading": True}
        wait_c = float(a.get("cool_wait_seconds", 600))
        while t is not None and t > t_ok and waited < wait_c:
            if waited == 0:
                log(f"yardstick: CPU {t:.0f} C, waiting up to {wait_c / 60:g} minutes for {t_ok:.0f} C or cooler "
                    f"before a clock match")
            time.sleep(20)
            waited += 20
            stop_check("waited for the CPU to cool down")
            t = cpu_temp(cfg)
        if t is not None and t > t_ok:
            why = f"the CPU stayed at {t:.0f} C (above {t_ok:.0f} C) for {waited} s before the start"
            log(f"yardstick: not played now ({why})")
            return {"skipped": why}
        if conc != conc_set:
            log(f"yardstick: other programs use {others:.1f} of {n_threads} threads, so {conc} games at once "
                f"instead of {conc_set}")
    min_conc = int(a.get("min_concurrency", 4))
    stopped = []                 # (games at once, hottest reading) of attempts the heat guard stopped
    # [anchor] running_marker: a file that exists exactly while a clock match plays, so that other jobs
    # (the Opus session's trainings and matches) can keep off the PC meanwhile. Since 2026-11-15 23:36 (agent
    # review finding 3b) it stays for the WHOLE retry loop, cool-downs included, and goes when the loop has ended.
    marker = Path(str(a["running_marker"])) if a.get("running_marker") else None

    def _mark(text: str) -> None:
        nonlocal marker
        if marker is not None:
            try:
                marker.write_text(text + chr(10), encoding="utf-8")
            except OSError:
                marker = None

    try:
        while True:
            stop_check("was about to start a clock match")   # inside the try: a marker of a cool-down goes too
            stamp = _new_stamp(out_dir)
            flog = out_dir / f"fastchess_{stamp}.out"
            cmd = [s["fastchess"], *_engine_args(cand, cand_name), *_engine_args(ref, ref_name), "-each", "proto=uci",
                   f"tc={tc}"]
            if s.get("timemargin_ms"):
                cmd.append(f"timemargin={int(s['timemargin_ms'])}")
            cmd += ["-openings", f"file={s['book']}", f"format={s.get('book_format', 'epd')}", "order=random",
                    "-srand", str(seed), "-rounds", str(max(1, games // 2)), "-games", "2", "-repeat",
                    "-concurrency", str(conc), "-recover", "-ratinginterval", str(int(s.get("ratinginterval", 20))),
                    "-pgnout", f"file={out_dir / f'games_{stamp}.pgn'}", "min=true", "-autosaveinterval", "0",
                    "-log", f"file={out_dir / f'fastchess_{stamp}.log'}", "level=warn"]
            decl = {"written": now(),
                    "engine": {"name": cand_name, "exe": cand.exe, "exe_sha256": _sha256(cand.exe), "net": str(net),
                               "net_sha256": _sha256(net), "options": cand.options},
                    "reference": {"name": ref_name, "exe": ref.exe, "exe_sha256": _sha256(ref.exe), "options": ref.options,
                                  "rating": a.get("rating"), "rating_source": a.get("rating_source")},
                    "games": games, "openings": s["book"], "opening_order": "random", "seed": seed, "clock": tc,
                    "timemargin_ms": s.get("timemargin_ms"), "concurrency": conc, "concurrency_set": conc_set,
                    "other_programs_threads_before_start": (None if others is None else round(others, 1)),
                    "attempts_stopped_for_heat_before_this_one": stopped,
                    "stop_rule": (f"exactly {games} games, no early stop, no adjudication; if the CPU stays at its heat "
                                  f"limit for a minute the match is stopped, thrown away whole and played again from the "
                                  f"start with fewer games at once (the temperature does not depend on who is winning)"),
                    "tool": "fastchess (official release binary)",
                    "kind": "yardstick match against a reference engine; not a rating, not a gate",
                    "command": cmd}
            atomic_write_json(out_dir / f"declaration_{stamp}.json", decl)
            log(f"yardstick: {cand_name} ({Path(str(net)).name}) vs {ref_name} {ref.options}, tc {tc}, {games} games, "
                f"concurrency {conc}")
            t0 = time.time()
            guard = MatchHeatGuard(cfg, f"the yardstick match against {ref_name}", clock=True)
            _mark(f"{now()} clock match against {ref_name}, {games} games, {conc} at once")
            # fewer games at once take longer in the same proportion
            rc = run_logged(cmd, flog, cwd=str(out_dir), env=child_env(cfg),
                            timeout=float(a.get("max_minutes", 60)) * 60 * conc_set / max(1, conc), guard=guard)
            _log_heat(guard)
            if not guard.aborted:
                break
            # stopped (for heat, or because the reading went away): nothing of this attempt counts. Cool down, then
            # fewer games at once, or give up for now.
            blind = bool(getattr(guard, "aborted_blind", False))
            stopped.append([conc, guard.cpu_max])
            (out_dir / f"STOPPED_FOR_HEAT_{stamp}.txt").write_text(
                f"{now()}: stopped by the heat guard "
                + ("because the temperature reading went away" if blind else f"at {guard.cpu_max} C")
                + f" with {conc} games at once; the games of this attempt (games_{stamp}.pgn) are not counted"
                + chr(10), encoding="utf-8")
            if conc <= min_conc or len(stopped) >= 3:
                why = (f"stopped {len(stopped)} time(s) for heat (CPU up to {guard.cpu_max:.0f} C), the last time with "
                       f"{conc} games at once") if guard.cpu_max is not None else (
                       f"stopped {len(stopped)} time(s), the last time with {conc} games at once")
                log(f"yardstick: not played now ({why})")
                return {"skipped": why}
            conc = max(min_conc, conc - 4)
            lim = cfg.get("limits") or {}
            t_ok = float(lim.get("heat_add_worker_c", float(lim.get("cpu_temp_pause_c", 92)) - 2.0))
            _mark(f"{now()} clock match against {ref_name}: cooling down before attempt {len(stopped) + 1}")
            waited, t = 0, cpu_temp(cfg)
            while t is not None and t > t_ok and waited < float(a.get("cool_wait_seconds", 600)):
                time.sleep(20)
                waited += 20
                stop_check("cooled down after a stopped attempt")
                t = cpu_temp(cfg)
            # finding 3a / 3c (2026-11-15 23:36): a replay only when it is cool enough, with a reading, with no busy
            # file, and with room left by the other programs; otherwise not played now (owed to the next round)
            why, no_reading = None, False
            if t is None and bool(a.get("need_temperature", True)):
                why = "no CPU temperature reading after the stopped attempt, so a replay could not be watched"
                no_reading = True
            elif t is not None and t > t_ok:
                why = f"the CPU stayed at {t:.0f} C (above {t_ok:.0f} C) for {waited} s after the stopped attempt"
            elif any(f.exists() for f in busy):
                why = (f"{', '.join(f.name for f in busy if f.exists())} appeared during the cool-down (another job "
                       f"has the graphics card)")
            elif a.get("share_cpu", True):
                import os
                n_threads = int(os.cpu_count() or 1)
                others = others_busy_threads(float(a.get("share_measure_seconds", 10)))
                room = clock_concurrency(conc_set, others, n_threads, min_conc)
                if room <= 0:
                    why = (f"other programs use {others:.1f} of {n_threads} processor threads after the stopped "
                           f"attempt; a match on the clock would not be fair now")
                else:
                    conc = min(conc, room)
            if why is not None:
                log(f"yardstick: not played again now ({why})")
                return {"skipped": why, "no_reading": no_reading}
            seed += 1
            log(f"yardstick: playing it again from the start with {conc} games at once (CPU now "
                f"{'no reading' if t is None else f'{t:.0f} C'})")
    finally:
        if marker is not None:
            marker.unlink(missing_ok=True)
    res = parse_fastchess(tail_text(flog, 400000))
    res.update(exit_code=rc, seconds=round(time.time() - t0, 1), net=str(net), reference=ref_name,
               reference_options=ref.options, tc=tc, concurrency=conc, log=str(flog), heat=guard.summary(),
               reference_rating=a.get("rating"), reference_rating_source=a.get("rating_source"),
               attempts_stopped_for_heat=stopped,
               other_programs_threads_before_start=(None if others is None else round(others, 1)))
    if "games" not in res or res.get("games", 0) == 0:
        raise RuntimeError(f"fastchess produced no games (exit {rc}); output tail:" + chr(10) + tail_text(flog, 3000))
    log(f"yardstick: {res.get('games')} games, W-L-D {res.get('wins')}-{res.get('losses')}-{res.get('draws')}, "
        f"Elo {res.get('elo')} +/- {res.get('elo_err')} against {ref_name}, "
        f"time forfeits {res['time_forfeits_by_engine'] or 0}")
    return res
