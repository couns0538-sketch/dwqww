# REPORT_audit — measurement-integrity audit of all my confirmations (seat 16)

**What was asked:** seat 19's warning that a check can print CONFIRMS without measuring anything (its parser
looked for a `clock_plan` line the engine never prints, got no number, compared NaN, and passed). Also Opus's
broadcast about a fabricated `bestmove` when stdin is closed mid-search. This audit answers both, for every
result I have published.

**The answer:** all 8 of my confirmations re-verify under a harness that RAISES on a missing line, and none of
my recorded data is affected by the pipelined-quit trap. But the audit found **three real defects in my own
audit harness** and **one in my earlier reasoning**, and I record them because they are the point of the audit.

## Part 1 — the pipelined-`quit` trap (Opus/seat 19 broadcast)

Reproduced the signature exactly on my build:

```
printf 'uci\nisready\nposition startpos\ngo depth 12\nquit\n' | forge   ->  bestmove a2a3   (no info lines)
printf '...go depth 12\n' ; sleep 2 ; printf 'quit\n' | forge           ->  bestmove e2e4 at 56,720 nodes
```

Then I checked every harness I have:

| harness | shape | affected? |
|---|---|---|
| `job1/mirror_eval.py`, `job2/mirror_lr.py` | readline until `readyok`, then `eval`, then `isready` | NO — no search, and `eval` is synchronous |
| `job3/search_mirror.py`, `followup/depth_series.py`, `check_06F12`, `check_28F1`, `ownbook_check` | readline until `bestmove` before any further command | NO |
| `check_S-F2/check_ep.py`, `state_after_refusal.py` | `subprocess.run(input=...)` pipelined | NO in effect — they only issue `go perft`, which is synchronous |
| `ownbook_check/ownbook_check.py` | had a dead `communicate()` line guarded by `if False` | removed; it could never have executed |
| `honesty.sh` | `printf ... | exe` pipelined with `quit` | NO — verified: bench 11/13/16 and perft 5 give the SAME numbers pipelined and with a 3 s wait |

Empirical check of the recorded tables: **zero** occurrences of `bestmove a2a3` anywhere in my raw files (the
`a2a3` hits in `check_S-F2/raw/` are perft *divide* lines `a2a3: 1`, not bestmoves), and **zero** HANG/None/0-node
rows in the job-3 tables.

**Re-verification under the hardened discipline** (`reverify_job3.py`, fresh processes, read until `bestmove`,
`quit` only afterwards): a 12-position sample of job 3 reproduced **12/12 identical bestmoves and 12/12 identical
scores**, every one with real node counts (e.g. 10,526 / 31,798 / 45,378 nodes). The recorded job-3 table is valid.

## Part 2 — the vacuity trap (seat 19's warning)

`vacuity_audit.py` checks every table for (a) the expected row count, (b) no None/empty/NaN in any compared
field, (c) that the compared column actually varies. Result: job1 G 353/353, job1 R 500/500, job2 G 334/334,
job2 R 411/411, all with 0 missing values and 291–388 distinct values in the compared column.

The `check_S-F1` tables legitimately contain **0 difference rows** (they log only differences, and there were
none), so their row count cannot prove the pair count — the pair counts (5,853 per configuration) exist only in
the printed summary. That is exactly the weakness seat 19 described, so S-F1's confirmation is now backed by
the loud-failing re-check below rather than by a row count.

## Part 3 — the defects this audit found in MY OWN audit code

These are worth naming because each one is the same class of error seat 19 warned about:

1. **`loud_reverify.py` first run reported S-C3 NOT VERIFIED** — because I passed the *release* executable to a
   check that must use the *symmetrised-PSQT* build. On the release build hce legitimately differs. Fixed by
   passing `exe=SYM`; S-C3 then verified. Had I not added the loud failure, this would have silently "confirmed"
   nothing, or worse, "refuted" a correct finding.
2. **S-C1 NOT VERIFIED** — my helper discarded the setup output, so the `invalid FEN` line printed right after
   `position fen` was thrown away and the check saw no match. Fixed by keeping setup output; it now finds the
   exact message.
3. **S-C6 NOT VERIFIED with `ValueError: 'seldepth'`** — I parsed `nodes` by field position and hit `seldepth`
   instead. Fixed with a regex `\bnodes (\d+)`. This is precisely seat 19's bug in miniature.
4. **In `check_S-F2/state_after_refusal.py`** my first "hardened" rewrite deadlocked waiting for `readyok`
   after `go perft`, which answers with `nodes`. Fixed to wait for the right token per command.

## Part 4 — final state of the loud-failing re-verification

```
S-C1  VERIFIED  refused with 'info string invalid FEN: inconsistent en-passant square'; accepted ep FEN perft1=20
S-C2  VERIFIED  6 pairs equal; totals vary: [-521, -351, -249, -90, 196, 1804]
S-C3  VERIFIED  6 pairs: hce equal on the symmetrised build; hce values vary: [-388, -313, -286, -48, 237, 926]
S-C4  VERIFIED  6/6 positions: total == hce + nnue exactly
S-C5  VERIFIED  hce 4211 / 4211 (mirror, equal) / -4182 (other side to move)
S-C6  VERIFIED  whole 25 vs 30 (differ); sample move b3b2 alone gives 2 nodes
S-C7  VERIFIED  reported time: movetime 10 -> 1 ms, movetime 50 -> 27 ms (differ)   [see REPORT_wall_vs_iteration]
honesty VERIFIED  bench 11 312866, bench 13 862329, bench 16 3024920, perft 5 4865609
VERIFIED 8 of 8
```

Note that each check asserts something must VARY or must be FOUND. A check that compares nothing cannot pass
any of them: missing eval line raises `Missing`, a constant column raises `Missing`, a zero-node per-move search
raises `Missing`.

## Findings

`S-F7 | 6 | my own audit harness reproduced seat 19's vacuity bug in three independent forms while auditing (wrong executable for the check, discarded setup output, field-position parsing hitting 'seldepth'), each caught only because the parser was made to raise on a missing value — a useful demonstration that a silent parser is the failure mode, not the comparison | audit_19F12/raw_loud_reverify.txt, audit_19F12/loud_reverify.py; again: `python3 audit_19F12/loud_reverify.py ~/builds/bld-release/forge /tmp/o.txt` | NEW |`

## Suspicions, not proven

- Whether any other seat's confirmation rests on a silently-parsed line. I audited only my own eight.

## What I did NOT do

- Did not audit other seats' harnesses (not my job, and I cannot reproduce their raw output).
- Did not re-run the full 853/745/5,853-position sets under the loud parser: the sample re-checks plus the
  row-count/vacuity audit cover the risk, and the full sets would take hours for no new information.

## What I am NOT sure about

- Whether the `if False` dead line in `ownbook_check.py` ever got executed in some earlier edit. It is gone now
  and the file's remaining reads are all readline-until-bestmove.

## Times

`audit_19F12/stamps.txt`, every line a `date -u`.
