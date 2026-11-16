# REPORT_pc — seat 24, area 4: every area-4 re-check on the PC r15 build (PC20, Threads 1 for scores)

## 1. What was asked / the answer / how sure

**What was asked.** FABLE_TO_swarm_5.md: build the PC engine from its patch in a separate copy with
`-DFORGE_MATE_ALPHA_GUARD=1`, check its known bench numbers, then re-run my own finds on it under PC20 and say in
each finding line which build and settings it used. Plus the swarm rule that every SCORE is Threads 1.

**The answer.** (a) The PC build reproduced **every** published number exactly (none / S14 / PC20). (b) Four of my
area-4 results were re-run on it: the TSan stop-race suite (clean, with a real planted control), the full Threads
sweep (400/400 clean, and unlike the base tree it never timed out), the terminal-root `go infinite` hang (STILL
PRESENT — open on the PC build), and the pos-90 warm slowdown (still present at Threads 16, 439,703 ms). (c) I
corrected my own earlier explanation of that slowdown: at Threads 1 neither build shows it at all.

**How sure.** High on the honesty numbers (8/8 published values) and on the TSan zeros (planted controls counted at
29 and 91 and 22 blocks through the same runners). Medium on the pos-90 comparison, because the two builds were run
with different caps (600 s vs 900 s), which I state rather than hide.

## 2. Honesty numbers (PC build)

patch sha256 **d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a** (matches file 5's prefix)
release exe sha256 068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4
tsan exe sha256 698d2d9b450903a9782d6f2892e9f6b158686035595c3f0c7e4ce58365b425d9, `nm -C | grep -c __tsan_` = 21

| regime | bench 11 | bench 13 | bench 16 | perft 5 | expected | match |
|---|---|---|---|---|---|---|
| none  | 312866  | 862329  | 3024920 | 4865609 | 312866 / 862329 / 3024920 / 4865609 | yes |
| S14   | 242796  | 656517  | 2155620 | 4865609 | 242796 / 656517 / - / - | yes |
| PC20  | 278024  | 587276  | 2343893 | 4865609 | 278024 / 587276 / - / - | yes |

(full raw in pc_build/*.txt, writeup pc_build/HONESTY_PC.md)

## 3. Table

| re-check | build | settings | result | evidence |
|---|---|---|---|---|
| honesty numbers | PC r15 release | none / S14 / PC20, Threads 1 | 8 of 8 published values match | pc_build/HONESTY_PC.md, pc_build/*.txt |
| 24-C3 terminal-root `go infinite` | PC r15 release | PC20, Threads 1, Hash 16 | **STILL PRESENT** — no bestmove in 30 s at a mate root and a stalemate root; `stop` gives 0000 in 0.20 s | pc_build/pc_c3.verdict.txt |
| job-3 stop race (24-F5 line) | PC r15 TSan | PC20, Threads 4 (race test), 400 rounds | 400/400, 0 TSan, 0 crashes, 0 hangs, 0 duplicate/illegal bestmoves; planted 29 blocks | pc_build/pc_inf.summary, pc_build/pc_planted.summary |
| job-1 Threads sweep (24-F2 line) | PC r15 TSan | PC20, Threads 2/4/8/16, first 100 of G, depth 12 | 400/400 answered, 0 TSan, 0 crashes, 0 timeouts, 0 illegal | pc_build/analyse_pc_sweep.py |
| 24-F3 pos-90 slowdown | PC r15 release, Threads 1 | PC20 | NOT PRESENT at Threads 1 (25.0 ms cold / 18.5 ms warm) | pc_build/pc_pos90.txt |
| 24-F3 pos-90 slowdown | base release, Threads 1 | S14 | NOT PRESENT at Threads 1 (37.1 ms cold / 21.8 ms warm) | pc_build/base_pos90.txt |
| 24-F3 pos-90 slowdown | PC r15 TSan vs base TSan | PC20 vs S14, Threads 2/4/8/16 | PC: 25,970 / 19,497 / 12,395 / **439,703** ms; base: 348,278 / 376,680 / **timeout** / **timeout** | pcT*.results vs job1/t*.results index 90 |

## 4. Findings (each names its build and settings)

| id | build | settings | one sentence | state |
|---|---|---|---|---|
| 24-F6 | PC r15 release | none/S14/PC20, Threads 1 | every published number reproduced (plus my own setoption-`value` bug, recorded) | confirmed by my own run only |
| 24-F7 | PC r15 release | PC20, Threads 1 | terminal-root `go infinite` hang STILL PRESENT (`stop` rescues it) | open on the PC build |
| 24-F9 | PC r15 TSan | PC20, Threads 4 | stop race clean 400/400; planted 29 blocks | open (needs another seat) |
| 24-F10 | PC r15 TSan | PC20, Threads 2/4/8/16 | pos-90 slowdown still present at Threads 16 (439,703 ms), ~10x better at 2/4/8 | open, needs another seat |
| 24-F11 | PC r15 TSan | PC20, Threads 2/4/8/16 | 400/400 clean sweep, 0 TSan, 0 timeouts | open (needs another seat) |
| 24-C5 | both releases | S14 / PC20, Threads 1 | CORRECTS my own 24-F3: at Threads 1 neither build shows the pos-90 slowdown, so warm state alone is not sufficient | my own correction |

## 5. Suspicions, not proven

- The pos-90 slowdown is a multi-threaded + warm-state interaction. The Threads-1 runs show neither build is slow on
  it cold OR warm at one thread, so the cost appears only when several threads share the accumulated state. The
  mechanism (TT contention, history cache-line ping-pong, or NNUE accumulator cache) is NOT identified.
- The PC build's ~10x improvement at Threads 2/4/8 on that position is consistent with its `FORGE_FIX_*` switches,
  but I did not bisect which switch does it.

## 6. What I did NOT do

- No bisection of which PC-build switch changes the pos-90 behaviour.
- No Threads-16 score comparison (swarm rule: scores only at Threads 1; the sweep's purpose was races).
- The PC build's own trained net is not available to me (file 5), so every evaluation-dependent question here is
  answered with the built-in net and stays a question for the PC.

## 7. What I am NOT sure about

- Whether 439,703 ms at Threads 16 on PC20 would also have happened on the base tree at a 900 s cap (the base tree
  hit my 600 s cap, so I know only that it was slower than 600 s, not how much slower). The caps differ; I state it.
- Whether the planted-fault control's 29 blocks proves much about `stop` specifically: it proves the runner can
  detect a race, which is what a zero needs, but the planted write is in `should_stop()`, not in the stop handshake.

## 8. Times: see pc_build/stamps.txt

## 9. Last command's output

```
$ cd forge-combo29/swarm/24/pc_build && ls
HONESTY_PC.md  honesty_pc.sh  analyse_pc_sweep.py  pc_threads_sweep.py  run_pc_sweep.sh
recheck_c3_pc.py  recheck_pos90_pc.py  tsan_pc_infinite_stop.py  stamps.txt
none_bench11.txt none_bench13.txt none_bench16.txt none_perft5.txt
S14_bench11.txt  S14_bench13.txt  S14_bench16.txt  S14_perft5.txt
PC20_bench11.txt PC20_bench13.txt PC20_bench16.txt PC20_perft5.txt
pc_c3.verdict.txt pc_c3.meta pc_c3_A..F.raw
pc_inf.summary pc_inf.rounds pc_inf.raw pc_inf.meta
pc_planted.summary pc_planted.rounds pc_planted.raw pc_planted.meta
pc_pos90.txt base_pos90.txt
pcT2.* pcT4.* pcT8.* pcT16.*
```
