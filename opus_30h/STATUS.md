# STATUS - Opus 30-h job (branch opus-30h-20261103, worktree D:\o30\wt, scratch D:\o30)

Plan approved 2026-11-03 (PLAN.md, defaults D1-D4). Worktree created 16:17 PC clock. No sub-agents. No Elo claims.
User goal (16:2x): work the full 30 hours; when one thing is blocked, improve the unblocked ones; 1-hour bug hunt at the
end; check that it works in Forge.

## GPU
Not released (npt keeper: live line s39, window to 2026-11-08 00:00 PC). Training therefore runs on the CPU
(own torch fine-tune from the lock net, `opus_30h/a/o30_fit.py`), which needs no GPU; the GPU path stays a follow-up.

## Done so far
| item | state |
|---|---|
| 0 base re-verify | kit v2.3 -Expose of the unpatched lock = fd3a5190... on pc1 and pc2 |
| A port (EvalFileV2) | OFF pins PASS; lock net as v2 = lock pins d11-d22 (3 layouts); parity 10000/10000 x 4 nets x AVX2/SSE/scalar; walk 830k plies x 3 nets 0 mismatches; in-search verify clean; kit v2.3 pc1 = pc2 df1f140b (v2 path 0.71x of the lock: cold PGO), kit v2.4 -PartialTraining pc1 = pc2 8704d302 (v2 path 0.959x, CI 0.929-0.990) |
| A scorer | `o30_score.exe` reproduces AL1 b0.6 0.014310027 / b1.0 0.004572428 on the S31 subset; lock HCE = FHCE on all 1,024,286 rows |
| A trainer | `o30_fit.py selfcheck`: its own forward pass = the scorer (KB4 / OB8 warm start from the lock) |
| A data audit | running (`o30_data.py` -> D:\o30\data) |
| B options | 22 new tunables (defaults = lock pins PASS), 22 / 22 live; kit build waiting for CPUs 0-1 |
| B tuner | `tune_spsa.py` + `tune_spsa.ps1` + `selftest_10min.ps1` written; self-test not run yet |

## Finding so far (17:4x, written early on purpose)
Three facts point the same way: the crew's bigger pure nets lost ~100 Elo to the lock (4 gates); the lock net is
converged on its own data (a KB1 / OB8 fine-tune moves S31 b0.6 by < 1e-6 in 30M positions at two learning rates);
the only number that moved clearly was the jobA val loss, whose labels come from 20k-node searches instead of the
5k-node self-play. The ceiling looks like the LABELS, not the architecture. Gate-next for the crew therefore includes
the 50M relabel (R14-B relabel2.py, costed at 78.7 h) feeding a v2 retrain - on the GPU path once a window exists.
CPU plan: N1 (KB1 / OB8) runs on CPU 0; KB4 gets a 2-hour decider on CPU 1 after the SPSA self-test; if it does not
clear the rule in a/RESULTS.md, CPU 1 goes to the SPSA main run at once.
