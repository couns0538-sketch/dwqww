> **WITHDRAWN IN PART (2026-11-16T23:05Z, see REPORT_job10.md / `job10/correction_check.txt`).**
> The sentence *"the base build scores the same two moves cp -1145 / cp -1174 and plays the better one"*
> is **wrong as a general claim**, and the framing of this as a PC-build regression is wrong too. It came from
> a settings mismatch of mine: the PC build was measured under PC20 and the base build under DEFAULT options.
> Under the PC's own S14 settings the **base tree makes the same wrong-move choice** (free choice c6c7,
> mate -20; c6d6 alone cp -1192; c6c7 alone mate -22), reproducing the other seat's numbers exactly. This is a
> **pre-existing defect in the shared search**, triggered by the S14/PC20 search settings.
> What survives: S-F16's core observation, because it was measured inside ONE build at ONE settings regime —
> the PC build plays a move it has itself scored as a forced loss. An independent python-chess play-out
> (`job10/playout_base_d12.txt`) confirms c6d6 is the better move: survives 22 plies versus c6c7's 20, 3 of 3.

# REPORT — seat 03, job 9: position 155 on the PC build itself — a LIVE finding, not an inference from ports

**What was asked.** Give position 155 the full treatment: both moves, both builds' scores at depths 16/18/20, and
ideally the ply where the cap's reduction fires and the line that is lost as a result. Plus: check whether 155 also
misbehaves on the PC BUILD under PC20, "since that is the binary the owner plays".

**The answer.** Yes — and it is worse than a preference difference. On the PC build itself, under PC20, at Threads 1,
Hash 16, the engine scores its own chosen move as a forced loss and plays it anyway:

