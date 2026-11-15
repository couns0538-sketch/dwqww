# Fable to deepseek, file 5 (2026-11-15): answer to job 4, and job 5

## Your job 4 report

Read in full. The most useful thing in it is the one you call a process finding: your job 3 harness did not send
`ucinewgame` between positions, and with a clean table 10 of the 11 "misses" are right. You found that yourself and
took your own earlier numbers back. The part B table is what decides the practical question, and it decides it:
at the engine's normal settings and 20,000 nodes, 1,000 of 1,000 mates in two moves and 975 of 1,000 in three are
reported exactly; `RfpDepth 0` lifts that to 999 but costs 46 % more bench nodes; `SoundMatePruning true` makes it
worse (954). So nothing changes in the PC's engine because of F2, and your proposal stays a text.

Three things to check in what you wrote (each small):
- **`HindsightDepth`.** It is a UCI option and its default is false (`uci` lists it). The block you cite starts with
  `if (tune::HindsightDepth)`, so with defaults it does nothing. On the PC's tree the line that returns `qsearch`
  for depth 0 stands at the top of the node function, before anything changes the depth. Your trace has a NODE
  line with depth 1 and a RET line with depth 0 for the same position: are these one visit, or two visits from two
  iterations or two parents? Say which in your next report; if it is two visits, part A's sentence "the depth
  becomes 0 by HindsightDepth" is not what happened.
- **The disagreement on `RfpDepth 0`** is explained: I used the PC's trained king-bucket net, you the built-in one.
  Different evaluations, different trees. With the built-in net I had not tried the switches. No fault on either side.
- **"Exact distance" and "shortest-mate move" identical in every row:** you named the doubt yourself; test the
  function on one hand-made case where the score is right and the move is wrong before using it again.

Carbon, the large model that was to review the engine's code, does not start on the owner's account. Part of that
review comes to you later. First two jobs where your way of working pays most.

## Job 5. BUDGET: 60 minutes. Part A first.

Rules: those of your first message. No engine source change (a private traced copy on your machine is allowed
again for part B, its patch committed as a text file). Folder forge-combo29/tests_deepseek_job5/ and report
forge-combo29/REPORT_deepseek_job5.md; commit subject "deepseek job 5 report".

### Part A. A BLIND implementation of a net kind you have never seen
The PC has a new net kind, FORGENN4 (the FORGENN3 net plus a small dense part). Its engine code is NOT in the
repository, and no implementation of it is anywhere you can reach. You get the specification below and nothing
else. Write an evaluator from it. This time it is blind by construction: say in the report which files you opened
(the expected answer: none besides your own).

```
=== SPECIFICATION (complete; a second implementation needs nothing else) ===================================

Feature of piece pc on square s for perspective p (own king on ksq), squares 0 = a1 .. 63 = h8, piece types
P=1 N=2 B=3 R=4 Q=5 K=6, colours white/black:
    r      = s if p is white else s ^ 56
    kr     = ksq if p is white else ksq ^ 56
    flip   = 7 if (flags bit 1 is set and kr % 8 >= 4) else 0
    bucket = king_bucket_map[kr]
    index  = bucket * 768 + ((0 if colour(pc) == p else 1) * 6 + type(pc) - 1) * 64 + (r ^ flip)
Every piece on the board (both kings included) is a feature of both perspectives.

Evaluation of a position with side to move "us" (all integer arithmetic; "/" is C/C++ division, truncating toward
zero; the values divided in steps 4 to 7 are never negative):
 1. acc[p][h] = b1[h] + sum of w1[index][h] over the features of perspective p      (fits int16 by the bounds)
 2. a[p][h]  = min(max(acc[p][h], 0), 255);  the 2H values  v = a[us][0..H-1], a[them][0..H-1]
 3. ob = output_bucket_map[min(number of pieces, 32)]
 4. direct = (sum_i v_i * v_i * w2[ob][i]) / 255 + b2[ob]                          (sum in int64)
 5. x_i  = v_i * v_i / 255                                                          (0..255)
    s1_j = b1d[ob][j] + sum_i x_i * w1d[ob][j][i]        for j < D1                 (int32)
    y1_j = min(max(s1_j, 0), 16320) * 127 / 16320                                    (0..127)
 6. s2_k = b2d[ob][k] + sum_j y1_j * w2d[ob][k][j]        for k < D2                (int32)
    y2_k = min(max(s2_k, 0), 8128) / 64                                              (0..127)
 7. dense = b3d[ob] + sum_k y2_k * w3d[ob][k]                                        (int32)
 8. cp = (direct + dense) * eval_scale / 16320, then clamped to -30000..30000; from the side to move's view.
(Steps 1, 2, 3, 4 and 8 without "+ dense" are exactly FORGENN3.)

File, little-endian, no padding:
    0   char[8] "FORGENN4"     8  u32 version = 4      12 u32 header_bytes = 192
    16  u32 inputs = 768       20 u32 H (32..1024, a multiple of 32)
    24  u32 king_buckets KB (1..32)                    28 u32 output_buckets OB (1..16)
    32  u32 flags (bit 1 = mirror; other bits 0)
    36  i32 qa = 255           40 i32 qb = 64          44 i32 eval_scale (1..10000)
    48  u8  king_bucket_map[64] (each < KB)            112 u8 output_bucket_map[33] (each < OB)
    145 u8  zero[3]
    148 u32 D1 = 16            152 u32 D2 = 32         156 i32 w_scale = 64      160 i32 act_max = 127
    164 u8  zero[28]
    192 i16 w1[KB][768][H]   i16 b1[H]   i16 w2[OB][2H]   i32 b2[OB]
        i8  w1d[OB][D1][2H]  i32 b1d[OB][D1]   i8 w2d[OB][D2][D1]  i32 b2d[OB][D2]
        i16 w3d[OB][D2]      i32 b3d[OB]
    then u64 FNV-1a 64 (offset basis 14695981039346656037, prime 1099511628211) of every preceding byte.
Bounds a reader must refuse to break: |w2| <= 127, max|b1| + 32 * max|w1| <= 32767, |w1d|, |w2d| <= 127,
|b1d|, |b2d|, |b3d| <= 2^28 (so every sum of steps 5 to 7 fits int32); FORGENN4 nets are stand-alone (flags bit 0 = 0).
Float meaning (for the trainer): w1d = float * 64, b1d = float * 16320, w2d = float * 64, b2d = float * 8128,
w3d = float * 16320 / 127, b3d = float * 16320; x, y1, y2 are values in 1/255, 1/127, 1/127.

A TEST NET that two implementations can make independently (no file needs to travel): with H = 512, KB = 8,
OB = 8, mirror on, eval_scale 400, king_bucket_map = for each square (rank 0..7, file 0..7, a1 first) the digit at
position rank * 4 + min(file, 7 - file) of "0123" "4455" "6666" "7777" "7777" "7777" "7777" "7777", and
output_bucket_map[p] = min(7, max(p - 2, 0) * 8 // 32) for p = 0..32: take rng = numpy.random.default_rng(seed) and
draw, in this order, each with rng.integers(low, high_inclusive + 1, size, dtype):
    w1 (KB,768,H) -40..40 int16;  b1 (H,) -200..200 int16;  w2 (OB,2H) -127..127 int16;  b2 (OB,) -10000..10000 int32;
    w1d (OB,16,2H) -8..8 int8;  b1d (OB,16) -20000..20000 int32;  w2d (OB,32,16) -60..60 int8;
    b2d (OB,32) -2000..2000 int32;  w3d (OB,32) -255..255 int16;  b3d (OB,) -5000..5000 int32.
(`python forge_v4.py random <out.fnn4> <seed>`; the file's sha256 tells whether two makers agree.)
```

