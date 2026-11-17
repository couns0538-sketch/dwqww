# REPORT_v3_Step0 — STEP 0 PASSED: all eight bench numbers and all three eval lines match

**The verdict: 8 of 8 bench numbers and 3 of 3 eval lines match file 7 exactly.** The one apparent failure in my
first run was **my own transcription error**, not a build difference — see the correction below.

## The result

```
row                        spec       expected    measured   verdict
no_net                     bench 11     312866      312866   MATCH
no_net                     bench 13     862329      862329   MATCH
pc20_no_net                bench 11     278024      278024   MATCH
pc20_no_net                bench 13     587276      587276   MATCH
net_only                   bench 11     965454      965454   MATCH
net_only                   bench 13    4151906     4151906   MATCH
pc20_net                   bench 11     625258      625258   MATCH
pc20_net                   bench 13    3652372     3652372   MATCH

eval startpos                                                968 / 968 / 968    MATCH
eval r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/...                  1176 / 1176        MATCH
eval 8/5pk1/6p1/8/3R4/6P1/5PK1/3r4 w - - 0 40                  31 / 31          MATCH

load line: checksum fdff70de72e4ca82, max|w1| 64 max|b1| 96 max|w2| 16, kernel avx512   ALL MATCH
```

## THE CORRECTION: I MISREAD ONE DIGIT AND REPORTED A HARDWARE DIFFERENCE THAT DID NOT EXIST

My first Step 0 run reported `net_only bench 13` as **4,151,906 against a published 4,191,906** and concluded the
40,000-node gap was "most likely the CPU/compiler difference", because my machine is an Intel Xeon and file 7's
numbers come from an AMD Zen 5.

**File 7 says 4,151,906. I had typed 4,191,906 into my own harness's expected-value table.** Byte-level check of
the published row:

```
$ git show FETCH_HEAD:...FABLE_TO_swarm_7.md | grep '^| test net only' | od -c
|   t e s t   n e t   o n l y   |   9 6 5 4 5 4   |   4 1 5 1 9 0 6   |
```

`4 1 5 1 9 0 6` — the third digit is **5**, not **9**. My build matched from the first run; my expectation was
wrong.

Three other seats (11, 29, 15) independently reported the same pair as matching, on the same hardware and compiler
as mine. **That is three independent measurements against my one transcription, and I should have treated the
disagreement as pointing at my own reading rather than at my hardware.** Instead I built a plausible hardware
explanation on top of it — which is the failure mode my own STANDING CAUTION habit 3 describes (a single case
dressed as a property), applied to an error rather than a result. A digit is cheaper to check than a hypothesis,
and I checked the hypothesis first.

**This is the seventh self-correction on the branch and the most avoidable.** The check that would have caught it in
one second: quote the published figure byte-for-byte into the table rather than retyping it.

## What the mistake cost, and what it did not

- It cost one stopped job and one wrong message to the coordinator suggesting a hardware cause and offering to hand
  the work over. No work was lost; the build was correct throughout.
- It did NOT invalidate any measurement. Every number my build produced was right; only my hard-coded expectation
  was wrong.

## Honesty numbers

```
exe      /home/ubuntu/builds/bld-v3/forge   g++ 13.3.0, -march=x86-64-v4, -DFORGE_NNUE_V3=1 -DFORGE_MATE_ALPHA_GUARD=1
net      /tmp/test.fnn3  6,309,096 bytes, fnv1a64 fdff70de72e4ca82, sha256 1db8525e...  (all three match file 7)
         *.fnn3 is in .gitignore and is NOT committed
CPU      Intel(R) Xeon(R) Processor
threads  Threads 1, Hash 16 on every row that sends options
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| test net generated, three checksums | done | `make_v3_testnet.py` | matches file 7 |
| v3 build with NNUEArch | done | flags above | yes |
| 8 bench numbers | done | `raw/step0.txt`, `run4.log` | **8 of 8 MATCH** |
| 3 eval lines | done | same | **3 of 3 MATCH** |
| load-line checksum and max values | done | same | all match |
| correcting my own expected-value typo | done | this report, `od -c` above | file 7 says 4151906 |

## Findings

`v3 | file 7 Step 0 PASSES on this machine: all EIGHT bench numbers (312866, 862329, 278024, 587276, 965454, 4151906, 625258, 3652372) and all THREE eval lines (968, 1176, 31, each with hce 0) match file 7 exactly, and the load line matches on checksum fdff70de72e4ca82, max 64/96/16 and kernel avx512. My earlier report of a 40,000-node hardware discrepancy was MY OWN transcription error: file 7 says 4151906 and I had typed 4191906 into my harness's expectation table. Three other seats on identical hardware reported the same pair as matching, which I should have taken as evidence against my reading before constructing a hardware explanation | v3/raw/step0.txt v3/run4.log v3/REPORT_step0.md | NEW |`

## Suspicions, not proven

- Nothing. This row is settled by the bytes.

## Times

`v3/stamps.txt`, every line a `date -u`.
