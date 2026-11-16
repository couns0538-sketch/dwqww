# deepseek6 long 23 — PREDICTION (written before the first recount command)

Item: RECOUNT glmflash5's jobs 23 and 24 from its `gamelist_M*.txt` files with my own code:
W-L-D, the five pair outcomes, pair Elo with its 95 % interval, and how many openings any
two matches share.

Model: DeepSeek V4.1 Flash 1017. Time written: see stamps.txt (first line).
Method fixed by this prediction: my own Python (no line of glmflash5's `job23_stats.py`),
reading only the ten committed `gamelist_M51..M60.txt`. Pairing assumption taken from the
files (rows 2k-1 and 2k are one opening, opponents swapped on the same FEN — verified in
`pairing.txt` before any count).

## What I predict the recount will find

1. **All ten files have 2000 rows and 1000 complete pairs**, no dangling game. Kill range:
   any file with a row count other than 2000, or a pair whose two rows carry different FENs
   (beyond what `pairing.txt` prints), kills this line.
2. **W-L-D and Elo reproduce glmflash5 to the digit** for all ten matches — same W, L, D,
   same Elo to 0.01, same 95 % half-width to 0.01. Kill range: any of the ten differing by
   one game anywhere, or any Elo differing by more than 0.01.
3. **The pair-outcome vector n5=[0,0.5,1,1.5,2] counts** reproduce exactly, and every
   identity line glmflash5 printed (`mates = W+L`, `n5 sums to pairs`, `W+L+D = 2*pairs`)
   holds in my count. Kill range: any identity failing in my recount.
4. **The "identity endings" claim is arithmetically right but semantically a coincidence**:
   mates = W+L will hold, yet it holds because *every decisive game in these lists ends by
   mate* (there is no resignation and no adjudication in the configs), not because a mate
   implies the winner. Prediction: in every list, White mates + Black mates = the number of
   decisive games exactly, and the per-ending table has exactly the five ending kinds seen
   in the samples. Kill range: any decisive game whose ending string is not "White mates"
   or "Black mates", or any mating string in a drawn game.
5. **Matches are played on disjoint opening slices**, so the answer to "how many openings any
   two matches share" is **0 for every one of the 45 pairs of matches**. Reasoning: the
   generator removes every opening used before, and each of M51..M60 uses its own `start=`
   window. Kill range: any pair sharing one or more openings (then the generator's "used"
   set was stale, which is a real finding about glmflash5's job 23/24 opening hygiene).
   Second, weaker sub-prediction: M51/M52/M53 are three 1000-opening windows inside one
   4000-line file and M54 re-uses the M53 window (`start=2001`), so M53 and M54 share
   **1000 of 1000** openings with each other while sharing 0 with the rest. In job 24 the
   six windows are disjoint across a 6000-line file, so all 15 pairs there share 0.
6. **Colour balance**: because every opening is played twice with colours swapped and the
   lists are even, the recount's White-wins minus Black-wins equals W-L of the candidate only
   in aggregate; I predict each list has 1000 games with `cand` as White and 1000 as Black.
   Kill range: any list where `cand` is not White in exactly half its games.
7. **The Elo signs glmflash5 reported are reproduced by my own formula** (pair-score
   Elo with the pair-variance interval): I predict M51 -4.00, M52 +5.04, M53 +4.17,
   M54 +1.22, M55 +16.52, M56 +1.39, M57 +11.82, M58 +3.65, M59 +7.30, M60 -1.91, all to
   +-0.01. (This is a deliberate *reproduction* test of the published numbers, not a guess:
   the kill range is 0.01 on each.)
8. **A finding I expect and will name**: M55 (+16.52) and M60 (-1.91) are the two ends of
   the spread over ten 1000-pair looks of things that should be nearly identical in strength;
   the 95 % intervals of the individual looks overlap heavily, so the correct reading of this
   set is the pooled number, not any single look. Prediction: the pooled variant@2000
   estimate over the five 2000-node looks lands in [+4, +9], i.e. inside glmflash5's own
   [+1.35, +12.00] and inside its point +6.67.

## What would make me report "not comparable" instead of a number
A list whose rows cannot be paired (odd count, unparseable field count, missing result
string). Then that match gets no Elo line at all and the report says why.
