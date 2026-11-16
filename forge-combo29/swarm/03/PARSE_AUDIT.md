# PARSE AUDIT — seat 03, after seat 19's measurement-integrity warning

Seat 19 reports a check that searched for a line the engine never prints, compared NaN, and printed "CONFIRMS"
without measuring anything. I re-audited every place in my folder where a value from engine output is parsed, and
added a checker that fails loudly: `assert_measured.py`.

## The rule I now apply

A result may only be recorded when (1) the line that carries the number was actually FOUND, (2) the number parsed
is an integer/number and not NaN/None/empty, and (3) the count of positions actually measured equals the count
expected. `assert_measured.py` enforces all three and exits non-zero otherwise.

## Every parse site in my folder

| file | what it parses | can a miss pass silently? | verdict |
|---|---|---|---|
| `job1/engine_perft.py` | the `nodes <N>` line of `go perft d` | no: loops until a `nodes ` line or raises `RuntimeError` on EOF; a missing value aborts the batch and is counted in `restarts` | sound |
| `job1/py_perft.py` | python-chess `perft()` return values | no: a pure function call, not parsed text | sound |
| `job1/compare.py` | the two JSON files | no: a missing value is counted as `MISSING` in its own counter and never as equal — the table shows `missing measurements: 0/314` explicitly | sound, and now also asserted by `assert_measured.py perft` |
| `job2/filter_special.py` | python-chess board API | no: no text parsing at all | sound |
| `job2/ep_common.py` | python-chess board API | no: no text parsing; has a known-answer self-test (`ep_common.py` prints `pass: True`) | sound |
| `job2/ep_construct.py` | python-chess board API | no: 0 constructed would print `constructed class-B positions: 0`; it printed 320 | sound |
| `job2/divide_sets.py` | `move: count` divide lines and the `nodes ` line | no: it reads until `nodes ` or raises; a move line only counts if it contains `:` | sound |
| `job2/ep_divide.py` (**old**) | divide lines | **it printed a summary from whatever it got** — no assertion on the node total | **replaced** by `ep_divide2.py`; both agree |
| `job2/ep_divide2.py` | divide lines and the `nodes ` total | no: reads until `nodes `, breaks on EOF, records the line in the output | sound |
| `honesty.sh` (**old**) | `grep -E "^Nodes searched|Nodes:"` — **the engine prints neither** | **yes**: the grep printed nothing and I read the numbers from a second, different grep. The pinned numbers in HONESTY.txt were correct, but that pattern was dead | **replaced** by `honesty2.py`, which matches the token it actually reads and prints MATCH/MISMATCH per pin |
| `check13/fake_engine.py` | n/a (a control) | n/a | control only |

Two real defects found by this audit, both mine, both cosmetic in their effect but real in their method:
1. `honesty.sh`'s `grep -E "^Nodes searched|Nodes:"` matches **nothing** in this engine's output. The numbers I
   published came from `grep -E "info string bench|^nodes"`, which does match. Re-proved with `honesty2.py`: all
   four pins MATCH.
2. `divide_sets.py`'s summary was printed to the terminal and never written to a file, so REPORT_job1.md and
   REPORT_job2.md quoted output that was not in the branch. Re-run with `> div_*_summary.txt`; the saved files say
   5000 of 5000 and 314 of 314, 0 missing, 0 extra.

## Evidence

```
$ python3 assert_measured.py perft job1/eng_R.json 4 5000
OK job1/eng_R.json: 5000 positions x depths 1..4 all integer; sums [113656, 2647591, 75639746, 2196757662]
$ python3 assert_measured.py perft job1/py_R.json 4 5000
OK job1/py_R.json: 5000 positions x depths 1..4 all integer; sums [113656, 2647591, 75639746, 2196757662]
$ python3 assert_measured.py perft job2/eng_special.json 4 314
OK job2/eng_special.json: 314 positions x depths 1..4 all integer; sums [8555, 266744, 8642784, 283188329]
$ python3 assert_measured.py perft job2/py_special.json 4 314
OK job2/py_special.json: 314 positions x depths 1..4 all integer; sums [8555, 266744, 8642784, 283188329]
$ python3 assert_measured.py perft check13/eng.json 4 5000
OK check13/eng.json: 5000 positions x depths 1..4 all integer; sums [113231, 2678512, 77182397, 2260227623]
$ python3 assert_measured.py divide job1/div_R_summary.txt 5000
OK job1/div_R_summary.txt: 5000 of 5000 positions reported, both counts present
$ python3 assert_measured.py divide job2/div_special_summary.txt 314
OK job2/div_special_summary.txt: 314 of 314 positions reported, both counts present
```

Negative controls (these MUST fail, and do):

```
$ printf 'positions checked: 0 of 0\n' > /tmp/bad1.txt; python3 assert_measured.py divide /tmp/bad1.txt 5000
FAIL /tmp/bad1.txt: checked 0 of 0, expected 5000    (exit 1)
$ echo '{"results": {"0": {"1": 0, "2": 0}}}' > /tmp/bad2.json; python3 assert_measured.py perft /tmp/bad2.json 2 5000
FAIL /tmp/bad2.json: 1 positions in file, expected 5000    (exit 1)
```

## What this changes in my recorded findings

Nothing in the results: every value behind S-F1, S-F2, S-F3 is a non-zero, python-chess-identical count at four
depths, and none of the three could be produced by a missing or NaN number (a NaN comparison is unequal, and my
comparison counts unequal as a difference). What changes is that the assertion now exists as a file that would have
caught the failure mode, and two defective helper files (`honesty.sh`'s grep pattern, `ep_divide.py`'s pipelining)
are replaced and marked as replaced rather than quietly fixed.
