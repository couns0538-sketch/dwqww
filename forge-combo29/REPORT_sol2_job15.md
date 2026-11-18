# sol2 — Job 15 hard-link replication and four matched path lengths

## Step 0 — machine and frozen identities

Debian Clang 19.1.7 was verified. The cloud VM reports an AMD EPYC 9V74, five logical CPUs on five guest cores, one thread per core and 32 MiB of L3 cache. The cgroup capacity is four CPU equivalents. The replay driver and each engine use logical CPU 2. Both frozen Job 13 Clang ThinLTO executables matched their SHA-256 pins, and the net768, book, replay driver and workload signature matched Job 14. Each build completed a fresh W replay with the fixed launch environment. [Machine and gate receipts](sol2/job15/step0-command.raw.txt) · [Build hashes](sol2/job15/clang-executables.raw.txt) · [Workload pins](sol2/job15/workload-pins.raw.txt)

Both Step 0 builds match W with 20 games, 2,247 searches, 7,905,938 last-info nodes, 9,189,426 final nodes and trace `7f78d3aec021ab01`. W uses PC20, Threads 1, Hash 16 MiB, net768 and `go softnodes 2000` on book lines 7001–7020. [r15d](sol2/job15/step0/r15d.result.raw.txt) · [kF](sol2/job15/step0/kF.result.raw.txt) · [W signature](sol2/job15/known-answer.txt)

## Step 1 — paths, executable identities and environment

| Arm | Engine argv[0] | Characters | Device | Inode | SHA-256 |
|---|---|---:|---:|---:|---|
| P0 | `/workspace/work/sol2-job13/build-clang-selfplay-r15d/forge` | 58 | 27 | 278740 | `540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834` |
| H1 | `/workspace/work/sol2-job14/hard-link-to-r15d-at-a-substantially-longer-launch-path/forge` | 88 | 27 | 278740 | `540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834` |
| R40 | `/workspace/work/sol2-job15/arms/r1/forge` | 40 | 27 | 274916 | `540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834` |
| K40 | `/workspace/work/sol2-job15/arms/k1/forge` | 40 | 27 | 274918 | `da5df215a6aa255261d4e5574474da7c82aad1a9e95df83e15d5b38963ef439d` |
| R56 | `/workspace/work/sol2-job15/arms/r2xxxxxxxxxxxxxxxx/forge` | 56 | 27 | 274920 | `540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834` |
| K56 | `/workspace/work/sol2-job15/arms/k2xxxxxxxxxxxxxxxx/forge` | 56 | 27 | 274922 | `da5df215a6aa255261d4e5574474da7c82aad1a9e95df83e15d5b38963ef439d` |
| R72 | `/workspace/work/sol2-job15/arms/r3xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 274924 | `540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834` |
| K72 | `/workspace/work/sol2-job15/arms/k3xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 274926 | `da5df215a6aa255261d4e5574474da7c82aad1a9e95df83e15d5b38963ef439d` |
| R88 | `/workspace/work/sol2-job15/arms/r4xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 88 | 27 | 274928 | `540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834` |
| K88 | `/workspace/work/sol2-job15/arms/k4xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 88 | 27 | 274932 | `da5df215a6aa255261d4e5574474da7c82aad1a9e95df83e15d5b38963ef439d` |

Each engine receives `LC_ALL=C` and `TZ=UTC`, 16 bytes, SHA-256 `4d41c4c11fcc6efa3bd339441ec9b26e6a1442056205420dc4b11e93dbff2570`. [Arms](sol2/job15/arms.txt)


P0 and H1 retain the Job 14 device and inode. The R and K arms are fresh copies at matched path lengths. [Arm construction](sol2/job15/make_arms.py.txt)

## Prediction graded

The prediction was published alone at `a7fcd6857afb88e20b7c0b92bdc5e65c61f47f6c` after Step 1 and before T1.

