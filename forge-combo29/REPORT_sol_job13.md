# Sol — Job 13 EvalSwingMult replication and dose

## Step 0 and gates

1. **Step 0 passed all eight fresh-process pins.** Defaults gave 312866, 862329 and 3024920 bench nodes, and 4865609 at perft 5. S14 gave 242796 and 656517. PC20 gave 278024 and 587276. The unchanged counting executable SHA-256 was `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333`. The verified official build printed `fastchess alpha 1.8.3 20261107-d7b47e8`. The official book SHA-256 was `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. [Step 0 raw output](sol/job13/step0-count.raw.txt) · [Build and opening receipts](sol/job13/build.txt)
2. **K2 passed 50/50.** With plain PC20 on both sides at 20,000 nodes, every pair had the same FEN and move list, reversed engine colors and 1–1 points. W-L-D was 23–23–54, with pentanomial `[0, 0, 50, 0, 0]` in 100 games. [K2 PGN](sol/job13/raw/K2.pgn) · [K2 output](sol/job13/raw/K2.out)
3. **C2 passed.** At 10,000 versus 20,000 nodes per move with otherwise plain PC20, A scored 17–115–68 in 200 games. Pentanomial `[29, 44, 24, 2, 1]`, Elo −186.25 and 95% interval [−223.98, −148.52]. The score met the −100 control and its upper bound was below zero. [C2 PGN](sol/job13/raw/C2.pgn) · [C2 output](sol/job13/raw/C2.out) · [Gate readback](sol/job13/gates-K2C2.txt)

The [prediction](sol/job13/prediction.txt) was the sole file in commit `a4370619e26830503283f0269de5f6acc19bda35`. Both gates passed before that commit and both slots started after the push. K2 and C2 used four workers each. Slot 1 held two workers for E2. Slot 2 used two for E3k and then two for E6. Fastchess printed a rating block at every completed pair in the three measured matches. [UTC stamps](sol/job13/stamps.txt)

## Prediction grades

| Forecast | Guess | Observed | Grade |
|---|---:|---:|---|
| E2 Elo | +7.00 | -4.52 | KILLED (sign) |
| E3k Elo | +6.00 | +14.60 | KILLED |
| E6 Elo | +11.00 | +16.69 | KILLED |
| Pooled interval excludes zero | yes | no | KILLED |

4 KILLED, 0 survive, 0 ungraded.

## Table H. EvalSwingMult paired-game results

W-L-D is from A's perspective. Displayed 95% intervals use the fastchess pentanomial Elo ± halfwidth convention. A completed pair supplies both games.

| Match | Status | Games | W-L-D | Pentanomial | Elo [95%] | Elo / 173.89 |
|---|---|---:|---|---|---|---:|
| E | complete | 2000 | 555-499-946 | 35, 234, 411, 280, 40 | +9.73 [+0.02, +19.44] | +0.0560 |
| E2 | complete | 2000 | 530-556-914 | 51, 256, 399, 256, 38 | -4.52 [-14.55, +5.51] | -0.0260 |
| E + E2 pooled | complete: interval reconstructed from summed penta counts | 4000 | 1085-1055-1860 | 86, 490, 810, 536, 78 | +2.61 [-4.38, +9.59] | +0.0150 |
| E3k | complete | 2000 | 723-639-638 | 78, 205, 377, 235, 105 | +14.60 [+2.95, +26.25] | +0.0840 |
| E6 | complete | 1000 | 304-256-440 | 21, 110, 205, 128, 36 | +16.69 [+2.02, +31.36] | +0.0960 |

Pooled interval excludes zero: no.

## Facts

- All five matches finished before 07:19:53Z. E2 and E3k launched in the same UTC second, 06:35:06Z. E3k finished at 06:41:13Z and E6 took its slot in that same second. E6 finished at 06:59:55Z and E2 at 07:12:11Z. Each scored game belonged to a complete pair. [Independent counts and checks](sol/job13/independent-Job13.txt)
- At 20,000 nodes and dose 3, the second seed gave −4.52 Elo and its interval included zero. The two seed counts summed to W-L-D 1085–1055–1860 and pentanomial `[86, 490, 810, 536, 78]` in 4,000 games. The pooled Elo was +2.61 with interval [−4.38, +9.59]. The two seeds each had 1,000 unique opening FENs and shared two of them. The requested pool includes both encounters.
- Dose 3 at 2,000 nodes gave +14.60 Elo [+2.95, +26.25] in 2,000 games. Dose 6 at 20,000 nodes gave +16.69 [+2.02, +31.36] in 1,000 games. Each had a positive interval on its own seed. All four preregistered guesses missed the specified grading rule. [PGNs and raw fastchess output](sol/job13/raw)

## Suspicions

Dose 3 may help more at the 2,000-node budget. The stronger dose may behave differently at the hard budget. These comparisons leave budget, dose and seed effects partly entangled.

## What I did not do

All matches ran on the unchanged Forge counting build in Codex Cloud. Engine source, weights, training and the owner's running tune were outside this job.

## What I am not sure about

Job 12 E was selected after screening settings. E2 is a new seed with the same dose and nodes. The pool includes the selected run, so the E2 row carries the independent replication result on its own. E6 and E2 compare different doses against zero on different opening-order seeds. A direct 6-versus-3 match and transfer to another evaluation remain unmeasured.

## Reproduction

Both engines used Forge PC r15 at `6b98f2170a3210e71beed04bbd2553972c253ed7`, GCC 14.2.0, CMake 4.2.3 Release, libstdc++ 6.0.33, glibc 2.41, x86-64-v4 and `FORGE_MATE_ALPHA_GUARD=1`. Each side used PC20, one thread, Hash 16 MiB, one PV, OwnBook false and built-in AL1 s198 with weights-source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. A's effective override was `EvalSwingMult=3` in E2 and E3k and 6 in E6. B retained 0. Each preflight saved all answer lines through `readyok`. [Match sidecars](sol/job13/raw) · [Forge build](REPORT_sol_job4.md)

The official fastchess build and EPD were reused and rehashed. All matches paired each randomly selected FEN in both colors, with seeds 7111 through 7115, fixed nodes and a 300-move limit. E and E2 used the same match protocol at 20,000 nodes with separate seeds. E3k used `go nodes 2000` for both engines. The measurement ceiling was 07:19:53Z, 50 minutes from the claim. [Clock and slot records](sol/job13/stamps.txt) · [Job 12 protocol](REPORT_sol_job12.md)

From `forge-combo29/sol/job13`, with Python 3 and python-chess 1.11.2, these commands regenerate the checks, match totals and prediction grades.

```sh
python3 analyze_matches13.py gates raw
python3 analyze_matches13.py table raw --job12-raw ../job12/raw --prediction prediction.txt
```

[Complete PGN and output readback](sol/job13/readback.txt) · [Precommit tree readback](sol/job13/precommit-readback.txt)
