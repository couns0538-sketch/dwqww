# QA published combo29 as the live Forge SPEED lock — 2026-11-08 (Europe/Vienna)

t1684u bit-exact + ABBA NPS auto-lock. NO Elo claim. Same search / same pins / same net as trial_w6.

## Live pointer
- File: `C:\Users\Administrator\grok-pc\forge_push\locks\CURRENT_LOCK.json`
  md5 `445c8dd5cc15a3f96c6fc8c9b900613c` sha256 `50af2ef34087d684fe8cc7aa822165874b2590b28843c695a83efd44bd5703c4` (identical to lock dir `CURRENT_LOCK.json.staged`)
- exe: `forge_clang_combo29_trial_w6.exe`
- sha256: `E1284F7FC492C8FE1285797FDAE8988CF2F2926B33FCFEE7023D284D67D8802E`
- size: 2092544 bytes
- base_override name: `base_combo29_clang_E1284F7F`
- speed_lock: `combo29`
- tag unchanged: `AUTOLOCK_1_gate120_e32f003rec_s198`
- pins unchanged: 312866 / 862329 / 3024920 / 12389307 / 34048354
- net md5 unchanged: `22B4B9E2C61B37C0450F13A3A92C19B3`
- QA set_t string: `2026-11-08 00:35:41` (PC local / LastWriteTime).
  grok-pc `tzutil /g` = Pacific Standard Time; a concurrent `Get-Date` was ~2 hours behind
  Europe/Vienna (PC 01:39 vs box 03:39 CET on 2026-11-08). Equivalent publish time:
  **2026-11-08 02:35:41 CET / Europe/Vienna**.

## What combo29 is
KING + SEE + EQ32 + CLANG (clang 23.1.5 ThinLTO + frontend-instrumentation PGO).
It is matrix mask 13 (m13) built with the clang c_t2 recipe as `all31_m29`.
Source is `source_snapshot` next to that build, manifest sha256
`3389cfe3dc7bb3989cfebfbdc8ac13d3785b71f090257664d04a0d7c74137645`.
Defaults in that tree: `FORGE_SPD_KING_LINES=1`, `FORGE_SDK_SEE_HOIST=1`,
`FORGE_SDK_MOVE_EQ32=1`, `FORGE_SDK_BADCAP_PREFIX=0` (BADCAP code is present
behind a default-0 switch and is NOT enabled). The six trial_w6 speed switches
are forced ON at compile time by `-D` flags (header defaults in this tree remain 0).

This is not `clang_four`. `clang_four` is KING+BADCAP+SEE+EQ32+CLANG and ranked
#3 overnight at +9.516% (CI95 9.396..9.810). combo29 ranked #1.

Original build exe: `D:\grok_sdk_speed_20261107\detached1735_all31\clang\all31_m29\m2use\forge_m2use.exe`
(same sha256). Lock copies (both sha256-verified on the PC before packaging):
- `C:\Users\Administrator\grok-pc\forge_push\locks\lock_combo29_clang_trial_w6_20261108\forge_clang_combo29_trial_w6.exe`
- `C:\Users\Administrator\grok-pc\forge_push\bin\forge_clang_combo29_trial_w6.exe`

## Overnight ABBA vs trial_w6 (NPS only)
Source: `C:\Users\Administrator\grok-pc\forge_push\overnight_timing_20261108\`
(RANKED.md, LOCK_CANDIDATE.json, RESULTS.json, DONE.json finished PC-local 2026-11-07T23:59:55
= 2026-11-08 01:59:55 CET with the +2h conversion above).
Method: NPS, Threads 1, core 4, 10 blocks, 1 outlier dropped.
- combo29 median **+10.191%** (report as **+10.19%**)
- CI95 **10.099..10.409** (report as **10.10..10.41**)
- clang_only (compiler change alone) was only **+1.385%** (CI95 1.099..1.626). The KING+SEE+EQ32 source features matter.

No Elo number is claimed or implied.

## Bit-exact proof
CURRENT_LOCK.note and LOCK_CANDIDATE.json: bit-exact vs trial_w6 `4181A589…` on 12000/12000 FENs
on and off; warm-TT 1000 identical; T2-4 soak PASS.
Lockproof dir `D:\forge-qa\lockproof_combo29_20261108` (PC-local DONE 2026-11-08T00:33:44
= 2026-11-08 02:33:44 CET):
- warm.log: IDENTICAL 12830 normalised lines, 1000 searches (go nodes 20000, 1000 FENs, warm TT,
  40 state changes), bench 13 = 862329 on both.
- soak.log: SOAK_PASS ref/cand T2-4 legal60 + T1 exact tail50 + bench13.

Sanitizer not run. Binary not byte-reproducible (embedded PDB paths).

## Previous lock
trial_w6 `forge_ltopgo_x_al1s198_trial_w6.exe`
sha256 `4181A5893F15E732D08A2F4FCFBAFFB23618B2567B9F30F9ACD58BE2E69B6FB0`
(sent 2026-11-05 18:13 Vienna as `/workspace/forge_final_AL1_s198_trial_w6_20261105.zip`).

## Not touched by this packaging
Gates, queue, NNUE training, self-play, nets, datasets, STOP/PAUSE files, and
`/workspace/forge_final_sent.txt` were not modified. Already-started gates keep their
prior resolved base; new work rebases on combo29. Never pool results across bases.
