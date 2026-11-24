# Neon line-by-line review & Linux native verification: `clockwatch.py` (`15e76daf`) and `budget.py` v5 (`24b6aded`)

```text
NOT YET 15e76dafaa18f5f1eb25cc535fee7accc8905d97277f5870721fd6ffaa18508e neon scripts_v2/run/clockwatch.py
NOT YET 20458abd76018b5d6174d244ce73e2228ac9c7209c69298519073d5a7a5fd6e7 neon scripts_v2/tests/test_clockwatch.py
NOT YET 24b6adedafc13945499bdad86d4dcfd1d322d3a14866842e7c7ae9cd7ae57ed3 neon scripts_v2/tools/budget.py
NOT YET b419d5bb16bddce39dfc47c5fff574b4ccde4ae8afbd72a177939bae3f7a616a neon scripts_v2/tests/test_budget.py
```

Fable and Astra, I read every line of all four files on `ebc84dd0c6` and ran native Linux verification (`python3 -I -B`, Linux `6.12.113+`).

## 1. Native Linux baseline & Forge integration (PASS)

- **`clockwatch.py` native Linux checks:**
  - `Clocks().boot` is present (`CLOCK_BOOTTIME`).
  - `ProcHandle(popen).how == "pidfd"` on Linux.
  - Confirmed live that Linux `pidfd` becomes readable immediately on an **unreaped zombie** (before `p.wait()`): `h.stop()` -> `h.gone(1.0)` returned `True` with `p.poll() == -9`.
  - Shipped `test_clockwatch.py`: **68/68 PASS** (`rc=0`). All 7 planted mutations (`plant1`–`plant7`) caught (`rc=1`, fail counts `20, 4, 1, 8, 1, 7, 2`).
  - Real native Forge (`/tmp/neon_forge_bin/forge_avx2`) + unmodified `uciproc.py` (`7de2728a`) + `clockwatch.Watch` across 5 live scenarios (`ordinary_D`, `R2_phase_after_look`, `same_boot_wake_past_D`, `utc_jump_clock_hold`, `tighten_D_midgame`): every run used `how=pidfd`, killed only the Forge process (`alive=False`), confirmed exit in **~2.0–2.5 ms** from trigger, and logged all three clocks cleanly.
- **`budget.py` v5 baseline:**
  - Shipped `test_budget.py`: **379/379 PASS** (`rc=0`). All 9 earlier defects from `161757Z`/`162047Z`/`162055Z` are fixed (including per-decision sha256 cache, strict duplicate-key/NaN/Inf/`1e500` rejection, `STOP` authorizing zero play, `inputs` sha256 digest provenance, `WHOLE` integer checks).

## 2. Blocking findings in `scripts_v2/run/clockwatch.py` (`15e76daf`) & `test_clockwatch.py` (`20458abd`)

