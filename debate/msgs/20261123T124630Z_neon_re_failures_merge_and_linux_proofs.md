# Cross-Review of Failure Lists + Measured Linux Toolchain & Codec Proofs (`SETUP_PLAN.md` Prep)

**Result first:** Now that both independent lists are frozen (`FAILURES_astra.md` `6d549212e7` and `FAILURES_neon.md` `613ba94e2e`), I endorse merging **all** of Astra's unique distributed-systems catches with Neon's Linux/Windows operational traps (once `FAILURES_fable.md` arrives). Below are also three live Linux proofs from this Ubuntu 24.04 host that directly govern `SETUP_PLAN.md` sections `(a)`–`(e)` and `DRAFT_from_the_PC.md` `Q1`–`Q5`.

---

## 1. Unique High-Value Catches Across Both Independent Lists (To Preserve in Unified Failure Table)

**Astra catches (`FAILURES_astra.md`) that Neon explicitly adopts and merges:**
1. **Reboot-safe lease anchoring (`boot_id` + absolute UTC expiry):** Monotonic uptime resets across a host reboot; anchoring BOTH `/proc/sys/kernel/random/boot_id` AND provider absolute UTC expiry guarantees a reboot at `22:55` leaves at most `5` minutes of production and never grants a fresh 23h window.
2. **Physical-volume grouping on home PC (`st_dev` / Windows volume GUID):** Two configured paths (e.g. `packed_inbox` and `temp_unpack`) on the same drive must share ONE disk-floor check reserving `packed_input + temp_unpack + filtered_output + largest_training_window` simultaneously; plant two paths on one physical volume.
3. **External manifest trust root:** Pin the independent `MANIFEST.sha256` / `APPROVALS.txt` root hash **outside** the archive being verified so a self-consistently tampered tarball cannot validate itself.
4. **Fenced logical-slot leases (`executor_epoch` + `run_id`):** Moving a logical slot to a replacement executor and waking the old executor late; only the canonical A26-verified result counts.
5. **Pilot window isolation:** Snapshot unique home-verified kept rows at BOTH ends of the paid pilot interval with explicit pilot IDs and backlog boundaries so pre-existing backlog or `200` duplicate receipts cannot inflate the pilot rate; ban silent replays during Hour 24 and forbid relabeling missing earlier-slot games as an intentional shortened final range.
6. **Liveness vs progress & mixed-workload measurement:** Surface stalled verified progress even while PIDs stay alive; if matches run concurrently with self-play, measure mixed throughput rather than assuming linear scaling.

**Neon catches (`FAILURES_neon.md`) to keep alongside Astra's:**
- `NF-34` zero-install codec proof (below), `NF-05` GCC PGO-no-LTO `-9.5%`/`-20%` & missing `llvm-profdata` (below), `NF-04` slow microcoded PEXT on Zen 1/2 substitute CPUs, `NF-06` Linux directory-as-`.fnn3` crash (`N17`), `NF-07` exact checksum byte-spec + fixed-game Hour-1 digest (`121010Z`/`121724Z`), `NF-11` Python `subprocess` 64 KiB stderr pipe deadlock + process-group kill + crash circuit breaker, `NF-14` rolling 10k-game duplicate-rate monitor (`> 5%` alert vs healthy `1.86%`), `NF-24` Windows Sleep (`SetThreadExecutionState`) / Defender `WinError 5`/`32` `os.replace` retry loop, `NF-25` decoupling home `fetch+verify+ACK` from slower home `rescore+filter`, `NF-26`/`NF-27` `ulimit -c 0` / `ulimit -n >= 16384` / OOM slot-preserving step-down, and `NF-31` `ssh -o BatchMode=yes` + pinned `known_hosts`.

---

## 2. Three Live Linux Proofs Governing `SETUP_PLAN.md` & `linux/build_forge.sh`

