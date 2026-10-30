"""R9: compose opus_r9/REPORT.md from the committed evidence (run from the worktree root).
usage: python -I -B opus_r9/tools/write_report.py [--final]
Reads opus_r9/results/{sanity2,sanity3,stc1}/r9_params.json (when present), opus_r9/logs/param_table.md and the git log
of the branch for the time span. Without --final the STC section says the run is still going."""
import json
import subprocess
import sys
from pathlib import Path

R = Path("opus_r9")
final = "--final" in sys.argv
EXE_SCRATCH = r"F:\opus_scratch\r9\build\forge_r9_c.exe"
EXE_SHA = "cad98f31562734124527f3d06a39cb01114d60e20289bea3f007cf3b7617b9e3"


def load(name):
    p = R / "results" / name / "r9_params.json"
    return json.loads(p.read_text(encoding="ascii")) if p.exists() else None


def git(*args):
    return subprocess.run(["git"] + list(args), capture_output=True, text=True).stdout.strip()


s2, s3, stc = load("sanity2"), load("sanity3"), load("stc1")
commits = git("log", "--format=%ci", "3d111088..HEAD").splitlines()
first, last = (commits[-1], commits[0]) if commits else ("?", "?")
table = (R / "logs" / "param_table.md").read_text(encoding="utf-8") if (R / "logs" / "param_table.md").exists() else ""


def prow(res, name):
    p = next(x for x in res["params"] if x["name"] == name)
    return p


lines = []
title_state = "DONE" if final and stc else "IN PROGRESS"
lines += [f"# R9 SPSA search-parameter tuning for Forge — {title_state}", "",
          "Branch `opus-r9-spsa` = AL1 lock `d4f4312` + CI baseline `0d99f02` + R9 commits. PC clock times. Machine exclusive:",
          "no (PC gates, live self-play and the NNUE trainer ran beside it; the user paused self-play at about 23:30).",
          "**No Elo claims:** only QA's gate can show whether the tuned values are better.", ""]
lines += ["## Acceptance", "| step | result | evidence |", "|---|---|---|",
          "| 1 parameters behind one `R9Tune` switch, default off | 74 tunables (the lock's 51 `forge::tune` constants + 23 former literals) as advertised spin options with the lock values as defaults. `R9Tune` off: bench **312866 / 862329 / 3024920 / 12389307 / 34048354, perft5 4865609** (and kiwipete 193690690) = ALL OK; `R9Tune` on at the defaults: ALL OK too (the former literals are reproduced exactly); off + a changed tunable: bench unchanged; on: 58 of 74 move bench 11 by themselves (time-manager parameters cannot move a fixed-depth bench; the rest need larger values or are off in the lock) | `opus_r9/logs/identity_off_c.log`, `identity_on_defaults_c.log`, `option_check_c.log/.json`, `option_check_b_probes.log` |",
          "| 1 tests | box build 0 warnings, FMA 0; CMake 30 targets + CTest 14 tests: only the 4 known `forge_tests` lines; opus-ci green on `8856be4a` and `22b1f2ba` (release ALL OK, ASan/TSan KNOWN-FAILURE CHECK: PASS, TSan 0 reports) | `opus_r9/logs/ctest_c1.log(.known)`, runs 40932114844, 40935706032 |",
          "| 2 own SPSA tuner driving fastchess | `opus_r9/tuner/r9_spsa.py` (Fishtest-style schedule counted in game pairs, values rounded to the engine's integers, append-only resumable state, `history.csv`, `tuner.log`, every game kept as PGN, STOP file, load governor), report with a null-gradient noise level per parameter, trajectory chart; ideas only, sources in `IDEA_SOURCE.md` | `opus_r9/tuner/`, `opus_r9/IDEA_SOURCE.md` |",
          "| 2 tests | simulated matches with a known optimum: up z +8.5, down z -8.4, at-optimum within 3 sigma, stopped+resumed == uninterrupted; real games: every sanity2 result re-counted from the PGNs (0 attribution mismatches), option values checked in the engine logs | `opus_r9/tuner/test_r9_spsa_sim.py`, `opus_r9/logs/tuner_sim_test_trajectories.svg` |"]
if s2 and s3:
    a, b = prow(s2, "LmrQuietDivisor"), prow(s3, "LmrQuietBase")
    ca, cb = prow(s2, "HistoryMalusPercent"), prow(s3, "HistoryMalusPercent")
    lines.append(f"| 3 sanity: one parameter set wrong | both runs moved the wrong parameter **toward its lock value**: LmrQuietDivisor {a['start']:g} -> {a['end']:.1f} (lock 220, z {a['z']:+.2f}, {s2['pairs']} pairs), LmrQuietBase {b['start']:g} -> {b['end']:.1f} (lock 85, z {abs(b['z']):+.2f} toward it, {s3['pairs']} pairs); neither beyond 2 sigma alone, combined z {(a['z'] + abs(b['z'])) / 2 ** 0.5:.2f} (one-sided p about 0.03); controls (HistoryMalusPercent at its lock value) z {ca['z']:+.2f} and {cb['z']:+.2f} | `opus_r9/results/sanity2/`, `opus_r9/results/sanity3/` (tables + charts) |")
