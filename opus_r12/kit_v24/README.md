# M8 LTO+PGO kit: frozen workload, any-source build script, AL1 s198 opponent (box), PC recipe for QA
Engine Coder, 2026-10-30. Status: build-mode kit for CR. Node-identical compiler-only builds; **no speed or Elo claim** (box timing never counts; the PC ABBA is QA's).

## Files (md5)
| file | md5 | what |
|---|---|---|
| FROZEN_WORKLOAD.md | 7215a1ec5ffc1d6478f49f45e3959397 | the frozen profiling workload, its rules, and how it differs from the 8A4A00C9 training |
| workload/frozen_train_cmds.txt | 0e7e073bcc390796551726335af4a45a | sha256 1d52720a…ace30. `uci, isready, bench 11, bench 13, bench 16, isready, quit`. No setoption lines |
| workload/bench_fens.txt | 6586fc736550033d381eaa964bb0bdab | sha256 16f15893…1a835. The 8 bench FENs, extracted from the lock source by script |
| build_ltopgo.sh | 9a1c90eb74bdda84b65622f66b94fc7e | kit v2.1: box build of any SRC: plain + LTO+PGO, manifests (raw, header-stripped, arcs), checks (vfmadd fail, FAILED marker), node identity (`bash -n` OK). Kit v2 = 525758f3 kept as build_ltopgo.sh.v2final.bak; the older d70173d5 is build_ltopgo.sh.v2.bak (name taken before v2 was final) |
| build_ltopgo.ps1 | 7c910807edf9209ab1c459149ffd8b81 | kit v2.1 (v2 27fc1a06 kept as build_ltopgo.ps1.v2.bak): PC mirror of QA's build_lto.ps1 (md5 05f39e97) + frozen workload + manifests + identity (pwsh 7.4 parser: 0 errors, 0 case-colliding variable names; v1 404e1f55 kept as build_ltopgo.ps1.v1.bak); gcov-dump optional |
| tools/lp_check.py | fb4fbac8523e2e11aa1a9d6109a4ab3f | UCI checker: `run` (bench totals, perft5 startpos/kiwipete, per-FEN `go depth` nodes + bestmove) and `compare` |
| tools/gcda_arcs_digest.py | 74fda002a49c406b016287eb793b66c7 | per-.gcda sha256 of the edge (arcs) counters only. v2.1: exact-prefix strip, so a Windows drive colon no longer leaks the path (v2 f3f6cfd4 kept as .v2.bak) |
| tools/test_gcda_arcs_digest.py | e776b7efa45486ac3b9ea37c69966c4e | unit test: C:\ pc1 = pc2, \ vs / spellings, v2 regression shown, real box dump re-prefixed with C:, box run arcs manifest = 0c5ece46 |
| build_ltopgo.sh.v1_used_for_al1.bak | 4cbd63e3a98cd3e3edfce02b1095760e | the exact script version that made run al1s198_frozen_v1 (the final one only adds the arcs-manifest lines) |

## Usage (box)
    cd /workspace/forge-coder/m8_pgo/ltopgo_kit
    # AL1 opponent (done: runs/al1s198_frozen_v1, rerun runs/al1s198_frozen_v1b)
    bash build_ltopgo.sh --src ../src_al1s198 --tag al1s198_frozen_v1 \
      --pins d11=312866,d13=862329,d16=3024920,d20=12389307,d22=34048354 --perft-pins startpos=4865609,kiwipete=193690690 \
      --check-opt UseNNUE=false
    # any candidate (Strength: P27R, Sf26Bundle, ST-A v2 ...), e.g. ST-A v2 with its gate option:
    bash build_ltopgo.sh --src /workspace/forge-strength/stA-signedcorr-v2-al1-20261030/<src dir> --tag stA_v2_lp1 \
      --pins d11=312866,d13=862329,d16=3024920,d20=12389307,d22=34048354 --check-opt CorrSignedKey=1
- `--src DIR` any Forge tree (CMakeLists.txt at its root; read only). `--tag` new run name. Output goes to `runs/<tag>/` (or `--out DIR`). It refuses an existing tag and never overwrites or deletes.
- Steps:
  1. plain build (= the box lock recipe: CMake Release, `-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256`);
  2. instrumented LTO build (`-flto=1 -fuse-linker-plugin -fprofile-generate=<run>/profile -fprofile-update=single`, gcc-ar-14/gcc-ranlib-14);
  3. the frozen workload, sha256-checked and refused if it holds any `setoption`. It needs 3 bench lines and as many .gcda as object files;
  4. `gcda_manifest.txt` (sha256 of every .gcda, sorted bytewise, the mangled build path shown as `<BUILD>`), `gcda_manifest_nohdr.txt` (same, each .gcda hashed without its first 12 bytes), `gcda_arcs_manifest.txt` and `profile_archive_<tag>.tar` (all record only);
  5. the LTO+PGO build in the same build dir (`-fprofile-use -fprofile-correction -Wmissing-profile`). Real missing-profile/coverage warnings are counted from `warning:` lines only (not echoed command lines) and must be 0. `-flto` must be on the link line, and vfmadd is counted for both exes;
  6. node identity, plain vs LTO+PGO.
- Node identity always runs **OFF first: no setoption at all (every option at its default)**. Then one run per `--check-opt Name=Value` (repeatable; names may contain spaces), or per `--opt-set "N1=V1;N2=V2"` for a mask of several options. Each option run is compared plain vs LTO+PGO and also reported as "differs from OFF (live)" or "IDENTICAL to OFF" (identical proves nothing at these depths). Use `--expose` (both builds with FORGE_EXPOSE_TUNABLES=ON) only if the option must show in the uci list; release builds accept tunables silently. Options must be deterministic (Threads 1).
- `--pins` / `--perft-pins` add fixed expected OFF numbers (a candidate's OFF must equal the lock pins for a default-off change). `--depths` (default `11 13 16 20 22`) and `--fen-depth` (default 13) change the check depths.
- Exit 0 and `RESULT PASS` only if everything matches; any failure writes `runs/<tag>/FAILED` (do not use exes from such a folder). vfmadd > 0 fails. A source tree holding *.gcda, *.o or CMakeCache.txt is refused. Box rules are built in: nice 19, -j1, `flock /workspace/forge-coder/build.lock`, `taskset -c 5`, waits while load > 5; env-overridable as `CORE=`, `LOCK=`, `LOADMAX=` for other agents' rules. Logs use TZ=Europe/Vienna (crew log rule; %Z is printed).

## Usage (PC, QA only)
Copy the kit folder (workload\, tools\, build_ltopgo.ps1) and a fresh source copy to the PC, then:
`powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File build_ltopgo.ps1 -SrcDir <clean src copy> -Tag al1s198_frozen_pc1 -Pins d11=312866,d13=862329,d16=3024920,d20=12389307,d22=34048354 -PerftPins startpos=4865609,kiwipete=193690690 [-CheckOpt 'CorrSignedKey=1']`
- **Rebuild the PC AL1 opponent from a clean source copy** (a fresh copy whose files match the lock's SOURCES list: no obj_*/pgo_* dirs, .o, .gcda or .exe; the script refuses such leftovers). **8A4A00C9 is pre-freeze** (trained with setoption Threads/Hash/OwnBook), so it must not be one side of a gate whose other side uses workload v1. Build it **twice** (tags …_pc1 and …_pc2): **the forge_ltopgo exe sha256 must be equal for pc1 and pc2; that is the only binding check.**
- v2 (after CR_M8_LTOPGO_KIT_20261030, md5 2bb46961): stops on any non-zero exit (every g++, objdump, training exe, python call); use-stage objects must be newer than the training; manifest names normalised to `<BUILD>#obj_ltopgo#<unit>.gcda`, LF line ends, so two PC builds compare; vfmadd > 0 fails; `-flto` on the link line and LTO IR (`.gnu.lto_` sections) in every object are checked; gcov-dump.exe was required (dropped in v2.1); timeouts per engine run (-TrainTimeoutSec 3600, -CheckTimeoutSec 7200); any failure writes a `FAILED` marker in `<Work>\<Tag>` and exits 1.
- The compile and link lines are token for token QA's build_lto.ps1: `$F`, `-flto=1 -fuse-linker-plugin`, -static at link, per-object compiles into obj_ltopgo, and `-fprofile-use … -Wmissing-profile` on compile and link. Training uses QA's `cmd /d /c "exe < file"`, but with the frozen file.
- The plain exe uses the lock's direct g++ line (j1v2/lockref/2_build/build_windows.ps1, same token order). For AL1 it should reproduce lock 833C47F3; if it doesn't, bench is the identity check.
- Affinity 0x3 and BelowNormal, like QA's script (`-Affinity` changes it). It works in `<Work>\<Tag>\src_copy` and refuses an existing tag.
- v2.1 (after QA_M8_AL1_LTOPGO_BUILD_20261030, md5 0ce0d969): MSYS2 gcc 15.2.0 ships no gcov-dump.exe. If `-GcovDump` (default `C:\msys64\ucrt64\bin\gcov-dump.exe`) is missing, the build does **not** stop: gcda_arcs_manifest.txt contains `UNAVAILABLE (no gcov-dump)`, and SUMMARY.txt and the log say so. Added gcda_manifest_nohdr.txt. New SUMMARY.txt: exe sha256s, the three manifest states, identity result, RESULT line.
- Writes gcda_manifest.txt, gcda_manifest_nohdr.txt, profile_archive_<tag>.zip, gcda_arcs_manifest.txt (or UNAVAILABLE) and SUMMARY.txt. Then node identity with lp_check.py (needs python on PATH, or `-Python`). The last line names the exe for GATE_EXE.
- A -static Windows exe can show vfmadd hits from libm ifunc variants. Map the hits to functions; only hits in Forge code count. 8A4A00C9 had 0.

## Results: AL1 s198 on the box (src_al1s198 = exact lock copy)
| exe | sha256 | md5 | vfmadd |
|---|---|---|---|
| forge_plain_al1s198_frozen_v1 | 97d7e27dada59c9297b07fb15a1396aa71d23f7cb6a79f6b94d4cf086ede6fc7 (= box lock reference) | 29ef29e72d60b91c5eec123cbcd8e9d7 | 0 |
| **forge_ltopgo_al1s198_frozen_v1** | **f8b6fa25b78a5b9f4b28ad286bb4ff1428211c16c5d309a1fa9c429a4e868d8f** | acafcaa537f1ad5428cf042354b95c6a | 0 |
| forge_instr_al1s198_frozen_v1 (not for use) | 53ef7cd20624558cd24ac4811fc07146456beed74a1c147ee9e9fe0320cec135 | b633ee1184628f0c0fd3e1b40d82bd20 | – |
- Warnings: plain 6, ltopgo 7 (the 6 known -Wconversion + 1 `using serial compilation of 3 LTRANS jobs`). Real missing-profile/coverage warnings: 0. `-flto` is on the link line.
- Profile: 8 .gcda for 8 objects. Training bench nodes 312866/862329/3024920 (= pins).
  - gcda_manifest.txt sha256 684a63a527f303891fad3b74d1181df2133f20061e65808465105a7c01196124
  - gcda_arcs_manifest.txt sha256 0c5ece46c8df3c47ee7b7cab002593b63c5d1d5fddbea78ae48ea300dc55ac99
  - profile_archive_al1s198_frozen_v1.tar sha256 ac0526c62089a9ce4466b26669db6df58eb918398f284055ee577f81ac980bcb
- The old box forge_lto_pgo (5fedf9d1…, trained WITH setoption lines) differs from f8b6fa25, so the training input does change the exe bytes. The opponent for gates under the frozen workload must be a frozen-workload build.

### Node identity, OFF (no setoption at all)
| item | plain | ltopgo | pin | |
|---|---|---|---|---|
| bench d11/d13/d16/d20/d22 | 312866/862329/3024920/12389307/34048354 | same | same | OK |
| perft5 startpos / kiwipete | 4865609 / 193690690 | same | same | OK |
| per-FEN go depth 13 nodes (fen0..7, ucinewgame each, default Hash) | 72062 209792 125478 51234 80137 64111 174097 85418 | same | – | OK |
| per-FEN bestmove | e2e4 e2a6 h2h3 b4f4 a2a3 f6h5 f7f6 d4c5 | same | – | OK |
NODE IDENTITY: ALL OK (runs/al1s198_frozen_v1/ident/off.compare.txt).

### Node identity, --check-opt UseNNUE=false (demo of the option path)
bench d11..d22 375354/907205/2448617/13573040/24506465, perft OK, per-FEN nodes 88651 291728 89016 49418 161136 3760 93022 130470: plain = ltopgo. "differs from OFF (live)", ALL OK (ident/opt1.compare.txt).

### Reproducibility (why there are two manifests)
- Whole-file .gcda sha256s are **not** reproducible run to run. Four training runs of the same instrumented exe (normal, again, and twice with `setarch -R`) gave different gcda_manifest hashes. gcov-dump shows the only differences are value-profile counters: `ior`/`topn`/`indirect_call` slots holding heap and stack addresses (ASLR), plus a `topn` divisor profile in uci.cpp holding the bench elapsed-ms values (timing). That is why `setarch -R` alone did not fix it.
- The edge counters ARE reproducible: gcda_arcs_manifest is identical (0c5ece46…) across all 4 runs and the v1b rerun.
- The exe IS reproducible:
  - an LTO+PGO rebuild from the second run's profile (different value counters, different build dir, logs/rebuild_repro.out) gave the same f8b6fa25;
  - a full rerun of the final script (runs/al1s198_frozen_v1b) gave plain 97d7e27d, ltopgo f8b6fa25, arcs manifest 0c5ece46, OFF identity ALL OK and gcda_manifest cb786e68… (different, as expected).
- CR also found that the .gcda header `stamp` differs after every rebuild, so whole-file hashes differ between builds even with equal counters. Equal arcs is necessary, not sufficient, for an equal exe (GCC also uses the value profiles).

## GATE_EXE record per LTO+PGO exe (v2.1, agreed by CR + QA; replaces CR's revised D2)
1. **exe sha256: the ONLY binding check.** Two clean rebuilds (pc1, pc2) must give the same forge_ltopgo exe sha256; that sha256 goes into GATE_EXE and is checked against the load line.
2. gcda_manifest sha256 (raw .gcda): **record only**. Raw .gcda hashes are never reproducible (header stamp changes every compile; value-profile counters hold addresses and timings).
3. gcda_manifest_nohdr sha256 (first 12 bytes = magic/version/stamp stripped): **record only**. Value-profile counters may still differ (see box check below).
4. gcda_arcs_manifest sha256: **record only**, or `UNAVAILABLE (no gcov-dump)` on the PC. (In v2 this README said a rebuild must reproduce it; that rule is withdrawn.)
- **An arcs match with a different exe sha256 is a NEW exe**: it needs its own OFF = pins precheck before game 1. pc1 != pc2 exe sha256: neither exe is used; report.
- Both gate sides: same build mode (LP vs LP) and same workload version (v1); never LP vs plain, never v1 vs a pre-freeze build such as 8A4A00C9.
- Box AL1 opponent record: exe f8b6fa25b78a5b9f4b28ad286bb4ff1428211c16c5d309a1fa9c429a4e868d8f (reproduced in runs v1, v1b, v2sh and CR's two rebuilds); arcs 0c5ece46c8df3c47ee7b7cab002593b63c5d1d5fddbea78ae48ea300dc55ac99, gcda_manifest 684a63a5… (run v1, archive profile_archive_al1s198_frozen_v1.tar), both record only.

### Header-stripped .gcda check on the box (kept runs, v2.1)
Three independent builds + trainings (runs v1, v1b, v2sh) plus 5 retrainings of v1's instrumented exe. Bytes 12-15 (the object checksum) were equal everywhere; only the stamp (bytes 8-11) changed per build, so stripping 12 or 16 bytes gives the same result.
- Equal in all 8 profiles: bitboard, eval, eval_params, nnue (4 of 8 units).
- Different between the 3 builds: board, book, search, uci (value profiles: addresses, bench ms). The two `setarch -R` retrainings (norand_1/2) agree except uci (bench elapsed ms).
- So gcda_manifest_nohdr does **not** reproduce across builds either; it only removes the stamp noise. Record only, as above. The exe was still identical (f8b6fa25) in all 3 builds.

## CR conditions
1. Threaded clocked smoke, Threads 1-4: **QA** (not done here).
2. Frozen workload + archived .gcda sha256: FROZEN_WORKLOAD.md + workload files, checked by sha256 in both scripts. Every option stays at its default during training. Manifests + archive are written per build. Both gate sides must be built with this kit (LP vs LP).
3. Exe sha256 in GATE_EXE + OFF = pins before game 1: box exe f8b6fa25…; the PC exe hash comes from QA's build_ltopgo.ps1 run, plus QA's OFF precheck.
4. Per-source node identity vs a plain build: built into both scripts (OFF + `--check-opt`/`-CheckOpt`), including per-bench-position nodes and bestmoves.

## Notes
- Box timing was not done and does not count.
- Nothing was run on grok-pc. No locks were touched. Nothing was deleted or pushed. No STOP/PAUSE files.
- Leftovers in runs/al1s198_frozen_v1, all kept:
  - repro_profile/, norand_1/, norand_2/: the reproducibility runs;
  - profile_repro_use/ + build_lp_repro/ + forge_ltopgo_repro: the rebuild check;
  - `*_VOID*.bak`: a first rebuild attempt that used mis-renamed gcda files (8 missing-profile warnings), voided and renamed.

## Regression of sh v2 (runs/al1s198_frozen_v2sh; 525758f3)
RESULT PASS, no FAILED marker: plain 97d7e27d… (= lock), LTO+PGO **f8b6fa25…** (same exe again), arcs **0c5ece46…** (reproduced), gcda_manifest 3ad578c9… (record only, differs as expected), OFF identity ALL OK, UseNNUE=false ALL OK and live. The instrumented exe (61bba7c3…) differs from v1's because it embeds the profile dir path.
- v2.1 sh adds only the nohdr manifest and wording; its commands were checked on the kept v2sh profile (same 12-byte-stripped hashes as the ps1 code and a python reference). No new box build.

## v2.2 (2026-10-30)
The .ps1 LTO+PGO use link adds `-Wl,--no-insert-timestamp`, so the MinGW PE TimeDateStamp and checksum no longer change between builds (QA saw pc1 and pc2 differ only at bytes 0x88 and 0xD8). The plain build and instrumented link are unchanged, so the plain exe still matches the lock 833C47F3. The .sh is unchanged because ELF has no link timestamp.

## v2.3 (2026-10-30)
The .ps1 has a `-Expose` switch, the same as the .sh `--expose`: it adds `-DFORGE_EXPOSE_TUNABLES=1` to both the plain and the LTO+PGO builds so the gate options show in the uci list, and SUMMARY.txt records `expose True/False`. Only uci.cpp reads that macro. Without `-Expose` every command line is the same as v2.2. `--no-insert-timestamp` and the pc1 = pc2 exe sha256 rule are unchanged. An exposed build is a different exe from the non-exposed one, so it needs its own pc1 = pc2 and OFF = pins check.

## v2.4 (Opus R12, 2026-10-30) - workload v2 for net builds, partial training switch
- `-Workload v2` (default `v1`): frozen workload v2 (FROZEN_WORKLOAD.md, second part): v1's bench 11/13/16, the same with
  EvalFileHalfKA = e19_final and = e9_best, and 8 `go nodes 200000` searches at Threads=2 per block. sha256 of
  frozen_train_cmds_v2.txt (52b8299e...) and nets_v2.txt (8448dae9...) are checked; nets by `-NetE19` / `-NetE9`
  (defaults: `grok-pc\forge_push\bin\r11_e19_final_bf1e347c.nnue`, `...\r11_e9_best_5380f866.nnue`). Training runs
  through `tools\train_driver.py` (waits for real output, checks net sha256 and loads); 9 bench lines are required.
- `-PartialTraining`: adds `-fprofile-partial-training` (GCC >= 10; the kit compiler is MSYS2 g++ 15.2.0) to every use
  compile and to the use link (checked on the link line). Functions that never ran in training are then compiled as
  without profile feedback (normal -O3) instead of for size. SUMMARY.txt records `workload ... partial_training ...`.
- `-CheckOptPins`: one pin string per `-CheckOpt` run (e.g. the net bench counts), passed to `lp_check.py compare --pins`.
- Multiple `-CheckOpt` / `-CheckOptPins` values need `powershell -Command "& build_ltopgo.ps1 ... -CheckOpt 'a','b'"`;
  `-File` passes `'a,b'` as ONE string.
- Defaults (no `-Workload v2`, no `-PartialTraining`, no `-CheckOptPins`) keep every v2.3 command line, so v1 builds
  (lock FD3A5190 and the other v2.3 candidates) are unaffected. A v2 build is its own build mode: it needs its own
  pc1 = pc2 exe sha256 and OFF = pins checks, and it is never compared or gated against a v1 build.
- The .sh (box) is unchanged: v2 is PC-only for now (net paths, Windows driver call).
- R12 runs: `opus_r12/tools/r12_build_chain.py` (waits for a free CPU pair, then runs the kit pinned to it).
- **Use `-Workload v2t1` for gated net builds.** `-Workload v2` (with the Threads=2 `go` part) does NOT reproduce: two
  clean builds gave different exes (12 hot functions differ, FROZEN_WORKLOAD.md "Measured"). v2t1 = v2 without that
  part (sha256 dca15f66...), node-deterministic, trained through the same driver.
