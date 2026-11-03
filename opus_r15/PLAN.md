# R15 plan (Opus, 2026-11-03, written 11:31 PC clock; ~6 h -> ends ~17:45)

## Context
Couns wants new, gate-ready Forge Elo candidates (OFF-by-default UCI options on the lock FD3A5190 source, LTO+PGO kit
builds) plus tools/skills that make Opus and the crew faster. Branch `opus-r15-20261103`, push about every 10 min
(no `[skip ci]`), writes only to `D:\o15` + the branch. User goal added mid-planning: when everything is done, a
30-minute bug check with all findings fixed; anything blocked is skipped and the time goes to the next item.

Facts found while planning (read-only):
- **Job 0 is already done.** All four R14-B Code Review fixes were committed and pushed today 10:05-10:31:
  f124ed3f (installer refuses linked copies), e29bf186 (fl_abba / fl_equal refuse warmup >= batches), 1656e093 (fl_fuzz
  bit-identity vs the default loader, "empty" outcome, --min-free-gb 50, --flips <= 1000) on opus-r14b-fast-loader
  (head 34ea50ee); d3ad6881 (pc_gate exit 1 on unreadable counters) on opus-r14b-status (head be7fdbfc); tests
  test_installer 38/38, test_cli 51/51, test_tools 43/43. R15 re-verifies only.
- Base = lock source git d4f4312 (= `grok-pc\forge_push\qa_ltopgo_al1_stage\src_al1s198_clean`) + QA kit v2.3
  `build_ltopgo.ps1` `-Expose` (R14: switch-0 build = FD3A5190 byte for byte, work dir D:\o14a\w).
- New options go into `tune::parameters()` in src/search.cpp (int, default 0): advertised under -Expose (the gate
  runner checks that), uci.cpp untouched.
- Running now: gate stB LmrCapVictim=1 vs AL1 (fastchess conc 4, Threads 2, 0xFFF0, BelowNormal), self-play Idle on
  4-15, npt trainer main thread Idle on CPU 3 (0x8); CPU ~85 %, RAM 14.4 GB free, D: 59 GB, C: 135 GB.
  Finished stB gate: 3000 games in 6:02 = ~497 games/h (speed baseline).
- Already gated or prepared, so NOT picked: every CorrHist/correction variant, PawnHist, ContHist4Pct, EvalOnlyStore,
  Hindsight, ThreatHist/HistRework, CheckOrderSee, CheckExtDepthCap, LmpOffKP, RfpOppWorse, RfpReturnBlend, PawnEgPrune,
  HistMalusPct, QsQueenPromoOnly, QsEvasionSeeNonPv, AspFailHighReduce, EvalSwing, FailHighBlend, FiftyDamp,
  Sf26 bits (NMP prior, LMR alpha gap, multicut corr, razor), E3 eval, LMR x captures (stB LmrTtCapAll / LmrCapVictim,
  packf2 NoisyLmrDiv), TtPruneV2 parts, **ReSearchAdjust (packb = deeper/shallower re-search, confirmed in
  packb_h256_src.zip)**, **CaptSeeDiv (packf2 = capture-score SEE threshold in the good-capture stage, confirmed in
  packf2_h256_src.zip)**, FB2-J3 SingularV2 (triple / PV double ext / multicut / deeper negative ext),
  **TtCutoffHistory (exists in R13 packc28, never gated alone)**.