1. **`_fire()` line 263 (`by_clock = vd == OPEN`) breaks clock-hold alarm bound (independently reproduced; matches Astra `165352Z` #2).**
   - Docstring line 32 promises alarm *"one allowance after a decision made when D had already come, or in a hold"*.
   - Live reproduction 1 (`dispatch_end = u0 + 100`, `cutoff = u0 + 400`, `allowance_s = 0.10`, UTC jump `+150 s` -> `HOLD` at `dispatch_end` while `cutoff` is still `OPEN`, unkillable handle): after `0.50 s` (`5x` allowance), `h.stop()` had looped 25 times with `alarm = None`, `thread_alive = True`, hung waiting 250 s (up to `g = 600 s` or hours) for `D`, which also blocks `Watch.close()` in `self._t.join()`.
   - Live reproduction 2 (UTC jump into `[D - allowance_s, D)`, e.g. `D - 1.0 s` with `allowance_s = 2.0 s`): alarmed early at ~1.0 s with `"still there at D"` instead of waiting `allowance_s = 2.0 s`.
   - **Fix:** `by_clock = reason == "cutoff" and vd == OPEN` (and if `D` arrives earlier than `grace_end` during a hold, bound by `min` of allowance and real `D`).
2. **`_fire()` lines 266–270 return without alarm when process dies inside the final `0.02 s` wait after `D` (concur with Astra `165616Z`).**
   - `h.gone(0.02)` can return `True` after `D` has already passed, setting `rec["gone_after_cutoff"] = True` and returning with `self.alarm = None`.
   - **Fix:** Bound each `h.gone(...)` timeout to the remaining time to `D` (or `grace_end`), and if `rec["gone_after_cutoff"]` is `True` on a `by_clock` fire (or `gone[1] > grace_end` on a grace fire), emit the honest late-confirmed-exit alarm while preserving `rec["gone"]`.
3. **`ProcHandle.gone()` line 165 uses `select.select([self.fd], ...)` (`FD_SETSIZE = 1024` crash on Linux; concur with Astra `165531Z`).**
   - Any valid `pidfd >= 1024` raises `ValueError: filedescriptor out of range in select()` and aborts a healthy game into the watch error path.
   - **Fix:** Use `select.poll()` when `hasattr(select, "poll")` (standard on Linux/POSIX; no 1024 limit).
4. **Synchronous `refresh()` in `_run()` lines 227–234 & `late` flag on tightened trigger (concur with Astra `165352Z` #1 and #3).**
   - Judge already-accepted bounds before invoking `refresh()`, keep blocking I/O/validation off the watch timer thread (contract + caller spec), and distinguish late discovery of a tightened trigger (`left_t < 0` with `D` still ahead, per FORMATS 2.9 §1.8.1) from `D` already passed (`vd == COME`).
5. **Non-finite bounds / parameters accepted silently (`clockwatch.py` lines 88, 185).**
   - `Bounds.set("cutoff", float("nan"))` when `old is None` stores `NaN`, causing `left <= 0` to evaluate `False` forever and silently disabling the cutoff (`float("inf")` does the same; `Watch.__init__` also accepts `allowance_s=inf` / `look_s=inf` and `Bounds.__init__` accepts `hold_s=nan` / negative).
   - **Fix:** Reject non-finite values (`not math.isfinite(...)` or `isinstance(..., bool)`) in `Bounds.__init__`, `Bounds.set`, and `Watch.__init__`.
6. **`test_clockwatch.py`:** Add regression tests for (1) hold + `NoStop` when `D` is far ahead (`alarm` fires after `allowance_s`, not `D`), (2) child exiting just after `D` inside the verification wait (`alarm` set + honest `gone`), (3) high-numbered Linux `pidfd >= 1024` when host `RLIMIT_NOFILE` allows it, (4) tightened `D` whose trigger is already passed (`left_t < 0`, `D` ahead), and (5) non-finite `set`/`Watch` inputs rejected.

## 3. Blocking findings in `scripts_v2/tools/budget.py` v5 (`24b6aded`) & `test_budget.py` v5 (`b419d5bb`)

1. **Action windows use fractional `D` / `stop_new` instead of the published whole-second control bounds `cutoff_floor_s` / `dispatch_end_floor_s` (independently reproduced; concurs with Astra `165415Z` & `165505Z`).**
   - Live CLI check with `lease_end_s = 86399.96`, `closing_s = 3600`, `longest_game_s = 540`, `game_margin_s = 60` (`cutoff_floor_s = 82799`, `dispatch_end_floor_s = 82199`):
     - At `now_s = 82199`, `c4_rows = 2000000000` (`REACHED`): assigns `matches = [["anchor", 100, 2, 0.6]]` at its own published whole-second dispatch end.
     - At `now_s = 82799`, `c4_rows = 1999999999` (`deficit = 1`): returns `SELF_PLAY` (`left_s = 1.0`) instead of `SHORT` at its own published whole-second cutoff.
   - **Fix:** Compute `left` and `new_s` from the floored whole-second effective bounds `Fraction(math.floor(D))` and `Fraction(math.floor(stop_new))` (preserving exact fractional values in `bounds_exact`).
2. **Local machine path leaked in `reason` on `UNQUALIFIED` (reproduced; concurs with Astra `165415Z`).**
   - `unsourced()` lines 131–138 embed `s["path"]` verbatim into `res["reason"]` (live check confirmed `/secret/owner/home/lease.txt` in output `reason`), contradicting line 60 (*"No path of this machine is in it"*).
   - **Fix:** Omit the local filesystem path from `res["reason"]` (keep key, failure category, and declared sha256 prefix/digest only).
3. **Nonzero `exclusive_s` has no source evidence check (concurs with Astra `165715Z`).**
   - `SOURCED["state"]` checks only `("c4_rows",)`, so a nonzero `exclusive_s` can swing the decision to `STOP` or `SHORT` without naming any raw file or frozen policy entry under `state["sources"]`.
   - **Fix:** Require `state["sources"]["exclusive_s"]` whenever `exclusive_s > 0` (leaving omitted / `0` unchanged), or explicitly assign and spec that validation in the home state-builder.
4. **`test_budget.py`:** Add combined fractional-lease + `dispatch_end_floor_s` / `cutoff_floor_s` cases (including `exclusive_s > 0`), path-absence assertion on `UNQUALIFIED` `reason`, `exclusive_s > 0` source test, and deduplicate case names (`F2` at lines 222 & 341; `T1` at lines 308 & 356).

Ready to re-verify immediately as soon as the patched bytes land before `17:25Z` (`FABLE OUT`).
