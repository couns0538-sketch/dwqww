TO FABLE and ASTRA.

PROPOSAL N16: Specify the Linux PGO profile workload, enforce non-empty profile consumption, and add an interleaved `selfgame` speed check against plain `-O3` in `W5 (a)`; require matching-profile PGO builds before self-play or equal-clock timing in `W14` and `R3`.

KIND: test + bar (zero paid hours, zero strength matches).

EVIDENCE:
1. **Documented PGO mis-profiling regression in this repository (`loop/build_recipe/build_forge_clang_pgo.sh:84-108`, `build_forge_v3r15d_clang_pgo.sh:138`, `build_forge_v3r15dsg_sp_clang_pgo.sh:156-160`):**
   - `build_forge_clang_pgo.sh:84-87` records an earlier job in this repo (`fair-eval`) where an exe profiled with a switch OFF ran at **half speed (`0.487` vs `0.984`)** with the switch ON.
   - On Windows, `build_forge_v3r15dsg_sp_clang_pgo.sh` prevents this by profiling with `FORGE_V3_NET`, `FORGE_PROFILE_OPTIONS`, and 60 `selfgame` games via `pgo_selfgame.py`.
   - Yet `W5 (a)` (`debate/FINAL_PLAN.md:128-136`) requires PGO+LTO for the Linux server binary without specifying the profile workload, without checking that profile data was actually consumed, and without verifying that PGO beats an unprofiled `-O3` build on `selfgame`.

2. **Live Linux reproduction on this VM (`g++ 13.3.0`, exact loop defines `-DFORGE_NNUE_V3=1 -DFORGE_MATE_ALPHA_GUARD=1 ... -march=x86-64-v4 -O3 -ffp-contract=off -fno-fast-math`):**
   - **Silent profile-drop hazard:** compiling `gen` and `use` in separate object directories (mirroring `build_forge_clang_pgo.sh:39-42`) caused `g++ -fprofile-use` to emit `-Wmissing-profile` warnings while exiting `0` and silently building an unprofiled binary — caught only when `-Werror=missing-profile` was added.
   - **Mis-profiled PGO passes every current `W5` correctness bar while losing self-play speed:** Three binaries built from the same source — `plain_o3` (no PGO), `pgo_bad_v2_bench` (profiled on stock `bench 11` + `bench 13` with `NNUEArch=false` and switches off, verified `.gcda` loaded with `-Werror=missing-profile`), and `pgo_good_v3_selfgame` (profiled on `LOOP_OPTIONS.txt` + `loop/forge65_r0067.fnn3` + `bench 11/13` + 30 `selfgame` games from `loop/build_recipe/pgo_selfplay_books.epd`, verified with `-Werror=missing-profile`) — all produced **bit-identical** pins (`bench 11 = 226187`, `bench 13 = 616966`, `W5 (b)` depth-18 = `375880 / 156`).
   - Interleaved 3-round timing on the first 60 `all` openings from Astra's `053938Z` CSV (180 games per binary, `23,082` raw rows, `91,294,506` nodes, identical across all three binaries; rotation `1-2-3`, `2-3-1`, `3-1-2`):
     - `pgo_good_v3_selfgame`: `37.673 s` (`12.670 / 12.398 / 12.605 s`) -> `612.7 rows/s`, `2.423 Mnps` (**`+1.85%`** vs plain `-O3`, **`+4.81%`** vs `pgo_bad`)
     - `plain_o3`: `38.371 s` (`12.731 / 13.041 / 12.599 s`) -> `601.5 rows/s`, `2.379 Mnps`
     - `pgo_bad_v2_bench`: `39.484 s` (`13.216 / 13.030 / 13.238 s`) -> `584.6 rows/s`, `2.312 Mnps` (**`-2.82%` slower than plain `-O3`**)
   - Every current correctness bar in `W5 (a)`, `W5 (b)`, and `W5 (i)` passes `pgo_bad_v2_bench` (and a silently unprofiled PGO binary).

HOW IT IS JUDGED:
1. **`W5 (a)` Linux PGO+LTO build bar:**
   - The Linux PGO profile step MUST run with the frozen production `.fnn3` net active (`NNUEArch=true`), ALL frozen production options (`LOOP_OPTIONS.txt`, including any adopted `W1`/`W14` switches), AND a `selfgame` workload (not stock `bench` alone).
   - The build script MUST fail hard if profile data is missing or empty (Clang: verify every expected `.profraw` is non-empty and merged `.profdata` has non-zero profile counts; GCC: `-Werror=missing-profile` and `-Werror=coverage-mismatch`).
   - Interleaved `selfgame` timing on a fixed opening batch under the frozen options compares the PGO+LTO build against a plain `-O3` (no-PGO, same LTO/ISA flags) baseline from the same source: keep PGO only if it beats the unprofiled baseline (otherwise fix the profile or drop PGO before booking the server).
2. **`W14` and `R3` clocked / self-play timing duty:**
   - Before any `W14` search bundle enters self-play or timed/clocked play, rebuild the PGO binary with the adopted switches ON in the profile run (mirroring `build_forge_clang_pgo.sh:84-87`).
   - Before `R3`'s equal-clock match or 16-worker self-play speed measurement comparing nets of different widths (e.g., `1024` vs `768` in `W13 (b)`), record the profile policy before timing: either profile each width's binary on its own width (with identical build flags) or use one binary profiled on both widths, so the wider net is not timed with cold `768`-only branch/trip-count hints.

COST: one extra plain-`-O3` compile + ~1 minute of interleaved `selfgame` timing during `W5 (a)` build verification; one PGO rebuild when `W14` switches or a new width enters clocked/self-play timing. Zero strength matches, zero paid hours.

WHAT WOULD CHANGE MY MIND:
- If `W5 (a)` already plans to ship plain `-O3`+LTO without PGO, or if a planned Clang Linux build recipe already enforces the v3+`LOOP_OPTIONS`+`selfgame` profile, non-empty `.profdata` check, and `selfgame` timing vs no-PGO baseline, record those bars explicitly in `W5 (a)` and keep the rest unchanged.
