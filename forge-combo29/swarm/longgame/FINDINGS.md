# Long-game replay: the composite over thousands of plies

**Seat:** late-swarm audit. **Build:** `6b98f217`, g++ 13.3, `-DFORGE_MARCH=x86-64-v4`, Release.
**Pins (all four matched before recording):** bench 11 = **312,866**; bench 13 = **862,329**;
bench 16 = **3,024,920**; `go perft 5` = **4,865,609** (`go`/`bench` sent on **stdin**; no `quit`
was ever piped into a live search — the driver reads to `bestmove` first).
**Search:** `go depth 8` on every ply. **Settings:** engine defaults (Hash 32, Threads 1, all
development flags off) — no `setoption` was sent except the arms that say so.

---

## The result

**Replaying real games move by move in one process changes the MOVE on 46% of plies, and it
never changes whether the engine bails.** That is the whole finding, and the two halves have very
different consequences.

| measurement | value |
|---|---|
| games replayed | **200** (from the repo's PGNs at `6b98f217`) |
| plies searched | **27,788** (`position fen <start> moves <prefix>`, `go depth 8` each) |
| fresh-process arm | **40 games, 5,401 plies** (sample fixed before measuring) |
| **in-process vs fresh, bestmove differs** | **2,486 / 5,401 = 46.0%** |
| in-process vs fresh, node count differs | 5,358 / 5,401 |
| **in-process vs fresh, bail differs** | **0 / 5,401 — in either direction** |
| **`ucinewgame` between plies vs fresh** | **5,401 / 5,401 byte-identical** |
| drawn-root bails seen | **89**, one in **89 of 200 games** (44.5%), 1 per **312** plies |
| every bail at the game's last ply | **89 / 89** |
| **every bail predicted independently** | **89 / 89**, and 27,692/27,692 positions agree |
| RSS, 27,788 plies | **42.2 MiB** at every one of 277 samples from ply 300 to the end (+1.6 MiB total) |
| wall time | 78.0 s total, mean 0.39 s/game, max 1.63 s |

**The 46% is a difference, not a defect.** Scored against a depth-14 fresh oracle on 200 sampled
diverging plies, the in-process move is **better in 78, equal in 39, worse in 83** (median delta
**0 cp**, mean +2, range −64/+132). It is the same engine reaching different equally-good moves
because its table is warm — which is what a table is for. **No strength claim survives here in
either direction**, and the honest reading is that depth-8 move identity is simply not a property
this engine has across processes.

**The bail result is the important one, and it is a clean negative.** This was the most serious
finding available — a bail in-process but not fresh would be a position-identity failure. **It
does not happen.** The bail predicate is evaluated on the board built from the sent move list
alone (`search.cpp:2251`), it does not consult the table, and warm state cannot move it. All 89
bails were re-checked in fresh processes: same move 89/89, still bailing **89/89**, and the move
is the `go perft 1` head **89/89**. 96 terminal `0000` roots likewise agreed 96/96.

---

## What each reset state does to a replay

The four TT states of §7 trap 3, measured for the first time on the replay composite rather than
on a two-search fixture. Divergence against fresh, same 5,401 plies:

| state between plies | bestmove differs from fresh | note |
|---|---|---|
| **nothing** (warm table, warm histories) | **2,486 = 46.0%** | the plain GUI shape |
| **`Clear Hash`** | 2,378 = 44.0% | cold table, **warm histories** |
| **`setoption name Hash value 32`** (same value) | 2,378 = 44.0% | **byte-identical to `Clear Hash`, 0/5,401 differences** |
| **`ucinewgame`** | **0 = 0.0%** | full signature identical, 5,401/5,401 |

So `Clear Hash` and the same-value `Hash` resend remove only ~2% of the divergence: **the table
was never the main carrier — the histories are.** And the trap-3 claim that a same-value `Hash`
resend *equals* `Clear Hash` reproduces exactly at replay scale (0/5,401 differences in bestmove,
score, nodes, seldepth and pv length), which is a much harder test than the 30 positions it was
originally established on.

`ucinewgame` being a perfect cold reset at this scale is the operationally useful number: **a GUI
that sends `ucinewgame` between games and nothing between plies is still 44.2% divergent from a
fresh process** (`uncgame` arm, 2,387/5,401), because within a game the table and histories
accumulate exactly as they do in the plain session. **Resetting between games does not make a
replay match a fresh process; only resetting between plies does.**

### The divergence is path-dependent, which is what makes it a leak and not an offset

The same 200 games replayed in **reversed order**, same process shape: **11,385 of 27,788 plies
(41.0%) answer differently** from the forward run. A fixed warm-up offset would give the same
answer regardless of what ran before. This does not. The engine's answer for a given position
depends on the whole preceding sequence in the process.

**Determinism control (both directions):** re-running the identical session gave **0/27,788**
full-signature differences, and re-running 200 fresh processes gave **0/200**. So this is a
reproducible state effect, not noise — the §7 trap-3 warning ("a reusable harness gets a
stable-looking wrong number") holds at 27,788 plies.

---

## The drawn-root bail, in detail

**Every firing, with the checks the brief asked for.** 89 firings, all from the session arm,
each re-run in a fresh process and against `go perft 1`:

| check | result |
|---|---|
| session move == fresh-process move | **89 / 89** |
| fresh process also bails (0 nodes, empty pv) | **89 / 89** |
| session move is the generator's head (`go perft 1` first move) | **89 / 89** |
| **in-process bail where fresh does not bail** | **0** |
| **fresh bail where in-process does not** | **0** |

**Independent prediction, so the count is not the engine vouching for itself.** A python-chess
walk predicts "bail" from the sent move list alone — position occurs a 3rd time, or halfmove ≥ 100,
or insufficient material — and matches **89 / 89 firings with zero false positives**, over all
27,692 positions that have a legal move. An earlier version of this script predicted **0 of 89**
and the disagreement was a defect in the script (it yielded the board *before* pushing the move,
lagging the engine by one ply), not in the engine; it is recorded here because the first number it
produced was wrong in the direction that would have looked like an engine bug.

**These 89 are a lower bound on bail frequency, and the reason matters.** Every one sits at the
**last ply of its game** (89/89), because the PGNs are fastchess games that **terminate at the
threefold**. The replay therefore never asks the engine about a mid-game threefold — it asks about
the terminal one. Measured exposure in this corpus: **max occurrence count at any searched ply was
3, and only ever at a final ply.**

**So the mid-game case was planted.** A legal 4-ply cycle found in the game's own position, played
three times, 10 fixtures × 4 reset states × 2 arms:

| fixture | bails |
|---|---|
| position sent a **3rd** time (10 fixtures) | **40 / 40**, both arms |
| identical fixture, position sent a **2nd** time (10 controls) | **0 / 40**, both arms |

Every bail plays the generator head, session and fresh agree on **bestmove and node count in
40/40**, and the twofold control never bails — so the threshold is 3 occurrences, and no reset
state (`ucinewgame`, `Clear Hash`, `Hash` resend) can suppress or provoke a bail. **A planted
mid-game threefold bails identically in-process and fresh.**

**The literal `position startpos moves` form**, which no repo game can exercise (every one of the
5,689 PGN games carries `[SetUp "1"]` + `[FEN]`): 20 self-play games generated **from startpos**
and replayed move by move, 3,420 plies. **46% bestmove divergence, 0 bail disagreements.** Two
games reached a genuine mid-game threefold during replay and both bailed *at that ply* — in the
session arm and the fresh arm alike.

**One thing this test cannot see.** A bail also fires on `halfmove_clock >= 100` and on
insufficient material, and it fires on the *searched* position's own count. Nothing about warm
state can change the board the predicate reads, so the negative is structural rather than lucky —
but it is a negative about one predicate, and the engine's other warm-state-dependent paths below
are where the real exposure sits.

---

## Memory and time: a flat RSS, with its positive control

RSS every 100 plies over the full 27,788-ply session:

```
plies      0   40.6 MiB
plies    100   42.1 MiB
plies    200   42.1 MiB
plies    300   42.2 MiB   <- last change of any kind
plies  27788   42.2 MiB   <- identical at all 276 further samples
```

**Four distinct RSS values in 27,788 plies**; the entire rise is **+1.6 MiB**, all of it in the
first 300 plies. From ply 300 to the end — 27,488 plies — every sample is the same number to the
KiB. **There is no slow leak.** Peak `hashfull`
during real search was **40 of 1000**, so the table was never close to full and eviction was never
exercised — the flat curve is about allocation, not about a table cycle.

**The flat null needed a positive control and has one:** the same instrument reads
**40.6 → 1,032.6 → 40.6 MiB** across `Hash 32 → 1024 → 32`. It can see a 1 GB allocation, so a
1.6 MiB ceiling over 27,788 plies is a measurement. **Limitation, stated:** this run used Hash 32
and reached hashfull 40, so a leak that only appears under table pressure (Hash 1024+, or
thousands of distinct positions saturating the table) is outside what this evidence covers.

**Time does not drift either.** Median nodes per 2,000-ply block: 3,072 / 2,959 / 3,281 / 3,110 /
2,800 / 3,157 / 2,738 / 3,062 / 3,095 / 3,445 / 3,109 / 3,441 / 2,964 / 3,573. Mean wall per
search 2.45–3.28 ms across the whole run, no monotone trend. A slow leak in time would show here;
it does not.

---

## Score calibration: the warm table is not less accurate

An analysis tool shows a number. Against a depth-18 fresh truth on 150 plies, mean absolute score
error at depth 8:

| arm | mean abs err | median |
|---|---|---|
| in-process session | **751.2 cp** | 34.0 |
| fresh depth 8 | 801.7 cp | 37.0 |
| **depth 1, cold (positive control)** | **1,015.9 cp** | 59.0 |

Paired median difference **0 cp** (trimmed mean −4.2 cp over the 140 non-outlier rows); the
session is worse on 69 plies, better on 72, tied on 9. **The warm table does not degrade the
reported score at this depth.** The depth-1 control proves the metric can tell a bad score from a
good one — and catching that control was not automatic: run inside the same process it returned
the *depth-18* score (error 0.0 at the median) because the depth-18 search had just filled the
table. That is trap 3 again, now with a measurement attached.

### A second finding: the warm table finds mates the fresh process misses

27 of 5,401 plies report a **different score TYPE** (`mate N` vs `cp N`) in-process versus fresh.
**21 of the 27 are in-process-only mates** (6 the other way). These are not artifacts: at depth 16
in a fresh process, **18 of those 21 are confirmed mates.** Eleven of them are one consecutive
run in game `g181`, where the warm session announces `mate 6..9` at every ply while the fresh
depth-8 process reports `cp ±2100..2500` and misses the mate entirely.

- `g181` ply 116: session **`d8f8 mate 9`**, fresh `cp 2104 d8f8`; fresh **depth 16** gives
  **`d8f8 mate 19`**. The in-process answer is the better one.
- 3 of the 21 do not confirm at depth 16 (e.g. `g181` ply 120, session `mate 7` where depth 16
  gives `cp 3053` — still winning, still not a mate). So the direction is right and the horizon is
  not exact.

**Practical reading: a GUI replaying in one process will report mates that a fresh-process tool
never sees. That is a difference a user will notice, and it makes "the GUI said mate 6, your tool
said +2.3" a reproducible, explainable disagreement rather than a bug in either.**

---

## What I had to withdraw, and what is left untested

- **Withdrawn before it was reported: "0 of 89 bails predicted."** It was my script's off-by-one,
  not the engine's. Corrected to 89/89.
- **A 0-node / empty-pv flag is not a bail.** My first pass counted 185 "bails"; 96 of them are
  **terminal roots** (`bestmove 0000`, `score mate 0`, no legal moves at the game's last ply). The
  bail count is **89**, and every table here separates the two. Any earlier seat's zero-node
  number should be re-checked for this conflation.
- **`go depth 8` is a weak oracle for "is this move worse"**, which is why §"move quality" uses
  depth 14 and reports a symmetric result rather than a defect.
- **Untested: the bail predicate under a warm table in a *threaded* search** (`Threads > 1`). All
  of this is single-threaded, matching the default. Fixed-depth threading is already a
  1.24×–2.00× pessimisation per §, so it was not run.
- **Untested: table pressure.** Hash 32, peak hashfull 40/1000. A leak or a bail interaction that
  needs a saturated table would need Hash 512–1024 and a much longer replay.
- **Untested: `ponder`.**
- **The 46% is one number about depth-8 move identity**, and it would very likely shrink at
  greater depth as the search converges. It says nothing about playing strength, and the depth-14
  and depth-18 oracles both say the moves are equivalent in value.
- **The corpus is not from startpos.** All 5,689 repo PGN games carry `[FEN]` headers, so the
  brief's literal command form had to be exercised on generated self-play (3,420 plies) instead of
  on real games. Both give the same answer, but they are different populations.

## Reproduce

```bash
cd forge-combo29 && mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DFORGE_MARCH=x86-64-v4
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 make -j4
cd ../swarm/longgame
python3 scripts/extract_games.py evidence/games.json   # 200 games, 27,788 plies
python3 scripts/sample.py                              # fixes the 40-game sample
python3 scripts/replay.py session      --out evidence/session.jsonl
python3 scripts/replay.py fresh        --out evidence/fresh.jsonl
python3 scripts/replay.py unc          --out evidence/unc.jsonl
python3 scripts/replay.py uncgame      --out evidence/uncgame.jsonl
python3 scripts/replay.py clearhash    --out evidence/clearhash.jsonl
python3 scripts/replay.py hashresend   --out evidence/hashresend.jsonl
python3 scripts/bail_predict.py
python3 scripts/replay.py bailcheck --bails evidence/session.jsonl --out evidence/bailcheck.json
python3 scripts/planted_threefold.py
python3 scripts/startpos_arm.py
python3 scripts/move_quality.py
python3 scripts/score_calibration.py
python3 scripts/rss_control.py
python3 scripts/summary.py                             # regenerates every number above
```

`scripts/summary.py` reads only `evidence/` and reproduces each figure in this report.
Evidence JSONL uses short keys; `evidence/keys.json` is the map.
