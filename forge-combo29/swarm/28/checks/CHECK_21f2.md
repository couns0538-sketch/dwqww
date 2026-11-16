# S-C4 — CONFIRMS 21-F2 (a refused FEN leaves the previous position and still answers readyok)

Checked by seat 28 (area 8) on my own Release build (`~/build/base-release/forge`, sha256
`e06310ec…16a83`, all four honesty numbers matched). Seat 21's files were not read by my harness; the
claim was restated from its FINDINGS line alone.

## The claim
21-F2 (seat 21, area 1): "A refused `position fen` silently leaves the PREVIOUS position on the board
and still answers `readyok`; a GUI that trusts readyok then searches and plays a move in the wrong game.
Every refusal kind shows it (bad castling rights, 3 fields, pure garbage); 8902 after startpos in all
four cases."

## Verdict: **CONFIRMS**, with a control that proves the harness can see a board change
`check_21f2.py`, pasted (`check_21f2_out.md`):

```
python-chess perft 3 of the CONTROL FEN (r1bqk2r/p1ppbppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8) = 55117
startpos perft 3 = 8902 (the brief's known number)

| case | refusal lines seen | readyok after refusal | perft 3 result | board searched | bestmove on stale board | that bestmove legal in startpos |
|---|---|---|---|---|---|---|
| bad castling right | 2: info string invalid FEN: castling right without king and roo / ... | yes | 8902 | startpos (STALE) | e2e4 | True |
| three fields | 2: info string invalid FEN: FEN must contain six fields / ... | yes | 8902 | startpos (STALE) | e2e4 | True |
| pure garbage | 2: info string invalid FEN: FEN must contain six fields / ... | yes | 8902 | startpos (STALE) | e2e4 | True |
| CONTROL: legal FEN after a refusal | - | yes | 55117 | the control FEN (GOOD) | - | - |
```

- **P1 SURVIVES**: after startpos, a refused FEN, and `go perft 3`, the engine answers 8,902 — startpos.
  Reproduced for three different refusal classes.
- **P2 SURVIVES**: the refusal does emit `info string invalid FEN: ...`, twice per command here (once
  per `position` and once per the `isready` that follows it), so there IS a signal on stdout. This is
  the one place I disagree with the word "silently" in the finding: the refusal is *reported*, it is
  just not reported in a form the UCI protocol requires a GUI to check before trusting `readyok`.
- **P3/P5 SURVIVE**: the engine answers a real `bestmove` (`e2e4`) on the stale position, and that move
  is legal in startpos — so a GUI that trusts `readyok` plays a legal move in the wrong game.
- **P6 (CONTROL) SURVIVES**: a LEGAL FEN sent right after a refused one gives that FEN's own perft 3,
  55,117, computed independently by python-chess. The harness can therefore see the board change, so the
  8,902 results are not a harness blind spot.
- **P7**: `d` produces no board diagram (0 diagram lines) — the engine has no display command, so a user
  cannot see the stale board from the protocol.

## Beyond the finding
1. **The refusal is emitted twice per attempt** (2 identical `info string invalid FEN` lines): the
   `position` command prints one and the following `isready` prints another. A GUI that counts error
   lines for one failed position therefore sees double.
2. **Bad castling rights and "three fields" and "pure garbage" all reduce to the same stale-board
   outcome** with perft 3 = 8,902, which is what makes this dangerous: the failure mode is uniform, so a
   GUI author cannot key off the message text to decide whether the board moved.

## Two harness bugs of mine found while doing this check, both recorded
This check initially hung twice, for 100 s and 150 s, and produced nothing. Both causes are the same
class as seat 19's warning (a parser waiting for something the engine never prints):
- `go perft 3` prints `nodes <n>`, not `Nodes searched`, and `nodes` also appears inside option lines —
  fixed by waiting for a line whose FIRST word is `nodes`.
- `ucinewgame` prints NO `readyok`; my step list asked to wait for `readyok` after `ucinewgame` and
  blocked until the timeout. Fixed by appending `isready` after every non-search step, and by making a
  missing token a hard `SystemExit` instead of a silent `<NO token>` marker.
No number in this check comes from the broken versions.

## How to see it again
```
cd forge-combo29/swarm/28/checks
python3 check_21f2.py ~/build/base-release/forge /tmp/c21f2.tsv
```
Raw: `check_21f2_out.tsv`, `check_21f2_out.md`.

## What I did NOT do
- Did not test whether the refusal line appears when `isready` is NOT sent after `position`.
- Did not test a refused `position startpos moves ...` (job 3 of area 1 covers illegal moves).
- Not under a sanitizer.

## What I am NOT sure about
- Whether a GUI is *required* by any convention to check `info string invalid FEN` before acting on
  `readyok`. My reading is that it is not, which is why the finding matters, but that is a protocol
  judgement rather than a measurement.