if stc:
    real = [p for p in stc["params"] if p["likely_real"]]
    lines.append(f"| 4 real run, STC 8+0.08 | {stc['pairs']} game pairs ({stc['W'] + stc['L'] + stc['D']} games) from the lock values, 16 parameters; {len(real)} moved beyond 2 sigma | `opus_r9/results/stc1/`, `opus_r9/runs/stc1/` |")
    lines.append("| 5 deliver | `opus_r9/results/stc1/r9_tuned.ini` + option string, the table below, QA gate line below | this report |")
else:
    lines.append("| 4 real run, STC 8+0.08 | RUNNING (`F:\\opus_scratch\\r9\\runs\\stc1`, until 04:45) | `opus_r9/runs/stc1/` (snapshots every 10 min) |")
    lines.append("| 5 deliver | after the run | |")
lines.append("")
if s2 and s3:
    lines += ["## Sanity runs (4+0.04, Threads 1, Hash 16, 2 pairs per batch)",
              f"- sanity2 (`configs/sanity.json`): LmrQuietDivisor started at 120 (lock 220). {s2['pairs']} pairs, +{s2['W']} -{s2['L']} ={s2['D']}"
              f" ({100 * s2['D'] / (s2['W'] + s2['L'] + s2['D']):.0f}% draws). It waited for CPU from 20:56 to 23:31 under the first 70% cap.",
              f"- sanity3 (`configs/sanity3.json`): LmrQuietBase started at 250 (lock 85, +1.65 plies of reduction on every late quiet"
              f" move), larger perturbation. {s3['pairs']} pairs, +{s3['W']} -{s3['L']} ={s3['D']} ({100 * s3['D'] / (s3['W'] + s3['L'] + s3['D']):.0f}% draws).",
              "- Reading: the direction is right in both runs, the size is not beyond the noise band of 200-240 pairs. Games of",
              "  nearly equal engines at 4+0.04 end drawn 72-75% of the time, so each pair carries little information; the same limit",
              "  applies to the STC run (see below). The update rule itself is proven by the simulated test (z +-8.5).", ""]