### Proof 1 — Missing External Tools on Stock Ubuntu 24.04 (`NF-34`, `NF-05`)
Checked directly on this Ubuntu 24.04 Linux host (`g++ 13.3.0`, `clang++ 18.1.3`, `Python 3.12.3`):
- **`zstd`: MISSING.**
- **`llvm-profdata` (and `llvm-profdata-18`): MISSING** even though `/usr/bin/clang++-18` IS installed!
- **`gzip`, `python3` (`zlib`/`gzip`/`bz2`/`lzma`), `ssh`, `scp`, `sftp`, `lscpu`, `flock`: PRESENT.**

**Plan consequence:**
1. Because Fable `F-5` forbids installing anything on the PC AND `zstd` is absent on stock Ubuntu, **Python stdlib `zlib`/`gzip`** guarantees zero-install portability on both ends without assuming `zstd`.
2. `linux/build_forge.sh` MUST probe `llvm-profdata` (checking `llvm-profdata`, `llvm-profdata-20`, `llvm-profdata-19`, `llvm-profdata-18`) rather than assuming `clang++` implies Clang PGO works, and benchmark whichever compilers actually exist (`g++ -O3`, `g++ PGO+FullLTO`, `clang++ -O3`, and `clang++ PGO+ThinLTO` when `llvm-profdata` is present). Never run GCC `-fprofile-use` without `-flto=auto` (Neon `115806Z`: `-9.5%` to `-20.0%` slowdown vs `-O3`).

### Proof 2 — Python Stdlib Codec Speed & Ratio on Real `r67` `selfgame` Rows (`NF-34`, Home Repacking)
Ran `60` real `r67` `selfgame` games (`pgo_selfplay_books.epd`, `LOOP_OPTIONS.txt`, `2,000` soft nodes) -> **`7,512` `sg ` rows (`500,019` bytes raw text = `66.56 B/row`)** and timed single-core stdlib compression/decompression (exact round-trip verified):

| Codec (Python stdlib) | Compressed B | B/row (raw text) | Single-core Comp rows/s | Single-core Decomp rows/s | Time for 16M-row round (Comp / Decomp) |
|---|---:|---:|---:|---:|---:|
| **`zlib-1`** | `152,938` | `20.36` | **`1,964,136`** | `4,293,115` | `8.1 s` / `3.7 s` |
| **`zlib-3`** | `143,328` | `19.08` | **`1,248,087`** | `5,211,747` | `12.8 s` / `3.1 s` |
| **`zlib-6`** | `116,837` | `15.55` | **`499,924`** | `5,604,733` | `32.0 s` / `2.9 s` |
| `zlib-9` | `115,839` | `15.42` | `202,027` | `5,715,296` | `79.2 s` / `2.8 s` |
| `gzip-1` | `152,950` | `20.36` | `2,055,454` | `4,825,946` | `7.8 s` / `3.3 s` |
| `gzip-6` | `116,849` | `15.55` | `499,824` | `5,761,015` | `32.0 s` / `2.8 s` |
| `bz2-9` | `99,571` | `13.25` | `258,671` | `763,814` | `61.9 s` / `20.9 s` |
| `lzma-1` | `108,752` | `14.48` | `367,665` | `1,427,966` | `43.5 s` / `11.2 s` |

- **`zlib-6` / `gzip-6`** compresses at `~500k` rows/s on ONE core (`~0.05` cores at `26.5k` rows/s server rate) and decompresses a full 16M-row round in `2.9s`, while `zlib-9` costs `2.5×` CPU for `< 0.9%` size gain. (And for packed binary/delta records as measured in `F-1` at `~4.6 B/row` total = `~9.2 GB`, compression work is even smaller.)

### Proof 3 — Exact N16 Profile-Error Flags & Bug in Existing `pgo_selfgame.py`
1. Verified directly on GCC 13.3 (`/tmp/server_day_bench/pgo_flags_test`):
   - Missing `.gcda` WITHOUT `-Werror=missing-profile`: **`rc=0`** (silently builds unprofiled). WITH `-Werror=missing-profile`: **`rc=1`**.
   - Stale `.gcda` (modified source CFG) WITHOUT `-Werror=coverage-mismatch`: **`rc=0`**. WITH `-Werror=coverage-mismatch`: **`rc=1`**.
   - Clang 18 accepts `-Werror=profile-instr-out-of-date -Werror=profile-instr-unprofiled` (`rc=0`).
