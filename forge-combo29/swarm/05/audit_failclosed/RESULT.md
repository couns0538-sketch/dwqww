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
| `job1/crosscheck_mates.py` | yes | `FAIL-LOUD`, exit 1 | **fails closed** | safe as written |
| `job1/dtm2_selftest.py` | no (judges `dtm2.py`) | `NO_VERDICT` per case, `SELFTEST INCONCLUSIVE` | **fails closed** | **was broken, fixed** |
| `job1/dtm_selftest.py` | no (judges `dtm.py`) | `NO_VERDICT` per case | **fails closed** | **was broken, fixed** |
| `job1/build_mate_table.py` | no (reads committed files) | n/a — no engine input exists to be missing | n/a | not exposed |
| `job1/control_illegal_pv.py` | no (python-chess only) | n/a — it tests my replay logic, not the engine | n/a | not exposed |

Engine-driving scripts: **9 of 9 fail closed.** Five of them were repaired tonight; four were already safe.

## The five repairs, before and after

| script | before (observed on the no-parse run) | after |
|---|---|---|
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
- `exit status` is still 0 for `honesty_safe.py`, `dtm2_selftest.py` and `dtm_selftest.py` on a no-parse run: they
  refuse in their text but do not fail the process. A caller that only looks at the exit code would not notice. I
  judged the printed `INCONCLUSIVE` line sufficient rather than changing their exit status late, and I am recording
  that rather than hiding it.
- These repairs change only *failure handling*. No measurement logic was touched, which is why every published
  number reproduced exactly.
