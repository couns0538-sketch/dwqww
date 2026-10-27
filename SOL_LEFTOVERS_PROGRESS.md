# SOL_LEFTOVERS_PROGRESS (Opus 5.5) — one line per job: job | branch | state | note
# Source queue: SOL_LEFTOVERS_FOR_CLAUDE.md (QA, 2026-10-27). Sol's branch forge/sol-pack31-20261025 @ 17aa0ca read only.
# Engine ports are based on d4f4312 (verbatim AL1 lock tree + baseline evidence + CI recipe; this repo's main is not a source tree) with the CI-only commit 0d99f02 cherry-picked.
# Resume notes for jobs wound down without commits: F:\opus_scratch\sol_resume_notes\ (S30/S31/S35/S38).
S11 | opus-sol-S11 | DONE (e0c129b1) | MaterialKeyTable (UCI, default off) = Sol's material_key table-sum on AL1; ON==OFF==AL1 on all refs incl. scalar NNUE (PC+Linux); CI 40478253767+40478254153 green; quiet-runner ON/OFF d16 +0.2% d20 +1.7%, >=+2% rule not met; no Elo claim
S13 | opus-sol-S13 | DONE (5ccfe1ac) | Sol's cc3efc96 ported verbatim (switch FORGE_S13_TT_CHILD_PREFETCH + UCI TtChildPrefetch, both default off); default build = lock binary; checker-fix re-review PASS; ON==OFF all refs; null 640/ProbCut 217 child prefetches; CI 40481055829+40481055934 green; NPS no measurable effect; no Elo claim
S18 | opus-sol-S18 | DONE (1713f1b2) | t200-t500 CPU smoke on the PC (renamed trainer copy, BelowNormal, 6 GiB RAM floor); loss table; run1==run4 byte-identical; shards/histograms match Sol (manifest order differs on Windows: finding); t200 vs Sol Linux ref: loss lines + .inc identical, float .pt differ <=7.5e-9; no net adoption
S12 | opus-sol-S12 | DONE (d0574f53) | lazy updates already in AL1 (and opus-O2); Job A cause written (int32 ON kernels 10-12x float instructions + 288-insn conversion per eval; refresh 8/bench); null-move alias not ported (UNVERIFIED)
S14 | opus-sol-S14 | DONE (9dca2a54) | nothing left in AL1 (fixed picker + squares_ mailbox; static audit of the lock exe: 0 allocation calls); follow-ups: bad_captures_[64] unguarded (buffix not in AL1), 3,328 B zero-fill per picker (NPS UNVERIFIED)
S34 | opus-sol-S34 | DONE (042cf3e9) | v2 validator (deployed-driver profile, autopromote annotations, option rules, case-dup keys); live file: 13 real legacy duplicate starts, 0 false errors; 51 fixtures, 31 tests, 10/10 mutants caught
S22 | opus-sol-S22 | COVERED by opus-O1 (report pushed, 80edf0d) | Sol's open T2 node observation = O1 bug 1 (SmpExactNodes)
S30 | opus-sol-S30 | DONE (46894c18) | study with file:line citations: G104 early H1 not repeated by G104c (+7.18); e24->e48 at fixed data -1.6e-5 b0.6 (noise level, seed sd 7.1e-6); data size -1.68e-4 per doubling (23 runs); loss has not predicted Elo; replicas byte-identical (synthetic data, pipeline only)
S31 | opus-sol-S31 | IN PROGRESS (main session, finishing) | avg tool (.inc/.bin/.pt; .pt = .bin byte for byte), md5 identities, parity 49,999/50,000 exact + 1 float32/64 boundary case, production holdout table (f006 avg2/3/4 -2.2/-3.4/-4.6e-6 b0.6 vs ep48, inside seed noise), PC runner
S35 | opus-sol-S35 | DONE (5ad87037) | pwsh7 harness, 4 scenarios, 9 targets; live conc7_watch 3/4 (F1 rotation dedupe), v3 fix 4/4 not deployed (needs CR); ReadAllText negatives FAIL S1
S38 | opus-sol-S38 | DONE (627130b8) | gate_time_audit + deterministic fixture; = RESULT.md/GATE_RESULTS.csv on 7 real gates; G125 nps asymmetry 3.68% flagged
S15 | opus-sol-S15 | DONE (3d22bb52) | SPSA harness v2 = Sol v1 + PC run driver; 51 tunables; 29 tests, 16/16 mutants; fixture 2 params x 4 iterations at Idle; no tune applied; fixed v1 -maxmoves adjudication + e.p. FEN mismatch
S16 | opus-sol-S16 | DONE (b591ca92) | real 013/014 vs the 29 training shards: 6,069 of 231.9M rows overlap (5,042 label conflicts), 0 straddling games, 0 whole-file dups; Sol filter v3 (4 Windows fixes) 41/41
S17 | opus-sol-S17 | DONE (be60912c) | Sol gamesplit v2 (5 Windows fixes) 14/14; real split of 2,930,566 rows (33,467 games): leak 0 (independent audit), manifest + SHA256SUMS
S29 | opus-sol-S29 | DONE (81a80312) | FORGE_SPEEDSTACK (default OFF) = S11 table key + S13 child prefetch; OFF = lock binary; ON: 5 depths/perft/kiwipete exact, FMA 0, UCI list identical, ASan/UBSan/TSan 0 (CI 40484808127); applies on base L and B (lock+buffix); advisory ABBA d16 +0.18% d20 +0.50%; step 8 (2026-10-27): PC switch-on build node-exact, PC NPS A/B under load -0.4..+0.3% (inside noise)
S19 | opus-sol-S19 | DONE (1ad4e5e4) | per-phase WDL scale fit tool; reference k=2.25; held-out log-loss of the table <= constant on text916 (=), data32 (synthetic, k~0), production shards read-only (0.42697 vs 0.43457; k 2.24 endgame .. 3.46 middlegame); UNPROVEN for strength
S20 | opus-sol-S20 | IN PROGRESS (main session) | depth-8 rescoring of a 1M lock self-play sample: pilot 10k PASS (format, STM sign 94%, 5 mates, no NaN; 200 vs original labels mean +14.1 cp, |d| 66.8); self-play done (11,700 games, 1,110,116 positions, md5 98dddc98); full 1M rescoring running
S21 | opus-sol-S21 | DONE (f7731fe8) | research only: every net overflows int16 on 28-86% of 200k positions (CR bounds reproduced); research export parity: guaranteed 0.9-1.4 cp mean / 9-14 cp max, observed-range 0.3-0.45 cp; forward == engine 916/916
S46 | opus-sol-S46 | DONE (cb6d8956) | config-driven simulator, 27 fixtures, real 2026-10-25 replay 13/13 identical; live script differs only on the step-5 suffix fixture (G55/G56 bug)
S47 | opus-sol-S47 | DONE (99365efc) | Part A net-only + Part B audit packet (never grants CR); real AUTOLOCK_1 net-only PASS; AL1 audit INCOMPLETE (old UCI list missing)
S44 | opus-sol-S44 | IN PROGRESS (main session) | 23 net gates; opponent from RUN_INFO (G98/G103/G105-G112/G122/G123 were vs AL1); exact fastchess GSPRT reproduced on all; per-gate stopping-rule simulation (Whitehead adjustment) running
S32, S37 | opus-sol-S32/S37 | IN PROGRESS (sub-agent, 2026-10-27) |
S39, S50 | opus-sol-S39/S50 | IN PROGRESS (sub-agent) |
S40, S42, S43 | opus-sol-S40/S42/S43 | IN PROGRESS (sub-agent) |
S41, S45, S49 | opus-sol-S41/S45/S49 | IN PROGRESS (sub-agent) |
S04fix-S08fix | opus-sol-S04fix..S08fix | IN PROGRESS (sub-agent) |
S09fix, S10fix | opus-sol-S09fix/S10fix | IN PROGRESS (sub-agent) |
S25fix-S28fix, S33fix, S48fix | opus-sol-<JOB>fix | IN PROGRESS (sub-agent) |
S36, S24 | — | QUEUED (last; inputs found on Sol's branch: Job C + S01 patches and tree sha256 lists; int32 shelf patch) |
# Other user jobs (2026-10-27): C3 follow-up (opus-C3 581ad5da: watchdog obeys searchmoves, DebugSearchDelayMs debug-only, CI green) | O1-LTT info line (opus-O1-LTT da677d70) | S-IT intended threefold (opus-sol-SIT edc25191, CI release/ASan/TSan green; quiet-runner NPS pending)
