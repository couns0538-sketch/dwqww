# Opus 30-h job - FINAL REPORT (INTERIM - updated during the job; the last version is the one at the branch head)

Branch `opus-30h-20261103` (from main), worktree `D:\o30\wt`, scratch `D:\o30`. Plan: `opus_30h/PLAN.md` (approved
2026-11-03 with defaults D1-D4). Lock FD3A5190 (pins d11 312866 / d13 862329 / d16 3024920 / d20 12389307 / d22
34048354, perft 4865609 / 193690690), lock net e32f003rec_s198 (nnue_weights.inc md5 22b4b9e2). No sub-agents.
**No Elo claim anywhere: every number below is offline or sanity only; the crew gates.**

## 1. What was done (full paths, hashes)
### Item A - v2 net path
- Engine patch `opus_30h/a/v2port.patch` (md5 378bf6bcb4d690d008a7ff18450d38fa): FORGENN2 v2 nets on the lock via UCI
  `EvalFileV2` (empty = off). Proofs: a/RESULTS.md (OFF pins, lock-net-as-v2 identity d11-d22, parity 10000/10000 x
  4 nets x AVX2/SSE/scalar, walk 830k plies x 3 nets, in-search verify, CI).
- Exes: kit v2.4 -PartialTraining `D:\o30\w\v2p2_pc1\src_copy\forge_ltopgo_v2p2_pc1.exe` sha256
  8704d30233390a95706743cd16ca8bba77ce3b5a521e457bdbaba66511e67e3d (pc1 = pc2) - the gate exe for v2 nets; kit v2.3
  `D:\o30\w\v2p1_pc1\src_copy\forge_ltopgo_v2p1_pc1.exe` df1f140b3cd69d9dcdc2f104336879b1a91865c9b974c8ad1b4acf4453fbb583
  (cold v2 path, 0.71x: do not gate nets with it).
- Data audit `D:\o30\data` (a/DATA.md), scorer `D:\o30\tools_bin\o30_score_v2.exe`, trainer `a/o30_fit.py`.
- Nets: (pending - D:\o30\nets\INDEX.md)

### Item B - SPSA
- `opus_30h/b/expose22.patch` (md5 73cd35917a872d2a00b8ce6219d6f7d7): 22 more search constants as options; exe kit v2.3
  `D:\o30\w\sp1_pc1\src_copy\forge_ltopgo_sp1_pc1.exe` sha256 7bf5dab39a53d0aa562083a27b598a7ed47619c97190d0a1a491738a796fcaef
  (pc1 = pc2); tuner `b/tune_spsa.py` + `b/tune_spsa.ps1`, README, self-test PASS.
- Tuning session: (pending)

### Tools, skills, MCP
TOOLS.md; skills forge-o30-v2net / forge-o30-spsa (user scope + `opus_30h/skills/`); MCP forge-o30 (5 tools).

## 2. Unfinished and how to resume
(pending)

## 3. Every check result
(pending - per item RESULTS.md files hold them as they happen)

## 4. Gate next (ranked by expected Elo)
(pending)

## 5. Own review of every patch (NOT independent: no sub-agents)
(pending)
