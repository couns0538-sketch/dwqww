# Linux Server-Day Reference Tools (`machine_check.py` & `build_forge.py`)

Author: Neon (2026-11-23), built per Fable `205239Z` section 4, `SETUP_PLAN.md` v2.2 (section 4, D1, D2, D3, D4, D5, D10, D15, N16, section 7 rows 5 & 44), Astra `140827Z` / Fable `210950Z` section 3, and `FORMATS.md` 2.1 section 0 (canonical ASCII JSON, no floats, create-only `os.link` publication with file + directory `fsync`).

Standard library only. Offline. Run with `python3 -I -B` and a NEW work directory; zero use of system temp folders; zero writes outside the supplied work directory (and the explicit volume directories during `machine_check.py`'s cleaned-up hard-link probes).

## Files

- `machine_check.py` — Linux pre-flight machine check (`stage: "preflight_hardware"`), pure integer D3/D4 budget/shortfall admission (`admit_budget_d4`, per Astra `140827Z` & Fable `210950Z` section 3), dual-mode storage admission (`admit_storage_modes`, normal vs all-fallback + resident-bytes pause line per Astra `141912Z` & Fable `212259Z` section 2), and host instance identity probing (`probe_instance_identity` / `same_provable_instance` per `FORMATS.md` 2.2 section 1.3, hashing identifiers and refusing `null == null` placeholders). Walks `/proc/self/cgroup` through every `/sys/fs/cgroup` ancestor (v2 + v1 fallback), intersects `sched_getaffinity` with per-CPU `/proc/cpuinfo` ISA flags, checks effective memory (`min(MemTotal, cgroup memory.max)`), `RLIMIT_NOFILE`, `RLIMIT_NPROC`/`threads-max`/`pids.max`, `RLIMIT_CORE=(0,0)`, physical filesystem deduplication (`st_dev`), `ST_RDONLY`/`ST_NOEXEC`, free inodes, atomic create-only `os.link` (`EEXIST` preserves both candidates) + directory `fsync`, `/proc/sys/kernel/random/boot_id`, live PID-1 `systemd` (D15), `sshd`, C++ compiler, and `lzma`/`zlib`/`hashlib`/`sqlite3` round-trips.
- `tests/test_machine_check.py` — 15 self-contained checks (`M1`–`M15`) covering every planted resource/cgroup/ISA/mount/inode/systemd/boot_id/corrupt-cgroup failure, live real-host probe, Astra's D4 shortfall vector (`80,000 s`, `C4=0`, `2B` target, `20,000 r/s` safe tested rate), Astra's dual-mode 180 GB vs 167.61 GB normal / 197.30 GB fallback storage vector, and `FORMATS.md` 2.2 section 1.3 genuine reboot vs cloned spool / unprovable placeholder check.
- `build_forge.py` — Linux multi-variant C++ build (`plain_o3`, `plain_o3_lto`, `pgo_nolto`, `pgo_lto`), strict symlink-refusing `SOURCE.sha256` verification, pre-flight ISA/affinity check via sibling `machine_check.py`, zero shell word-splitting (safe inside spaced paths even under GCC `-flto=auto` `lto-wrapper`), strict UCI known-answer checks against `known/{profile,verify,startup,n12_batch}.json` with steady per-line timeouts and 4-form `info string` allow-list, full per-unit `.gcda` + `-Werror=missing-profile -Werror=coverage-mismatch` enforcement, optional interleaved multi-worker D10/N16 self-play comparator verifying bit-identical game digests, and 4 planted fault modes (`bad_source_hash`, `profile_error`, `missing_profile`, `other_source`).
- `tests/test_build_forge.py` — 6 end-to-end checks (`B1`–`B6`) on frozen `loop/source` (`SOURCE.sha256` + `known/`): all 4 planted faults, existing `--work-dir` refusal, and clean `plain_o3_lto` + `pgo_lto` build + `verify`/`startup`/`n12_batch` + 2-worker D10 self-play comparator inside a spaced path (`"b6 clean spaced"`).
- `MANIFEST.sha256` — exact SHA-256 of every file in this directory plus trailing `digest <sha256>`.

## Usage (always pass a NEW work directory)

```text
python3 -I -B debate/server_day/ref/neon/tests/test_machine_check.py "/path/to/new_mc_test"
python3 -I -B debate/server_day/ref/neon/tests/test_build_forge.py \
  loop/source loop/forge65_r0067.fnn3 debate/server_day/scripts/workloads debate/server_day/scripts/known "/path/to/new_bf_test"

python3 -I -B debate/server_day/ref/neon/machine_check.py \
  --work-dir "/path/to/new_mc_out" \
  --variant avx2_pext --min-threads 8 --min-ram-bytes 17179869184 \
  --volume "spool:/path/to/spool:268435456000:100000:1" \
  --require-systemd --require-sshd

python3 -I -B debate/server_day/ref/neon/build_forge.py \
  --work-dir "/path/to/new_build_out" \
  --source loop/source \
  --net loop/forge65_r0067.fnn3 \
  --workloads debate/server_day/scripts/workloads \
  --known debate/server_day/scripts/known \
  --variant avx2_pext --modes plain_o3_lto,pgo_lto \
  --bench-workers 4 --bench-games 8 --bench-reps 2
```

Every executable script requires three exact-byte `YES <sha256> <path>` votes before server-day use.
