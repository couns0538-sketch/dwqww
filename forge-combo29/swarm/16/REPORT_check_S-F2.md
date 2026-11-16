# REPORT_check_S-F2 — CONFIRMS seat 06's S-F2 (area 6), seat 16

**What was asked:** check another seat's NEW finding, reproduced from its command file alone with a harness I
wrote myself: seat 06's S-F2, "a FEN whose ep square is unreachable is REFUSED with
`info string invalid FEN: inconsistent en-passant square` (board.cpp:325-333 ...)".

**The answer:** CONFIRMED. Of 15 ep-square FENs, 9 are refused and 6 accepted; the FEN in the finding is
refused with exactly `info string invalid FEN: inconsistent en-passant square`; no crash, no hang, no
sanitizer line; every accepted FEN's `go perft 1` equals python-chess's legal move count. The answer lines
are of two kinds: `inconsistent en-passant square` (board/pawn not where the ep field claims) and
`invalid en-passant square` (field not on rank 3/6, or not lowercase). Reading `board.cpp` confirms the code
location; the finding's line range is right but its cited condition list is INCOMPLETE — the check at
`board.cpp:319` (rank must be 3 or 6, lowercase) is the one that produces the *other* message, and the
finding does not mention it.

**How sure:** high — 15 fresh processes, the finding's exact FEN reproduced, and the code read at the exact
lines. The one thing my run adds beyond the finding: a refused FEN keeps the PREVIOUS position
(`go perft 1` = 5 then 5 after a refused `position fen`), which the finding does not state.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-release/forge
sha256  e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
bench 11 312866  bench 13 862329  bench 16 3024920  go perft 5 4865609   (all equal; see ../HONESTY.txt)
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| the finding's exact FEN, own harness | done | `raw/startpos_e6_w.txt`, `raw/results.json` | refused, `info string invalid FEN: inconsistent en-passant square` |
| 15 ep-square variants | done | `raw/results.json`, `raw/*.txt`, `check_ep.py` | 9 refused / 6 accepted, 0 crashes, 0 hangs |
| accepted FENs vs python-chess perft 1 | done | `raw/results.json` (`accepted_perft_mismatch 0`) | all 6 equal |
| control: same startpos board with `-` ep | done | `raw/ctrl_no_ep.txt` | accepted, perft 1 = 20 = python-chess |
| code location read | done | `board.cpp:317-333` via `Read` | conditions match; message at 319/320 is a SECOND message the finding omits |
| state after a refused FEN | done | `raw/state_results.json`, `state_after_refusal.py` | previous position KEPT (5 then 5), accepted FEN replaces it (5 then 20) |
| sanitizer run | NOT done (not asked; release build) | — | "0 sanitizer lines" here means nothing |

## The measurements

```
cases 15  refused 9  accepted 6  accepted_perft_mismatch 0  hangs 0  sanitizer_lines 0
REFUSED  startpos_e6_w  -> info string invalid FEN: inconsistent en-passant square
REFUSED  startpos_e3_w  -> info string invalid FEN: inconsistent en-passant square
REFUSED  startpos_e6_b  -> info string invalid FEN: inconsistent en-passant square
REFUSED  startpos_e3_b  -> info string invalid FEN: inconsistent en-passant square
REFUSED  no_pushed_pawn -> info string invalid FEN: inconsistent en-passant square
REFUSED  file_a_empty   -> info string invalid FEN: inconsistent en-passant square
REFUSED  rank1          -> info string invalid FEN: invalid en-passant square
REFUSED  rank8          -> info string invalid FEN: invalid en-passant square
REFUSED  uppercase      -> info string invalid FEN: invalid en-passant square
```

Accepted and equal to python-chess perft 1: `legal_e3` (20), `legal_d6` (31), `no_capturer` (30),
`no_ep_square` (26), `legal_ep_capture` (27), `ctrl_no_ep` (20). Note `no_capturer` (a legal ep square with
no white pawn able to capture) is ACCEPTED — so the refusal is about the *pawn that just moved*, not about
whether a capture exists.

## Findings

`S-C1 | CONFIRMS S-F2 | check_S-F2/raw/results.json + check_S-F2/check_ep.py | the finding's FEN is refused
with `info string invalid FEN: inconsistent en-passant square`; 9 of 15 ep FENs refused, all accepted ones
match python-chess perft 1; and the finding's code citation is incomplete — `board.cpp:319` produces a second
message `invalid en-passant square` that the finding does not mention.`

## Suspicions, not proven

- Whether an ep-square FEN that is accepted but whose ep capture would be illegal (pinned pawn) is handled
  right: I did not construct that case with a king exposed on the ep file. `no_capturer` is close but has no
  pin. A follow-up set is needed.

## What I did NOT do

- No sanitizer build, so nothing here says anything about memory safety of the refusal path.
- Did not read seat 06's `out_special.txt`; I used only its command line, as the rules require.
- Did not test ep FENs through `position startpos moves` (an ep square arising from a move list).

## What I am NOT sure about

- Whether the second message (`invalid en-passant square`, rank-1/8 and uppercase) should count as part of
  S-F2 or as a new finding. I report it as a correction to the finding's code citation, not as a new finding,
  because the behaviour "an ep field that cannot be real is refused" is the same behaviour.
- Whether the finding intended "unreachable" to include the missing-capturer case, which the engine accepts.

## Times

`stamps.txt` — every line is a `date -u`.

## Last command output

```
$ git status --short
 M check_S-F2/stamps.txt
?? REPORT_check_S-F2.md
?? check_S-F2/check_ep.py
?? check_S-F2/last_cmd.txt
?? check_S-F2/raw/
?? check_S-F2/state_after_refusal.py
$ ls
check_S-F2
FINDINGS.md
honesty.sh
HONESTY.txt
job0_honesty
job1
REPORT_check_S-F2.md
REPORT_job1.md
SEAT.txt
STATUS.md
$ ls check_S-F2
check_ep.py
last_cmd.txt
prediction.txt
raw
stamps.txt
state_after_refusal.py
$ ls check_S-F2/raw
ctrl_no_ep.txt
file_a_empty.txt
legal_d6.txt
legal_e3.txt
legal_ep_capture.txt
no_capturer.txt
no_ep_square.txt
no_pushed_pawn.txt
rank1.txt
rank8.txt
results.json
sentinel_then_bad_ep.txt
sentinel_then_good_ep.txt
startpos_e3_b.txt
startpos_e3_w.txt
startpos_e6_b.txt
startpos_e6_w.txt
startpos_then_bad_ep.txt
startpos_then_good_ep.txt
state_results.json
uppercase.txt
```

