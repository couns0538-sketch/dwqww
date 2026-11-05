# T02-02: Filter-only retrain: drop capture-best-move rows by a short search, skip early plies
Status: PARTIAL (the trainer flags of the npt w4 runs and the Lichess rows' write-time filters are PENDING, crew)

## Source
- Stockfish PR 4314 (net nn-60fa44e376d9; its fishtest runs started 2022-12-29): https://github.com/official-stockfish/Stockfish/pull/4314
  fishtest STC https://tests.stockfishchess.org/tests/view/63adb3acae97a464904fd4e8 ,
  LTC https://tests.stockfishchess.org/tests/view/63ae0ae25bd1e5f27f13d884 (TC / book read from the fishtest API).
- nnue-pytorch PR 222 (turned the fixed ply cut of PR 4314 into a loader parameter):
  https://github.com/official-stockfish/nnue-pytorch/pull/222

## Licence
Stockfish ff7cee4244 and nnue-pytorch c625702757: GPL-3.0 (notes/T02/licences.md): ideas only. Read: PR text and
fishtest run data only, never source.

## Mechanism
Same data set and same net size as the master net; only the rows change. (1) An offline pass runs a short multipv-2
search (depth 6) on each stored position and removes it when the best move found is a capture (run over ~93 % of the
Leela/SF part and 99 % of the SF DFRC part; parts that were not filtered were left out). (2) The loader skips every
position with game ply <= 28. Rationale: a position whose best move is a capture is not quiet, so its stored search
value is not a value the static net can see; early plies are book-like near-duplicates.

## Forge fit
Lock source: no datagen or filter code (`tools/forge_has.sh 'datagen|gensfen|selfplay|self_play'` = 0 hits).
Data side (skills forge-selfplay-datagen, forge-nnue-data): the self-play writer already drops rows whose 5000-node
best move is a capture / ep / promotion, in-check rows, mate scores, |cp| > 3000 and bound scores, so (1) is done at
write time for self-play rows (with the writer's own search, not a separate multipv-2 pass). The J1 / R11 binpack
writer stores a constant ply 40 and a null king move in every record, so the trainer's ply skip and move-based skip
cannot act on Forge binpacks: (2) is NOT done, and plies 9-28 (after the 8 random opening plies) are all in the data.
Whether the Lichess rows were capture / check filtered when written: PENDING (crew).
Change: carry the true game ply into the binpack at conversion (or cut rows with ply <= P there; own start P = 20,
range 12-32). Filtering only removes rows, so the 4,088-key overlap cannot grow; re-run the T02-01 check anyway.

## Expected gain
Source (PR 4314, filter-only retrain, fixed arch HalfKAv2_hm, same data): local fixed 25k nodes +5.1 +- 1.5; fishtest
STC 10+0.1, book UHO_XXL_+0.90_+1.19, 1 thread: passed SPRT [0, 2], 36,504 games, W 9847 L 9538 D 17119 = +2.9 Elo
(computed from W/L/D); LTC 60+0.6, same book: passed SPRT [0.5, 2.5], 36,592 games, W 10017 L 9717 D 16858 = +2.9 Elo
(computed). The two filters were never tested apart.
Forge estimate: +0 to +5 Elo for the next npt net of the same size, **UNPROVEN** (the capture part is already done at
write time for self-play rows; only the ply cut is new; a weaker net may react more or less to the same noise).

## Effort
Crew 2-4 h (converter flag keeping the real ply or cutting ply <= P, row counts per ply bucket, overlap re-check).
CPU: one conversion pass (R11-sized, a few hours on 3 threads). GPU: two npt runs of the w4 size and length at the
same seed (cut vs no cut).

## Test plan
Pre-gate: row counts per ply bucket before / after; overlap 0 (T02-01 tool); export parity 12k exact; lock OFF bench
pins unchanged (net option empty); WAC 300 ON / OFF. Gate: new net vs the same recipe without the cut, UHO SPRT
[0, 5] at STC, then LTC; against AL1 only once an npt net is gate-competitive.

## OFF-by-default design
No engine change: the net loads through EvalFileHalfKA (default empty = lock eval, bench pins unchanged). The data
change is a converter switch (`--min-ply P`, default 0 = today's J1 bytes), so the default output is byte-identical.