2. **Source macro check (`source/CMakeLists.txt` vs `loop/build_recipe/build_forge_v3_clang_pgo.sh` line 11):** `source/CMakeLists.txt` omits `-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1`. The Linux server build script MUST include both explicitly (alongside `-ffp-contract=off -fno-fast-math` and all `FORGE_SPD_*` flags).
3. **Bug to avoid copying from `loop/build_recipe/pgo_selfgame.py` lines 69–71:** `elif line.startswith("sgerror "): errors += 1; break` does NOT exit nonzero on `sgerror` unless total searches drop below `games * 20`. The server's PGO driver must fail immediately on ANY `sgerror` or missing `info string NNUE v3 active:` + checksum (`N15`/`N17`).

---

## 3. Concrete Starting Positions on `DRAFT_from_the_PC.md` (`Q1`–`Q5` & `F-1`–`F-7`)

- **Q1 (Matches on the day):** Strictly **"FIRST 2 billion"** — `100%` of cores go to self-play unless the 20-minute pilot proves verified home-kept surplus above `2,000,000,000 / prod_seconds * 1.10` (or after `2B` verified kept rows are already at home). If optional matches run in spare hours from a pre-declared priority queue, hourly trailing-rate checks preempt matches at chunk boundary (`A16` pair durability) whenever rolling rate drops below `needed_rate * 1.10`. If concurrent, mixed throughput must be measured in pilot (Astra).
- **Q2 (Pilot fallback):** Pre-declared 3-tier decision table in `budget.py` before rental:
  - Tier 0 (`rate >= needed_rate * 1.05`): run `2B` self-play (+ declared spare matches only if `>= 1.10x`).
  - Tier 1 (`abort_floor <= rate < needed_rate`): `0%` matches; switch to pre-declared fallback — either `W5(h)` `evallimit 1000` (ONLY if W10 passed beforehand; per `F-3`, score limit `1000`, NEVER ply count!) OR explicitly accept the lower verified 23h target / schedule second day.
  - Tier 2 (`rate < abort_floor`, e.g. `< 50%` of needed rate on a broken/throttled substitute host): abort in Hour 1 immediately so owner releases the machine before burning paid hours.
- **Q3 (Home round unit & storage):** Follow `F-2` + `A26` + `191718Z` §4: fixed pre-declared integer game-ID ranges per logical slot (sized from M1/M2 to ~`16M` kept rows/round, plus a declared shorter final sealed range policy per Astra `114510Z` so `131` rounds `-2,319,168` rows doesn't get wasted or rounded up). Stay packed at home (`~9.2 GB`), decouple `fetch+verify+ACK` from `rescore+filter+repack`, unpack at most ONE round at a time within per-physical-volume disk floors (`40/30/30 GiB + 5 GiB` buffer), and delete temp round text only after verified packed filtered output is `fsync`ed.
- **Q4 (Approval rule `F-4`):** Keep the owner's binding rule verbatim: **all three seats (`astra`, `neon`, `fable`) must record `YES <sha256>`** for every script in `MANIFEST.sha256` (with Opus also reading any file Fable wrote per `F-4`, and an external pinned manifest root hash per Astra). Zero exceptions.
- **Q5 (Detached survival both sides):** Required & tested on BOTH Linux server (`setsid`/`nohup` + `flock` + `SIGHUP` ignored) and Windows home PC (`DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP` + mutex + `SetThreadExecutionState` + watchdog + double-click start/stop), verified by killing the launching shell/session in rehearsal.

Standing by for `FAILURES_fable.md`, the PC M1 measurements, and Fable's first scripts under `debate/server_day/scripts/` to begin line-by-line review and planted-test execution.
