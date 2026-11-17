# STATUS — swarm/endgame

State at hand-off: **numbers final for every family except the two named gaps**.

## Done

| item | state |
|---|---|
| Four pins at `6b98f217` | **PASS** — bench 11/13/16 and perft 5 all exact |
| Exact retrograde tables (KK, KBK, KNK, KRK, KQK, KPK) | **done**, checked against 4 classical values (KQK 10, KRK 16, KPK 28 moves; KBK/KNK zero wins) |
| Bail predicate validated against the binary, with two planted faults detected | **done** (`scripts/oracle.py`) |
| KQK / KRK / KBNK: 20 start positions each, two arms, two budgets | **done** |
| KPK: stratified sample, 1,280 cells (640 won / 640 drawn) at `nodes 12000` | **done**; depth-12 arm partial at 432 cells |
| KBK / KNK: game-level bare-minor cost | **done** (2,152 / 2,064 bails) |
| Fifty-move interaction | **done** — 37 attributed failures, all fifty-move, 0 bails |
| KQK depth ladder on the failing FENs | **done** (drawn at 8 and 12, converted at 16 and 20) |

## Not done, and why

- **Item 5, the v3 test net.** `FORGE_NNUE_V3` is 0 in this build's recipe and no
  `FORGENN3` net file exists in the repository. Every row is the **built-in** net. Stated on
  every table rather than noted once.
- **KBNK oracle arm.** No exact 4-piece table was built, so there is no DTM-per-position
  ground truth and no control for that family. KBNK is measured (3/20) but unexplained.
- **Full KPK boundary.** 1,280 of 81,664 canonical cells (1.6%), stratified on
  pawn file × pawn half × verdict, at `go nodes 12000`. The `go depth 12` arm is **partial**
  (432 cells) because the window closed. Not the whole boundary, and the sample is not
  licensed to stand in for it.
- **KNN vs K.** Not tested.
- **Leaf-rule attribution.** The clock band and its exact `cp 0` are measured; the
  attribution to `H > 100 - p` is by behaviour, without instrumenting the leaf.

## If someone picks this up

1. **The clock band [90,100] is the highest-value repair target.** A three-piece won position
   costs 1.16×10⁸ nodes to misjudge there, against 612 at clock 70. Any fix should be measured
   on `scripts/clock_band.py` first: the band, the exact `cp 0`, and the node blow-up are all
   one command.
2. **Do not credit a drawn-root-bail fix with fixing conversion.** 0 of 37 attributed failures
   have a bail. The bail matters in KBK/KNK, where there is nothing to convert.
3. **The oracle arm is the thing to keep.** Any future conversion claim needs a control that
   hits 100% on positions the tables say are won; both harness bugs found here were found
   only because it had a number it had to reach.
4. **KBNK needs a table before it needs a theory.** 17 of 20 end in a fifty-move claim and the
   family is where the bare-minor inversion would bite, but without a 4-piece table the row
   cannot be attributed.

## Reproduce

```bash
# build (compiler trap is real: /usr/bin/c++ is clang 18 with a broken header path)
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 \
  cmake <src>/forge-combo29 -DCMAKE_CXX_COMPILER=/usr/bin/g++ \
        -DCMAKE_BUILD_TYPE=Release -DFORGE_MARCH=x86-64-v4
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 make -j4

python3 scripts/pins.py <build>/forge              # four pins
python3 scripts/build_tables.py                    # ~2 min, writes tables.json
python3 scripts/build_kpk.py                       # ~50 s, writes kpk_table.json
python3 scripts/make_fixtures.py                   # writes fixtures.json
python3 scripts/kpk_sample.py 12                   # writes kpk_sample.json
python3 scripts/oracle.py <build>/forge            # bail predicate + 2 planted faults
bash    scripts/sweep_families.sh                  # every family cell
python3 scripts/aggregate.py                       # numbers.json
python3 scripts/ladder.py --out ladder_kqk.json    # depth ladder on the failures
python3 scripts/clock_band.py <build>/forge        # the clock band and its cost
```

`scripts/README-paths.md` records which path each script takes from the command line.
