# Neon Memory (8h Continuation — Phase 2: Server-Day Plan)

Updated: 2026-11-23T22:04:00Z (UTC).
Active branch: `debate/server-plan-20261123` (Astra branch: `origin/debate/server-plan-20261123-astra`).

## Phase & Schedule (`232555Z`, `FABLE OUT` `001806Z`)
- **Phase 0 COMPLETE (`17:25Z`):** `FORMATS.md` 2.9 (`ac566296`), `SETUP_PLAN.md` 2.7 (`4100b2a5`), 7/9 `scripts_v2/` files **3/3 YES**.
- **Phase 1 COMPLETE (`17:25Z` – `21:25Z`):** Canonical `debate/engine_plan/ENGINE_PLAN_8H.md` (`dfc0a0c2c1`, `28,404` bytes, `73` lines, SHA-256 **`f8fb81979f803c587b76a44a2d374f04a37c16797ad8b493a61f8b56d6655867`**) holds **2/2 EXACT `AGREE`** (ready for Fable's `21:55Z` inspection). Exp 8C (`8B_divV`) closed honestly (`56.56%` pooled `1.5+0.02`, `46.25%` on 20p `3.0+0.04` -> stays unpromoted candidate).
- **ACTIVE NOW — Phase 2 (Hours 5–8, `21:25Z` – `01:25Z` Nov 24): SERVER-DAY PLAN (`~3h21m` left).**
- **Strict rules:** Only touch `debate/` (never `source/`); nothing personal/secret; update memory ~every 10 minutes; plain pushes only.

## Phase 2 Vote & Audit Ledger (`MANIFEST.sha256` at `8e705146`)
### Already 3/3 `YES` (Phase 0) — 7 files
- `run/engine_lines.py`, `run/uciproc.py`, `tests/test_uciproc.py`, `run/record.py`, `tests/test_record.py`, `tools/budget.py`, `tests/test_budget.py`.

### Newly 2/2 `YES` (Astra + Neon, awaiting Fable) — 4 files
- `run/clockwatch.py` (`b55857dc...`) + `tests/test_clockwatch.py` (`c103d0c2...`): Neon **YES** (`220400Z`; 139/139 PASS incl. Linux P1 high-FD pidfd; 20/20 plants exit=1). Answered Opus `pidfd` fallback Q#3.
- `unit/forgeday.service` (`e389cd99...`) + `tests/test_unit.py` (`57d018bb...`): Neon **YES** (`220400Z`; 13/13 PASS; 9/9 plants exit=1; `systemd-analyze verify` rc=0 on systemd 255.4; flagged `systemd >= 254` gate for `RestartSteps`/`RestartMaxDelaySec`).

### Remaining 8 `scripts_v2/` Pairs (16 files) — Astra voted `NOT YET` on all 8; Neon independent audit + extra bug hunt NEXT
1. `run/worker.py` (`218f7eae...`) + `tests/test_worker.py` (`a602037e...`) — Astra: finalizer accepts foreign/empty range seal.
2. `run/packer.py` (`1db13462...`) + `tests/test_packer.py` (`ee1e0db6...`) — Astra: idle restart in fallback forgets `probe_piece`.
3. `run/launcher.py` (`f9545304...`) + `tests/test_launcher.py` (`2cf7e0f4...`) — Astra: accepts `>= 10000` rounds rejected by worker/packer.
4. `run/bootguard.py` (`fa8ab1b5...`) + `tests/test_bootguard.py` (`06fb0c24...`) — Astra: missing journal/withheld slot yields `-1` contradicting prior RESUME.
5. `run/terminal.py` (`9d640c11...`) + `tests/test_terminal.py` (`51702bf8...`) — Astra: missing whole range seal silently drops completed games from closing count.
6. `tools/make_control.py` (`5f8dacae...`) + `tests/test_make_control.py` (`14ed7d71...`) — Astra: old run's pilot report accepted on substitute header + FORMATS 1.2 evidence-hash doc split.
7. `home/custody.py` (`d46817f2...`) + `tests/test_custody.py` (`a42965f1...`) — Astra: confirms old run A receipts under run B + missing-header explicit confirm exits 0.
8. `run/guard.py` (`67384d4b...`) + `tests/test_guard.py` (`a0802304...`) — Astra: wrong-run/empty `CLOSED.json` exits 0 + wrong-run/empty round seal in `sealed_rounds()` authorizes extension + `terminal: null`.

### Remaining Phase 2 Deliverables (Target completion before `01:25Z`)
1. **Batch 2 (`22:05Z–23:05Z`):** Independent line-by-line audits, test executions, additional bug hunts, and exact-hash votes on all 8 remaining `scripts_v2/` pairs (in two clean batches so Opus gets complete defect lists fast!).
2. **Batch 3 (`23:05Z–23:55Z`):** Full line-by-line review of all 14 files in `debate/server_day/specs/` (`7ed7b3ec2c`, set hash `430a52d6...`) — verify every hand-computed number, link, failure case, and `systemd >= 254` / `pidfd` / rehearsal check -> issue exact corrections or `AGREE 430a52d6...`.
3. **Batch 4 (`23:55Z–01:20Z`):** Re-audit any revised Opus drops + co-author & jointly `AGREE` plain-words `debate/server_day/FINAL_FOR_THE_OWNER.md` before `01:25Z` (Fable checks once at `01:55Z`).
