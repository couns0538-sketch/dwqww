# CHECK of seat 08's 08-F22 — the fifty-move defect has a score BAND and a single NODE SPIKE

**Verdict: CONFIRMS 08-F22, every number to the node.**

Harness: `check_08f22.py`, my own (not a copy of the finder's script). PC r15 build, **PC20**,
**Threads 1**, Hash 16, `go depth 10`, every halfmove counter from 85 to 99 in its own fresh process,
on their board `1K6/8/8/3R4/8/8/8/k7 w - - H 1` (won K+R vs K). Raw: `check_08f22_pc.txt`.

## Results, pasted in full

```
H      score       nodes       depths_reached
85     mate 8      35652       10
86     cp 294      87480       10
87     cp 342      67952       10
88     cp 271      178232      10
89     cp 279      306279      10
90     cp 231      930573      10
91     cp 0        7251835     10
92     cp 0        1459778     10
93     cp 0        1004522     10
94     cp 0        108603      10
95     cp 0        81364       10
96     cp 0        9329        10
97     cp 0        4729        10
98     cp 0        541         10
99     cp 0        200         10

counters scoring exactly cp 0: [91, 92, 93, 94, 95, 96, 97, 98, 99]
of those, at H>=91 (the claimed BAND): 9 counters [91, 92, 93, 94, 95, 96, 97, 98, 99]
largest node count: H=91 with 7251835 nodes; median of the other counters 87480; ratio 82.9x
=> shape: SCORE BAND + SINGLE NODE SPIKE at one counter
```

## Side by side with the finding

| quantity | seat 08 | mine | agree? |
|---|---|---|---|
| H=91 nodes | 7,251,835 | **7,251,835** | **exact** |
| median of other counters | 87,480 | **87,480** | **exact** |
| ratio | 82.9x | **82.9x** | **exact** |
| cp 0 band | H=91..99 | **H=91..99** (9 counters) | **exact** |
| H=0 cost for comparison | 14,470 | (not measured here) | not tested |
| shoulder at 92-93 | 1,459,778 / 1,004,522 | **1,459,778 / 1,004,522** | **exact** |
| H=94-98 cheaper than normal | yes | **yes** (108,603 down to 541) | **exact** |

Six of seven quantities match to the digit, including both shoulder values. The seventh (the H=0
baseline of 14,470) I did not measure in this run, so I do not confirm or dispute it.

## What the two shapes mean, in plain terms

- **The score defect is CHRONIC**: nine consecutive counter values all return exactly `cp 0` on a won
  K+R vs K position. This is not a one-off — for H=91 through 99 the engine believes the position is
  drawn and would steer for a "draw" while a rook up.
- **The node cost is a ONE-TIME CLIFF**: 7.25 M nodes at H=91 only, then decaying 1.46 M, 1.00 M, and
  below normal. Crossing the boundary costs one expensive search; the wrong verdict then persists
  cheaply.

That distinction is the useful part for the owner: a fix should be judged on the band (the wrong
verdict for nine counters), not on the node spike, which is a symptom of the crossing rather than a
recurring cost.

## Note on H=85

The row at H=85 reports `mate 8` where 86-90 report cp scores. That is outside the finding's claim
(H>=91) and I record it as an observation, not as evidence either way; a mate score at a lower counter
is not obviously wrong for a won K+R position.
