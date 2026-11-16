# Missing-parse audit — every checker I wrote tonight (seat 05, area 5)

Asked for by the owner after my `job1/mate_check.py` false-verdict path was reported:

> for each one, does a missing parse produce a verdict, and is that verdict a pass or a fail? A check that fails
> closed on a missing parse is fine; one that fails toward a verdict is not. Record the answer as a table, one row
> per script. Make sure the negative control for that path is committed.

## How it was measured (the committed control)

`audit_failclosed/stub_no_score.sh` is a fake engine: it answers `uci`/`id`/`isready`/`bestmove 0000` correctly but
**never prints an `info ... pv ... score` line**, so any parser looking for a score finds nothing.
`audit_failclosed/failclosed_probe.py` runs **every** verdict-producing script against that stub and records the
exit code, the verdict words it printed, and which way the verdict went. Raw output per script:
`audit_failclosed/raw/<script>.stub.txt`; the table below is `audit_failclosed/raw/probe_table.txt`.

Two scripts judge *my own python checkers* rather than an engine, so the engine stub cannot reach them.
`audit_failclosed/probe_selftests.py` is their correct instrument: it puts a stub `dtm2.py` / `dtm.py` that prints
nothing earlier on the path and re-runs them. Output: `audit_failclosed/raw/probe_selftests.txt`.

## The table

| script | drives an engine? | missing parse → what happens | direction | verdict |
|---|---|---|---|---|
| `job1/mate_check.py` | yes | `NO_VERDICT`, counted unknown, no mismatch | **fails closed** | **was broken, fixed** |
| `audit19f12/honesty_safe.py` | yes | `NO_PARSE — not measured` per line, `INCONCLUSIVE` | **fails closed** | **was mislabelled, fixed** |
| `audit19f12/parser_audit.py` | yes | `FAIL-LOUD`, exit 1 | **fails closed** | safe as written |
| `audit_seat10/audit_10_clearhash.py` | yes | `FAIL-LOUD`, `INCONCLUSIVE`, exit 1 | **fails closed** | **was broken, fixed** |
| `check_15f3/check_15f3.py` | yes | `FAIL-LOUD`, exit 1 | **fails closed** | safe as written |
| `check_15f3/deadmaterial_scope.py` | yes | `FAIL-LOUD`, exit 1 | **fails closed** | safe as written |
| `check_15f3/knn_same_material.py` | yes | `FAIL-LOUD`, exit 1 | **fails closed** | safe as written |
| `check_15f4/check_15f4.py` | yes | `FAIL-LOUD`, `INCONCLUSIVE`, exit 1 | **fails closed** | **was broken, fixed** |
| `job1/crosscheck_mates.py` | yes | `NO_VERDICT` per case, `INCONCLUSIVE`, exit 3 | **fails closed** | **was broken (printed AGREE from nothing), fixed** |
| `job1/dtm2_selftest.py` | no (judges `dtm2.py`) | `NO_VERDICT` per case, `SELFTEST INCONCLUSIVE` | **fails closed** | **was broken, fixed** |
| `job1/dtm_selftest.py` | no (judges `dtm.py`) | `NO_VERDICT` per case | **fails closed** | **was broken, fixed** |
| `job1/build_mate_table.py` | no (reads committed files) | n/a — no engine input exists to be missing | n/a | not exposed |
| `job1/control_illegal_pv.py` | no (python-chess only) | n/a — it tests my replay logic, not the engine | n/a | not exposed |

Engine-driving scripts: **9 of 9 fail closed.** Seven scripts in this folder were repaired tonight; four were
already safe as written; the two that never touch engine output are not exposed (they are listed with `n/a`).

## The repairs, before and after (seven scripts)

