# SOL_LEFTOVERS_PROGRESS (Opus 5.5) — one line per job: job | branch | state | note
# Source queue: SOL_LEFTOVERS_FOR_CLAUDE.md (QA, 2026-10-27). Sol's branch forge/sol-pack31-20261025 @ 17aa0ca read only.
# Engine ports are based on d4f4312 (verbatim AL1 lock tree + baseline evidence + CI recipe; this repo's main is not a source tree) with the CI-only commit 0d99f02 cherry-picked.
# Resume notes for jobs wound down without commits: F:\opus_scratch\sol_resume_notes\ (S30/S31/S35/S38).
S11 | opus-sol-S11 | IN PROGRESS (sub-agent, 2026-10-27) | then S13 by the same agent
S13 | opus-sol-S13 | IN PROGRESS (same sub-agent, after S11) |
S18 | opus-sol-S18 | PARTIAL (c86282d4) | inputs pin-checked 42/42; t200/t300/t400/t500 NOT STARTED; main session resumes (REPORT.md resume plan)
S12 | opus-sol-S12 | DONE (d0574f53) | lazy updates already in AL1 (and opus-O2); Job A cause written (int32 ON kernels 10-12x float instructions + 288-insn conversion per eval; refresh 8/bench); null-move alias not ported (UNVERIFIED)
S14 | opus-sol-S14 | DONE (9dca2a54) | nothing left in AL1 (fixed picker + squares_ mailbox; static audit of the lock exe: 0 allocation calls); follow-ups: bad_captures_[64] unguarded (buffix not in AL1), 3,328 B zero-fill per picker (NPS UNVERIFIED)
S34 | opus-sol-S34 | PARTIAL (0c016ffc) | live forge_gates.json copied read-only; Sol v1: 123 false UNSUPPORTED_FIELD + 246 false strict errors; v2 validator not written (resume steps in REPORT.md)
S22 | opus-sol-S22 | COVERED by opus-O1 (report pushed, 80edf0d) | Sol's open T2 node observation = O1 bug 1 (SmpExactNodes)
S30 | opus-sol-S30 (local only, d4f43124) | PARTIAL, nothing committed | inputs located, facts checked; resume notes saved
S31 | — | NOT STARTED | inputs located (f006 ep45-48 .pt on the PC)
S35 | — | NOT STARTED | pwsh 7.6.8 present; watcher copies located
S38 | — | NOT STARTED | GATE_RESULTS.csv has time_losses/crashes columns
S15, S16, S17 | — | QUEUED (main session, after S18) |
S29 | — | QUEUED (after S11/S13: stacks their node-exact survivors) |
S19, S20, S21, S32, S37, S39-S50, S36, S24 | — | QUEUED |