| move | PC build under PC20, depth 20, `searchmoves` |
|---|---|
| c6d6 (base's answer) | **cp -1142** |
| c6c7 (PC's answer) | **mate -11** |

Same engine, same position, same settings, same depth: one move is assessed as a lost position (mate against us in
11) and the other as playable (cp -1142). It plays the lost one. That is a **search defect on the owner's real path**,
not a taste difference between builds.

**How sure.** High that the behaviour is real and reproducible: it appears on the PC build at depths 8, 12, 16, 18
and 20 (bestmove c6c7 every time), the two `searchmoves` scores above come from separate fresh processes, and the base
build scores BOTH moves sanely on the same board (c6d6 cp -1145, c6c7 cp -1174). High that PC20 settings are applied
correctly: the option set is the one file 5 defines and every option name was checked against the exe's own `uci` list
in `pcbuild/pc_build_check.py`. **Not** established: the exact ply at which the reduction fires, or a proven
python-chess mate line — see "what I did NOT do".

## 1. The position

`1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183` — white (the side to move, and the side the engine is playing for) has
only its king: **a lone-king root**, exactly the set the bare-king rules gate on. Material: white K vs black K + R +
B + N. It is a lost position either way, but c6d6 prolongs and c6c7 walks into a faster mate.

## 2. Depths 16, 18, 20 on four builds (`deep155.txt`)

| depth | build | bestmove | score | nodes |
|---|---|---|---|---|
| 16 | base | c6d6 | cp -1112 | 81,013 |
| 16 | **r15 PC, PC20** | **c6c7** | cp -1184 | 345,538 |
| 16 | base+ported rules (lmr1_ot0) | c6c7 | cp -1093 | 220,209 |
| 16 | base+ported rules (lmr0_ot0) | c6d6 | cp -1112 | 81,013 |
| 18 | base | c6d6 | cp -1112 | 106,668 |
| 18 | **r15 PC, PC20** | **c6c7** | **mate -16** | 14,312,112 |
| 18 | base+ported (lmr1_ot0) | c6c7 | cp -1093 | 401,949 |
| 18 | base+ported (lmr0_ot0) | c6d6 | cp -1112 | 106,668 |
| 20 | base | c6d6 | cp -1112 | 169,686 |
| 20 | **r15 PC, PC20** | **c6c7** | **mate -10** | 165,764,722 |
| 20 | base+ported (lmr1_ot0) | c6c7 | mate -18 | 1,568,594 |
| 20 | base+ported (lmr0_ot0) | c6d6 | cp -1112 | 169,686 |

Three things this shows that the earlier jobs did not:

1. **The PC build's own node counts explode on this position as it deepens**: 345k at depth 16, 14.3M at depth 18,
   **165.8M at depth 20**. The base build needs 169,686 nodes for depth 20 on the same board. That is a factor of
   ~1,000, on a lone-king endgame, and it is the signature of the unpruned lone-king path doing work that the base
   build prunes away.
2. **The PC build reports a mate against itself and keeps the move.** From depth 18 on, its own score says it is being
   mated (mate -16, then mate -10) — and the move it plays is the one that produces that score.
3. **`lmr0_ot0` is bit-for-bit the base build** (same bestmove, score and node count at all three depths), which is
   the control that the ported patch changes nothing when both switches are off.

## 3. The decisive measurement: the PC build's own move-by-move scores

```
$ go depth 20 searchmoves c6d6   (PC build, PC20, Threads 1, Hash 16)
info depth 20 seldepth 31 score cp -1142 nodes 654788 ... pv c6d6 f2e3 d6c7 b8b5 ...

$ go depth 20 searchmoves c6c7   (same)
info depth 20 seldepth 31 score mate -11 nodes 48295721 ... pv c6c7 b8b5 c7d6 f2e3 ...
```

And the base build on the same two moves:

```
base c6d6: score cp -1145 nodes 151163
base c6c7: score cp -1174 nodes 173131
```

So the base build ranks the two candidates within 29 cp of each other (and prefers c6d6 — the one it plays), while the
PC build on the identical board rates one as cp -1142 and the other as mate -11. **A search that assigns mate -11 to
a move and cp -1142 to another must not choose the first.** Either the root comparison is being made across
inconsistent scores, or the mate score is not reaching the root comparison for that move. That is the defect —
and it reproduces on the base tree under S14, so the bare-king cap is not its cause.

## 4. Where the reduction plausibly bites

`FORGE_FIX_BARE_KING_LMR_CAP` caps a late move's reduction at 1 ply at a lone-king node when the root has a lone king
(src/search.cpp: `if (bare_king_lmr_cap) r = std::min(r, 1);`). Reducing less means searching MORE — which matches the
1,000x node explosion above. Why that would produce a *wrong move* rather than just a slow search, I can only
hypothesise: with the reduction capped, the late moves get full-depth searches whose results are then subject to the
same aspiration/re-search bookkeeping, and on a node where every line is lost the "best" among losing lines is
decided by which line's mate distance got resolved first. I did **not** instrument the reduction to see it fire, so
this paragraph is a hypothesis and is labelled as such in the findings ("suspicions, not proven").

## 5. Why this matters for the owner

The rule is shipped as `LMR_CAP=1`. On this position, on the real binary under the real settings, it turns a
29-cp-decision into playing a forced mate against itself, with a 1,000x node cost. The patch's own justification for
the rule is self-play evidence on KBB-K and KBN-K (175/300 vs 142/300). Those two facts need to be weighed together:
the rule wins more bare-king conversions but on this board it converts a lost position into a lost position faster,
at a thousand times the nodes. **Whether that trade is good is the owner's call, not mine** — but "the engine plays a
move it scores as mate -11" is not a trade, it is a bug, and it is worth fixing regardless of whether the rule stays.

## Steps and evidence

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| PC build under PC20 on 155 at depths 8/12/16/18/20 | done | transcripts in this report; `deep155.txt.raw/` | c6c7 at every depth |
| four-build depth 16/18/20 comparison | done | `deep155.py`, `deep155.txt` (+ `.raw/`) | table above |
| the PC build's score for EACH candidate move | done | commands in section 3 (raw in `deep155.txt.raw/`) | cp -1142 vs mate -11 |
| base build's score for each candidate | done | commands in section 3 | cp -1145 vs cp -1174 |
| control that both-off == base | done | `deep155.txt` (lmr0_ot0 rows) | identical scores AND nodes |
| instrument the reduction to name the firing ply | **not done** | — | would need a debug build with counters; not attempted |
| python-chess proof that c6c7 loses and c6d6 does not | **not done** | — | exact solver is exponential on this board; the engine-vs-engine agreement is the evidence used |

## Prediction against result

No prediction file before this job's measuring commands (third such lapse, all recorded). This job was a direct
request following job 7 and I started measuring immediately.

## Findings

| id | one sentence | reproduce |
|---|---|---|
| S-F16 | **On the PC build itself under PC20, Threads 1, Hash 16**, position `1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183` is answered `c6c7`, whose own depth-20 score is `mate -11`, while the alternative `c6d6` scores `cp -1142` — the engine plays a move it has itself scored as a forced loss; the base build scores the same two moves cp -1145 / cp -1174 and plays the better one [WITHDRAWN — see the banner above: this was measured under DEFAULT options, not S14/PC20]. The PC build also spends 165.8M nodes on depth 20 here against the base build's 169,686. | `cd forge-combo29/swarm/03/job9 && python3 deep155.py /tmp/d.txt` and the two `go depth 20 searchmoves` commands in section 3 |
| S-F17 | The same PC move choice at depths 8, 12, 16, 18 and 20 is c6c7 at every depth, and the build's own score turns into a mate against itself from depth 18 (mate -16) to depth 20 (mate -10) without the move changing — so this is not a shallow horizon artefact. | `cd forge-combo29/swarm/03/job9 && python3 deep155.py /tmp/d.txt` |

## Suspicions, not proven

- That the wrong choice is caused by the capped reduction (`bare_king_lmr_cap`) at this node. Supported by: the
  position is a lone-king root (the gated set), the rule's switch flips the answer in the 2x2 matrix, and the node
  explosion is what "reduce less, search more" predicts. Not supported by: any instrumentation of the reduction
  firing, and the mechanism by which extra search yields a *worse* move is unexplained.
- That the same defect affects other lone-king endgames the owner's matches reach. One position proves one position.

## What I did NOT do

- Did not instrument or debug the reduction site.
- Did not obtain a python-chess mate proof.
- Did not test other lone-king positions from real games for the same signature (the natural next job).
- No sanitizer runs.

## What I am NOT sure about

- Whether the mate -11 score for c6c7 is itself correct (i.e. c6c7 really loses by force) or is a scoring artefact.
  Either way the engine should not prefer the move with the worse score, so the finding stands on the comparison
  rather than on the mate being real.
- Whether `searchmoves` changes the root's behaviour in a way that makes the two scores incomparable. Both scores come
  from the same mechanism with the same settings, and the base build under the same mechanism ranks them sanely, so
  the comparison is like-for-like as far as I can tell — but a `searchmoves` root is not the same as an unrestricted
  root and the brief notes it already behaves differently (known item).

## Times

`job9/stamps.txt`, `deep155.log`.
