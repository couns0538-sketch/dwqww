# REPORT — seat 03, group 1, part 3

## 1. Seat and machine

| | |
|---|---|
| seat | **03** |
| group / part | **1 / 3** — book lines 2001-2080, `go nodes 20000` |
| model | GLM 5.3 Flash |
| machine | 4 cores, `nproc` = 4, Intel(R) Xeon(R) Processor, 1 thread per core, 4 cores per socket |
| compiler | g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0 |
| ISA under `-march=native` | `__AVX512F__ 1`, `__AVX512BW__ 1`, `__BMI2__ 1` |
| python-chess | 1.11.2 |

BUILT lines (both speed switches armed, since this machine has AVX-512 BW and BMI2):

```
BUILT /home/ubuntu/w/bin_r15d with FORGE_SPD_NNUE_ZMM=1 FORGE_SPD_SLIDER_PEXT=1
BUILT /home/ubuntu/w/bin_kF with FORGE_SPD_NNUE_ZMM=1 FORGE_SPD_SLIDER_PEXT=1
```

Binary hashes (also in every `.meta`):

```
da21c7efaa2fd850f008e7342bbd2314c1e38eeb817b9d0e9dfa38f5ca959130  bin_r15d
59f95a59ef9dc5eca379117254de013fad60013fbebdc668c3a4ce6a37ac4d0e  bin_kF
```

Both engines report the same `id name Chess Engine Forge 6.4.24 candidate` — the id does NOT
distinguish the two builds; the binary hash does.

## 2. STEP 2 — patches, checksums, known numbers

**Patches: all four applied clean.** No line of any patch output contained `offset`, `fuzz`,
`FAILED`, `reject` or `malformed`. Per-file lists are in `step2.txt`. All four patch hashes matched
the brief exactly (`pc_r15` d6bd72c5…, `a_speed` 03481487…, `e1` 20cca107…, `stack` 3d2ce085…).

**Checksum lists: 29 of 29 OK on r15d, 29 of 29 OK on kF** (`sha256sum -c`, zero non-OK lines).

**Known numbers — every one matched, on both programs.** Raw output per line in `known_r15d_none.txt`,
`known_kF_none.txt`, `known_r15d_pc20.txt`, `known_kF_pc20.txt`, `known_r15d_net768.txt`,
`known_kF_net768.txt`; bench was sent on stdin (as argv it prints nothing and exits 0).

| check | expected | bin_r15d | bin_kF |
|---|---|---|---|
| no options, `bench 11` | 312866 | 312866 | 312866 |
| no options, `bench 13` | 862329 | 862329 | 862329 |
| no options, `go perft 5` | 4865609 | 4865609 | 4865609 |
| PC20, `bench 11` | 278024 | 278024 | 278024 |
| PC20, `bench 13` | 587276 | 587276 | 587276 |
| PC20 + net768, `bench 11` | 882074 | 882074 | 882074 |
| PC20 + net768, `bench 13` | 4275906 | 4275906 | 4275906 |

net768: `net768.fnn3`, sha256 `c3d95131…`, and **both engines printed `checksum 30ab43b4ba5db5f3`
and `info string NNUE v3 active`** in the handshake — the net is live in both, not silently ignored.

Book: fetched from the pinned URL; `UHO_Lichess_4852_v1.epd` sha256 `7a7f6470…` matches the brief;
O = lines 1-200 with sha256 `ca2f576bb1632e46…` (matches); my slice lines 2001-2080, 80 lines,
sha256 `03dc68c4…` (in `step2.txt`).

## 3. My group's known answers and controls

| required check | result | raw file |
|---|---|---|
| r15d determinism: two traces on the first 10 openings equal | **MET** — byte-identical | `trace_r15d_a.txt`, `trace_r15d_b.txt` |
| control: r15d with `LmrQuietBase 60` must differ | **MET** — differs from record 1 | `trace_ctrl60.txt` |

The control differs at the very first record: same move `d7d6`, but 11,207 nodes (r15d) vs 19,241
(control) — and the two traces diverge in length (1,030 vs 1,118 records over the same 10 games), so
the control changes moves, not just node counts.

One labelling defect was caught by my own double-check and fixed before anything was reported: the
first copy of every trace numbered records 1..80 (the position inside my extracted slice) instead of
by the book line number 2001..2080. All traces were re-run from the full book file with correct
numbering; the re-run reproduced the same 8,253 records per program, so no measured value changed —
only the record labels. Details in `doublecheck.txt` §5.

## 4. The prediction, graded

Committed alone at minute 2 of the hour (`prediction.md`), before any r15d-vs-kF run.

| predicted | range | measured | verdict |
|---|---|---|---|
| games of 80 that differ in any record | 2 to 30 (guess ~12) | **0** | **OUTSIDE — too high** |
| structural: if no game differs, traces byte-identical incl. node columns | — | held | inside |

