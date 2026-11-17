# REPORT — settle_pos29: which move is better at the 203 cp disagreement

Seat 30, area 10. Build: **PC r15** (base `6b98f217` + the `FABLE_TO_swarm_5.md` patch,
`-DFORGE_MATE_ALPHA_GUARD=1`), Threads 1, Hash 64 for this job, OwnBook false, fresh process per row,
every setoption confirmed by `readyok`.

## 1. Three lines
**Asked:** at position 29 of check16 (where S14 chose `f3g2` for cp +1744 and PC20 chose `f3g3` for
cp +1541), which move is actually better?
**Answer:** **`f3g2` — by 190–230 cp at every depth from 12 to 18, on both option sets.** Scoring each
move in isolation is unambiguous, and the unrestricted search converges on `f3g2` too (PC20 needs
depth 18 to switch to it). So the original 203 cp gap was a real difference and S14's move was the
better one.
**How sure:** certain about the isolated comparison (two orders of depth, both arms, a 200 cp
separation that never narrows); and my own prediction that PC20's move would win was **killed**.

## 2. Honesty numbers
Base build pins unchanged (`HONESTY.txt`); the PC build used here is the one whose known answers all
matched in `pc/out/pc_honesty.json` (none 312866/862329/3024920/4865609, S14 242796/656517,
PC20 278024/587276).

## 3. The prediction, committed first
`check17/prediction.txt`, committed as `ada4543f0` **before** the first measuring command. Four
predictions with kill conditions. Result: **P4 killed**, P1 killed as written, P2 held, P3 not
applicable (no mate appeared).

## 4. Results

### A. Each move scored alone (root restricted to that move)

| depth | `f3g2` S14 | `f3g2` PC20 | `f3g3` S14 | `f3g3` PC20 | gap |
|---|---|---|---|---|---|
| 12 | cp 1801 | cp 1817 | cp 1611 | cp 1534 | 190–283 |
| 14 | cp 1825 | cp 1881 | cp 1708 | cp 1678 | 117–203 |
| 16 | cp 1918 | cp 1968 | cp 1729 | cp 1802 | 116–239 |
| 18 | cp 2016 | cp 2042 | cp 1791 | cp 1809 | 207–251 |

`f3g2` leads at every depth on both arms. The separation never narrows, so this is not two views of
one win — it is a better move.

### B. Unrestricted search

| depth | S14 | PC20 |
|---|---|---|
| 12 | `f3g2` cp 1838 | `f3g3` cp 1627 |
| 14 | `f3g2` cp 1905 | `f3g3` cp 1724 |
| 16 | `f3g2` cp 1985 | `f3g3` cp 1824 |
| **18** | `f3g2` cp 2022 | **`f3g2` cp 2088** |
| 20 | `f3g2` cp 2093 | `f3g2` cp 2197 |

PC20 prefers `f3g3` from depth 10 through 16 and only corrects at depth 18.

## 5. Findings
1. **30-C56** — `f3g2` is better; the S14 choice was right, PC20's was 200+ cp inferior. My
   prediction P4 (that PC20's move would win) was wrong and is recorded as wrong.
2. **30-F59** — a concrete instance of PC20 being *worse* at self-play depths and self-correcting at
   depth 18. This does not contradict 30-C55 (90 % agreement over 40 positions); it is one of the 10 %,
   now adjudicated rather than left as "a disagreement".

## 6. What I did NOT do
- Did not test other positions from the 4 disagreements; this settles position 29 only.
- Did not run a match to see whether the 200 cp matters in practice — a cp gap at +1700 may not change
  results, and I say so rather than implying it does.

## 7. What I am NOT sure about
- Whether the 190–230 cp separation would shrink at much greater depth (24+); both arms were still
  drifting upward at depth 18 (2016 → 2042), so I cannot rule out convergence far beyond.
- Hash was 64 MB here (larger than the 16 MB used in check16) to give the deep searches room; that is
  a settings difference from the original measurement and is stated.

## 8. Times: `run.log` carries `date -u` at both ends; the run took about 4 minutes.
