# STATUS — swarm/pruning

**State: complete enough to report. Pushed ahead of the 09:30Z deadline.**

## Headline

1. **`SoundMatePruning=true` loses forced mates.** 5 of 90 cells go from a
   correct mate to a non-mate score, all reproducing on the pristine `6b98f217`
   build. Two have a unique mating move. Minimal repro in `FINDINGS.md` §1.
   Recommendation: keep it off (its current default).
2. **The default pruning paths did NOT lose or mis-distance a mate** on a
   corpus where every class provably fired. All six distinct wrong cells were
   fixed by *more depth* on the same unablated engine — horizon, not pruning.
3. **`go mate N` disables every pruning gate** (`mate_moves_ == 0` guard on every
   predicate). Any mate-safety audit using `go mate` measures nothing. All
   numbers here are `go depth N`.

## Verification performed

| gate | result |
|---|---|
| four honesty pins, base + clean + probe builds | **all match** (`check_probe_identity.py`) |
| probe is passive (no ablation ⇒ identical pins) | **yes**, 3 arms × 4 pins |
| every counter fires on a planted fault | **yes** (`check_instruments_live.py`) |
| every ablation changes the search | **yes**, 6/6 classes |
| corpus is actually distinct positions | **asserted**; caught a real `ucinewgame` bug |
| oracle vs known answers | **7/7** |
| oracle vs 3 planted wrong oracles | **3/3 caught** |
| every corpus FEN: python-chess AND engine accepted | **30/30** |
| distances cross-checked by 3 independent solvers | **30/30 agree** |

## Left untested (stated, not hidden)

- Zugzwang where the side to move has **non-pawn material** and every move
  loses. The engine's `has_non_pawn_material` gate means bare-king zugzwang
  cannot reach null move at all, so my five fixtures bound only that case.
- Mates longer than 3 moves as the *target* (searched to depth 12, so they are
  exercised, but a mate-in-6 requiring discovery is not represented).
- Middlegame mating nets; corpus is synthetic endgames.
- No strength claim of any kind.

## Files

- `FINDINGS.md` — result first, then evidence, then the untested list.
- `scripts/` — build, 3 instrument checks, corpus builder, corpus verifier,
  oracle + self-test, depth sweep, options test, zugzwang test, matrix, ablation.
- `evidence/` — `mate_safety_rows.json` (240 rows), `matrix.{json,md}`,
  `options.json`, `zugzwang.json`, `ablation*.json`, `depth_control.{json,txt}`.

## Branch / PR

`swarm/pruning` → `main`. Text and small JSON only; no binaries committed.