| script | before (observed on the no-parse run) | after |
|---|---|---|
| `crosscheck_mates.py` | a missing verdict became `"(none)"`, `dv=None`, and printed **`AGREE`** whenever the brute force also had no answer — **a pass from two absences** | `NO_VERDICT` per case, `SUMMARY agree=0 disagree=0 no_verdict=N`, `INCONCLUSIVE`, exit 3 |
| `mate_check.py` | a missing `dtm2` verdict fell through to `MISMATCH` — an **invented REFUTES** | `NO_VERDICT`, `SUMMARY ok=0 mismatch=0 unknown=1`, `RESULT: INCONCLUSIVE` |
| `audit_10_clearhash.py` | `[None, None, None]` printed `RESULT: does NOT reproduce this shape` — an **invented REFUTES** | `FAIL-LOUD: 3 of 6 searches produced NO parseable node count`, `INCONCLUSIVE`, exit 1 |
| `check_15f4.py` | printed `RESULT: does NOT confirm on my positions` — an **invented REFUTES** | `FAIL-LOUD: no info/pv line was observed in any of the 24 searches`, `INCONCLUSIVE`, exit 1 |
| `dtm_selftest.py` | printed 4 × `MISMATCH` from absent verdicts — **invented refutations** | `NO_VERDICT` per case, `MISMATCH count=0` |
| `dtm2_selftest.py` | printed `SELFTEST PASS` from 10 absent verdicts — **an invented PASS** (the worst direction) | `NO_VERDICT` per case, `SELFTEST INCONCLUSIVE — 10 of 10 cases produced no parse` |
| `honesty_safe.py` | printed `MISMATCH` for a missing number, which reads as a failed engine | `NO_PARSE — not measured`, `HONESTY RECHECK INCONCLUSIVE` |

Note the two opposite failure modes, both fatal to a check's value: four of my scripts would have manufactured a
**refutation**, and one (`dtm2_selftest`) would have manufactured a **pass**. The pass is the worse of the two
because nobody re-examines a green result.

## The repairs did not change any published number

Every repaired script was re-run on real input afterwards:

| script | real-input result after the repair | same as published? |
|---|---|---|
| `audit19f12/honesty_safe.py` | `HONESTY RECHECK PASS 4/4` (312866 / 862329 / 3024920 / 4865609) | yes |
| `check_15f4/check_15f4.py` | `RESULT: CONFIRMS …` | yes |
| `job1/dtm2_selftest.py` | `SELFTEST PASS` (10/10) | yes |
| `job1/mate_check.py` | `SUMMARY ok=4 mismatch=6 unknown=0` | yes |
| `audit_seat10/audit_10_clearhash.py` | `RESULT: CONFIRMS seat 10's shape` (56,720/4,951/4,516 vs 56,720×3) | yes |
| `dtm_selftest.py` | superseded by `dtm2_selftest.py`; still safe on the stub | n/a |

## Reproduce the whole audit

```
cd audit_failclosed
python3 failclosed_probe.py      # every engine-driving script against the no-score stub
python3 probe_selftests.py       # the two selftests against a stub dtm2.py / dtm.py that prints nothing
```

Both print, at the end, an explicit line stating whether any script produced a passing verdict from a no-parse run.
After the repairs that line reads `No script produced a passing verdict from a no-parse run.`

## Honest limits of this audit
- The stub prints `bestmove 0000` but no score. That catches "score absent"; it does not catch a checker that
  mis-reads a *malformed but present* score (e.g. `score cp` with no number). I did not build a malformed-score stub.
- (Fixed — see the exit-code table below. The limitation that used to be here no longer applies.)
- These repairs change only *failure handling*. No measurement logic was touched, which is why every published
  number reproduced exactly.


## Exit codes — what each repaired script now returns

A printed `INCONCLUSIVE` line protects a human reader but not a caller that chains scripts: exit 0 is success to any
`&&`, `set -e` or job runner. So on a no-parse run the code is **3**, deliberately distinct from both 0 (measured and
agreed) and 1 (measured and disagreed). All five scripts that had an incorrect exit status are verified in **both**
directions by `audit_failclosed/exit_codes.sh`;
raw output `audit_failclosed/raw/exit_codes.txt`.

| script | 0 | 1 | 3 | verified no-parse / real |
|---|---|---|---|---|
| `audit19f12/honesty_safe.py` | all four node counts parsed and equal | a parsed count differs from the expected value | no node count parseable | **3 / 0** |
| `job1/mate_check.py` | rows compared, none mismatched | a row mismatched | no row produced a parsed comparison | **3 / 1** |
| `job1/crosscheck_mates.py` | all cases compared and agreed | a case disagreed | no case produced a parsed comparison | **3 / 0** |
| `job1/dtm2_selftest.py` | every case parsed and agreed | a parsed verdict disagrees with brute force | a case produced no verdict line | **3 / 0** |
| `job1/dtm_selftest.py` | every case parsed and agreed | a parsed verdict disagrees | no verdict line | **3 / 1** |

