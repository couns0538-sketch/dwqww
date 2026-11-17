# S-F8's practical impact measured: a pinned-move verifier gets the MOVE back but the SCORE wrong in 25 of 25

Build: **PC r15** `068f0927`, **PC20 (22 options asserted per cell)**, Threads 1, Hash 16, OwnBook false,
`go depth 10`, fresh process per cell. 25 legal self-play positions (`tests_r3fu_12`), all validated with
python-chess before use.

## Why this needed measuring

S-F8 and S-P6 established that **a `searchmoves` restriction that excludes nothing still changes the reported
score** (startpos with all 20 legal moves named: cp 29 vs 25). That is a real defect, and it has been OPEN for
the whole run.

**But the severity depends on a question neither finding asked:** a training pipeline that re-searches with the
intended move named gets back two things — a **score** and a **bestmove**. If only the score moves, the damage
is confined to score targets. **If the move moves, the label itself is wrong** and a corpus built that way is
corrupted. Different severities; nobody had distinguished them.

So I measured three arms per position:

| arm | command |
|---|---|
| **A** | `go depth 10` — unrestricted |
| **B** | `go depth 10 searchmoves <all legal moves>` — a restriction that excludes nothing |
| **C** | `go depth 10 searchmoves <A's bestmove>` — **what a verifier actually does** |

**Arm C is the one that matters and neither S-F8 nor S-P6 measured it.** A pipeline pinning one move is not
making the same comparison as a pipeline naming all twenty.

## The result

```
arm B — all legal moves named
    same bestmove  19/25      <- the MOVE changes in 6 of 25
    same score      2/25      <- the SCORE changes in 23 of 25

arm C — only the unrestricted bestmove named
    same bestmove  25/25      <- trivially: it is the only option
    same score      0/25      <- THE SCORE CHANGES IN EVERY SINGLE POSITION
```

**A vs C score delta: mean +1.08, range −32 to +31, and |delta| ≥ 10 cp in 14 of 25 positions.**

## What this means, arm by arm

### Arm C is the damaging one, and it is worse than S-F8 said

**A verifier that pins the move always gets that move back — the answer is guaranteed by construction, not
earned.** That is the trap: the pipeline believes it has confirmed the move, when the restriction has removed
every alternative. And the score it records is **different from the unrestricted score in 25 of 25 positions**,
by ≥10 cp in 14 of them.

So a corpus built by "pin the move, record the score" has:
- **the move guaranteed correct** (trivially, and worth nothing as verification),
- **the score wrong in every position tested**, sometimes by 30 cp.

**That is the concrete training-data harm S-F8 implied and never quantified.** It should stop being described
as "the score is 7 cp off" (startpos, one position) and start being described as **the score is wrong in every
position, and the move check is vacuous.**

### Arm B changes the MOVE too — 6 of 25

This is new and it is worse than a score defect. Naming all legal moves changes the reported bestmove in
**6 of 25** positions:

```
A d2e1   vs  B d4c5    (cp -40  /  cp -49)
A d4d5   vs  B e2e4    (cp  61  /  cp  64)
A f3f4   vs  B f1d3    (cp  89  /  cp  89)   <- same score, DIFFERENT MOVE
A e2g3   vs  B c1e3    (cp  52  /  cp  51)
A e8g8   vs  B h5h4    (cp -73  /  cp -73)   <- same score, DIFFERENT MOVE
A h3h4   vs  B f1g2    (cp  48  /  cp  80)
```

**Two of those are score-tied and still choose a different move**, which means the restriction is not merely
perturbing evaluation — it is changing the tie-break/search order enough to reorder equal-scoring moves. So an
"all moves named" restriction cannot be used as a no-op control, which is exactly how several harnesses in this
run have used it.

## The recommendations

1. **Never use `searchmoves` naming all legal moves as a no-op control.** It is not a no-op: it changed the
   move in 6 of 25 and the score in 23 of 25.
2. **Never use `searchmoves <one move>` to verify a move.** The check is vacuous by construction — the
   restriction guarantees the answer — and the score it returns is not the score the engine would report.
3. **If a score must be recorded for a specific move, record the unrestricted score of the position and note
   the move separately.** The two are not interchangeable and the difference reached 32 cp here.
4. **Label the limit honestly: 25 positions, depth 10, one build.** The direction is unambiguous and the
   mechanism is explained by IIR and TT-store suppression at a restricted root (S-F8a/S-C4), but the exact
   rates at depth 12+ and on other builds are not established here.

## Controls

- **Every FEN verified legal with python-chess before use** — a refused FEN silently plays startpos in some
  engines, which would have turned 25 positions into one repeated position.
- **Option count asserted per cell** (`n_applied == 22`), so no row carries a wrong settings label.
- **Arm B's move list is counted, not assumed** (`len(legal)` recorded per position).
- **Sensitivity control**: if no score differed anywhere, the harness would be blind — one differs, so PASS.
  This is the check that makes a null result meaningful here, and there is no null result anyway.

## Files

- `pc/check_sf8_impact.py` — the three-arm harness, with the four controls above.
- `out19c46/sf8_impact_25x10.json` — every cell, with the chosen move, score, nodes and settings count.

---

# Boundary added after the fact: pinning distorts absolute scores but preserves RANK ORDER

The four recommendations above are about **absolute** scores. A cross-seat result depends on a weaker property,
and it holds.

Seat 25's S-C50 compares two candidate moves by scoring **both** with `searchmoves` pinned at depth 20, then asks
which setting's preferred move scores higher. That uses pinned scores in a **relative** comparison. So the
question is not "is a pinned score equal to a free score" (it is not, S-C72: 25 of 25 differ) but **"does pinning
preserve the order between two candidates"**.

Measured, 8 positions, PC20, depth 10, both candidates pinned the same way:

```
fen                                    A bestmove/score   pinned1  pinned2   pin rank == free rank?
r2qkbnr/ppp1pppp/3pb3/8/1n...          c7c5 / 44          40       -34      yes
r2qkbnr/pp2pppp/3pb3/2p5/1...          c2c3 / -36         -44      -153     yes
r2qkbnr/pp2pppp/3pb3/2p5/1...          b4c6 / 30          33       -127     yes
r2qkbnr/pp2pppp/2npb3/2p5/...          d2e1 / -40         -41      -58      yes
r2qkbnr/pp2pppp/2npb3/2p5/...          c5d4 / 51          47       -215     yes
r2qkbnr/pp2pppp/2np4/2p2b2...          d4d5 / 61          78       -132     yes
r2qkbnr/pp2pppp/2np4/2p2b2...          f5d7 / -39         -65      -306     yes
r2qkbnr/pp1bpppp/2np4/2p5/...          d4d5 / 49          60       -108     yes

rank order agrees: 8 of 8
```

**The absolute distortion is large and real** — 44 → 40, 61 → 78, −39 → −65 — **and the ordering is unchanged.**
Because a comparison of two pinned candidates applies the same distortion to both, it cancels.

**So the boundary on S-C72 is:**

| use of a pinned score | verdict |
|---|---|
| recording an **absolute** score for a position | **unusable** — wrong in 25 of 25, up to 32 cp (S-C72) |
| verifying that a **move** is best | **vacuous** — the restriction makes it the only option (S-C72) |
| comparing **two candidates both pinned the same way** | **usable** — rank order preserved 8 of 8 (S-C76) |

Seat 25's S-C50 is in the third row and its conclusion stands. Anyone using the first two rows should stop.
