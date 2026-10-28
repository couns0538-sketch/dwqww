# A1 Correction-history / history rework (UCI `HistRework`, default 0) — DONE

Branch `opus-sol-A1` = AL1 s198 lock `d4f4312` + CI baseline `0d99f02` (cherry-picked as `1aa5d209`) + 3 commits (+ the
REPORT commit):

| commit | content |
|---|---|
| `a8b63aae` | Engine, test and tools:<br>- `include/forge/hist_rework.hpp` (new)<br>- `include/forge/search.hpp`, `src/search.cpp`, `src/uci.cpp`<br>- `tests/hist_rework_tests.cpp` (new) and `CMakeLists.txt`<br>- `opus_round1/sol_A1/tools/*`, `tsan_extra.sh` |
| `e61d6688` | Evidence: design note, SPRT plan, patch, IDEA_SOURCE, README, PC step logs, FILES.txt, SHA256SUMS [skip ci] |
| `21722b24` | CI evidence of run 40515121020, refreshed FILES.txt and SHA256SUMS [skip ci] |

No gate was run. Strength is UNPROVEN; there is no Elo or speed claim. Work and results by a sub-agent; this report text
is its hand-back.

**What it does.** One new UCI option: `option name HistRework type spin default 0 min 0 max 3`.
- **0 (default):** the lock search. Every new statement sits behind `search_options::hist_rework != 0`.
- **1, 2, 3 (tune steps):**
  - **Threat-keyed quiet history.** A second butterfly table indexed by `[side][from attacked by a lesser enemy piece][to attacked by a lesser enemy piece][from][to]`.
    - "Lesser" means enemy pawns for pawn/knight/bishop moves, plus minors for rooks, plus rooks for queens, and nothing for the king.
    - It learns the same bonuses and maluses as the lock table, using the lock's gravity rule (`apply_history`).
    - `quiet_history` reads it as 50 / 75 / 100 % of the butterfly term, so the ±16384 scale is unchanged.
  - **Correction blend.** A third correction table keyed by pawn structure × non-pawn material (Zobrist pawn key mixed with the N/B/R/Q counts per colour).
    - Weight 50 / 75 / 100 (×0.01).
    - It learns the lock's residual step with a gravity update: `e += s − e·|s|/8192`.
    - The lock's pawn and material tables keep their exact rules.

| # | acceptance line | result | evidence (`opus_round1/sol_A1/`) |
|---|---|---|---|
| 1 | One new option, default OFF | PASS: listed by `uci` | `logs/uci_options.log` |
| 2 | OFF lock identity (`uci_check --full`) | PASS, ALL OK on the PC: bench 312866 / 862329 / 3024920 / 12389307 / 34048354, perft5 4865609, kiwipete 193690690 | `logs/uci_check_full_off.log` (exe sha256 84ca028a…), `logs/uci_check_full_off_v1.log` |
| 3 | FMA 0 | PASS on the PC exe and the Linux CI exe | `logs/build_final.log`, `logs/ci/.../opus-ci-release/identity.log` |
| 4 | CTest known-only | PASS: 14/15; only `forge_tests` fails, with its 4 known lines; known-failure check PASS | `logs/ctest_release.log`, `logs/ctest_release_known_failures.log` |
| 5 | CI release / ASan / TSan green | PASS, run **40515121020** success:<br>- release job 122226949280: Linux ALL OK, FMA 0<br>- asan job 122226950606: no sanitizer report<br>- tsan job 122226950297: 0 reports, hook PASS | `logs/ci/run40515121020_opus-ci/` |
| 6 | Every ON value changes nodes (d11 / d13) | PASS: OFF 312866 / 862329; value 1 = 373261 / 1043893; value 2 = 320427 / 881902; value 3 = 336192 / 869621 | `logs/bench_sweep_full.log` |
| 7 | ON 5-depth sweep, no blowup (> 1.5x) | PASS: highest ratio 1.264 (value 3, d20), lowest 0.839 (value 2, d22). Node table below | same |
| 8 | UBSan clean with ON at max | PASS:<br>- CI: ASan+UBSan (recover off) ran the new test, including searches at `HistRework=3` with HistoryBonusMax / Quadratic / Linear = 10000 / 100 / 500 and MaterialCorrectionWeight = 300<br>- PC: MinGW trap-mode UBSan build. OFF `uci_check` ALL OK; bench d11/13/16 at value 3 with those maxima; unit test 0 failures<br>- A positive control shows the trap build dies on a signed overflow that the plain build silently wraps | `logs/ci/.../opus-ci-asan/`, `logs/ubsan/`, `logs/ubsan_positive_control.log` |
| 9 | Unit test hits the overflow bounds | PASS: 9,420,634 checks, 0 failures. `PASS BOUND` lines show each bound reached exactly:<br>- history entries saturate at ±16384 (bonus 10000)<br>- worst-case `quiet_history` = −49152<br>- worst-case corrected eval = ±144 / 152 / 160 cp<br>- joint entry reaches and holds ±8192<br>- exhaustive gravity and blend domains | `logs/hist_rework_tests_cmake_release.log`, `logs/hist_rework_tests_v2.log` |
| 10 | A planted bug makes the test fail | PASS: 12 of 12 mutants caught; the unmutated baseline passes | `logs/mutation_check.log` |
| 11 | 2–3 tune steps | PASS: levels 1, 2, 3 | design note §1 and §5 |
| 12 | Written overflow proof | PASS: Lemma G plus bounds for every table and every product/sum in update and read, with int widths | design note §4 |
| 13 | Deliverables | PASS: `forge_astra_A1_corrhist_20261027.patch` (applies byte-exact to lock tree 294dbed), `forge_astra_A1_design_20261027.md`, `forge_astra_A1_sprt_plan_20261027.md` | `logs/patch_apply_check.log` |
| 14 | No new warnings | PASS: the same 6 pre-existing `uint16_t` `-Wconversion` lines as the lock | `logs/warnings_lock.txt`, `logs/warnings_a1.txt` |

