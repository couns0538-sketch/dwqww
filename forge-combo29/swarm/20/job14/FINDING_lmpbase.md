# seat 20 — job 14: how far does the `LmpBase=8` mate loss reach?

Answer: **it is narrow and it is a delay, not a breakage.** Mates that need 1 ply are unaffected; a mate that needs
3 plies is not scored as a mate at any depth 8–14 under either setting (both settings report cp there, so that is a
separate thing about shallow mate-in-3 detection, not an `LmpBase` effect); and on the one board where the mate is
deep (−7 to −4), `LmpBase=8` replaces the mate score with a large cp score at depths 10 and 12 and first reports a
mate only at depth 14 — a delay of about two to four plies.

Raw: `out_ladder.txt`, `lmpbase_ladder.json`. Script: `lmpbase_ladder.py`.
Build `/agent/repos/build-base/forge` sha256 `e06310ec…` (4/4 pins). Every PV replayed with python-chess.

## The ladder (python-chess counts are mine, printed by the script)

| board | mate-in-1 count | mate-in-3 count |
|---|---|---|
| `6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w` ("mate1") | 1 (`d1d8`) | 53 |
| `6k1/6pp/8/8/8/8/5PPP/R5K1 w` ("mate-in-3") | **0** | 18 (`g1h1 g8h8 a1a8`) |
| `8/8/1p6/8/p3p3/8/2Kpk3/8 w` (S-F19 board) | 0 | 0 (deeper than 3 plies) |

My first version of this ladder mislabelled the rook board as "mate-in-3" when it was mate in ONE (`c1c8`) — the
script now prints the counts and the mislabelled board is gone from the table.

## Results (`go depth D`, LmpBase default 4 vs 8)

| board | LmpBase | d8 | d10 | d12 | d14 |
|---|---|---|---|---|---|
| mate1 | default | mate 1 ✓ | mate 1 ✓ | mate 1 ✓ | mate 1 ✓ |
| mate1 | **8** | mate 1 ✓ | mate 1 ✓ | mate 1 ✓ | mate 1 ✓ |
| mate-in-3 | default | cp 1219 | cp 1295 | cp 1320 | cp 1368 |
| mate-in-3 | **8** | cp 1267 | cp 1283 | cp 1346 | cp 1359 |
| S-F19 board | default | cp −2665 | **mate −7 ✓** | **mate −7 ✓** | **mate −6 ✓** |
| S-F19 board | **8** | cp −2667 | **cp −2884** | **cp −3114** | **mate −9** (truncated 17/18) |

(✓ = PV verified as a real checkmate in exactly the claimed plies.)

Three separate facts, and it matters not to merge them:
1. **Mate in 1: untouched** by `LmpBase=8` at every depth.
2. **Mate in 3: never scored as a mate at depth 8–14 by either setting.** Both report cp around +1200 to +1360,
   with `LmpBase=8` very slightly higher. So this is *not* an `LmpBase` effect — it is a shallow-detection fact that
   would have been easy to mis-attribute. I did not chase it further (it is outside this job's question).
3. **The deep mate (S-F19 board): `LmpBase=8` loses the mate score at depths 10 and 12**, giving a large cp
   instead, and recovers a mate at depth 14 — with a *longer* claimed distance (−9) than the default's d14 (−6).

## So the honest statement about S-F19
`LmpBase=8` **delays mate discovery** on a deep forced mate: at depths where the default already proves mate, it
reports a big negative cp. It is not "broken": the same setting finds the mate two plies deeper. What a user sees
in a game is a slower conversion and a score that looks like a losing position rather than a mate; in analysis it
means `mate N` cannot be trusted across tunings.

## Where my predictions went
1 held (mate-in-1 untouched). 2 held. 3 held (the mate it does report is longer: −9 vs −6 at d14). 4 held where a
mate was reported (17/18 truncated at d14 — no full-length PV to verify, so the "consistent" claim is limited to
the default rows). 5 held: I report it as a delay, not as breakage.

## What I did NOT do
- Not the mate-in-3 detection question (a real, separate observation: neither setting finds a 3-ply mate by depth
  14 — worth its own job).
- Not other depths (16, 18, 20) to find where `LmpBase=8` first reports the mate.
- Not other positions; one deep-mate board.

## What I am NOT sure about
- Whether the cp −3114 at depth 12 under `LmpBase=8` is a *wrong evaluation* or merely the correct score of a
  truncated search. It verifies as "not a mate"; whether White is really lost by 3114 cp needs an independent
  evaluation, which I did not do.

## Commands that show it again
```
python3 lmpbase_ladder.py /agent/repos/build-base/forge /tmp/o
```
