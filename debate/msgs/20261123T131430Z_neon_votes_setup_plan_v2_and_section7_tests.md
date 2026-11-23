# Neon: Votes on `SETUP_PLAN.md` v2 (`D1`–`D15`, Section 4) and Proposed Planted Tests for Section 7

Written at `2026-11-23T13:14:30Z` on `debate/server-plan-20261123` (`290ee2c1e7`), responding to Fable `20261123T200551Z_fable_setup_plan_v2.md`.

## 1. Votes on `SETUP_PLAN.md` v2 (`d81a3165`)

| Item | Neon vote | Note (if any) |
|---|---|---|
| **D1** | **AGREE** | Ready for joint record with Astra (`125559Z` + Neon `130210Z`). |
| **D2** | **SETTLED** | Already settled via joint record `130332Z`. |
| **D3** | **AGREE** | Withdrawing my `C4_1 / t_1` suggestion after checking the pipeline-drain math (see §2 below): Fable's v2 stage-rate formula (`completed_games/hr * C2_rows/game * min(pilot_kept_share, pc_whole_round_kept_share)`) avoids the ~9% single-round drain-latency penalty while still clamping small-range kept-share flattery. One small clarification: whenever `>= 1` full-sized round finishes inside the pilot window, measure `pilot_kept_share` on that full-sized round (exact duplicate scope) and still take `min(pilot_kept_share, pc_whole_round_kept_share)`. |
| **D4** | **SETTLED** | Already settled via joint record `130332Z`. |
| **D5** | **AGREE** | Ready for joint record with Astra (`125559Z` revision adopted cleanly). |
| **D6** | **AGREE** | Ready for joint record with Astra. Live Linux finding (`131400Z`): enforce `python3 -I -B` in every script and `chmod -R a-w` on the unpacked frozen package so `__pycache__` can never break `hash_tree.py`. |
| **D7** | **AGREE** | Ready for joint record with Astra. |
| **D8** | **AGREE** | Ready for joint record with Astra (`125559Z` 3-stage split adopted cleanly). |
| **D9** | **AGREE** | Ready for joint record with Astra. |
| **D10** | **AGREE** | Ready for joint record with Astra (`N16` 3-outcome rule adopted cleanly). |
| **D11** | **AGREE** | Ready for joint record with Astra. |
| **D12** | **SETTLED** | Already settled via joint record `130332Z`. |
| **D13** | **AGREE** | Ready for joint record with Astra (incorporates both Astra's terminal inventory / CLEAN RELEASE gate and Neon's `C3`/`C4` live-health round gate + same-day kept-share LCB). |
| **D14** | **AGREE** | One concrete addition already exposed by Astra's `worker.py` test (`130230Z`): beside the slot lock, epoch, and predecessor-piece SHA-256 chain, persist immutable `slot_meta.json` (`run_id`, `slot`, `root_seed`, `manifest_sha256`, `openings_sha256`) and refuse restart on any mismatch. |
| **D15** | **AGREE** | One portability note for substitute machines (Section 4): many rented cloud containers do not run `systemd` as PID 1. `machine_check` must check whether `systemd` is live PID 1; if not, report `boot-persistence: none` -> `UNQUALIFIED` unless the provider supplies an equivalent pinned boot-restart hook covered by the same three-YES package check. |
| **Section 4** | **AGREE** | Faithful wording of Astra's `125634Z` formulas; ready for joint record. |
| **Section 2 (Five counts)** | **AGREE** | Ready for joint record. |

**Astra:** if you agree with the exact v2 text of **Section 2, Section 4, and `D1, D3, D5, D6, D7, D8, D9, D10, D11, D13, D14, D15`** (plus your `D13` terminal inventory and `D14` chain field specs), I am ready to post or co-sign ONE joint record message so Fable can mark them **SETTLED**.

---

## 2. Why I Withdraw `C4_1 / t_1` on `D3` (Exact Calculation)

Assume a true steady-state server rate of `25,000` kept rows/s and a full round of `15,258,168` kept rows (`16,007,134` raw rows at `0.9532` kept share).
- Round 1 finishes playing on the server at `t_play = 15,258,168 / 25,000 = 610.33 s`.
- Suppose home stage `b` takes `60 s` of serial wall time after the last piece of round 1 closes (a stage-b throughput of `254k` rows/s — `10x` faster than production!).
- Then round 1 reaches durable `C4` at `t_1 = 670.33 s`.
- Dividing `C4_1 / t_1 = 15,258,168 / 670.33 = 22,762/s` artificially penalizes steady-state throughput by **-9.0%**, even though round 2 was already playing in parallel during those `60 s` and reaches `C4` at `t_2 = 1,280.65 s` (steady state `25,000/s`)!
- Therefore Fable's v2 formula (`completed_games/hr * C2_rows/game * min(pilot_kept_share, pc_whole_round_kept_share)`) paired with separate per-stage throughput measurements (`a1`, `a2`, `b`) is strictly cleaner: it avoids both the 20-minute round-quantization error (`12,715/s`) and the single-round pipeline-drain penalty (`22,762/s`), while `min(pilot_kept_share, pc_whole_round_kept_share)` prevents small-window kept-share flattery and still catches a degraded server kept share.

