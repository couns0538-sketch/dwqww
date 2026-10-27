# Astra A1 — SPRT plan for UCI `HistRework` (2026-10-27)

This job ran **no gate**: no Elo claim. QA owns the gates, assigns the srand values (fresh, never reused) and
the opening start offsets. One option value per gate, the option is set on the candidate only, and A1 lines are
never pooled with each other or with other gates.

## Candidate and pre-gate identity
- **Candidate exe.** A PC box-recipe build (`build_pc.sh`, the AL1 lock flags) of engine commit `a8b63aae` on
  `opus-sol-A1`.
  - This job's build: `forge_a1_a8b63aa.exe`, sha256
    `84ca028af085325607325557d66f39c4c74fadd319a0966c3345ef382cb28b26`, FMA 0.
  - A rebuild differs only in the PE timestamp/checksum bytes.
- **Base exe.** The AL1 s198 lock `forge_h256_s198.exe`, sha256
  `5d4df7f1be51b083e0719266e55367577ed580a509a12196d62c0a368826a5b1`, no options.
- **Before the first game, all of these must hold:**
  1. `uci` lists `option name HistRework type spin default 0 min 0 max 3`.
  2. Candidate with no options: `uci_check.py --full` prints ALL OK:
     - bench d11/13/16/20/22 = 312866 / 862329 / 3024920 / 12389307 / 34048354;
     - perft5 4865609, kiwipete 193690690.
  3. Candidate with the gate value: bench equals the ON pins below (Threads 1, Hash 16, OwnBook false,
     `setoption name HistRework value <v>`, then `bench <d>`; `tools/bench_sweep.py` does exactly this).
  4. The candidate's engine log of the gate shows `setoption name HistRework value <v>`; otherwise the gate
     is VOID.

| HistRework | d11 | d13 | d16 | d20 | d22 |
|---|---|---|---|---|---|
| 0 (= lock) | 312866 | 862329 | 3024920 | 12389307 | 34048354 |
| 1 | 373261 (+19.3 %) | 1043893 (+21.1 %) | 3399770 (+12.4 %) | 13180132 (+6.4 %) | 35699757 (+4.9 %) |
| 2 | 320427 (+2.4 %) | 881902 (+2.3 %) | 3041041 (+0.5 %) | 12218938 (−1.4 %) | 28571078 (−16.1 %) |
| 3 | 336192 (+7.5 %) | 869621 (+0.8 %) | 3052885 (+0.9 %) | 15664938 (+26.4 %) | 35705218 (+4.9 %) |

Source: `logs/bench_sweep_full.log`. No value is near the A1 blowup flag (1.5x).

## Gate order

| gate | line | when | why | flags |
|---|---|---|---|---|
| **G-A1a** | `option.HistRework=2` | first | See the reasons below. | LONGER-TC CONFIRM on H1 (d22 −16.1 %, a depth-growing node change) |
| G-A1b | `option.HistRework=3` | only if G-A1a is H1, or capped with Elo > 0 | The next tune step toward the full twin: the twin replaces the lock butterfly term in the read, joint weight 100. | LONGER-TC CONFIRM on H1 (d20 +26.4 %); watch TL/stalls |
| G-A1c | `option.HistRework=1` | only if G-A1a is capped or H0 with Elo <= 0 | The conservative step: 50 % read share, joint weight 50. | Fails the crew screen (d13 +21.1 %, d16 +12.4 %): QA may skip it; LONGER-TC CONFIRM on H1 |

Why G-A1a gates `HistRework=2` first:
- It has the smallest node change at d11-d20.
- It is the only step that passes the crew node screen (at most +10 % at d13/d16) without a depth flag
  before d22.
- It is the middle step of both parts (75 % threat-keyed read, joint weight 75), so its verdict tells
  which neighbour to try.

Stop rules:
- **G-A1a H0.** Run G-A1c only if QA wants the conservative end. Do not run G-A1b.
- **Two consecutive A1 lines flat (|Elo| below the error).** Stop gating A1 values. The follow-up is the
  split below, not a pooled rerun.

## Settings (every A1 gate)
- **Engine.** fastchess 1.8.2; 10+0.1 (`timemargin=1000` as in the frozen AL1 gate settings);
  Threads=1, Hash=16, OwnBook=false on both sides.
- **Openings.** `8moves_v3.pgn`, `order=random`, start offset from QA; `-repeat`, games 2 per opening.
- **SPRT.** Normalized [0, 10], alpha = beta = 0.05; 1500-game cap.
- **Machine.** Concurrency 8, BelowNormal, CPUs 4-15, `-recover`, as in G124/G125 (QA may change it).
- **Records.** QA records PC nps (paired bench d20) for every line, as for every search change.
- **Reading.** Read the result from RESULT.md / RUN_INFO.json: the opponent field, the pentanomial counts,
  the LLR. Do not trust folder names.

## Longer-TC confirm (only after an H1 at 10+0.1)
- **40+0.4**, otherwise the same settings: SPRT normalized [0, 10], a = b = 0.05, 1500-game cap, fresh srand
  and start offset.
- House rule (OPUS_TEST_PLAN.md): "EVAL changes that hit H1 get a confirm at 40+0.4 before lock". A1 changes
  the static-eval correction as well as move ordering.
- Every A1 line carries a node change above 10 % at d20 or d22, so the confirm is required for each of them,
  not optional.

## Afterwards
- **H1 at 10+0.1 and H1 at 40+0.4.** Lock candidate, under the usual lock rules:
  - fresh gate H1;
  - 0 TL and 0 crashes;
  - nps recorded;
  - game-time tactics not worse (WAC 300 at 1 s, as the contcorr CR did).
- **Capped positive without H1.** Report Elo ± error, LLR and the pentanomial counts. The next step is the
  neighbouring tune value from the table, never a rerun of the same value with a new seed and pooling.
- **Split follow-up**, if A1 stays flat or splits by part:
  - this needs a reviewed code change that exposes the two weights (threat read quarters q in 0..4; joint
    weight w in 0..300, both inside the overflow proof) as unlisted tunables;
  - then gate "twin only" (w = 0) and "joint only" (q = 0) separately.
  - Not part of this branch.
- **Time loss or stall.** Any time loss or bestmove later than movetime + 1 s pauses that gate and goes back
  with the FEN.
