# Memory file of neon

Rule 5 of `debate/README.md`: update and push this file about every 10 minutes and whenever your context is nearly
full. Every time in it comes from `date -u +%Y-%m-%dT%H:%M:%SZ`, never from my head.

## Who I am
- Name in this debate: neon
- Model: Gemini 4 Neon
- Started: 2026-11-23T03:40:08Z
- Last update: 2026-11-23T04:18:13Z
- Phase: 2 DEBATE (all three READY; Fable posted PLAN v3, BOARD Phase 2, three PC measurements, F1; Phase 3 starts ~06:10Z our clock, hard stop 06:40Z).

## What I have read
- [x] `debate/README.md`, `debate/PLAN.md` (v3), `debate/STATE.md` (corrected hard cap 8,000), `debate/BOARD.md` (Phase 2), `debate/READ_CHECK.md`
- [x] All 26 source files (11,566 lines), `loop/LOOP_OPTIONS.txt`, `source/R65_NOTE.txt`, `loop/build_recipe/build_forge_clang_pgo.sh`
- [x] All Fable evidence files: `fable_filter_shares_round136.*`, `fable_a1_roundtrip_round136.md`, `fable_a4_lmr_switch_same_rule.md`, `fable_n4_crosstab_round136.*`
- [x] All messages up to shared `8d877df7e1` and Astra `aea8dc9ca6`.

## Local verification runs (in `/tmp/forge-bin/`, repo untouched)
- Linux builds: `forge_v4` (AVX-512+PEXT), `forge_v3_pext` (AVX2+PEXT), `forge_v3` (AVX2 no-PEXT), `forge_san` (ASan+UBSan, 0 errors), `forge_cmake` (stock `CMakeLists.txt` lacks defines -> `bench 11 = 278016`).
- Verified pins: defaults `bench 11 = 312866`, `bench 13 = 862329`, `perft 5 = 4865609`; r67 `bench 11 = 226187`, `bench 13 = 616966` (FNV-1a `290bbb0b2e578ac`, SHA-256 `737f197808fef489017cf46f4daf76663d805bb01761e2b1781fc46fa7c9fc28`).
- Verified `A4` (`LmrDeeperShallower value true` + r67 `LOOP_OPTIONS.txt`) on Linux: both `forge_v4` and `forge_v3_pext` print `bench 13 = 595569` (exact match to Fable and Astra).
- Verified Astra's Hash blind-spot catch (`uci.cpp:1245`): `bench 13 = 616966` under Hash 16 and 32, while live `go depth 18` gives `375880` (`hashfull 156`) vs `375868` (`hashfull 78`).
- Traced `search.cpp:1974,1991`: all five `qsearch_child` call sites (`1877, 1913, 1991, 2078, 2165`) already satisfy `!root_node && excluded.is_none()`.
- Checked `uci.cpp:529-544`: `evallimit` breaks before `records.push_back`, so `evallimit 1000` is a runtime parameter with no C++ edit, and offline replay must drop the crossing row + suffix, relabel earlier rows counterfactually, and re-run the result-contradiction filter.

## Proposals & convergence status
- `A1`–`A5`: ACCEPTED / TO MEASURE (A2); Neon agreed with independent checks on all 5. Fable's A3 deduplication question answered by Astra (`aea8dc9ca6`/previous).
- `N1`–`N7`: ACCEPTED / TO MEASURE (N4, N5, N7) in `PLAN.md` v3; Neon agreed with all Fable PC corrections/additions and Astra's `N4` counterfactual replay rules.
- `N8` (worker IDs + kill-restart rehearsal + cheap NVIDIA Triton smoke test & quantized eval parity) & `N9` (fixed teacher net provenance + matched `teacher_weight=0` ablation): Astra AGREE; awaiting Fable's reply.
- `F1` (2,000-soft-node non-inferiority SPRT `[-3, 0]`): Neon AGREE with `[-3, 0]` SPRT and AGREE with Astra's DISAGREE on cap fallback (treat cap without boundary as inconclusive, not post-sequential fixed CI) + single-run `A vs A` as pipeline/speed test + pentanomial SPRT + fallback `[-5, 0]` if runner overhead makes 100k games slow + sync `PLAN.md:333-334`.

## Next steps
- Push `20261123T041813Z_neon_re_f1_a4_n1_to_n7.md` + this memory file.
- Inspect untouched plan items (`P5`, `P6`, `P12`, `Section 5` execution order, `Q2` 2B architecture/speed/node-odds protocol, `Q2b` rented server depth/mix) for any real evidence-backed gaps, while monitoring Fable's answers to `N8`/`N9`/`F1` and any new `F2+`/`A6+` proposals.
