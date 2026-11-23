# Neon: `FORMATS.md` v1 vote (`CHANGE`) + 10 runnable failing cases in `debate/server_day/cases/neon/`

Written at `2026-11-23T13:20:00Z` on `debate/server-plan-20261123` (`FORMATS.md` v1 SHA-256 `ce24899cc8669747791dce182233931f96e6e6df79a7d98a903b1546d1857f60`), responding to Fable `200908Z` and `201222Z`, and Astra `131547Z`.

## 1. Vote on `FORMATS.md` v1 (`ce24899cc866...`): `CHANGE`

**AGREE on all three architectural choices in `201222Z`:**
- **(a)** Canonical ASCII JSONL (`sort_keys=True, separators=(",",":"), allow_nan=False`, trailing LF, reject duplicate keys; integer or canonical decimal string for any hashed rate).
- **(b)** Zero operational upstream writes to the server during the day (no ACKs/receipts sent upstream; home computes outstanding from seals minus receipts).
- **(c)** One piece never spans two rounds (piece closes cleanly at every round boundary).

**Seconding all 6 changes in Astra `131547Z`:**
1. **Two distinct zero-row states in §2.2:** distinguish `completed_zero_rows` (full `sgend` + replay verified, e.g. real N12 game 3 threefold draw with legal moves remaining!) from `opening_ended_nomoves` (independent rules check proves 0 legal moves). Without this split, §2.2 line 96 would refuse N12 game 3!
2. **Non-circular bootstrap for `RUN.json`, `RANGES.json`, and `D - g`:** freeze `RUN.json` + pilot ranges before pilot play, then write an immutable `SCHEDULE.json` (linked by `run_fingerprint` and pilot evidence, or use a distinct production `run` ID) whose effective cutoff can only tighten; publish any short final round as an immutable successor schedule before dispatching its first game.
3. **Per-slot endpoints in `RANGES.json` (§1.5):** allow per-slot `(first, last)` overrides (and slots with 0 games) so `A26` unequal final ranges are representable.
4. **Exact game-ID grammar & journal durability (§1.3):** keep `<run>-w<slot:03d>-g<counter:08d>` (matching existing `worker.py` and tests); separate atomic temp+rename+dir-fsync for immutable files from append-only newline-terminated JSONL for `journal.txt`/`progress.jsonl` (mid-file damage -> hard fail; torn trailing line recovered only from durable evidence).
5. **Immutable day-1 offer per logical piece (§0 & §1.6 & §2.1):** publish one immutable offer per seal on day 1; a different `seal_sha256` at an existing `(slot, index)` is a fork (keep both in quarantine, halt slot credit).
6. **Out-of-order custody vs chain-eligible `C1` (§2.1):** record durable receipts for out-of-order pieces (so storage/capacity counts include them) separately from chain-eligible `C1` (unbroken chain from genesis).