| Comparison | Predicted CPU B/A | Observed CPU B/A | Ratio in range | Expected reading | Observed reading | Reading met |
|---|---:|---:|---|---|---|---|
| T1 | 0.960–1.025 | 1.0004 | Yes | Path effect not replicated | Path effect not replicated | Yes |
| T2 | 0.980–1.050 | 0.9984 | Yes | Path effect not replicated | Path effect not replicated | Yes |
| U40 | 0.905–0.979 | 0.9468 | Yes | kF faster at every length and THE SAME by Q | For U40, the interval is wholly below 1. kF faster at every length and THE SAME by Q | Yes |
| U56 | 0.905–0.992 | 0.9523 | Yes | kF faster at every length and THE SAME by Q | For U56, the interval is wholly below 1. kF faster at every length and THE SAME by Q | Yes |
| U72 | 0.905–0.992 | 0.9526 | Yes | kF faster at every length and THE SAME by Q | For U72, the interval is wholly below 1. kF faster at every length and THE SAME by Q | Yes |
| U88 | 0.905–0.992 | 0.9455 | Yes | kF faster at every length and THE SAME by Q | For U88, the interval is wholly below 1. kF faster at every length and THE SAME by Q | Yes |
| V40 | 0.995–1.105 | 1.0528 | Yes | Swapped estimate below one | Swapped estimate below one | Yes |
| V88 | 0.995–1.105 | 1.0468 | Yes | Swapped estimate below one | Swapped estimate below one | Yes |

The descriptive swapped-ratio range was 0.92–0.99. The observed estimates were V40 0.9483 (within range) and V88 0.9504 (within range).

[Original prediction](sol2/job15/prediction.txt) · [UTC checkpoints](sol2/job15/stamps.txt)

## Step 2 — timing comparisons

Each run starts a fresh engine and driver on the same logical CPU with W and the same replacement environment. Odd blocks use ABBA and even blocks use BAAB. The first arm runs once as a recorded warm-up before its block. Only the four timed runs enter a block ratio. A run that fails the signature gate excludes its block. Engine CPU is user plus system time for the reaped engine process. Wall is the full driver call interval. Ratios are B divided by A. The complete rows give the mean and its Student t interval from the 16 block ratios with 15 degrees of freedom. [Timing command](sol2/job15/run_campaign.sh.txt) · [Independent readback](sol2/job15/timing_readback.py.txt)

| Comparison | A | B | Metric | Blocks | Median | Pooled B/A | Mean | 95% t interval, df 15 | Below 1 |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| T1 | P0 | H1 | Engine CPU | 16/16 | 1.0070 | 1.0004 | 1.0020 | [0.9754, 1.0286] | 7/16 |
| T1 | P0 | H1 | Wall | 16/16 | 1.0050 | 0.9996 | 1.0014 | [0.9738, 1.0291] | 8/16 |
| T2 | H1 | P0 | Engine CPU | 16/16 | 1.0111 | 0.9984 | 0.9999 | [0.9725, 1.0272] | 7/16 |
| T2 | H1 | P0 | Wall | 16/16 | 1.0122 | 0.9987 | 1.0002 | [0.9723, 1.0281] | 7/16 |
| U40 | R40 | K40 | Engine CPU | 16/16 | 0.9510 | 0.9468 | 0.9472 | [0.9317, 0.9628] | 15/16 |
| U40 | R40 | K40 | Wall | 16/16 | 0.9561 | 0.9523 | 0.9527 | [0.9365, 0.9689] | 15/16 |
| U56 | R56 | K56 | Engine CPU | 16/16 | 0.9518 | 0.9523 | 0.9527 | [0.9346, 0.9709] | 14/16 |
| U56 | R56 | K56 | Wall | 16/16 | 0.9584 | 0.9577 | 0.9582 | [0.9394, 0.9770] | 14/16 |
| U72 | R72 | K72 | Engine CPU | 16/16 | 0.9563 | 0.9526 | 0.9532 | [0.9360, 0.9705] | 16/16 |
| U72 | R72 | K72 | Wall | 16/16 | 0.9623 | 0.9588 | 0.9594 | [0.9423, 0.9764] | 14/16 |
| U88 | R88 | K88 | Engine CPU | 16/16 | 0.9472 | 0.9455 | 0.9459 | [0.9177, 0.9741] | 15/16 |
| U88 | R88 | K88 | Wall | 16/16 | 0.9536 | 0.9514 | 0.9519 | [0.9229, 0.9808] | 15/16 |
| V40 | K40 | R40 | Engine CPU | 16/16 | 1.0457 | 1.0528 | 1.0542 | [1.0237, 1.0847] | 2/16 |
| V40 | K40 | R40 | Wall | 16/16 | 1.0386 | 1.0461 | 1.0475 | [1.0169, 1.0781] | 2/16 |
| V88 | K88 | R88 | Engine CPU | 16/16 | 1.0421 | 1.0468 | 1.0474 | [1.0280, 1.0667] | 1/16 |
| V88 | K88 | R88 | Wall | 16/16 | 1.0349 | 1.0401 | 1.0406 | [1.0209, 1.0604] | 2/16 |

## Declared readings and arithmetic

