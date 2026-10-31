---
name: forge-lock-port
description: Port a near-miss Forge patch or an R3-stack / bundle feature onto the AL1 lock tree (git d4f4312 = src_al1s198_clean = lock FD3A5190's source) as an off-by-default option, and prove the port - fresh LF lock copy with a scratch git repo, monolithic vs O3-split layouts, anchored port scripts, exact ON-node references, line-set proof, handoff layout. Use for any "port X to the lock / make X gate-ready as LTO+PGO" job (R13 P1 items: B1, packa, bnd68, packc, eos49, Sf26 splits, Syzygy).
---

# Porting a feature onto the lock tree (R13, 2026-10-31)

Rules first: [[forge-pc-rules]]. Build + checks after the port: [[forge-candidate-checks]], [[forge-ltopgo-pgo]].
Tools: branch `opus-r13-p1-nearmiss-ports`, folder `opus_r13/tools/`.

## Facts
- Lock source = **git d4f43124dde1d1e37de90e18930e374f32ea7ffa** = `C:\Users\Administrator\grok-pc\forge_push\qa_ltopgo_al1_stage\src_al1s198_clean`
  (20 files, all blobs equal). Monolithic `src/search.cpp` (1531 lines), 8 units: bitboard board book eval eval_params nnue search uci.
- O3 804c6e1b split search.cpp into `src/search/*.inc` + ThreadData ("no behaviour change"). Everything built on the R3
  stack (opus-r3-stack, forge-bundle-int: Opus C2 CorrHistPlus, C6 CuckooRep, ...) is on that split layout; the hunks map
  back 1:1 onto the lock's search.cpp (same function bodies, same member names: Worker::, stack_, root_history_index_).
- Written on the monolithic layout (apply with `patch -p1 -F0`): Astra A1 HistRework a8b63aae, C6 board part 2cb0babd,
  packa.patch, packc.patch, sf26bundle_al1.patch. FB2-J3 33e295b4 needs hand edits (2 of 4 hunks fail).
- R3's macro instances (alphabeta.inc included once per FORGE_SEARCH_FN) become ONE template parameter on the lock:
  `template <bool Cuckoo> int search(...)`, child calls through `search_child<Cuckoo>` / `qsearch_child<Cuckoo>`
  (12 call sites: 8 search + 3 qsearch in search(), 1 qsearch in qsearch()); root dispatch picks the instance.

## Steps
1. `bash opus_r13/tools/fresh_lock.sh C:/o13/p1/<item>` (git archive with core.autocrlf=false + scratch repo, base commit).
2. Apply monolithic patches with `patch -p1 -F0` (dry run first); drop CMakeLists hunks (no CMake in the lock tree), keep
   new test files and build them by hand (`g++ ... tests/x.cpp src/board.cpp src/bitboard.cpp`, asserts on).
   Commit each applied source separately in the scratch repo.
3. Split-layout code: copy whole helper files unchanged where possible (correction_plus.hpp/.inc, cuckoo.inc wrappers),
   then a port script `opus_r13/tools/port_<item>.py` with anchored edits (`assert text.count(old) == 1`, LF bytes).
   Header needing search.hpp constants: include it from search.hpp right after them (close/reopen `namespace forge`).
   New options: same UCI names, types, ranges and defaults as the original; advertise them (the gate runner checks that).
4. Plain build `opus_r13/tools/plain_build.sh <repo> <out>` (lock g++ line + Expose, CPUs 2-3 BelowNormal; ~20 s), then
   `lpc.sh <exe> off.json 0x4` (OFF pins, perft, per-FEN d13 nodes) and `lpc.sh <exe> on.json 0x8 --opt N=V`.
5. **Binding port proof = exact ON nodes vs the original wherever it was benched on the AL1 tree** (all depths). R13 B1:
   BundlePreset=B1 280182/758456/3357587/11208630/20560049, TtPruneV2 alone 309157/736967/2960397/12062561/34293668,
   CorrHistPlus=1 d11 318363 (forge-bundle-int BUNDLES.md) - all matched first time. On a mismatch bisect with singles.
   Patches made on the old h256e12 base (packa/packc/packe2r) cannot match (other net): say so.
6. Line set: `lineset_diff.py ORIGINAL.patch PORT.patch [--exclude-path REGEX]` (sorted +/- multiset, whitespace-
   normalised). Mechanical ports: EQUAL after excluding dropped files. Layout ports: list the categories (macro/instance
   lines, split-file includes, R3 option headers vs the port's option block) - the node proof is the binding one.
7. Port patch = `git diff <base> HEAD` in the scratch repo (a/ b/ headers, applies with `patch -p1` on a clean lock copy).
   Keep `opus_r13/.gitattributes` = `* -text` so patches stay LF in checkouts.

## Handoff layout (per item folder `opus_r13/p1/<item>/`)
README.md (exe path + sha256 pc1 = pc2, exact setoption gate lines, PC precondition = exact ON bench 13 nodes + OFF pins,
check table with evidence paths, notes), `<item>_port.patch`, IDEA_SOURCE.md (origin commits + idea sources, GPL = ideas
only), logs under `opus_r13/p1/logs/`. Exe in `C:\o13\handoff\<item>\` (F: was under its 50 GB floor), never in git.

## Pitfalls
- `git archive` / checkouts convert to CRLF here (core.autocrlf=true): always `-c core.autocrlf=false`.
- bash -> powershell -> exe quoting breaks on `;` and quotes: run Python tools via `run_pinned.py --mask 0xC -- tool.py`.
- A tunable with a non-zero default (NonPawnCorrWeight 100) is a parameter, not a switch: check it with
  `cand_checks.py --new-param N=default`, switches with `--new-opt`.