**Correction to what this file said a moment ago.** I first wrote that only three scripts needed the exit code and
that `mate_check.py` and `crosscheck_mates.py` "already end in `sys.exit(1)`". That was wrong — I asserted it from
memory instead of grepping, and both in fact had **no exit call at all** and returned 0 on a no-parse run. Worse,
`crosscheck_mates.py` had a distinct variant of the same defect: a missing verdict became `"(none)"`, `dv` became
`None`, and when the brute force also had no answer it printed **`AGREE`** — a pass manufactured from two absences.
Both are now fixed and both are in the table above. That is the second time tonight my own claim about my own script
was wrong until I tested it, which is the point of the probe being a committed script rather than a review.

`dtm_selftest.py` returns 3 against the real tree today for an honest reason: `dtm.py` was superseded by `dtm2.py`
and no longer exists, so the script has nothing to measure. That is the correct answer, not a failure — previously it
would have printed a wall of `MISMATCH` lines against a missing file and looked like a refutation.

`parser_audit.py`, `audit_10_clearhash.py`, `check_15f3/*.py` and `check_15f4.py` already ended in `sys.exit(1)`
after their `FAIL-LOUD` line; they are unchanged.

## The common cause: every one of them judged in the ABSENCE of a value

These were not separate slips. They are one defect with a name, and the name matters because it tells you where
to look next. **Every one of them evaluated a condition over an empty set of observations and read the result of
that empty evaluation as evidence.** The logic is always the same shape:

- `all(observed == wanted for observed in [])` is `True` → "every position behaved" from zero positions.
- `next(..., sentinel)` returning the sentinel → the comparison then runs against the sentinel, not against data.
- a counter that was never incremented → "0 anomalies" is indistinguishable from "0 measurements".

The instances, in both directions:

| instance | the empty thing | what it was read as |
|---|---|---|
| `job1/dtm2_selftest.py` | 10 absent verdict lines | **PASS** — `all()` over nothing is true |
| `job1/mate_check.py` | `next(..., "(no verdict)")` | **REFUTES** — the sentinel was compared as if it were a measurement |
| `audit_seat10/audit_10_clearhash.py` | `[None, None, None]` | **REFUTES** — `None` compared as a number |
| `check_15f4/check_15f4.py` | 0 observed pv lines out of 24 searches | **REFUTES** — `all()` over nothing, then read as "the claim failed" |
| `job1/dtm_selftest.py` | 4 absent verdict lines | **REFUTES** ×4 — same sentinel comparison |
| `job1/crosscheck_mates.py` | a sentinel `"(none)"` on one side and `None` on the other | **PASS** (`AGREE`) — two absences matching each other |

This is the same **vacuity trap** the swarm hit four separate times tonight, and the reader should see that it is a
pattern rather than a coincidence:

1. **Seat 19** (the original report): a check searched for a `clock_plan` line the engine never prints, got no
   number, compared NaN, and printed `CONFIRMS` — a confirmation from nothing.
2. **Seat 10, finding 10-F2**: deepseek6 long56's "illegal bestmoves 0" was vacuous because its legality guard was
   gated on a `pos_line` the engine never emits — a fake engine answering `bestmove a1a8` still scored "illegal 0".
3. **Seat 16, finding S-F7**: while auditing, that seat reproduced the vacuity bug in **three** independent forms
   (wrong executable handed to a check, setup output discarded so the refusal line was never seen, field parsing
   hitting `seldepth` instead of `nodes`) — each caught only after the parser was made to raise on a missing value.
4. **Seat 05 (mine, this audit)**: five checkers in the dangerous direction — three manufacturing a refutation
   (`mate_check`, `audit_10_clearhash`, `check_15f4`) and two a pass (`dtm2_selftest`, `crosscheck_mates`) — plus
   `dtm_selftest` doing the same in miniature, and `honesty_safe` mislabelling an absence as a mismatch. Every one of
   them judged in the absence of a value.

The lesson that generalises, and the reason the negative control is now committed rather than described: **the
failure was never in the comparison, it was in the parser being silent.** A parser that returns a sentinel, a `None`,
an empty list or a `0` instead of raising has already decided the outcome — the comparison downstream is decoration.
All of them are fixed by making the absence explicit and fatal (distinct text, exit 3), and the same stub that caught them
stays in `audit_failclosed/` so a seventh cannot slip in unnoticed.