| Metric | Path effect T1/T2 | H1/P0 swapped ratio | kF faster at every length | kF/r15d swapped at 40 | kF/r15d swapped at 88 |
|---|---|---:|---|---:|---:|
| Engine CPU | Not replicated | 1.000994 | Faster at every length | 0.948325 | 0.950393 |
| Wall | Not replicated | 1.000487 | Faster at every length | 0.954114 | 0.956443 |

Each swapped ratio uses the square root of the forward pooled ratio divided by the reverse pooled ratio. The extreme-length ratios are descriptive.

| Metric | Length | U mean m_L | CI half-width / 2.131 (s_L) | Weight w_L |
|---|---:|---:|---:|---:|
| Engine CPU | 40 | 0.947207870 | 0.007299933 | 18765.593069 |
| Engine CPU | 56 | 0.952719588 | 0.008522904 | 13766.540802 |
| Engine CPU | 72 | 0.953240997 | 0.008076633 | 15329.900433 |
| Engine CPU | 88 | 0.945911660 | 0.013225784 | 5716.855023 |
| Wall | 40 | 0.952709605 | 0.007610077 | 17267.197451 |
| Wall | 56 | 0.958198471 | 0.008842240 | 12790.143544 |
| Wall | 72 | 0.959362791 | 0.007996431 | 15638.949480 |
| Wall | 88 | 0.951859213 | 0.013603725 | 5403.613756 |

| Metric | Complete U lengths | Weighted mean m_w | Q | Q cutoff | Reading |
|---|---:|---:|---:|---:|---|
| Engine CPU | 4 | 0.950211932 | 0.502290219 | 7.81 | THE SAME |
| Wall | 4 | 0.956029710 | 0.518221834 | 7.81 | THE SAME |

Weights are 1/s_L². The weighted mean uses their sum as its denominator. Q sums ((m_L − m_w)/s_L)² across completed lengths.

[T1](sol2/job15/T1/summary.txt) · [T2](sol2/job15/T2/summary.txt) · [U40](sol2/job15/U40/summary.txt) · [U56](sol2/job15/U56/summary.txt) · [U72](sol2/job15/U72/summary.txt) · [U88](sol2/job15/U88/summary.txt) · [V40](sol2/job15/V40/summary.txt) · [V88](sol2/job15/V88/summary.txt)

### T1

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.0026 | 0.9973 |
| 2 | BAAB | 0.9534 | 0.9519 |
| 3 | ABBA | 1.0113 | 1.0107 |
| 4 | BAAB | 0.9313 | 0.9278 |
| 5 | ABBA | 0.9998 | 0.9993 |
| 6 | BAAB | 1.0222 | 1.0234 |
| 7 | ABBA | 1.0158 | 1.0166 |
| 8 | BAAB | 0.9532 | 0.9524 |
| 9 | ABBA | 0.9861 | 0.9878 |
| 10 | BAAB | 1.0788 | 1.0800 |
| 11 | ABBA | 1.0560 | 1.0594 |
| 12 | BAAB | 0.9017 | 0.8955 |
| 13 | ABBA | 1.0871 | 1.0883 |
| 14 | BAAB | 1.0145 | 1.0133 |
| 15 | ABBA | 1.0231 | 1.0259 |
| 16 | BAAB | 0.9955 | 0.9931 |

[Inputs](sol2/job15/T1/inputs.txt) · [Raw runs](sol2/job15/T1/runs.jsonl.txt) · [Summary](sol2/job15/T1/summary.txt) · [Command](sol2/job15/T1-command.raw.txt)

### T2

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.0103 | 1.0118 |
| 2 | BAAB | 1.0476 | 1.0505 |
| 3 | ABBA | 1.0439 | 1.0435 |
| 4 | BAAB | 0.9276 | 0.9261 |
| 5 | ABBA | 1.0758 | 1.0770 |
| 6 | BAAB | 1.0134 | 1.0140 |
| 7 | ABBA | 0.9692 | 0.9687 |
| 8 | BAAB | 0.9437 | 0.9433 |
| 9 | ABBA | 1.0120 | 1.0125 |
| 10 | BAAB | 0.9254 | 0.9236 |
| 11 | ABBA | 1.0204 | 1.0216 |
| 12 | BAAB | 0.9591 | 0.9602 |
| 13 | ABBA | 1.0153 | 1.0130 |
| 14 | BAAB | 0.9606 | 0.9602 |
| 15 | ABBA | 1.0987 | 1.1020 |
| 16 | BAAB | 0.9753 | 0.9754 |

