# REPORT_check_S-F3 — CONFIRMS seat 06's S-F3 (area 6), seat 16

**What was asked:** check seat 06's S-F3 from its command alone: "every left-right asymmetry in the
hand-written eval comes from the Texel-tuned PSQT table and from no other term: 98.2% of G positions differ
left-right, and 0 of 334 differ once only the PSQT table is symmetrised (perft 5 unchanged at 4,865,609)".

**The answer:** CONFIRMED, and it corrects MY OWN earlier number. I symmetrised every PSQT entry myself
(`symmetrise_psqt.py` averages each `(rank, file)` with `(rank, 7-file)`, MG and EG separately), built a
scratch copy, and ran MY OWN left-right harness unchanged on the same 334 positions:

```
                        hce differs     nnue differs    total differs
unpatched 6b98f217      328 of 334      327 of 334      334 of 334
PSQT symmetrised          0 of 334      327 of 334      327 of 334
```

HCE differences go to **exactly 0**; the residual NNUE differences are seat 06's S-F5/S-F6 territory, not the
hand-written eval. `go perft 5` is unchanged at 4,865,609 on the patched build (3 runs).

**How sure:** high. This is a decisive experiment, not a correlation: a before/after on the same harness and
the same positions, with the only change being the table. My job-2 note that "PSQT explains only r = 0.35"
was a fault in MY predictor (I compared a raw PSQT-sum delta against a phase-blended evaluation — MG and EG
are interpolated by game phase, so a MG-only sum cannot track it). S-F3 is right and my predictor was wrong;
I record that plainly.

## Honesty numbers

```
unpatched build  /home/ubuntu/builds/bld-release/forge
  sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
  bench 11 312866  bench 13 862329  bench 16 3024920  perft 5 4865609   (all equal)
patched build    /home/ubuntu/builds/bld-sympsqt/forge
  sha256 a22075dd34793025e6503ec361ee30981fd2b1b69d0a389430f9e72bbe02b7db
  bench 11 328417  bench 13 881261  bench 16 3346671  perft 5 4865609
```

The patched build's BENCH numbers differ from the pins — the evaluation feeds pruning, so a changed eval
changes the bench tree. That is expected and is why the patched build is used only for eval/perft statements,
never for a bench-based comparison. `raw/PATCHED_HONESTY.txt` holds this. The patch is committed as TEXT only
(`psqt_symmetry.patch.txt`, 368 lines changed, applies with `patch -p1` without fuzz — verified against a
fresh copy of the file from 6b98f217).

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| my own PSQT symmetriser | done | `symmetrise_psqt.py` | 6 piece types, 368 table lines rewritten |
| patch as text, applies clean | done | `psqt_symmetry.patch.txt` | `patch -p1 --dry-run` → "checking file ... PATCH_APPLIES_CLEAN" |
| build the patched engine (scratch worktree outside the repo) | done | `raw/PATCHED_HONESTY.txt` | builds, perft 5 = 4,865,609 |
| same harness, same 334 positions, unpatched vs patched | done | `raw/G_sympsqt.tsv` vs `../job2/raw/G_lr.tsv` | hce 328 → 0; nnue 327 → 327 |
| perft 5 unchanged, 3 runs | done | `raw/PATCHED_HONESTY.txt` | 4,865,609 each time |
| the claim "and from no other term" | done | `raw/G_sympsqt.tsv` | after symmetrising, every remaining left-right difference is nnue-only: hce differs 0 of 334 |
| exactly the 6 positions that were already hce-equal | done | see below | 6 of 334, listed |

## The 6 positions whose hce was already left-right equal on the unpatched build

```
R3b3/p3r1pp/2p2p2/2N1k3/2p1NP2/4P3/P4KPP/8 b - - 0 1   total -451 vs -417  (nnue only)
6k1/p5p1/4P3/5pP1/8/6NP/P1r1b3/R5K1 b - - 0 1          total  -61 vs  -53  (nnue only)
8/8/1N6/p1p5/K1P2k2/PP6/1r6/8 b - - 0 1                total   99 vs   49  (nnue only)
1K6/4n3/4k3/8/8/N7/8/8 b - - 0 1                       total   -1 vs   10  (nnue only)
2r1r3/pp3k2/q3ppp1/3p1n1p/1P1P3P/P2P3Q/R3NPP1/4R1K1 b - - 0 1  total 142 vs 179  (nnue only)
8/1R6/8/7K/2kp4/8/2P2r2/8 b - - 0 1                    total  186 vs  159  (nnue only)
```
So 328 + 6 = 334 — the arithmetic closes exactly, which is a second independent sign that the only HCE
asymmetry is the PSQT table.

## Findings

`S-C3 | CONFIRMS S-F3 | check_S-F3/raw/G_sympsqt.tsv (again: `python3 job2/mirror_lr.py ~/builds/bld-sympsqt/forge job2/G_nocastle.fens /tmp/o.tsv /tmp/m.txt`) | symmetrising the PSQT table (my own script, text patch applies with patch -p1) takes hce left-right differences from 328/334 to exactly 0/334, perft 5 unchanged at 4,865,609, and the remaining 327 differences are nnue-only; also CORRECTS my job-2 line that PSQT explained only r=0.35 — that was my MG-only predictor, the engine blends MG/EG by phase |`

## Suspicions, not proven

- Whether the NNUE residual left-right difference (327/334) is intended: the net is a trained function of
  the position, and a left-right flip is a different position, so I expect it is; but "the net is not
  file-symmetric" is a property of the weights, not something I measured separately.

## What I did NOT do

- Did not test the patched build on R positions (only G's 334) — the claim is a property of the table, and
  334 positions with the change landing exactly on 0 is decisive enough for the claim as stated.
- Did not commit any engine source file: only a `.patch.txt`.
- Did not investigate the NNUE side (seat 06's S-F5/S-F6 cover it).

## What I am NOT sure about

- Whether seat 06's own symmetrisation used the same averaging rule as mine. Its result (0 of 334) and mine
  (0 of 334) agree, but I did not read its `symmetrise_psqt.py` — deliberately, since the rules say to
  reproduce from the command alone.

## Times

`stamps.txt`, every line a `date -u`.

## Last command output

(pasted into `last_cmd.txt` at commit time)

## Last command output

```
$ git status --short
 M check_S-F3/stamps.txt
?? REPORT_check_S-F3.md
?? check_S-F3/last_cmd.txt
?? check_S-F3/patched_honesty.sh
?? check_S-F3/psqt_symmetry.patch.txt
?? check_S-F3/raw/
?? check_S-F3/symmetrise_psqt.py
$ ls
check_S-F1
check_S-F2
check_S-F3
FINDINGS.md
honesty.sh
HONESTY.txt
job0_honesty
job1
job2
REPORT_check_S-F1.md
REPORT_check_S-F2.md
REPORT_check_S-F3.md
REPORT_job1.md
REPORT_job2.md
SEAT.txt
STATUS.md
$ ls check_S-F3
last_cmd.txt
patched_honesty.sh
prediction.txt
psqt_symmetry.patch.txt
raw
stamps.txt
symmetrise_psqt.py
$ ls check_S-F3/raw
bench_11.raw
bench_13.raw
bench_16.raw
go_perft_5.raw
G_sympsqt.meta
G_sympsqt.summary
G_sympsqt.tsv
meta.txt
PATCHED_HONESTY.txt
```