**Node table** (bench, Threads 1, Hash 16, OwnBook false; the first build gave identical counts):

| HistRework | d11 | d13 | d16 | d20 | d22 |
|---|---|---|---|---|---|
| 0 | 312866 | 862329 | 3024920 | 12389307 | 34048354 |
| 1 | 373261 (+19.3%) | 1043893 (+21.1%) | 3399770 (+12.4%) | 13180132 (+6.4%) | 35699757 (+4.9%) |
| 2 | 320427 (+2.4%) | 881902 (+2.3%) | 3041041 (+0.5%) | 12218938 (−1.4%) | 28571078 (−16.1%) |
| 3 | 336192 (+7.5%) | 869621 (+0.8%) | 3052885 (+0.9%) | 15664938 (+26.4%) | 35705218 (+4.9%) |

**SPRT plan (summary; full plan in `forge_astra_A1_sprt_plan_20261027.md`).**
- **First gate: `HistRework=2`.** It has the smallest node change at d11–d20 and passes the crew's ≤ +10 % screen at d13/d16.
  - Settings: 10+0.1, SPRT [0,10], cap 1500, against the lock exe 5d4df7f1…
- **Then `HistRework=3`**, only if the first gate is H1 or capped with Elo > 0. It has a d20 flag (+26.4 %).
- **`HistRework=1` last or skipped.** It fails the crew screen at d13 (+21.1 %) and d16 (+12.4 %).
- **On any H1:** a 40+0.4 confirm is required.

**Spec parts covered elsewhere, so skipped.**
- Continuation correction: contcorr and C2 bit 1.
- Correction blends keyed on non-pawn piece *placement*: NonPawnCorr and C2 bit 4.
- Uses of the correction magnitude: O5 CorrMargins and O8 CorrExt.
- CorrGravity is not resubmitted: the lock's pawn and material tables keep add-and-clamp; only the new joint table uses gravity.

## Findings
- The "natural uncovered" parts were partly tried before, in the omni-s pack (`C:\Users\Administrator\grok-pc\forge_push\stage_omni_s\omni_s_h256.patch`, read only):
  - S1 `CorrUpdateMode`, which is CorrGravity, and S3 `ThreatHist` (threat key = attacked by *any* enemy piece).
  - They were queued as G63/G64/G68 but never run; no gate folders exist.
- A1 differs from both, as argued in design note §3:
  - its threat key is "attacked by a *lesser* piece" for the moving piece's type, not "attacked by anything";
  - it learns from cutoffs, unlike the parked static P14 ThreatOrderPct;
  - it leaves the lock's correction tables untouched.
- Recent gates in this family against h256_e12 all stopped at the cap with no H1:

  | gate | Elo |
  |---|---|
  | packa_w60 | +11.1 ± 7.9 (LLR 2.48) |
  | packa_w55 | +6.5 |
  | contcorr60 | +5.1 |
  | pawnhist_div4 | +4.6 |

- The PC's system git config has `core.autocrlf=true`, so `git archive` and `git apply` in a fresh repo write CRLF. Use `-c core.autocrlf=false` for byte-exact patch checks.
- MinGW has no libubsan, so the local UBSan check uses `-fsanitize-undefined-trap-on-error`; the positive control above shows it works.

## Left / UNVERIFIED
- No gate: Elo is UNPROVEN for all three levels.
- NPS not measured. ON and OFF search different trees, and the PC is loaded; the sweep's nps figures are single runs.
- Threads > 1 ran only on CI (TSan hook, Threads 4). Locally everything ran with Threads 1, per the PC rule.
- About +200 KiB per search thread is allocated even when the option is OFF.
- A split follow-up (gating the two parts separately) needs a code change that exposes the two weights; not in this branch.
- Untracked `tools/__pycache__/` folders made by CTest are in the worktree. They were not committed and not deleted.

## Process notes (main session, from the sub-agent's hand-back)
Writes only under `F:\opus_scratch`; nothing deleted or killed; no force-push; only the literal push command; every run at
`nice -n 19` with Threads 1, builds `JOBS=1`, free RAM 9.6–11.5 GB before each build. External services: none posted to; one
read-only web search (Parallel Search) for idea sources.

Machine exclusive: no.

## Quiet-runner OFF-path NPS (follow-up, added by the main session)
Branch `opus-offguard`, workflow run 40520714508 (GitHub ubuntu-24.04, g++-14 box flags; `opus-offguard:opus_round1/offguard/REPORT.md`):
the OFF build of `a8b63aae` against the lock `294dbed3`, 10 ABBA runs per side, nodes identical, identity ALL OK.
- CPU NPS B/A: d16 0.9919 (−0.81%, 95% CI −1.35 .. −0.27), d20 0.9902 (−0.98%, CI −1.22 .. −0.73). **The OFF path costs
  about 1%**; both CIs exclude 0.
- `Worker::search` grew 12,737 → 13,337 bytes and `Worker::qsearch` 4,233 → 4,812; every thread also carries the table
  of about 200 KiB when OFF. Which part costs more was not isolated.
- Relevance: only if A1 is merged with the option off by default. A gate gain for HistRework=2 must cover this 1%; a
  compile-time switch (as in S13) would make the default build the lock binary.
