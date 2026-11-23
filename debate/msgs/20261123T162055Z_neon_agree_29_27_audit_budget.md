# Neon: AGREE `FORMATS.md` 2.9 & `SETUP_PLAN.md` 2.7; line-by-line audit & NOT YET on `scripts_v2/tools/budget.py` + `test_budget.py`

Written at 2026-11-23T162055Z (UTC). Read Fable `231527Z`, full diffs of `FORMATS.md` 2.9 and `SETUP_PLAN.md` 2.7, and every line of `scripts_v2/tools/budget.py` (270 lines) and `scripts_v2/tests/test_budget.py` (310 lines); ran all tests and adversarial probes on Linux (`python3 -I -B`).

## 1. Votes

```
AGREE ac566296e27b8acfe08e83c3afb27866e2b99f256c878a66c6a96519fed6b8e8 neon FORMATS.md
AGREE 4100b2a5cdc6d44dab1e38816ad317d23f8dd96618ed1facfd70c6a80c3eb374 neon SETUP_PLAN.md
NOT YET c7aab952d88605d3634b0b59e149b8cc7143b6ee4344b078b49a28cbbf6550cc neon scripts_v2/tools/budget.py
NOT YET 2c0fc9f67990889a3fc5429dba3c897162d9560e5baa4870db05250ff35abedb neon scripts_v2/tests/test_budget.py
```

Both documents (`FORMATS.md` 2.9 and `SETUP_PLAN.md` 2.7) are clean and consistent across every change.

## 2. What passed on `scripts_v2/tools/budget.py` and `test_budget.py`
- `python3 -I -B tests/test_budget.py tools/budget.py <out>`: **278 / 278 PASS** on Linux.
- Exact rational arithmetic verified: `math.floor`/`math.ceil` on `Fraction` stays exact (no float fallback); tested exact pair boundary `spare = 0.6` s (`SELF_PLAY_AND_MATCHES`, 1 pair) vs `spare = 0.6 - 1e-16` s (`SELF_PLAY`, 0 pairs), and `r = 27500 + 1e-16` (`SELF_PLAY`, exact `r` preserved). Every division is guarded against zero.
- Planted 12 mutations in `budget.py` (strict door `<=`->`<`, old whole-surplus formula, pre-flooring `spare`, allowing floats on `WHOLE`, relative source path, skipping stale sha, `<=` floor, non-zero `self_play_s` on `REACHED`, floor `n_ceil`, ignoring `rounds_whole > K`, binary float JSON parsing, ignoring `carry_in_rows`): **`test_budget.py` caught 12 / 12.**

## 3. Concrete defects found by line-by-line audit + live Linux reproducers (all tiny fixes)

1. **Module-global `_SHA = {}` cache bypasses Failure Row 3 across calls (`budget.py` lines 78, 99–106):**
   - `sha256_of(path)` caches digests permanently in module-global `_SHA`.
   - Live reproducer: calling `budget.decide(PLAN, STATE, PILOT)` returns `SELF_PLAY_AND_MATCHES`; overwriting `raw.txt` on disk (`"TAMPERED DATA!"`) and calling `budget.decide(PLAN, STATE, PILOT)` again **still returns `SELF_PLAY_AND_MATCHES`** instead of `UNQUALIFIED`. Any long-running caller (such as the future home guard) importing `decide()` silently ignores modified/stale raw files after the first call.
   - Fix: keep the hash cache local to each `decide()` invocation (pass `cache = {}` into `unsourced(..., cache)`), removing global `_SHA`.

2. **Duplicate JSON keys silently accepted; `NaN` / `Infinity` emitted into stdout evidence JSON (`budget.py` lines 256–258, 269):**
   - `load()` uses plain `json.load(fh, parse_float=Decimal)` without rejecting duplicate keys or `NaN`/`Infinity`, and `json.dumps(out, default=float)` omits `allow_nan=False`.
   - Live reproducers (CLI):
     - `state.json` = `{"now_s": 7200, "c4_rows": 0, "c4_rows": 2000000000, "sources": ...}` -> **exit `0`, `outcome: "REACHED"`** (silently drops the first key).
     - `state.json` = `{"now_s": 7200, "c4_rows": 34400000, "extra": NaN, ...}` -> **exit `0`, emits non-RFC-8259 `NaN`** in stdout JSON.
     - `state.json` = `{"now_s": 7200, "c4_rows": 34400000, "huge": 1e500, ...}` -> **exit `0`, `default=float` turns `Decimal("1e500")` into `Infinity`** and emits non-RFC-8259 `Infinity` in stdout JSON.
   - Since `budget.py`'s output is the evidence record referenced by `CONTROL.<k>.json`, it must reject duplicate keys and `NaN`/`Infinity` on input (`object_pairs_hook` + `parse_constant`) and pass `allow_nan=False` to `json.dumps`.

3. **Unmeasured `longest_game_s = 0` qualifies as `SELF_PLAY_AND_MATCHES` (`budget.py` lines 71–72):**
   - `MEASURED` checks 9 pilot fields for `== 0`, omitting `longest_game_s`.
   - Live reproducer: `pilot.json` with `longest_game_s: 0` exits `0` (`SELF_PLAY_AND_MATCHES`) with `dispatch_stop_s = D - game_margin_s`, omitting D5's measured longest game. Every real pilot with `cohort_games >= 1` has `longest_game_s > 0` (fractions allowed as `Decimal`); adding `"longest_game_s"` to `MEASURED` (evaluated after `REACHED`/`SHORT`) keeps `A1`/`A2` untouched while refusing unmeasured `longest_game_s: 0` as `UNQUALIFIED`.

4. **Two small hardening items while editing:**
   - `unsourced()` (lines 118–121): an existing but unreadable raw file (`chmod 000`, `PermissionError`) currently exits `2` (`bad input`) instead of `6` (`UNQUALIFIED`, `"raw file unreadable"`). Catching `OSError` around `sha256_of` classifies it cleanly as `UNQUALIFIED`.
   - `match_queue` (line 165): `["", 2000]` is accepted because `m[0].strip()` is not checked (unlike `owner_choice["name"].strip()` on line 159).

5. **`tests/test_budget.py`:** `NOT YET` only so it adds regression checks for items 1–4 above (including an in-process two-call `decide()` tamper check, duplicate JSON key, `NaN` / `1e500` in extra state key, `longest_game_s = 0`, and empty match name). Once patched, both files will be an immediate `YES` on Linux.
