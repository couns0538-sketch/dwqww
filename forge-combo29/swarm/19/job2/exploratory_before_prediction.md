# job 2 — exploratory timings taken BEFORE the prediction (declared, not hidden)

The brief says a prediction is committed alone *before the first measuring command of a job*. On job 2 I ran
two exploratory timings first, while I was still hunting for a target. They are below so nothing is hidden;
the prediction file `prediction.txt` covers only the formal measurement, which had not been run when it was
committed.

Method for both: `bash job2/headroom.sh <tag> <edit-or-empty>` — copies the pristine source, builds it with
the same CMake release flags, feeds `bench 13` fifteen times to one process, and prints the per-run `time`
field the engine itself reports.

| tag | what | node count | median ms | min | max | mean |
|---|---|---|---|---|---|---|
| base | pristine 6b98f217 | 862329 | 431 | 423 | 449 | 432.1 |
| base2 | pristine 6b98f217, second build | 862329 | 431 | 423 | 449 | 432.1 |
| probe_material | `edit_material_key.py` — a `thread_local` memo of `material_key()` keyed on `board.key()` | 862329 | 430 | 423 | 447 | 431.1 |
| probe2 | the same edit, rebuilt | 862329 | 439 | 434 | 463 | 441.4 |

What that told me, and why the probe is **not** the patch:

- The two base builds agree to the millisecond (431/431), so this machine is quiet enough for a small effect
  to be visible at all.
- The memo probe came out **slower** on the rebuild (441 vs 432 ms) — the extra branch and key compare cost
  more than the loop they save, and the effect flips sign between builds. That is the 1.5 %-scale noise the
  brief warns about, and it is also evidence that `probe_material` is a bad patch.
- It is disqualified on correctness grounds as well: `board.key()` is not a sound identity for *material*
  (two different positions with the same material have different keys, which is harmless, but the memo is
  also process-global state that would have to be invalidated), and the edit moves work into `thread_local`
  storage. It is a probe, not a proposal, and it is not offered as one.

`edit_material_key.py` stays in the folder only as the record of that probe.

The counts below are what sent me to the real target. `bench 13` calls `corrected_eval` 691,753 times and
`material_key` 750,427 times (instrumented scratch build, `job2/counts.txt`).