[Inputs](sol2/job15/T2/inputs.txt) · [Raw runs](sol2/job15/T2/runs.jsonl.txt) · [Summary](sol2/job15/T2/summary.txt) · [Command](sol2/job15/T2-command.raw.txt)

### U40

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9608 | 0.9679 |
| 2 | BAAB | 0.9558 | 0.9608 |
| 3 | ABBA | 0.9763 | 0.9817 |
| 4 | BAAB | 0.9141 | 0.9167 |
| 5 | ABBA | 0.9391 | 0.9448 |
| 6 | BAAB | 0.8818 | 0.8843 |
| 7 | ABBA | 0.9391 | 0.9438 |
| 8 | BAAB | 0.9648 | 0.9712 |
| 9 | ABBA | 0.9475 | 0.9553 |
| 10 | BAAB | 0.9699 | 0.9751 |
| 11 | ABBA | 0.9517 | 0.9568 |
| 12 | BAAB | 0.9011 | 0.9058 |
| 13 | ABBA | 0.9616 | 0.9651 |
| 14 | BAAB | 1.0013 | 1.0109 |
| 15 | ABBA | 0.9400 | 0.9479 |
| 16 | BAAB | 0.9503 | 0.9551 |

[Inputs](sol2/job15/U40/inputs.txt) · [Raw runs](sol2/job15/U40/runs.jsonl.txt) · [Summary](sol2/job15/U40/summary.txt) · [Command](sol2/job15/U40-command.raw.txt)

### U56

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.8927 | 0.8979 |
| 2 | BAAB | 0.9333 | 0.9383 |
| 3 | ABBA | 0.9036 | 0.9079 |
| 4 | BAAB | 0.9116 | 0.9143 |
| 5 | ABBA | 0.9414 | 0.9461 |
| 6 | BAAB | 0.9549 | 0.9629 |
| 7 | ABBA | 0.9869 | 0.9945 |
| 8 | BAAB | 0.9759 | 0.9821 |
| 9 | ABBA | 0.9687 | 0.9732 |
| 10 | BAAB | 0.9714 | 0.9745 |
| 11 | ABBA | 0.9487 | 0.9539 |
| 12 | BAAB | 1.0142 | 1.0252 |
| 13 | ABBA | 0.9274 | 0.9316 |
| 14 | BAAB | 1.0006 | 1.0067 |
| 15 | ABBA | 0.9648 | 0.9693 |
| 16 | BAAB | 0.9475 | 0.9529 |

[Inputs](sol2/job15/U56/inputs.txt) · [Raw runs](sol2/job15/U56/runs.jsonl.txt) · [Summary](sol2/job15/U56/summary.txt) · [Command](sol2/job15/U56-command.raw.txt)

### U72

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.8754 | 0.8841 |
| 2 | BAAB | 0.9146 | 0.9194 |
| 3 | ABBA | 0.9972 | 1.0053 |
| 4 | BAAB | 0.9912 | 0.9938 |
| 5 | ABBA | 0.9476 | 0.9552 |
| 6 | BAAB | 0.9594 | 0.9627 |
| 7 | ABBA | 0.9386 | 0.9456 |
| 8 | BAAB | 0.9722 | 0.9808 |
| 9 | ABBA | 0.9541 | 0.9619 |
| 10 | BAAB | 0.9999 | 1.0049 |
| 11 | ABBA | 0.9593 | 0.9664 |
| 12 | BAAB | 0.9431 | 0.9489 |
| 13 | ABBA | 0.9531 | 0.9586 |
| 14 | BAAB | 0.9585 | 0.9669 |
| 15 | ABBA | 0.9717 | 0.9752 |
| 16 | BAAB | 0.9159 | 0.9199 |

[Inputs](sol2/job15/U72/inputs.txt) · [Raw runs](sol2/job15/U72/runs.jsonl.txt) · [Summary](sol2/job15/U72/summary.txt) · [Command](sol2/job15/U72-command.raw.txt)

### U88

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9520 | 0.9570 |
| 2 | BAAB | 0.9414 | 0.9502 |
| 3 | ABBA | 0.9425 | 0.9482 |
| 4 | BAAB | 0.9595 | 0.9666 |
| 5 | ABBA | 0.9757 | 0.9837 |
| 6 | BAAB | 0.9727 | 0.9786 |
| 7 | ABBA | 0.8911 | 0.8963 |
| 8 | BAAB | 0.9040 | 0.9080 |
| 9 | ABBA | 0.9617 | 0.9690 |
| 10 | BAAB | 0.9299 | 0.9369 |
| 11 | ABBA | 0.9104 | 0.9118 |
| 12 | BAAB | 0.9587 | 0.9646 |
| 13 | ABBA | 0.8888 | 0.8917 |
| 14 | BAAB | 0.9714 | 0.9759 |
| 15 | ABBA | 1.1015 | 1.1120 |
| 16 | BAAB | 0.8732 | 0.8793 |

