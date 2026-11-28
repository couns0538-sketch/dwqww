"""Heat limit for matches (added 2026-11-15, 08:00).

Why: until now only self-play (HeatGuard in datagen_uci.py) and the tuner obeyed the owner's CPU limit
([limits] cpu_temp_pause_c, 92 C). Matches played by fastchess did not: on 2026-11-15 match games beside a
training on the graphics card held the CPU at 92 to 94 C for 28 minutes. The owner asked that everything the
loop does keeps to the heat guards.

How, for a match at fixed nodes per move (no clock): the match is not paused. It is given FEWER PROCESSOR
THREADS (the CPU affinity of fastchess and its engines, a property of these processes only, no admin rights,
gone when they end). At the pause temperature or above on 2 checks in a row the match loses 2 threads (one
core), down to match_min_cpus (default: heat_min_workers, 4); 2 C or more above it, 4 threads at the first
check; at heat_add_worker_c or below on 2 checks in a row it gets 2 back. The engines then share fewer cores and run slower, and every game goes on: no engine is
stopped, no answer is late (there is no clock), and at fixed nodes the moves do not depend on speed.

A match on the clock (the yardstick against Stockfish) must not be slowed down while it runs: slowed engines
lose on time or play weaker, and the result would be worth nothing. So for such a match the guard watches, and
when the CPU is at the pause temperature on match_clock_abort_checks checks in a row (default 3, one minute) it
STOPS the match (`aborted` is then True). The caller plays it again from the start with fewer games at once
(nnloop.match.run_anchor does). Use clock_concurrency() before the start as well.
(Added 08:45 the same day: a 200-game clock test with 11 games at once beside a training on the graphics card
ran at 92 to 95 C for four minutes; the first version only reported that.)

No temperature reading (HWiNFO's log is off): nothing is changed. Switch: [limits] match_heat_guard = false.
"""
from __future__ import annotations

import os
import threading
import time

from .common import log, read_hwinfo


def cpu_temp(cfg: dict | None) -> float | None:
    """CPU temperature in C from HWiNFO's log, or None. NNLOOP_FAKE_CPU_FILE (a test hook) overrides it."""
    fake = os.environ.get("NNLOOP_FAKE_CPU_FILE")
    if fake:
        try:
            with open(fake, encoding="ascii") as fh:
                return float(fh.read().strip())
        except (OSError, ValueError):
            pass
    try:
        h = read_hwinfo(cfg)
    except Exception:  # noqa: BLE001
        return None
    return None if not h or h.get("cpu_c") is None else float(h["cpu_c"])


