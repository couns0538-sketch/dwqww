# CHECK of seat 10's warm/cold measurement rule — seat 05 (area 5), plus an audit of my own results

## Verdict: CONFIRMS, with the exact numbers

Seat 10's rule: *two identical unrestricted searches in ONE process, nothing between them, give 56,720 then 4,951
then 4,516 nodes; three separate processes give 56,720 three times; `ucinewgame` restores cold exactly; `Clear Hash`
does not.*

My harness on startpos, `go depth 12`, Threads 1, Hash 16:

| measurement | my values | seat 10's |
|---|---|---|
| one process, 3 identical searches, nothing between | **56,720 / 4,951 / 4,516** | 56,720 / 4,951 / 4,516 |
| three separate processes | **56,720 / 56,720 / 56,720** | 56,720 three times |

Digit-for-digit agreement on both halves. Raw: `raw/audit_10.txt`.

## Audit of my own results against this rule

**(a) `Clear Hash`: never used.** `grep -rn "Clear Hash\|clear_hash\|clearhash"` over my whole folder returns
nothing, so no baseline of mine came from it.

**(b) Which of my node-count claims are cold, and which are warm?** This is the part that matters, so here it is
claim by claim:

| claim | how it was measured | cold? |
|---|---|---|
| job1 O = 9,500,069 and G = 18,466,239 node sums | **one fresh process per position**, `ucinewgame` + `isready` before every `go`, reading to `bestmove` | **COLD** |
| job1b R = 12,230,484, median 46,976 | same harness, same discipline, one process per position | **COLD** |
| job2 fifty-move node counts (341 at clock 99, 19,621 at clock 0, etc.) | `threshold_probe.py` / `options_test.py`: **one fresh process per (fen, depth, option) point** | **COLD** |
| job3 / job3b `nodes 0` at terminal roots | one fresh process per (position, go) | **COLD** |
| S-F7's "64 info lines" | line count, not a node comparison | n/a |
| **`mate_repeat.py` control runs (job1, job1b)** | **COLD section: fresh process each; WARM section: one process, repeated searches** | **BOTH, AND LABELLED** |

The one place I compared repeated searches inside one process is `mate_repeat.py`, and its output has always
printed a `--- COLD (fresh process each) ---` section and a `--- WARM (one process, repeated searches) ---` section,
with every line prefixed `cold N:` or `warm N:`. So those tables are labelled warm where they are warm, which is
exactly what the warning asks for, and I have not silently re-labelled anything.

Worth noting: my warm rows show precisely the effect seat 10 describes — `job1/out/repeat_306.txt` has
`cold 0/1/2 = 17,021` twice... correction: `17,021` three times cold, then `warm 0 = 17,021`, `warm 1 = 889`,
`warm 2 = 562`. The warm drop is the same phenomenon. **No claim of mine rests on those warm numbers**: they were
recorded as a determinism control, and the control's conclusion (the *score* is identical cold and warm) is
unaffected by node counts.

**(c) Where my conclusions could have been damaged by warmth, and were not:** the S-F1/S-F9 mate-score findings
compare scores ACROSS DEPTH in one process sometimes (`mate_depth_probe.py` reuses one process for the depth ladder).
That is warm, and I say so here: the depth ladder runs in a single process, so the node counts in those ladders are
warm and must not be read as costs. Their *scores* are what I cite, and the same score sequence was reproduced by
`mate_repeat.py`'s cold section where I ran it (306: `mate 5` cold and warm alike; 192: `mate -12` cold and warm
alike).

## Reproduce
```
python3 audit_10_clearhash.py /tmp/build-rel/forge
```

## What I did NOT establish
- I did not re-measure any of my cold tables; the table above shows they were already cold by construction (fresh
  process per position), so re-running them would cost hours and change nothing. If a reader disagrees that "fresh
  process per position" is cold, that is the point to challenge, not the numbers.
- I did not test `Clear Hash` myself (I never used it); seat 10's claim about it stands on their evidence, and I say
  so rather than borrowing it.
