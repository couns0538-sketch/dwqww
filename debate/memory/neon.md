# Neon Memory (Server Day Debate)

Updated: 2026-11-23T14:30:00Z (UTC). Stop time: 18:35Z (~4h 05m remaining).
Active branch: `debate/server-plan-20261123`.

## Current state of the server-day plan
- **`SETUP_PLAN.md` v2.2** (`35b8c34424e4...`): ALL decisions `D1`–`D15`, Section 2, and Section 4 settled; Astra `140827Z` (D4 shortfall vs pre-flight hardware), `140908Z` (multi-process compressed rules throughput on Linux), and `141912Z` (dual-mode normal vs raw-fallback storage room: 180 GB covers 167.61 GB normal, not 197.30 GB all-fallback) all accepted by Fable (`210950Z`, `212259Z`).
- **`FORMATS.md` 2.2** (`02bd23ad...`, Fable `211918Z`):
  - Astra voted `AGREE` (`142053Z`). Both new `0.1` byte vectors (`94b4fd15...eaeaee`, `5902be33...f6f70f`) independently reproduced by Astra, Fable, and Neon on `ref/astra/fixtures/games.txt`.
  - Neon (`143000Z`) voted `AGREE` on all 2.1/2.2 content + `CHANGE` on 4 tight 2.3 closures (none holding `uciproc`/`record`/rules): (1) control-file `.zz` wire publication order (`offer.json.zz` last + `RUN/SCHEDULE/RESUME/FENCE/range-seal/TERMINAL` `.zz` companions + `offer_wire_*` in `receipt.json`); (2) stage a2 cross-checking every `seal.json` summary field (`ids_digest`, `first_counter`, `last_counter`, `games`, `rows`) against reconstructed `.raw`; (3) explicit lossless-reconstruction invariant for `binpack + meta.xz -> raw_sha256`; (4) `instance` `null != null` fail-closed rule for unreadable/placeholder DMI fields.
- **`ref/` split agreed by all three seats** (`211918Z` §3, `142053Z`, `143000Z`): `ref/astra/` and `ref/neon/` are independent Linux reference implementations + known-answer fixtures outside the paid day package; all PC-built `scripts_v2/` executables take their contracts/fixtures as data and require three exact-byte `YES`.

## Published Neon Linux reference (`debate/server_day/ref/neon/`, manifest `750eb3c9...`)
- `machine_check.py` (`12bbe402...`) + `tests/test_machine_check.py` (`b6a5db51...`): **15/15 PASS** live on Linux (`M1`–`M15`, including cgroup v2/v1, per-CPU ISA affinity, `st_dev` dedup, inodes, atomic `os.link`, D15 systemd, D4 shortfall `M13`, dual-mode 180 GB storage `M14`, `FORMATS.md` 2.2 `instance` + `null != null` `M15`).
- `build_forge.py` (`dca4ff56...`) + `tests/test_build_forge.py` (`b1c04f74...`): **6/6 PASS** live on frozen `loop/source` + `loop/forge65_r0067.fnn3` (`B1`–`B6`: 4 planted faults + clean `plain_o3_lto` & `pgo_lto` inside a spaced path with GCC `-flto=auto` relative-`cwd` fix, passing `verify`/`startup`/`n12_batch` + 2-worker bit-identical D10 self-play comparator).

## Approval Ledger State (`scripts_v2/`)
- **Package 1 (`scripts/`, 17 files):** `0` effective `YES` (frozen baseline).
- **`ref/astra/` (`14b195c1...`, `1cd6e159...`):** read line-by-line by Fable & Neon against `board.cpp`/`uci.cpp` (core rules 100% match; Neon noted 2 CLI durability/parsing details for `scripts_v2/home/` not to copy); stays independent reference outside paid package.
- **`scripts_v2/` batch 1 rev 2 (`94e7518e...` `engine_lines.py`, `42cf67d9...` `uciproc.py`):**
  - Passed 48/48 on PC and Linux; ALL 8 batch-1 bugs fixed.
  - **Astra (`142216Z`) voted `NOT YET`** (2 bugs: truncated `info depth 18 seldepth` / `option name Hash type spinach`; post-send arg validation + retired `send()`). Fable (`212259Z`) accepted and started repair.
  - **Neon (`143000Z`) voted `NOT YET`** with 4 ADDITIONAL live-reproduced bugs to include in the same repair pass: (1) `uciproc.py:191-194` hang when any unexpected line precedes `sgerror` (live 1.20 s full timeout!); (2) `uciproc.py:138-149` `send()` missing `MAX_LINE`/`str` check, `BrokenPipeError` leaving `self.gone == ""`, and missing `bool` rejection; (3) `uciproc.py:222-230` `uci_options()` truncating spaced `string` defaults; (4) `engine_lines.py:46,49,52` refusing valid `bestmove 0000` (`uci.cpp:671`), reminder to keep `option name Clear Hash type button` (`uci.cpp:789`), and blank-line `""` allowance.
  - **0 effective `YES` in `scripts_v2/` so far.**

## Next actions
1. Commit and push `ref/neon/` + `143000Z` message + memory update now.
2. Watch `origin/debate/server-plan-20261123` and `origin/debate/server-plan-20261123-astra` for:
   - Fable's `scripts_v2/` batch 1 rev 3 (`engine_lines.py`, `uciproc.py`, `test_uciproc.py`) -> run full test suite + native engine probes on Linux -> cast exact `YES` once clean!
   - `FORMATS.md` 2.3 (if Fable folds in Neon's 4 closures -> fast `AGREE`).
   - Next `scripts_v2/` drops (`record.py`, `home/` rules reader, `worker.py`, `packer.py`, `linux/`, `home/`, guards, tests) -> immediate line-by-line review + live Linux fault tests for EVERY script.
3. Update `debate/memory/neon.md` ~every 10 minutes; continue until `18:35Z` UTC.
