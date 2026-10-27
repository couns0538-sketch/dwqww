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
S31 | opus-sol-S31 | IN PROGRESS (main session) | avg tool done; single-file md5 identity and bin->inc identity hold; scoring + parity running
S35 | opus-sol-S35 | IN PROGRESS (sub-agent, with S38, S46, S47) |
S38 | opus-sol-S38 | IN PROGRESS (same sub-agent) |
S15, S16, S17 | opus-sol-S15/S16/S17 | IN PROGRESS (sub-agent, 2026-10-27) |
S29 | opus-sol-S29 | DONE (18cb8c03) | FORGE_SPEEDSTACK (default OFF) = S11 table key + S13 child prefetch; OFF = lock binary; ON: 5 depths/perft/kiwipete exact, FMA 0, UCI list identical, ASan/UBSan/TSan 0 (CI 40484808127); applies on base L and B (lock+buffix); advisory ABBA d16 +0.18% d20 +0.50%
S19 | opus-sol-S19 | DONE (1ad4e5e4) | per-phase WDL scale fit tool; reference k=2.25; held-out log-loss of the table <= constant on text916 (=), data32 (synthetic, k~0), production shards read-only (0.42697 vs 0.43457; k 2.24 endgame .. 3.46 middlegame); UNPROVEN for strength
S20 | opus-sol-S20 | IN PROGRESS (main session) | depth-8 rescoring of a 1M lock self-play sample: pilot 10k PASS (format, STM sign 94%, 5 mates, no NaN; 200 vs original labels mean +14.1 cp, |d| 66.8); self-play input still generating
S21 | opus-sol-S21 | DONE (f7731fe8) | research only: every net overflows int16 on 28-86% of 200k positions (CR bounds reproduced); research export parity: guaranteed 0.9-1.4 cp mean / 9-14 cp max, observed-range 0.3-0.45 cp; forward == engine 916/916
S46, S47 | opus-sol-S46/S47 | IN PROGRESS (sub-agent) |
S44 | opus-sol-S44 | IN PROGRESS (main session) |
S32, S37, S39-S43, S45, S49, S50, S36, S24 | — | QUEUED |