## Decisions (say so at approval if you want them different)
1. **No `Co-Authored-By` trailer** in R15 commits: it names a model company, and your R15 rule ("no vendor or
   model-company names ... in any commit message") takes precedence over the default trailer.
2. Writes: `D:\o15\...` and the worktree `D:\o15\wt` (branch opus-r15-20261103, from origin/main 5176ddf7,
   upstream unset at once). TMP/TEMP for builds = `D:\o15\tmp`. Skills go to `C:\Users\Administrator\.claude\skills\`
   (your "C:\Users\Administrator or D:\o15" rule) with copies under `skills/` on the branch; the project
   `.claude\skills` folder is not written.
3. CPU: own work on **CPUs 0-1 (0x3)**, one physical core away from the trainer (CPU 3) and the gate (4-15). The kit
   sets BelowNormal on itself (its own code); everything else runs Idle. At most 4 threads in total; in practice a kit
   build (1) + a smoke (2). pc_gate (fixed R14-B copy) before every build; gate speed (games/h from the running
   gate's PGN) recorded before and during own work.
4. Disk: `D: < 50 GB` or `C: < 30 GB` -> stop all writes, push what is committed, report (no fallback drive unless you
   say C:\o15 is allowed). pc_gate checks D: >= 51 GB before each build.
5. One exe per option (cleaner than one exe for all lines: no other option's code in a line's exe). "OFF and ON
   variants" = the same exe with no setoption (must give the lock pins) and with the ON setoption (must be live).
6. Tools needed by Job 1 (pin_check.ps1, cand_pack.ps1, smoke) are written first; each candidate is then finished end
   to end (exe, checks, INDEX row, CI row, push) before the next one starts, so a usage cut-off leaves N complete
   candidates.
7. No sub-agents (standing rule); all reviews are self-reviews written down as NOT independent.

## Step 0 - setup + Job 0 verify (~25 min)
- `D:\o15\{wt,w,src,cands,tmp,logs,job0,mcp}`; `git worktree add -b opus-r15-20261103 D:\o15\wt origin/main`,
  `git branch --unset-upstream`; `opus_r15/.gitattributes` = `* -text`; README/STATUS skeleton; first push.
- Job 0: `git clone --shared` of both R14-B heads into `D:\o15\job0\`, run test_installer.sh, test_cli.py,
  test_scope.py (fast-loader clone) and test_tools.sh (status clone) with outputs under D:\o15\job0; record shas +
  counts in `opus_r15/job0/RESULTS.md`. No re-fix unless a test fails (then fix on the R14-B branch, test, push).

## Step 1 - tools Job 1 needs (~45 min), all under `opus_r15/tools/`, each with README section + self-test
- `kit_build_r15.sh` = copy of `opus-r13-p2-sparse-l1:opus_r13/p2/speed2/kit_build_r14.sh` with `-Work D:\o15\w`,
  exports `D:\o15\src`, `-Affinity 0x3`, pc_gate = `opus_r14b/tools/pc_gate.ps1` (`-Drive D -Cpus 0,1`), TMP/TEMP.
- `pin_check.ps1 -Exe X [-Options 'N=V;...'] [-Mask 0x3]`: drives the exe over UCI at Idle (bench 11/13/16 [-Full adds
  20/22], `go perft 5` on startpos + kiwipete), parses `info string bench depth N nodes X` / `nodes N`, prints a table and
  PASS/FAIL vs the lock pins (with -Options: perft must still match, bench must differ = LIVE, else FAIL "dead option");
  writes JSON. Self-test: lock exe PASS; lock exe + `LmrQuietBase=86` -> LIVE (and FAIL in plain mode); missing exe
  and bad option -> non-zero exit.
- `cand_pack.ps1 -Name X -Patch P -Option N -On V [-Tag t] [-Sides pc1,pc2] [-NoPatch]`: fresh LF export of d4f4312
  (`git archive` with core.autocrlf=false), `patch -p1 -F0` (dry run first), cleanroom lint of the patch, kit_build_r15
  pc1 + pc2 with `-CheckOpt 'N=V'`, sha256 pc1 = pc2, copy exe to `D:\o15\cands\X\`, pin_check OFF + ON, smoke, writes
  `D:\o15\cands\X\RESULT.json` and the INDEX row (`D:\o15\cands\INDEX.md` + branch copy). First real run =
  **base re-verify**: `-NoPatch -Sides pc1` must give sha256 fd3a51903e73dc1fa20263f1dcc7a4eec506592e9f25e50b8f8739ca36873072.
- `smoke2m.py EXE --line 'N=V' --seconds 120 --threads 2`: self-play ON vs ON at a fast clock (2000+20 ms) from
  varied starts, every bestmove checked against the engine's own `go perft 1` list (as R13 selfplay_smoke.py), counts
  games / plies / illegal / crashes / hangs / time-overs; exit 0 only with 0 illegal, 0 crashes, 0 hangs. Self-test: a
  stub engine that plays an illegal move and one that exits must both FAIL.
- `cleanroom_lint.py PATCH|--commits RANGE`: added lines and commit messages free of vendor / model-company / other-
  engine names and licence headers (term list stored encoded), patch touches no uci.cpp `id author`, tools/openings or
  LICENSE. Self-test with planted bad patches.

## Step 2 - Job 1 candidates (~3 h; one exe each; order = cheapest first)
Every option: `tune::` int, default 0, advertised; own constants only (derived from Forge's existing values).
| # | option (ON) | idea / site in src/search.cpp | why it should gain (one paragraph each in REVIEW.md) |
|---|---|---|---|
| C1 | `PruneLmrHist` (1) | quiet futility / history / SEE pruning use the LMR depth INCLUDING the history term LMR itself applies: `lmr_depth += clamp(history / LmrHistoryDivisor, -2, 2)` (move loop, ~l.1063) | pruning then matches the depth the move would really be searched at: good-history quiets survive, bad ones are pruned earlier |
| C2 | `QsMovePrune` (3) | qsearch, not in check, after N legal moves: skip captures that give no check, are no promotion and do not recapture on the previous move's square (~l.831) | late qsearch captures (ordered by MVV + capture history) rarely raise alpha; qsearch is a large node share, so the saved nodes buy depth at STC; checks / recaptures keep tactics |
| C3 | `TtProbcut` (360 = 2 x ProbcutMargin) | non-PV, no excluded move: TT lower bound with tt_depth >= depth - 3 and tt_score >= beta + margin -> return beta + margin (right after the TT-cutoff block, ~l.926; also in check) | the TT already shows a large fail-high from a nearly deep enough search; re-proving it is wasted work |
| C4 | `IirShallowTt` (1) | IIR also when the TT move exists but tt_depth < depth - IirDepth (pv or cut node, ~l.1031) | a very shallow TT entry orders the node little better than no TT move; reducing first saves nodes, the re-search depth comes back next iteration |
| C5 | `ContHistSplit` (1) | continuation history tables split by (side was in check, move was a capture) of the move that indexes them; OFF uses table [0][0] = the lock's table (4 assignment sites + clear) | a piece-to-square follow-up after an evasion or capture means something else than after a quiet move; mixing them dilutes ordering |
| C6 (stretch) | `QsFutilitySee` (1) or `LowPlyHist` (1) | qsearch: futile stand-pat + non-winning capture (SEE < 1) pruned; or ply < 4 history for ordering | only if C1-C5 are done |
Per candidate (~30 min, kit build runs in the background while the next patch is written):
1. Patch in a scratch lock export; plain build (lock g++ line + Expose, 0x3 Idle) -> pin_check OFF PASS, ON LIVE.
2. `cand_pack.ps1` -> exe pc1 = pc2, kit SUMMARY (OFF ALL OK, ON differs from OFF, 0 missing-profile, vfmadd 0),
   pin_check OFF (d11/d13/d16 = pins, perft 4865609 / 193690690) + ON bench d11/d13/d16, smoke2m ON 0 illegal / 0
   crashes, sha256, INDEX row.
3. `opus_r15/cands/<X>/{<X>.patch, IDEA_SOURCE.md (generic wording, no names), REVIEW.md, logs/}`; matrix row in
   `.github/workflows/opus-r15-san.yml` (copy of R13 opus-r13-san.yml: lock d4f4312 + patch, ASan+UBSan, configs
   default / ON / max; branch filter only, no paths filter; cancel-in-progress) in the same commit; push; CI to green.
Zero-build extras after C1-C5, <= 15 min, listed separately in INDEX as "existing exe, never gated alone", not counted:
`TtCutoffHistory 1` on `C:\o13\handoff\packc28\forge_ltopgo_pkc.exe` (cf617e67, confirm sha + advertised),
`TtPruneV2 true` alone on the b1 exe; each with pin_check OFF/ON + smoke.

## Step 3 - rest of Job 2 (~50 min)
- `gate_summary.py GATE_DIR...|--all F:\forge_push`: from the fastchess .log + .pgn (+ RESULT.md / RUN_INFO.json if
  present): W/D/L, pentanomial, Elo +/- and nElo (formulas from forge-gate-stats), exact fastchess GSPRT LLR with the
  gate's bounds, illegal-move / time-forfeit / disconnect / crash counts (PGN Termination + log lines), games/h from
  GameEndTime; `--watch` mode for a running gate (normal-speed check). Self-test: >= 5 finished crew gates (copied
  read-only) must reproduce the printed W/D/L/Ptnml exactly and Elo/LLR to the printed rounding.
- `index_check.py D:\o15\cands\INDEX.md`: every exe exists, sha256 matches, option advertised default 0, ON in range.
- Skills (SKILL.md, user scope + branch copy): `forge-r15-candidates` (patch -> plain check -> cand_pack -> INDEX ->
  CI, pitfalls), `forge-gate-summary` (gate_summary / watch usage), plus a line in TOOLS.md for each tool.
- MCP: own stdio server `D:\o15\mcp\forge_uci_mcp.py` on the MIT `mcp` Python SDK in `D:\o15\mcp\venv` (setup script
  `setup_forge_mcp.ps1`, pinned version): tools pin_check, uci_options, bench, perft, gate_summary, gate_watch,
  pc_status; self-test client over stdio. Registration `claude mcp add --scope user ...` attempted; if refused it stays
  a documented command (skip, not blocked). Quick look (<= 5 min) for an existing licence-clean UCI MCP server first.
- `TOOLS.md`: purpose, command, how to verify, self-test result for every tool / skill / server.

## Step 4 - 30-minute bug check (budgeted, ~16:45)
Fresh exports: re-apply every patch, plain build, OFF/ON nodes equal the INDEX; re-hash every exe; re-run all tool
self-tests; re-read every diff (bounds, UB, int16 overflow, thread safety, OFF path identical); doc_lint (R14-B) over
the branch; CI list green; fix every finding, re-run, commit.

## Step 5 - Job 3 wrap-up (~25 min)
`D:\o15\FINAL_REPORT.md` (+ branch copy): what was done with full paths and full sha256 / md5, unfinished items,
every check result, "gate next" ranked ordinally by expected Elo with the mechanism (no Elo numbers, no claims),
own review per patch (NOT independent), time from commits (commit_span.py), owner items. Final push; advisor read.

## Verification (end to end)
- base: unpatched kit build sha256 = fd3a5190...; every candidate: pc1 = pc2, OFF pins d11/13/16/20/22 + perft via
  kit and pin_check, ON live, smoke 0 illegal / 0 crashes, CI ASan+UBSan green, cleanroom_lint PASS, option advertised
  default 0; INDEX checked by index_check.py.
- tools: each self-test passes and a planted failure fails.
- crew safety: gate games/h and trainer CPU share recorded before / during own work; pc_gate disk + RAM before every
  build; nothing written outside D:\o15, the branch and the user skills folder.

## Time and pushes
~11:50 setup, 12:15 tools, 13:00-16:00 C1-C5 (+C6), 16:00 Job 2 rest, 16:45 bug check, 17:15 report. Push every
~10 min (STATUS.md updated each time), `date` read before writing any time. If a candidate stalls > 45 min or a step
is blocked (permission, disk, CPU), record it and move to the next item.
