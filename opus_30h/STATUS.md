# STATUS - Opus 30-h job (branch opus-30h-20261103, worktree D:\o30\wt, scratch D:\o30)

Plan approved 2026-11-03 (PLAN.md, defaults D1-D4). Worktree created 16:17 PC clock. No sub-agents. No Elo claims.
User goal (16:2x): work the full 30 hours; when one thing is blocked, improve the unblocked ones; 1-hour bug hunt at the
end; check that it works in Forge.

## GPU
Not released (npt keeper: live line s39, window to 2026-11-08 00:00 PC). Training therefore runs on the CPU
(own torch fine-tune from the lock net, `opus_30h/a/o30_fit.py`), which needs no GPU; the GPU path stays a follow-up.

## Done so far (17:4x PC clock)
| item | state |
|---|---|
| 0 base re-verify | kit v2.3 -Expose of the unpatched lock = fd3a5190... on pc1 and pc2 |
| A port (EvalFileV2) | OFF pins PASS; lock net as v2 = lock pins d11-d22 (3 layouts); parity 10000/10000 x 4 nets x AVX2/SSE/scalar; walk 830k plies x 3 nets 0 mismatches; in-search verify clean; CI (ASan+UBSan, load check) green; kit v2.4 -PartialTraining pc1 = pc2 8704d302 (v2 path 0.959x the lock; kit v2.3 df1f140b: 0.71x, cold PGO) |
| A scorer | `o30_score_v2.exe` reproduces AL1 b0.6 0.014310027 / b1.0 0.004572428 on the S31 subset; lock HCE = FHCE on all 1,024,286 rows |
| A data audit | DONE: 304,999,573 train rows (= the npt binpack), 7,706 holdout-overlap rows skipped, jobA aligned 0 mismatches, 988,336 overrides, jobA val 8,821 rows |
| A trainer | selfcheck PASS; LR probes done (lock converged); N1 KB1/OB8 running on CPU 0 (to 2026-11-04 03:30); KB4 decider on CPU 1 (to ~19:50) |
| B options | 22 new tunables (defaults = lock pins PASS), 22 / 22 live; kit v2.3 exe pc1 = pc2 7bf5dab3; CI green |
| B tuner | tune_spsa + wrapper + README; SELFTEST PASS (selftest_2: 19 batches, 3 sessions); main run waits for a CPU |
| tools | MCP forge-o30 (5 tools, self-test 8/8, registered at user scope), skills forge-o30-v2net / forge-o30-spsa, TOOLS.md |

## Finding so far (17:4x, written early on purpose)
Three facts point the same way: the crew's bigger pure nets lost ~100 Elo to the lock (4 gates); the lock net is
converged on its own data (a KB1 / OB8 fine-tune moves S31 b0.6 by < 1e-6 in 30M positions at two learning rates);
the jobA val loss (20k-node labels instead of the 5k-node self-play labels) moved more than S31 only in the short
lr 1e-4 smoke (-5.5e-5 while S31 got worse by +2.8e-5) - suggestive, not proven (the 30M probes moved it -6.8e-6 /
+1.1e-5). The ceiling may be the LABELS rather than the architecture; KB4 (more capacity) is the test of the other side. Gate-next for the crew therefore includes
the 50M relabel (R14-B relabel2.py, costed at 78.7 h) feeding a v2 retrain - on the GPU path once a window exists.
CPU plan: N1 (KB1 / OB8) runs on CPU 0; KB4 gets a 2-hour decider on CPU 1 after the SPSA self-test; if it does not
clear the rule in a/RESULTS.md, CPU 1 goes to the SPSA main run at once.