[Inputs](sol2/job15/U88/inputs.txt) · [Raw runs](sol2/job15/U88/runs.jsonl.txt) · [Summary](sol2/job15/U88/summary.txt) · [Command](sol2/job15/U88-command.raw.txt)

### V40

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.0291 | 1.0255 |
| 2 | BAAB | 1.0263 | 1.0197 |
| 3 | ABBA | 1.0214 | 1.0139 |
| 4 | BAAB | 1.1069 | 1.0997 |
| 5 | ABBA | 1.0934 | 1.0856 |
| 6 | BAAB | 1.0454 | 1.0394 |
| 7 | ABBA | 1.0425 | 1.0366 |
| 8 | BAAB | 1.1147 | 1.1100 |
| 9 | ABBA | 1.0896 | 1.0818 |
| 10 | BAAB | 1.0909 | 1.0857 |
| 11 | ABBA | 1.0268 | 1.0166 |
| 12 | BAAB | 1.0607 | 1.0565 |
| 13 | ABBA | 0.9183 | 0.9120 |
| 14 | BAAB | 1.1653 | 1.1582 |
| 15 | ABBA | 1.0459 | 1.0379 |
| 16 | BAAB | 0.9900 | 0.9804 |

[Inputs](sol2/job15/V40/inputs.txt) · [Raw runs](sol2/job15/V40/runs.jsonl.txt) · [Summary](sol2/job15/V40/summary.txt) · [Command](sol2/job15/V40-command.raw.txt)

### V88

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.0451 | 1.0374 |
| 2 | BAAB | 1.0665 | 1.0570 |
| 3 | ABBA | 1.0228 | 1.0138 |
| 4 | BAAB | 1.0496 | 1.0445 |
| 5 | ABBA | 1.0793 | 1.0740 |
| 6 | BAAB | 1.0391 | 1.0325 |
| 7 | ABBA | 0.9885 | 0.9816 |
| 8 | BAAB | 1.0341 | 1.0313 |
| 9 | ABBA | 1.0995 | 1.0923 |
| 10 | BAAB | 1.0266 | 1.0165 |
| 11 | ABBA | 1.0671 | 1.0628 |
| 12 | BAAB | 1.0226 | 1.0142 |
| 13 | ABBA | 1.0687 | 1.0653 |
| 14 | BAAB | 1.0059 | 0.9981 |
| 15 | ABBA | 1.0139 | 1.0057 |
| 16 | BAAB | 1.1285 | 1.1230 |

[Inputs](sol2/job15/V88/inputs.txt) · [Raw runs](sol2/job15/V88/runs.jsonl.txt) · [Summary](sol2/job15/V88/summary.txt) · [Command](sol2/job15/V88-command.raw.txt)

## Facts

- The 8 complete comparisons contain 512 timed runs and 128 warm-ups. The independent readback checks each driver's W signature and recomputes ratios from the run receipts. [Independent readback](sol2/job15/timing_readback.py.txt)
- Procfs verified the supplied arguments, environment and executable inode for 640 of 640 complete raw run records. [Arm inventory](sol2/job15/arms.txt)

## Suspicions

The T pair keeps the executable device and inode fixed and swaps two launch paths. A reproducible difference here would identify a launch-path effect on this VM. T1 and T2 change the pathname characters and length together. Equal path lengths hold the string lengths fixed across each R/K pair, with a fresh file for each arm. [Arm receipts](sol2/job15/arms.txt)

## What this check cannot see

> The PC's Windows loader, its clang 23, its processor with 16 engines playing at once, its trained net (net768 is synthetic), its own self-play openings; other environment sizes than yours.

## What I did not do

The experiment uses the frozen self-play-profiled cloud builds, one pinned CPU and the fixed engine environment. This delivery contains text evidence. [Publication layout](sol2/job15/publication-layout.raw.txt)

## What I am not sure about

The Q statistic compares the completed U means relative to their measured uncertainty. The mechanism behind any launch-path difference and the gain on the owner's production build remain unresolved. W hashes moves and last-info nodes and verifies final soft-node counts as an aggregate.