**Neon's 8 additional changes to freeze in `FORMATS.md` v2 before coding:**
1. **§0 Server disk retention:** state explicitly that `closed/p<index>.raw` stays on the server alongside `out/w<slot>/p<index>.*` for the whole lease (matching Astra `131001Z` and `D2`), so Section 4 sizes for both.
2. **§1.4 / `record.py` `bind()` digest:** explicitly define `bind` to hash **`opening`** (line-1 move list) as well as `(game_id, sent, rows, end)` — closes Neon case `N6` (`openingend` mutated line-1 opening!). Also require `games >= 1` on every `p<index>.seal.json` (a slot with 0 open games at `D` writes no empty piece seal) and include `run_fingerprint` inside every `seal.json`, `offer.json`, `range.seal.json`, `receipt.json`, `verdict.json`, and `rounds/r<round>/report.json`.
3. **§1.6 Offer codec field (`D1`/`M7` compatibility):** instead of hardcoding `"form": "rawxz"` and `.meta.xz`, use `"form": "binpack" | "raw"` + `"codec": "lzma" | "zlib"` (with matching `.xz` / `.zlib` extensions) so `M7` can choose `lzma` or `zlib` without breaking the schema. Also specify exact allowed member filenames per `(form, codec)`, forbid `/`, `\`, `..`, and require `p<index>.seal.json` + every required payload member to be explicitly listed and verified in `members`.
4. **§1.3 Journal fields:** include `"bind"` (and `"rows": 0`) on `"empty"` lines, specify epoch-1 genesis `"last_index": -1, "last_seal": "genesis:<run_fingerprint>:<slot>"`, and record `"epoch": E` on every event (or require every event to follow an `"epoch"` header).
5. **§1.7 Range seal completeness:** add `"first_index"` (`-1` if 0 pieces in that round), `"first_prev_seal"`, and `"never_dispatched"` inside `dispositions`, and specify that an interrupted round at cutoff `D` writes a partial range seal (`"complete": false`) so nothing vanishes silently.
6. **§1.8 `TERMINAL.jsonl` exact missing-bytes accounting:** on every `"piece"` line include `"raw_bytes"`, `"packed_bytes"`, and `"offer"` (`<sha256>` or `null` if packer stopped before offering), so `D12` knows exact missing bytes even for pieces that never arrived at home. Include `"completed_at_utc"`, `"cutoff_reached"`, and `"stop_reason"` in the footer.
7. **§2.1 Stage `a1` monotonic `epoch` & relative path:** enforce **`epoch >= prev.epoch`** along every slot's piece chain (catches a stale epoch-1 worker appending after an epoch-2 handoff!), and store `"kept"` as a relative path under home root (portable if home root is remounted).
8. **§2.2 / §2.3 / §2.4 `A26` & `D13` fields:** include canonical 5-field `"identity"` per game in `verdict.json` plus explicit `A26` states (`accepted`, `completed_zero_rows`, `opening_ended_nomoves`, `duplicate` with `same_rows_as`, `conflict`, `set_aside` with `reason`); include `"status": "complete" | "partial"`, `"tb_probe_failures"` (any `> 0` forces `"partial"` and `C4 = 0`), `"kept_share"`, and `"missing_ids"`/`"set_aside_ids"`/`"conflict_ids"` in `rounds/r<round>/report.json`; add `"tb_rescore_rate_per_10k"` (row 34 alarm) and `"d13_complete_rounds_through_stage_b"` to `progress.jsonl`.

---

## 2. Ten Runnable Failing Cases Committed (`debate/server_day/cases/neon/`)

As requested in Fable `200908Z`, all 10 Neon cases (`N1`–`N10`) are now committed under `debate/server_day/cases/neon/` (`README.md`, `run_all.py`, `noflags.cpuinfo`, `spam_engine.py`, `error_path_and_bare_sgerror.transcript`).

- **Command:** `python3 -I -B debate/server_day/cases/neon/run_all.py debate/server_day/scripts /tmp/neon_cases_run`
- **Dependencies:** Python 3 stdlib + Bash only (`4.4 s` total wall time; `N2` uses a 5-line fake `CXX` shim against `loop/source` so it runs in `0.3 s` with no compilation).
- **Verified live against v1 `debate/server_day/scripts/` (`MANIFEST.sha256` member digest `9705a787bf51...`, left untouched after run):** **`SUMMARY: 0 PASS, 10 FAIL` (`rc=1`)** — every single one of `N1`–`N10` fails for its exact named bug (`N1` `cpu_check.sh` silent `rc=1`; `N2` `build_forge.sh` `$extra` word-split; `N3` `uciproc.py` `2.013 s` hang under `0.3 s`; `N4` `drive.py` `2.05 s` hang under `0.3 s`; `N5` `drive.py` `FileNotFoundError`; `N6` `record.py` unhashed `opening` on `openingend`; `N7` `packer.py` 0-byte `.sha256` `IndexError`; `N8` `check_run.py` `ERROR` path false positive + bare `sgerror` miss; `N9` `hash_tree.py` dangling symlink ignored + duplicate `sub/a.txt`; `N10` `make_workloads.py` missing argc `ValueError`).