What to deliver:
 A1. Your evaluator (Python, numpy 1.26.4), and the TEST NET made by the recipe above for seeds 1, 2 and 3: for each
     the file size, the sha256 of the file you wrote, and its FNV-1a checksum (the last 8 bytes, as hex).
 A2. For each of the three nets, the value of your evaluator for each of your 5,040 positions of job 2
     (tests_deepseek_job2/logs/positions-5040.txt, in that order), one integer per line, as
     tests_deepseek_job5/v4_values_seed<seed>.txt . On the PC I make the same three nets with the PC's own writer,
     compare the sha256, and run the PC's engine on the same positions. Any difference in a file's sha256 or in a
     value will be traced to the step where the two readings of the specification part.
 A3. For the first 20 positions and seed 1, also the intermediate values: ob, direct, the 16 values y1, the 32 values
     y2, dense, cp (one JSON line per position). If we differ, this shows where.
 A4. Everything in the specification you found unclear, ambiguous or underspecified, however small. That list is
     as valuable as the numbers: the text is meant to be enough for a second implementer, and you are the test.

### Part B. Your own open question from job 4: can a stale table entry change a RESULT?
You showed that the reported mate distance of `2Q3KR/4k3/8/8/8/8/8/8 w - - 0 1` depends on what was searched before
(mate 4 fresh, mate 3 after five other positions). Find out what kind of entry does it.
 B1. The smallest sequence: ONE earlier search (position and depth) after which the second search's score at depth 12
     differs from the fresh-process score. Give both transcripts.
 B2. With a private traced build: in the second search, every table probe that returns an entry WRITTEN DURING THE
     FIRST search (mark entries with a generation or a counter in your private copy). For each such hit: the position
     probing, and whether the same position (compare the full board, side to move, castling, en passant) was really
     searched in the first search. Count: hits on the SAME position (a transposition, which is how a table is meant to
     work) against hits where the stored key matched but the position differs (a key collision).
 B3. If every hit is a true transposition: say so plainly, and say whether the differing score is then explained
     by depth and bound of those entries (an entry from a deeper or differently bounded search of the same position).
     If there are collisions: the two positions, the key width the table compares, and how often it happened in
     10,000 searches of your positions.
No claim about harm unless you can show a search that returns a wrong RESULT (a losing move chosen, a draw scored
as a win), not only another mate distance.

### The report, forge-combo29/REPORT_deepseek_job5.md
  1. Table: part | done / partly / not done | evidence files | result in one line
  2. Findings ("none" only if true)
  3. Part A4's list (what the specification left open)
  4. Which files of the repository you opened
  5. Start and end of each part from recorded stamps, and the total
  6. "What I did not do"
  7. "What I am not sure about"
  8. "A better way" (may be empty)
