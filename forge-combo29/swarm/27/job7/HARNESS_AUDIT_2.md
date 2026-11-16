# Harness audit #2 — seat 10's warm-table rule (Clear Hash is NOT a cold baseline)

Rule (seat 10): two identical unrestricted searches in ONE process give 56,720 → 4,951 → 4,516 nodes; three
separate processes give 56,720 each. `ucinewgame` restores cold exactly; **`Clear Hash` does not** — it gives a
third value (40,569, deterministic). So a cold baseline is a fresh process or `ucinewgame`, never `Clear Hash`,
and node counts must not be compared across searches that shared a process.

I audited every script I committed by reading its process handling, not from memory.

## Verdict per script

| script | searches per process | cold baseline used | status |
|---|---|---|---|
| `honesty.sh` | bench / perft are synchronous in the UCI loop | fresh process per line | **OK** |
| `job1/f1_multipv_nodes.sh`, `f2_probe.sh`, `f3_root_draw.sh`, `f4_budget_bestmove.sh` | several .uci files, each its own process | fresh process per case | **OK** |
| `job1/runner.py`, `paced_runner.py` | one session per process | n/a (crash counting) | **OK** |
| `job2/f2_history_drift.py` | `Engine(exe)` per position for "cold"; one process for "warm" | fresh process for cold | **OK** — and the warm side is labelled warm by design, which is the whole point of S-F5 |
| `job2/f3_tt_vs_histories.py` | one process per VARIANT; the baseline variant is `ucinewgame` | `ucinewgame`, not Clear Hash | **OK** — Clear Hash was the SUSPECT, not the baseline |
| `job3/f1_board_checks.py` | perft only (synchronous) | n/a | **OK** |
| `job3/f3_halfmove_cap.py` | one process, several searches in sequence | uses refusal/`nodes 0` not node counts | **OK** — no node-count comparison |
| `job4/f1_options.py` | **ONE process for the Threads 1 vs 2 comparison** | — | **WRONG, corrected below** |
| `job5/f1_tt_lifecycle.py` | one process per try | n/a (crash counting) | **OK** |
| `job6/f1_eval_stability.py` | `eval` is synchronous; fresh vs after-search is the DELIBERATE contrast | fresh processes for the fresh phase | **OK** |
| `job7/f1_bound_sf8.py` | `run_once` = new `Engine` per cell | fresh process per cell | **OK** |
| `job7/f2_depth_ablation.py` | `cell()` = new `Engine` per cell | fresh process per cell | **OK** |
| `job7/f3_all20_mechanism.py` | `run()` = new `Popen` per call (read and verified) | fresh process per row | **OK** — I nearly "fixed" a bug that was not there; the correction note in the file now says so |

## The one real error, and its correction

`job4/f1_options.py` measured `Threads 1` then `Threads 2` in **one** process (the `measure()` helper reuses the
engine `e`). So the Threads 2 figure — 30,356 nodes — was a **warm** reading, not a cold one.

Re-measured with a fresh process each:

| | nodes at depth 10 | bestmove |
|---|---|---|
| Threads 1, fresh process | 13,102 | d2d4 |
| Threads 2, **warm** (the original job-4 row) | 30,356 | c2c4 |
| Threads 2, **fresh process** | **14,883** | c2c4 |

The conclusion in job 4 ("both configurations search; the move differs, which is normal for a parallel
search") survives; the *number* 30,356 does not and must not be quoted. `REPORT_job4.md` carries this
correction in place, in the row itself, labelled warm.

## What this does NOT change

- **S-F4 is corroborated, not weakened.** Seat 10's independent "Clear Hash gives a third value, 40,569" is
  exactly what S-F4 predicts: the table is cleared but the histories survive, so the state is neither cold nor
  fully warm. My repeat test (`job2/CHECK_s11F1.md`) compares three Clear-Hash searches against each other and
  against a patched build where `clear_hash()` calls `worker->clear()`; it is labelled "in ONE process" and its
  claim is that the patched build is bit-identical three times while the base drifts — which the rule makes
  *more* meaningful, not less.
- S-F5 was already a statement about warm state; nothing in it is re-labelled.
- All four honesty numbers are bench/perft, which are synchronous: unaffected, and re-verified with an immediate
  `quit` in `job1/HARNESS_AUDIT.md`.