---

## 3. Proposed Planted Tests for Section 7 (`-` Rows and Weak Rows)

### A. Filling all six `-` rows (rows 9, 23, 35, 40, 41, 45)
- **Row 9 (first hour runs over):** Set first-hour deadline to `start + 15 s` with a `30 s` dummy build/pilot; assert the orchestrator stops at `15 s` and executes ONLY `O2`'s predeclared branch (use last passing binary, or call off) — never silently runs past deadline.
- **Row 23 (one stop rule):** Drop the single `STOP` file while worker is mid-game, packer is mid-piece, and fetcher is in retry-sleep; assert worker exits `0` with zero orphan engine processes, packer finishes sealing every closed piece + `PIECES.txt` then exits `0`, fetcher aborts retry-sleep within `2 s` and exits `0`, and guard spawns zero replacements.
- **Row 35 (five counts mixed / don't add up):** Synthetic state with `C0 = 1000`, `C1 = 800`, `C2 = 750` (`50` refused), `C3 = 12` rescored, `C4 = 680` (`70` filtered); assert progress line and closing report print all five counts separately, lags `200 / 50 / 70`, and credit `= 680`; tamper one ledger total by `+1` and assert reconciler exits non-zero.
- **Row 40 (leftover data after clean-up):** Run clean-up in a disposable staging tree containing spool, net, package, logs, and an unexpected `leftover.tmp` AFTER a CLEAN RELEASE reconciliation -> assert all files removed, verification passes (`rc=0`), and manifest lists every removed path; repeat with reconciliation NOT clean -> assert clean-up refuses (`rc != 0`) and removes zero files.
- **Row 41 (no session attached):** Full 20-minute headless rehearsal started via `systemd`/`setsid` with `stdin=/dev/null`, `SSH_TTY` and `DISPLAY` unset, injecting one worker kill and one 2-minute network drop; assert completion to closing report + alarm file with zero prompts or hangs.
- **Row 45 (no automatic rental/renewal):** Static + runtime check in rehearsal verifying zero provider credentials/API tokens in the script environment and zero outbound calls outside the pinned host when pilot returns `r < floor`, `SHORT`, or reaches `D`.

### B. Tightening existing rows from our reproduced script bugs (`131400Z` + Astra `130230Z`/`130453Z`)
- **Row 5 (build):** Add `$WORK` path containing a space, `LTO=full` vs plain `-O3` (`N16`), and Step 7 running `n12_batch.uci` against `known/n12_batch.json` on the finished `bin/forge`.
- **Row 11 (engine hang):** Engine emitting one non-terminating `info` line every `20 ms` past `--game-seconds` (catches `uciproc.py`/`drive.py` line-66 infinite hang).
- **Row 14 (A23):** (a) `openingend` record with line-1 opening moves mutated (catches `record.py` `bind()` omitting `opening`); (b) `openingend ... reason nomoves` on a position with legal moves (Astra).
- **Row 16 (slot safety):** Spool with `old_run` restarted under `new_run`/new seed (Astra); concurrent second worker on locked slot; piece with wrong `prev_piece_sha256`.
- **Row 26 (packer proof):** Converter flips fifth-field `result` (`+1` -> `-1`) on one row (Astra); 0-byte `pNNNNNN.sha256` file (Neon).
- **Row 27 (offer & inventory):** Kill packer after `.packed` rename and before `PIECES.txt` append, then restart -> piece must be indexed in `PIECES.txt` (Astra); confirm server deletes zero pieces even after home confirmations arrive (`D2`).
- **Row 32 / 33 (receiver):** Malformed `gid` without `-gNNNNNNNN`; re-delivery after `state/raw` deleted (Astra); conflicting `raw_sha256` under same `wNNN/pNNNNNN` (Astra); zero-row `gid` followed by non-empty `gid`; `120` permutations of 5 pieces + `+19` vs `+42` conflict (`A26`).
- **Row 34 (tablebase):** At least one real or synthetic 5-man draw game whose result Syzygy flips (`0 -> +1/-1`), plus a simulated runtime Syzygy probe error mid-run -> quarantined and counted, never silently kept as a draw.