class MatchHeatGuard:
    """Watches one running match (a process and all its children). See the text at the top of this file.

    temp, apply, kill: replaced in tests (apply(pid, list of cpu numbers); kill(pid)).
    """

    def __init__(self, cfg: dict, what: str = "match", clock: bool = False, temp=None, apply=None, say=log,
                 kill=None):
        lim = cfg.get("limits") or {}
        self.cfg, self.what, self.clock, self.say = cfg, what, bool(clock), say
        self.on = bool(lim.get("heat_guard", True)) and bool(lim.get("match_heat_guard", True))
        self.t_pause = float(lim.get("cpu_temp_pause_c", 92))
        self.t_add = float(lim.get("heat_add_worker_c", self.t_pause - 2.0))
        self.every = float(lim.get("match_heat_check_seconds", lim.get("heat_check_seconds", 20)))
        self.min_cpus = max(1, int(lim.get("match_min_cpus", lim.get("heat_min_workers", 4))))
        self.step = max(1, int(lim.get("match_cpu_step", 2)))
        self.abort_checks = int(lim.get("match_clock_abort_checks", 3))     # clock matches only; 0 = never stop one
        self.aborted = False
        self.aborted_blind = False     # stopped because the reading went away (not for heat)
        # No temperature reading (HWiNFO not logging, as after the PC restarts of 2026-11-15): the guard is blind, so
        # it is careful instead: after blind_checks checks in a row a fixed-nodes match is confined to
        # blind_match_cpus threads until a reading is back. 0 switches this off. A match on the clock cannot be
        # confined, so (Opus 2026-11-15, agent review finding 4) it is STOPPED like a hot one after
        # max(blind_checks, match_clock_abort_checks) checks without a reading; its caller then does not replay it
        # without a reading (run_anchor). match_clock_abort_checks = 0 or blind_match_cpus = 0: the old behaviour.
        self.blind_cpus = int(lim.get("blind_match_cpus", 8))
        self.blind_checks = max(1, int(lim.get("blind_checks", 3)))
        self.blind = 0
        self.said_blind = False
        self._kill_fn = kill or _kill_tree
        self._temp = temp or (lambda: cpu_temp(cfg))
        self._apply_fn = apply or _set_affinity
        self.pid = None
        self.base: list[int] = []
        self.total = self.allowed = self.fewest = 0
        self.hot = self.cool = self.changes = 0
        self.cpu_max = None
        self.hot_s = 0.0          # seconds at or above the pause temperature
        self.lost_s = 0.0         # seconds of match time lost to the smaller share (for the caller's time limit)
        self.said_floor = self.said_clock = False
        self._stop = threading.Event()
        self._thread = None

    # ---- life cycle -------------------------------------------------------------------------------
    def start(self, pid: int) -> None:
        self.pid = int(pid)
        if not self.on:
            return
        try:
            import psutil
            self.base = sorted(psutil.Process(self.pid).cpu_affinity())
        except Exception as e:  # noqa: BLE001
            if not self.clock:
                self.say(f"match heat guard: cannot read the processor threads of the match ({type(e).__name__}); "
                         f"it only watches the temperature")
            self.base = []
        self.total = self.allowed = self.fewest = len(self.base)
        self._thread = threading.Thread(target=self._run, name="match-heat-guard", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.wait(self.every):
            try:
                self.tick()
            except Exception as e:  # noqa: BLE001
                self.say(f"match heat guard: error {type(e).__name__}: {str(e)[:120]}; the match goes on")

    def stop(self) -> dict:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=10)
        return self.summary()

    def summary(self) -> dict:
        return {"on": self.on, "clock": self.clock, "cpu_max_c": self.cpu_max, "seconds_at_limit": round(self.hot_s),
                "threads_total": self.total, "threads_fewest": self.fewest, "changes": self.changes,
                "seconds_lost": round(self.lost_s), "stopped_for_heat": self.aborted and not self.aborted_blind,
                "stopped_without_reading": self.aborted_blind}

    def lost_seconds(self) -> float:
        return self.lost_s

    # ---- one check --------------------------------------------------------------------------------
    def tick(self) -> None:
        t = self._temp()
        if t is None:
            # 7b (Opus 2026-11-15 23:40, agent review finding 7): a missing reading leaves the hot / cool counts as they
            # are (before: reset to 0, so alternating hot / missing readings never reached 2 or 3 checks in a row)
            self.blind += 1
            if self.blind_cpus > 0 and self.blind >= self.blind_checks:
                if not self.clock and self.total:
                    cap = max(self.min_cpus, min(self.total, self.blind_cpus))
                    if self.allowed > cap:
                        self.say(f"match heat guard: NO temperature reading on {self.blind} checks in a row (is HWiNFO "
                                 f"logging?). {self.what} runs on {cap} of {self.total} threads until one is back "
                                 f"(was {self.allowed})")
                        self.allowed = cap
                        self.fewest = min(self.fewest, cap)
                        self.changes += 1
                        self._apply_fn(self.pid, self.base[: self.allowed])
                    elif self.allowed < self.total:
                        self._apply_fn(self.pid, self.base[: self.allowed])    # engines started since the last check
                elif (self.clock and self.abort_checks > 0 and not self.aborted
                      and self.blind >= max(self.blind_checks, self.abort_checks)):
                    self.aborted = self.aborted_blind = True
                    self.say(f"match heat guard: NO temperature reading on {self.blind} checks in a row during "
                             f"{self.what} (is HWiNFO logging?). A match on the clock cannot be watched without one, so "
                             f"it is STOPPED; it is not played again until a reading is back.")
                    self._kill_fn(self.pid)
                    return
                elif not self.said_blind and not self.aborted:
                    self.said_blind = True
                    self.say(f"match heat guard: NO temperature reading during {self.what} (is HWiNFO logging?). "
                             + ("A match on the clock cannot be slowed down; it goes on unwatched."
                                if self.clock else "It cannot be given fewer threads here."))
            elif self.allowed < self.total:
                self._apply_fn(self.pid, self.base[: self.allowed])
            self._account()
            return
        self.blind = 0
        self.cpu_max = t if self.cpu_max is None else max(self.cpu_max, t)
        if t >= self.t_pause:
            self.hot, self.cool = self.hot + 1, 0
            self.hot_s += self.every
        elif t <= self.t_add:
            self.hot, self.cool = 0, self.cool + 1
        else:
            self.hot = self.cool = 0
        if self.clock and self.abort_checks > 0 and self.hot >= self.abort_checks and not self.aborted:
            self.aborted = True
            self.say(f"match heat guard: CPU {t:.0f} C on {self.hot} checks in a row during {self.what}. A match on "
                     f"the clock cannot be slowed down, so it is STOPPED and played again with fewer games at once.")
            self._kill_fn(self.pid)
            return
        if self.clock or not self.total:
            if self.hot >= 2 and not self.said_clock and not self.aborted and not (self.clock and self.abort_checks > 0):
                self.said_clock = True
                self.say(f"match heat guard: CPU {t:.0f} C during {self.what}. "
                         + ("It is played on the clock, so it is not slowed down; the hottest reading goes into its result."
                            if self.clock else "It cannot be given fewer threads here."))
            return
        new = self.allowed
        # 2 C or more over the limit: act on the first such check and take two steps at once (2026-11-15 08:57:
        # in its first real use the guard needed four minutes to get from 16 to 8 threads and the CPU reached 94 C)
        urgent = t >= self.t_pause + 2.0
        if self.hot >= 2 or (urgent and self.hot >= 1):
            if self.allowed > self.min_cpus:
                new = max(self.min_cpus, self.allowed - (2 * self.step if urgent else self.step))
            elif not self.said_floor:
                self.said_floor = True
                self.say(f"match heat guard: CPU {t:.0f} C and {self.what} is already down to {self.allowed} of "
                         f"{self.total} threads; the heat comes from other programs")
            self.hot = 0
        elif self.cool >= 2 and self.allowed < self.total:
            new = min(self.total, self.allowed + self.step)
            self.cool = 0
        if new != self.allowed:
            self.say(f"match heat guard: CPU {t:.0f} C, {self.what} now runs on {new} of {self.total} threads "
                     f"(was {self.allowed})")
            self.allowed = new
            self.fewest = min(self.fewest, new)
            self.changes += 1
            self.said_floor = False
            self._apply_fn(self.pid, self.base[: self.allowed])
        elif self.allowed < self.total:
            self._apply_fn(self.pid, self.base[: self.allowed])    # engines started since the last check
        self._account()

    def _account(self) -> None:
        if self.total and self.allowed < self.total:
            self.lost_s += self.every * (1.0 - self.allowed / self.total)