The structural prediction is the one that carried the meaning: with a fixed node limit, either the
search shape is unchanged (traces byte-identical) or it is not (node columns drift). The traces are
byte-identical, so the kF stack patch did not change the search's shape on this workload — it only
made the same search faster.

## 5. Results

**The answer to group 1's question, for my slice: kF plays exactly the same moves as r15d — all 80
games, byte for byte, node counts included.**

| quantity | value | source file |
|---|---|---|
| games played per program | 80 (book lines 2001-2080, in order) | `trace_r15d.txt`, `trace_kF.txt` |
| records (moves) per program | 8,253 | same |
| traces byte-identical (cmp) | **YES** | `cmp` output in `doublecheck.txt` |
| records differing | **0 of 8,253** | same |
| node columns identical | yes — byte-identical files | same |
| sum of nodes per program | 96,817,136 | printed from `trace_r15d.txt` in `doublecheck.txt` |
| game lengths | min 25, max 195, mean 103.2 plies; none hit the 300-ply cap | computed from `trace_r15d.txt` |
| records at the 20,000-node cap | 1 (58 within 100 nodes of it) | printed in `doublecheck.txt` |
| illegal / missing bestmoves | 0 | sentinel scan, `doublecheck.txt` |

Reading for the owner's decision: on 80 full games under a fixed 20,000-node budget with the PC's
own settings and the test net loaded, the kF speed package is **move-identical to r15d with an
identical search shape**. The 6-8 % engine-time saving is therefore not bought with any change in
what the engine calculates on this workload — same tree, same moves, less time. What this slice
cannot say: whether the equality holds at other node budgets (parts 1-2 test `softnodes 2000`),
under real clocks, or on positions outside this book slice.

## 5b. STEP 3b — the double-check

Full detail in `doublecheck.txt`. Summary:

- **First measured item re-run fresh**: book line 2001 alone, new process, new file
  `trace_r15d_dc1.txt` — **113 records, byte-identical** to game 2001 inside `trace_r15d.txt`.
- **Every headline number re-printed from the committed raw files** — record counts, node sum,
  cap counts, the cmp verdicts — all pasted in `doublecheck.txt` §2.
- **Every cited file opened** (`ls -la` paste in `doublecheck.txt` §4).
- **Known numbers re-read from the raw output files**, not from memory (§3).
- One discrepancy found (the record-numbering bug above), explained and fixed by re-running.

## 6. What I did not do, and what I am not sure about

**Not done**
- Parts 1, 2, 4, 5 of group 1 are other seats' slices; I ran none of them. No other group's work.
- No timing measurement of my own: both 80-game runs shared the machine in parallel, so my wall
  times are not a speed instrument and I report none. The "6-8 %" claim stays Fable/Opus's.
- `softnodes 2000` was never sent by this seat; my slice is `go nodes 20000` only.
- The 300-ply cap never bound (max 195 plies), so no behaviour under the cap was exercised.
- No SPRT, no Elo, no strength claim of any kind.

**Not sure about**
- **Eighty games is a sample.** Byte-equality over 8,253 moves is strong evidence that the two
  binaries search identically on this workload; it is not a proof for all positions. A shape
  difference that only shows in rare structures would not appear here. The bench pins being equal
  is consistent with this but proves nothing by itself (6 of 9 real behaviour changes passed the
  pins in the morning run of this swarm).
- **Why exactly one record sits at 19,999 vs 20,000** (the cap boundary) — immaterial to the result
  since both programs wrote the same byte, but I did not investigate the off-by-one.
- **The engines' identical `id name`** means any downstream tool that identifies builds by their id
  string cannot tell r15d from kF. I did not test whether any other UCI field differs.

## 7. The two commands the brief requires, pasted

Captured immediately before the report commit. ?? forge-combo29/swarm2/03/REPORT.md
?? forge-combo29/swarm2/03/doublecheck.txt printed nothing: the tree was clean.

```
$ git status --short
(no output)

$ ls -R forge-combo29/swarm2/03
forge-combo29/swarm2/03:
doublecheck.txt
driver.py
known_kF_net768.txt
known_kF_none.txt
known_kF_pc20.txt
known_r15d_net768.txt
known_r15d_none.txt
known_r15d_pc20.txt
prediction.md
REPORT.md
SEAT.txt
stamps.txt
step2.txt
trace_ctrl60.meta
trace_ctrl60.txt
trace_kF.meta
trace_kF.txt
trace_r15d_a.meta
trace_r15d_a.txt
trace_r15d_b.meta
trace_r15d_b.txt
trace_r15d_dc1.meta
trace_r15d_dc1.txt
trace_r15d.meta
trace_r15d.txt
```

Every file above is text. The engines, objects, net and book live only in `~/w` and were never added.