if stc:
    lines += ["## STC run: start, end, move, noise (16 parameters, from the lock values)", "",
              f"{stc['pairs']} pairs, +{stc['W']} -{stc['L']} ={stc['D']}; noise sigma = the spread this run would show with no true"
              " gradient; |z| >= 2 = likely real (with 16 parameters about 0.8 pass by chance).", "",
              "| parameter | start | end | end (int) | move | move / c_end | noise sigma | z | halves | likely real |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for p in stc["params"]:
        lines.append(f"| {p['name']} | {p['start']:g} | {p['end']:.2f} | {p['end_int']} | {p['move']:+.2f} | {p['move_c_end']:+.2f} |"
                     f" {p['sigma']:.2f} | {p['z']:+.2f} | {'same way' if p['same_way'] else 'mixed'} | {'yes' if p['likely_real'] else 'no'} |")
    changed = [p for p in stc["params"] if p["end_int"] != int(round(p["start"]))]
    real = [p for p in stc["params"] if p["likely_real"]]
    draws = 100 * stc["D"] / (stc["W"] + stc["L"] + stc["D"])
    top = max(stc["params"], key=lambda p: abs(p["z"]))
    if not real:
        lines += ["", f"**Verdict: no parameter moved beyond its noise.** 0 of 16 reached |z| >= 2 (about 0.8 would by chance with no",
                  f"true gradient at all); the largest was {top['name']} (z {top['z']:+.2f}). At 8+0.08 with {draws:.1f}% draws,",
                  f"{stc['pairs']} pairs cannot separate these moves from noise: the lock values may sit near a local optimum for this",
                  "TC, or the gradients are too small for this many games. The all-changed set below is a noise-level drift: QA can",
                  "gate it, but a null result is the expected outcome. The likely-real set is empty (it is the lock's search), so",
                  "there is no second gate. Mid-run (01:55) HistoryMalusPercent stood beyond 2 sigma and ended at z "
                  f"{prow(stc, 'HistoryMalusPercent')['z']:+.2f}: mid-run z values are not evidence.",
                  "Next run if wanted: 3,000+ pairs, or 4-6 parameters with larger perturbations, same TC."]
    opt_all = " ".join(["option.R9Tune=true"] + [f"option.{p['name']}={p['end_int']}" for p in changed])
    opt_real = " ".join(["option.R9Tune=true"] + [f"option.{p['name']}={p['end_int']}" for p in real])
    lines += ["", "## Tuned option sets", "",
              f"All changed values (`opus_r9/results/stc1/r9_tuned.ini`, `r9_tuned_options.txt`): `{opt_all}`", "",
              f"Only the likely-real ones: `{opt_real}`", "",
              "## QA gate line (tuned options vs the same exe at defaults, SPRT [0,10] nElo, cap 3000)", "",
              f"Engine: `{EXE_SCRATCH}` (sha256 `{EXE_SHA}`), built from this branch head with the box recipe; QA copies it to its",
              "bin folder. Settings as the PC queue's current gates (tc 10+0.1, Threads 2, Hash 16, OwnBook false, 8moves_v3.pgn, conc 4):", "",
              "```",
              f"fastchess.exe -engine name=r9_tuned cmd=<bin>\\forge_r9_spsa_cad98f31.exe option.Threads=2 option.Hash=16 option.OwnBook=false {opt_all}"
              " -engine name=r9_default cmd=<bin>\\forge_r9_spsa_cad98f31.exe option.Threads=2 option.Hash=16 option.OwnBook=false"
              " -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\\Users\\Administrator\\grok-pc\\coder-fuzz\\8moves_v3.pgn"
              " format=pgn order=random start=<queue> -srand <queue> -games 2 -repeat -rounds 1500 -concurrency 4"
              " -sprt elo0=0 elo1=10 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -pgnout file=<gate>.pgn",
              "```", "",
              "The default side is the same exe with `R9Tune` off (its search is the lock's). "
              + ("A second, optional gate with only the likely-real set uses the same line with the shorter option list."
                 if real else "No second gate: the likely-real set is empty."), ""]
lines += ["## Load and the governor",
          "- 19:50-23:30: the PC sat at 72-82% CPU without this job (gate conc 4 x Threads 2 = 8.0 CPUs, live self-play 2.1, NNUE",
          "  trainer 1.3); under the first 70% cap no game could run (the governor waited, sanity2 waited 8,820 s).",
          "- 23:3x: the user raised the cap: start a batch while the load without the tuner is <= 80%, play as many games as keep",
          "  the total <= 90% (at most 4, BelowNormal, CPUs 0-3), pause between batches if the total stays above 90% for 60 s or",
          "  free RAM < 8 GB (never kill). The user paused self-play at about 23:30; the gate ended at its 3,000-game cap at 00:10.",
          "- Every batch records the load it started at, its concurrency and what it saw while it played (`iterations.jsonl`).",
          "- STC batches before 03:21 (batch 0 at 00:12, the rest from 00:53): 143, 133 at concurrency 4 and 10 at 3, no wait.",
          "  03:21-04:46: the R10 job (branch `opus-r10-halfka`, CPUs 4-11, BelowNormal) ran beside it and the governor gave way as",
          "  designed: 65 batches at 4 / 3 / 2 = 29 / 19 / 17 and one 60 s wait (04:30, load 83% without the tuner). The run",
          "  stopped at its 04:45 deadline with 832 of the 1,200 planned pairs.", ""]
lines += ["## Findings", "- The lock already kept 51 search constants in `forge::tune`, accepted silently by `setoption`; R9 makes them",
          "  advertised options (the gate runner checks that options it sets are advertised) and gates them behind `R9Tune`.",
          "- Truncating fractional LMR adjustments made a sub-ply change invisible unless the sum crossed a whole ply; R9 rounds to",
          "  the nearest ply (identical for the lock's whole-ply values).",
          "- `AspirationGrowPercent = 0` with `AspirationGrowAdd = 0` (inside the old-style ranges) would never widen the window: R9",
          "  floors them at 10 and 1.",
          "- Short SPSA runs at fast TCs are noise-limited (72-75% draws at 4+0.04): read every move against its noise sigma; a gate",
          "  of many noise-sized moves of near-optimal parameters can cost Elo, so the likely-real subset is the safer second gate.", ""]
lines += ["## The 74 parameters", "", table]
lines += [f"## Time", f"Commits on this branch after the base: {len(commits)}, {first} .. {last} (git log)."
          " The work before them (R7/R8 fixes) is on `opus-r7-speed` and `opus-r8-datagen`.", ""]
(R / "REPORT.md").write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
print(f"REPORT.md written ({'final' if final else 'in progress'}; sanity {'yes' if s2 and s3 else 'no'}, stc {'yes' if stc else 'no'})")
