# Next job for Sol: 3.5 hours, four tasks in a fixed order (b, a+c, d), checkpoint every ~60 min

You are continuing work on the Forge C++ chess engine, repo couns0538-sketch/dwqww. Start from your own branch forge/sol-nnue-speed-audit-20261024 at 3afd230. New branch: forge/sol-next-20261024.
Lock = "h256_e12" = 1ab50b2d + net 6d22f612 = your commit f4911f2. It is always built with -DFORGE_NNUE_HIDDEN=256 and these flags: -std=c++20 -O3 -DNDEBUG -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread -Iinclude. Every patch you hand off is a -p1 patch against f4911f2.

Attached: REVIEW_3afd230_QA.md (our review of your checkpoint, read it first), nps_abba_bc.ps1 (our PC speed protocol template), CR_PASS_nnue_e16m.txt (the handoff format CR expects), CR_PASS_int16_ep10.txt plus fc_int16_ep10_src.tar.gz (our existing int16 path, H128-only, aborts on H256), check_nnue_simd_v2.py (our SIMD/FMA checker), FORGE_IDEA_BOARD_P22_P23.md (rules and the fallback search item).

## Standing rules (apply to everything)
- Ideas only. Never copy code, constants, or tables from another engine. Write each idea's source in IDEA_SOURCE.md.
- Every new behaviour sits behind its own switch, OFF by default. With every switch OFF the binary must give the lock bench exactly at all 5 depths (Threads 1, Hash 16, OwnBook false): d11 308972, d13 745494, d16 2460422, d20 11901452, d22 31111774. Also perft5 4865609 and kiwipete perft5 193690690.
- d11 precondition: before any other test of a build, run bench 11 with everything OFF. If it is not 308972, stop and report. Do not measure anything else on that build.
- No matches, no SPRT, no trainer or net changes. Never claim Elo.
- Print the exact FAIL lines from ctest, not just the count. Your "four known failures" are four FAIL lines inside one failing test (forge_tests), so 13/14. Report it that way.
- Keep it short. Skip new giant evidence bundles (no multi-GB oracle streams in git). Store hashes and summaries instead.

## Clock (T0 = when you start; hard stop at T0+3:25)
- T0+0:35 (b) done, plus checkpoint 1 commit.
- T0+1:20 (a+c) script done, plus checkpoint 2 commit.
- T0+2:30 int16 parity numbers must exist. If not, stop int16 completely and switch to the fallback (see d).
- T0+3:05 stop coding. Write SOL_REPORT_<date>.md and the CR handoff.
- T0+3:25 final push. Print the final commit SHA.
Commit and push a checkpoint about every 60 minutes, even if something is half done. Never hand off a half-done int16 patch as a candidate.

## (b) Bad-capture buffer: FIRST, about 35 min
search.cpp:361 `bad_captures_[bad_count_++] = move;` writes into std::array<Move,64> (line 453) with no bound. The capture list feeding it can hold up to 256 entries (moves_ line 450, MoveList::Capacity 256).
1. Confirm it or rule it out. Do NOT use the checker that was blocked last time. Instead build the normal engine with `-O1 -g -D_GLIBCXX_ASSERTIONS` (std::array operator[] then aborts on out-of-range). Note that ASan cannot see this overflow, because it stays inside the MovePicker object (bad_count_ is the next member). Feed it with plain UCI `position fen ... / go depth 3` on FENs that have more than 64 SEE-losing captures and promotions for the side to move. Two starting candidates are in REVIEW_3afd230_QA.md. They did not trigger at depth 2 on our box, because the engine's SEE counted fewer losing captures than our estimate. Search for denser ones with a small offline script: count captures where see_ge(move,0) is false, using the engine's own SEE through a tiny test harness linked against forge_core. That harness is a normal unit test, not a native fuzzer.
2. Either way, fix it: write a bound check, or size the array to MoveList::Capacity. This is not a switch. It must stay bench-identical at all 5 depths, because no real game reaches 64. Add a ctest case with the densest FEN you found.
3. Then run one ASan+UBSan bench (bench 13) and the _GLIBCXX_ASSERTIONS bench on the build with all your flags ON (FORGE_AVX512=1 FORGE_NNUE_ALIGN64=1), plus the full ctest under ASan/UBSan on that build. This closes your stage-3 gap.
Deliver as its own -p1 patch (buffer_fix.patch) with: bench at 5 depths, perft, ctest lines, and the FEN you used. Say plainly "confirmed overflow" or "not reachable with FENs tried, fixed defensively".

