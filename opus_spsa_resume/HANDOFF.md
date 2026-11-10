# HANDOFF: Code Review → QA (opus_spsa_resume, combo29)

This job played **no games**. Nothing was queued, no lock, gate, queue, STOP/PAUSE file, net or dataset was touched, and no tuned value or Elo is claimed. `confirm/PROPOSED_QA_ENTRY.json` is a proposal only. QA alone schedules gates and publishes locks.

## 1. For Code Review
| Item | What to check | Evidence |
|---|---|---|
| `patches/tune_gate_after_combo29.patch` (md5 8875a86e77b76f4953a19099eebcca13) | Default-OFF switches `RazorTune` / `QsTune`. With both macros at 0, nothing is compiled or registered. Switch 0 keeps the lock values even if the family's options are set; switch 1 applies them; back to 0 restores them. `search.cpp` is untouched. | `BENCH.md` §2–5: normalized PE identity lock = off; bench, perft and fens12k identical; 16 gate-semantics checks; warm1000 |
| `spsa/` harness | Crash safety (hash-chained ledger, atomic checkpoints, resume replays and re-verifies everything), pins, refusals, live guards | `TESTS.md` (harness 63/63, R9 equivalence) |
| `confirm/` pack | Single-use holdout registry (plus a second registry beside the holdout), fixed candidate rule (live run, pinned config, no post-completion rollback), pentanomial GSPRT, replay once with all PGNs, start-position leakage audit | `TESTS.md` (confirmation 39/39), `confirm/CONFIRM_PROTOCOL.md` |
| Reviews so far | M1, M2 (+ recheck) and M3 by one same-model reviewer subagent: **not independent** | `review/REVIEW_LOG.md` |

## 2. For QA, in order (only after Code Review)
1. **Staleness check.** Is `CURRENT_LOCK.json` still combo29, `forge_clang_combo29_trial_w6.exe` with SHA256 e1284f7f…802e?
   - If DR01, DR04, DR06, DR12, DR14, DR15, or any razoring, qsearch or static-eval change became the lock, this pack is stale (`PLAN.md` §5).
   - The tuner refuses any other exe by its pin.
2. **Tuning run** (uses the lock exe itself, whose scalars are existing UCI options):
   - Dry-run: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File bin\spsa.ps1 -Config configs\joint_razor_qs.json -RunDir <run dir>`. It prints the exact fastchess command and writes nothing.
   - **Live:** copy the config with `live.enabled = true` (this changes its sha256), write `<run dir>\LIVE_ACK.txt` with that sha256, then add `-Mode live -Live`. QA chooses concurrency, CPUs and time.
     - The sha256 is the harness's: over the config's canonical JSON, not `Get-FileHash` of the file. The refusal message of a first attempt without LIVE_ACK prints the expected value.
   - **Size:** N = 16000 pairs = 32,000 games at 10+0.1 (`PLAN.md` §4.7; synthetic justification in `BENCH.md` §6). The budget alternative is N = 4000 with r_end 0.005.
   - **Resume:** the same command plus `-Resume`.
   - **Rollback:** `bin\rollback.ps1 -RunDir <run> -ToCkpt <n>`, during the run only. A COMPLETE run is refused unless `-ReopenComplete` is given. A reopened run can never yield a candidate (no re-tuning until lucky), so finish suspect runs by starting a new run instead.
3. **Candidate:** `bin\confirm.ps1 -Command select -TrainingRun <run dir> -CandidateOut <cand.json>`. This is the fixed rule: the final θ of the COMPLETE live run, as the nearest feasible integers.
4. **Gate exe:** build `patches/tune_gate_after_combo29.patch` with `-DFORGE_RAZOR_TUNE=1 -DFORGE_QS_TUNE=1` using QA's recipe, then repeat the identity battery (`engine/qualify.py`, `BENCH.md` §3).
5. **Confirmation, primary route:** QA's own runner. Fill `confirm/PROPOSED_QA_ENTRY.json`:
   - candidate values, gate exe SHA256, srand (≠ 20261110), openings_start;
   - UHO book, SPRT [0,5], cap 40,000 recommended (5,000 decides only large effects).
   - Then audit the gate PGN: `bin\confirm.ps1 -Command audit -Protocol confirm\configs\audit_protocol_uho_example.json -Candidate <cand> -Pgn <gate.pgn>`. Before the audit, fill in the protocol's three fields:
     - `sprt` must equal the gate's own SPRT (cap 40,000 if the proposed cap was used);
     - `qa_gate` must hold the engine names in the PGN;
     - `training_config_sha256` must be the live run's RUN.json `config_sha256`.
     The train/screen `.keys` files are already pinned.
   - Claim only if all hold: QA's verdict is H1, the recomputation agrees, leakage is ≤ 1%, and `candidate_issues` is empty.
   - On H1, QA's longer-TC confirm (40+0.4) follows.
6. **Alternative route on G1:**
   - Edit `confirm/configs/confirm_protocol_G1_example.json` (cand_exe, training_config_sha256, qa_gate names, registry location).
   - Play the dry-run's fastchess command under QA's scheduler. The cap is 4,816 games, because G1 has 2,408 openings.
   - Recompute with `-Mode replay`, **once**, with all PGNs. An interim replay that reaches no decision before the cap is refused, because it would consume G1.
   - G1 serves one confirmation, ever. G2 and G3 need a written, QA-approved protocol change.
7. **Rollback at any point:** the lock exe with no options, or `option.RazorTune=0 option.QsTune=0` on the gate build (`confirm/ROLLBACK.md`).

## 3. Open items and limits
- **Git source commit of combo29: BLOCKED.** The build parent is the hash-bound snapshot (`AUDIT.md` §1).
- **Raw byte identity of rebuilt exes: UNRESOLVED** (embedded PDB path and GUID). Normalized PE identity holds.
- **Unproven:** the F1–F2 interaction (code-level only); C1/C3′ (heuristic priors); run-size adequacy (synthetic models only). Any non-default value is a SEARCH CHANGE, UNPROVEN, until QA's SPRT.
- **Live mode of the tuner was never exercised:** this job allows no games. Its fastchess command is shown by the dry-run, its PGN parsing is exercised by replaying R9's real fastchess smoke PGN and generated PGNs, and its guards are tested. Recommendation: QA's first live session runs a few batches with `-MaxBatches 2`, then `bin\spsa.ps1 -Command verify`.
- **This PC's paths:** the `bin\*.ps1` defaults for `-Python` and `-TempDir` name this PC and this job; pass your own.
