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
S30 | opus-sol-S30 (local only, d4f43124) | PARTIAL, nothing committed | inputs located, facts checked; resume notes saved
S31 | — | NOT STARTED | inputs located (f006 ep45-48 .pt on the PC)
S35 | — | NOT STARTED | pwsh 7.6.8 present; watcher copies located
S38 | — | NOT STARTED | GATE_RESULTS.csv has time_losses/crashes columns
S15, S16, S17 | opus-sol-S15/S16/S17 | IN PROGRESS (sub-agent, 2026-10-27) |
S29 | opus-sol-S29 | IN PROGRESS (main session) | FORGE_SPEEDSTACK = S11 table key + S13 child prefetch
S19, S20, S21, S32, S37, S39-S50, S36, S24 | — | QUEUED |