## (a+c) One Zen5 PowerShell script for grok-pc: about 45 min. You write it; we run it.
We run it on grok-pc: AMD Ryzen Zen5, Windows, g++ 15.2 (MSYS2/UCRT), exes in C:\Users\Administrator\grok-pc\forge_push\bin, outputs to D:\grok-pc-data\forge_push\speed_window. Start from nps_abba_bc.ps1, keeping its style (ProcessStartInfo, ProcessorAffinity pin, Normal priority, never kill other processes, STATUS file). Name it zen5_qualify_sol.ps1. Params: -Cpu (default 6), -Exes as a list of paths, -Depth 16.
It must do, in this order, and stop at the first failed step:
1. Identity: print sha256 of every exe. Run bench d11/13/16/20/22 on each exe. Every exe must equal the lock numbers above, else STOP "BADNODES".
2. Bit-exact check before any nps counts: run your oracle (a small .exe you provide, built from tools/nnue_million_oracle.cpp, Windows-buildable) over 1,000,000 positions for the AVX-512 build vs the scalar/OFF build. Interleave the two in chunks on the same pinned core, compare hashes, and print PASS/FAIL. Any FAIL stops the script and nps is not reported.
3. Noise floor: 6 A/A pairs (lock vs lock, pinned, palindrome order).
4. 14 ABBA pairs per candidate vs lock, Threads=1, same pinned core, order A B B A. The candidates are: OFF lock, AVX512 stage1, stage2, stage3 (align64), and the int16 build if it exists. Include an explicit AVX-512 ON vs OFF comparison (stage3 vs lock).
5. Verdict per candidate: FASTER only if at least 12 of 14 pairs are faster AND the median gain is beyond the A/A band (state the band). Otherwise NOISE, or SLOWER if 12+ of 14 pairs are slower. Treat stage 2 as a possible regression unless it is shown FASTER.
6. Where the time goes on Zen5: per-phase breakdown. If you can, add an optional `-Profile` switch that runs your tools/nnue_*benchmark style micro-bench (refresh / update / evaluate ns per call, AVX-512 vs OFF) and one bench 16 with internal counters (time in nnue::evaluate, nnue::update, movegen, search). Use the engine's own timers behind an OFF-default build flag, because Windows has no perf. Report the % split, not only pass/fail.
7. Write a CSV and a SUMMARY block: exe sha256, nodes_ok, per-pair %, median, mean, faster k/14, A/A band, verdict, bit-exact PASS, and the phase split.
Also give EXPECTED_OUTPUT.md: what a correct run prints (bench numbers, PASS lines, CSV header), and a 1-line build command per exe for g++ 15.2 on Windows. Run the script yourself on Linux under pwsh if you can, to catch syntax errors. Any Linux timing you get is only a dry run.

## (d) int16 quantised inference for H256: rest of the time, with a hard fallback
Goal: int16 weights with int32 (or wider where needed) accumulation for the H256 residual net, extending your AVX-512 and align64 work in nnue.cpp. Our earlier H128 version is attached (fc_int16_ep10_src.tar.gz, CR_PASS_int16_ep10.txt). It ABORTS on H256 at start-up, because the int32 output bound for e12 is 2,510,422,016 > 2^31-1 at output scale 8192. Fix that properly, for example with a per-group partial reduction into int64, or a lower output scale chosen from OUR weights' measured bounds. Use no other engine's constants. Derive the quantisation scales and clipping from our own weights, and document the derivation in IDEA_SOURCE.md.
- Switch: an OFF-default UCI option (name it NnueInt16, default false). With it OFF, H256 stays float and bench equals the lock at 5 depths. Enabling it must never abort. If the net is not representable, print an info string and stay on float. Gating or locking with it ON needs a separate crew vote later, so do not suggest it.
- Keep the effort in proportion. Inference is about 15.6% of node time, so the ceiling is about +8% nps. Do not spend more than 1 h on the abort fix. If it takes longer, or if less than 1.5 h is left after (a+c), go straight to the fallback.
- Parity report vs float on at least 100,000 FENs: max, mean and p99 |cp diff|, the number of sign flips, and the number of bestmove changes at depth 13 (use a subset if time is short, and state the size). Pass limits, fixed now: mean <= 2 cp AND max <= 30 cp. Report pass/fail against those.
- Also: d13 and d16 node counts with it ON, paired WAC300 at 1000 ms (OFF / ON / OFF on one core), nps via the paired protocol in (c) (a Linux dry run is fine; the PC run is ours), one ASan+UBSan bench with it ON, FMA count 0 in forge::nnue functions (check_nnue_simd_v2.py), and the uci option listed.
- Fallback (clock-triggered): if the parity numbers are not ready by T0+2:30, stop int16 and hand off P22 SingTtPv from FORGE_IDEA_BOARD_P22_P23.md instead (backup P23 RefutLmr if P22 does not fit). Use UCI options that are OFF by default, so the OFF bench equals the lock at 5 depths. Add a node screen with only that option ON at d13 and d16 (rule: no more than +10% vs lock), plus a short paired WAC300. Commit any unfinished int16 work only on a separate WIP branch, clearly marked "not a candidate".

## Handoff format (copy CR_PASS_nnue_e16m.txt's level of detail)
For each candidate (buffer_fix, int16 or P22): a zip of the full source tree plus sha256, the -p1 patch vs f4911f2, and a CR_DRAFT.md with:
- the d11 precondition result first
- the 5-depth bench, OFF and with each option ON separately (one row per option)
- perft5, kiwipete, ctest with exact FAIL lines, FMA 0, simdcheck v2 PASS
- paired WAC300 1000 ms, null-move cutoffs at d8 working, and every option name as printed by `uci`
- exact compile lines and exe sha256
- IDEA_SOURCE entry
One option per gate, and no options that change each other's code path.
Finish with SOL_REPORT_<date>.md, at most 1 page: what is verified vs claimed, what is still open, and the final commit SHA.