def _kill_tree(pid: int) -> None:
    """End the process `pid` and all its children (a match that must stop)."""
    try:
        import psutil
        p = psutil.Process(pid)
        procs = p.children(recursive=True)
    except Exception:  # noqa: BLE001
        return
    for q in [p, *procs]:          # fastchess first, so it starts no new engines
        try:
            q.kill()
        except Exception:  # noqa: BLE001
            pass


def _set_affinity(pid: int, cpus: list[int]) -> None:
    """Give the process `pid` and all its children exactly these processor threads."""
    if not cpus:
        return
    try:
        import psutil
        p = psutil.Process(pid)
        procs = [p, *p.children(recursive=True)]
    except Exception:  # noqa: BLE001
        return
    for q in procs:
        try:
            q.cpu_affinity(list(cpus))
        except Exception:  # noqa: BLE001
            pass


def others_busy_threads(seconds: float = 8.0) -> float | None:
    """How many processor threads the whole PC is using right now (measured over `seconds`), or None."""
    try:
        import psutil
        return psutil.cpu_percent(interval=seconds) / 100.0 * float(psutil.cpu_count(logical=True) or 1)
    except Exception:  # noqa: BLE001
        return None


def clock_concurrency(configured: int, others: float | None, n_threads: int, min_conc: int = 4) -> int:
    """Games at once for a match ON THE CLOCK when other programs use `others` threads. 0 = no room now.

    A clock match is only worth its result when every engine gets a whole thread. The loop's setting
    (12 games on 16 threads) leaves a quarter free; the same share of what is left is used here. With fewer
    than min_conc + 1 threads left the match is not played now.
    """
    configured = int(configured)
    if others is None:
        return configured
    room = float(n_threads) - float(others)
    if room < min_conc + 1:
        return 0
    return max(min_conc, min(configured, int(room * configured / float(n_threads) + 0.5)))
