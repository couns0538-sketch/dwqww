# Neon Memory (Server Day Debate)

Updated: 2026-11-23T13:49:12Z (UTC). Stop time: 18:35Z (~4h 46m remaining).
Active branch: `debate/server-plan-20261123`.

## Current state of the server-day plan
- **`SETUP_PLAN.md` v2.2** (`35b8c34424e4...`, Fable `203408Z`):
  - **ALL decisions `D1`–`D15`, Section 2, and Section 4 are SETTLED.** Every row of Section 7 has a planted test.
  - PC measurements (`M2`, `M3`, `M5`, `M6`, `M7`) are in Section 10. Note: Astra `134405Z` measured full `python-chess` move/FEN replay at `35,509` raw rows/s (11.5x slower than v1 parse/bind/opening `409,876` r/s) and caught a critical `uci.cpp` semantics edge: on `drawadj` (`uci.cpp:540-549`), the last `sg` row is pushed BEFORE `break` and BEFORE `make_move` (`571`), so its move is legal on `sgend fen` and NOT applied to `sgend fen`/`sgend moves`. Confirmed directly in `loop/source/src/uci.cpp:515-573`; M2 will need re-measurement on the PC with full rules replay.
- **`FORMATS.md` 2.1** (previewed in Fable `204334Z` §1, writing now):
  - Fable accepted ALL 10 points from Neon (`133945Z`, `134130Z`) and Astra (`133900Z`, `134153Z`): wire `.zz` compression of every control file, index-ordered `epoch` monotonicity, per-piece interval table `(first_counter, last_counter)` + on-disk 5-field payload index (`W5(e)`), fenced end-of-day + seal-only finalizer + `packed_bytes: null` for unoffered pieces, Stage `b` waiting while pieces are in transit + A26 conflict record, 0-row pieces offered as `"raw"` without converter failure, atomic `os.link(tmp, final)` no-overwrite publish, exact `.raw`/`bind` byte rules, `run_fingerprint`/join keys, no floats.
  - Added note (`134912Z`) to include the exact `drawadj` unplayed-last-row rule in §2.2.
- **Section 5 (first-debate Neon tools):** Closed cleanly (`204334Z` §4: recorded as non-evidence, no reconstruction during server-day hours).

## Approval Ledger State (`scripts/` v1 + `scripts_v2/` batch 1)
- **Package 1 (`scripts/`, 17 scripts):** `0` effective `YES` across all 3 seats. Frozen as historical baseline.
- **Package 2 (`scripts_v2/`, Fable `341cb266bc` — first 3 files, audited line-by-line & tested live on Linux `134912Z`):**
  - `test_uciproc.py` passed `31/31` on `scripts_v2/` and failed `15/27` on `scripts/` (v1) with our Linux AVX2+PGO+LTO build.
  - **HOWEVER, 5 targeted adversarial probes reproduced 5 real bugs -> `NOT YET` on all 3 (`134912Z`):**
    1. `scripts_v2/run/engine_lines.py` (`ec66b3d6f25f...`): `NOT YET` — line 40 accepts ASCII control bytes (`\x00`, embedded `\r`, `\x1b`, `\x7f`) in `INFO_ALLOWED` and `_OTHER` `.*` (embedded `\r` splits `.raw` lines in `splitlines()`!); line 29 `-?[01]` accepts `sgend result -0`.
    2. `scripts_v2/run/uciproc.py` (`15ff49a8bb75...`): `NOT YET` — (a) lines 84–88 & 106–111 allow `\x00`, embedded `\r`, control bytes on recv & send; (b) lines 98–103 `_exit_text()` calls `p.wait(timeout=5)` ignoring `secs`/`cutoff` (blocked `5.01 s` past `0.30 s` cutoff); (c) lines 152–153 `max_lines` leaves `self.gone == ""` (next `ready()` silently consumed 8 stale lines); (d) line 171 `uci_options()` omits `cutoff=None`; (e) lines 142–158 drop `info string ERROR NNUE v3` on `exit(2)` (`uci.cpp:1062/1223`) and hang to `EngineTimeout` on `sgerror` without `sgend` (`uci.cpp:499/556/1213`).
    3. `scripts_v2/tests/test_uciproc.py` (`02859ba14c38...`): `NOT YET` — missing test cases for all 5 bugs above; line 137 scans only `*.cpp` instead of `*.cpp`/`*.h`/`*.hpp`.
  - **0 effective `YES` in `scripts_v2/` so far.**

## Next actions
1. Commit & push `134912Z` review + memory update.
2. Watch for:
   - Fable's `FORMATS.md` 2.1 (read line-by-line and vote `AGREE` once clean!).
   - Revised `scripts_v2/` batch 1 (`engine_lines.py`, `uciproc.py`, `test_uciproc.py`) -> re-verify every byte & re-run all 5 adversarial probes -> issue `YES` when 100% clean!
   - Opus/Fable's next `scripts_v2/` files (`record.py`, `worker.py`, `packer.py`, `tools/`, `linux/`, `home/`, guards, tests) -> line-by-line review + live Linux fault tests for every single file.
3. Keep updating `debate/memory/neon.md` every ~10 minutes; continue until `18:35Z`.
