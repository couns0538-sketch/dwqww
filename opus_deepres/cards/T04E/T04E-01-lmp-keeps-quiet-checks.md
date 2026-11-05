# T04E-01: Late-move pruning keeps quiet checking moves
Status: COMPLETE

## Source
Reckless PR #818 "Guard LMP for moves that give checks", squash commit
https://github.com/codedeliveryservice/Reckless/commit/5e5443d798 (2026-03-25), PR
https://github.com/codedeliveryservice/Reckless/pull/818 (text = the two test blocks only, no prose), test logs
https://recklesschess.space/test/12650/ (STC) and https://recklesschess.space/test/12663/ (LTC) (text fields read;
dev branch "lmp-is-direct-check-again").
Context in the same history: #735 (2026-02-27) "10k movepicker bonus for direct checks", STC +3.13 / LTC +5.09.

## Licence
AGPL-3.0 at aec5cb2e80 (tools/licence_at.py, notes/T04E/licences.md): ideas only. Read: PR title, PR text, commit
message, test blocks, test-log text fields. No source file and no diff read; the exact rule is unknown (the branch
name points to direct checks; a depth limit, if any, is not stated).

## Mechanism
Once a node has tried "enough" quiet moves (the late-move-pruning count), engines stop trying the remaining quiets.
The idea: a quiet move that gives check is exempt, so quiet checks keep being searched after the count is reached
(they still face the SEE and extension rules every non-quiet move faces). Pruning by count is a guess that late
quiets are bad; a check changes the opponent's options so much that the count says little about it.

## Forge fit
LACKS. `bash tools/forge_has.sh 'skip_quiets = true|lmp_threshold\('` -> `search.cpp:1062`: LMP only sets
`skip_quiets` once `move_count >= lmp_threshold(depth, improving)` (LmpBase 4 + d^2, halved when not improving,
`:149-150`); the current move is still searched, but `MovePicker::next(skip_quiets)` then skips killers, counter
move and the whole quiet stage (`:368-394`), so every later quiet check is gone. Quiet futility (`:1064-1068`) is
already guarded by `!gives_check` for the move itself but also sets `skip_quiets`. Forge orders direct checks first
among quiets (+12000, `:532`), so most direct checks come before the count; what is lost are checks beyond the count
(bad history) and discovered checks (not in `direct_check`, `:474-477`). Reckless had its own direct-check ordering
bonus (#735) four weeks before #818, so the logged gain was measured on top of check-first ordering, as in Forge.
Change: a "checks only" quiet stage - when LMP fires, the picker still generates quiets but returns only
`direct_check` ones (check squares are already computed at `:462-472`); bit 2 also keeps them after futility.

## Expected gain
Reckless, 1 thread: STC 8+0.08 +2.84 +- 2.04 (95 %), n=28,536, LLR 2.92 [0,3]; LTC 40+0.4 +9.46 +- 4.06, n=6,500,
LLR 2.93 [0,3]. Book UHO_Lichess_4852_v1 (both logs), Hash 16 / 64 MB; W/L/D STC 7,260 / 7,027 / 14,249, LTC
1,681 / 1,504 / 3,315; adjudication win 3 x 400 cp, draw from move 30 6 x 10 cp. The LTC run stopped early (6,500
games), so its +9.46 is likely an overestimate.
Forge estimate: +1 to +4 Elo at STC, more at LTC **UNPROVEN** (Forge already sends direct checks early; the LTC
number has a wide error and comes from a single engine).

## Effort
Crew ~2-3 h (picker stage flag + loop line + option + proofs). CPU: STC SPRT [0,5] up to the 12k-game cap,
~13-25 h at 430-502 games/h; LTC confirmation about 4x the time per game. No GPU.

## Test plan
Pre-gate: OFF bench / perft pins equal to the lock; ON bench changes (expected), ON-at-0 identical; picker unit
check: a quiet direct check ordered past the LMP count is still returned with the option ON; T1/T4 movetime
smoke with engine-side legality; mate probe OFF/ON. Gate: UHO SPRT [0,5] at STC, then LTC (LTC decides: the source
gain tripled at LTC).

## OFF-by-default design
UCI option `LmpKeepChecks` (int 0-3, default 0): bit 1 = after LMP the quiet stage returns direct checks only,
bit 2 = same after quiet futility; 0 leaves `next()` and the loop byte-for-byte on the lock path, so OFF node
counts equal the bench pins. Own variants to try only if bit 1 passes: also discovered checks via `gives_check`
(cost per move), or keep checks only while `lmr_depth <= 6` (own start, range 3-12).
