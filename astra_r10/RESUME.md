# Astra R10 handover — UNPROVEN

Branch `astra-r10-3jobs`, worktree `D:\a10\wt`. All three jobs have been addressed
in order. No native worker remains active. All four packs are sealed and their
complete SHA256/MD5 coverage passed. They are SEALED_INCOMPLETE; no candidate is
accepted and no training clearance is granted. Do not rerun completed runtime
assembly, alias recovery, regression, preparation or sealing.

## Pack identities

Paths are relative to `D:\a10\wt\astra_r10`; hashes are SHA256 of SHA256SUMS.

| Pack | Identity |
|---|---|
|`job1/pack/`|1AF9E1C9850ECE6B1D7DA03F7046F982AF0999CBA8F140AD85C463967E8F85CD|
|`job2/pack_rule50/`|E635D4362A83E4BFC2682BCCA92C00B1458EB5A604DE1E124E96E430E74D3236|
|`job2/pack_optimism/`|0C2AEC6CC35320D495432977C14C88769437A11B04BEEBDFD16AFBD68C7020A7|
|`job3/pack/`|F02E6E139C198F9616EBA2A3510FF07B188C32D1BD8C6BF25DB80D16388DC25D|

Final Job3 verifier: `job3/packaging/verify-cpu2final01-launch/result.json`, SHA256
`35772CB06E61A13940137A34A479EF9D38634853C37B93D61224FC43BC318751`.
Native exit 0, 3949 files PASS, Idle one worker, no capture/disk-floor errors.
Independent final review closed with no open pack findings.
Sealed contents are immutable. Original rejected attempts remain as evidence.

## Exact next steps for the crew

1. **Job1, step 4 — Engine QA plus CR.** Review `job1/pack/REPORT.json`, its
   request and the timing evidence before scheduling any new work. R9 source
   `f43a26aeed2448379fc2916b25f31ead8707b0ec`; pc1=pc2=recovered executable
   `775EDEA1D476A3A18C64AF63F53C55D6E29A4571556AAD2666E87F18A6EF4284`.
   OFF/ON pins, perft, T1, raw-bit parity and detected negative control passed.
   Pinned fens12k SHA256
   `c01c0e6a49fb9aaab535058bd7280c33b8735e0f8bd40834f1c029843a75a265`.
   Timing stopped at CALIBRATION_FAIL: 39 complete A/A blocks, 10 eligible,
   eligible IQR 1.098525pp exceeded the preregistered 1pp limit. Candidate ABBA
   has 0 blocks; speed is UNPROVEN. T4 remains UNVERIFIED. Resolve load/noise
   and reserve fresh seeds before the crew's official timing/gates on UHO.
   R10 must not run gates, matches or SPRTs. No candidate speed conclusion or
   below-threshold claim follows from missing candidate ABBA.

2. **Job2, P4/P7 step 1 — CR plus Engine Strength.** Inspect the separate pack
   reports and retained recovery evidence. No implementation/fit is half-running.
   Missing authentic CR exports: `1e7b5d20`, `cc826b0a` including
   `crfix/delta/p4_v2nets_delta_crfix.patch`, and `129d440e`. Repeated recovery
   stopped; do not repeat the same failed lookup. New external evidence is needed.
   Start heads were P4 `df79fb6e33e0ec45e4bdf40cbbdfadb3b6fc27a6`, P7
   `cd9cb992fd6a6b05766d1117c1de441a430586a9`, status
   `43af044a14a375b653f3d0bc633d9f476325ca81`; recheck for newer Opus heads before
   any future work. Six authentic PGNs/hashes and fit inputs also need permitted
   exports. No candidate executable, parameter recommendation, parity result or
   held-out CI was produced. Keep rule50 and optimism separate, EvalMatScale 0;
   never touch Opus folders/branches or P5. Do not access F:.

3. **Job3, audit clearance prerequisite — Engine NNUE plus CR.** Read
   `job3/HANDOVER.md` and `job3/pack/REPORT.json`. Full audit is complete but
   game separation is UNVERIFIED: 999953 filtered rows versus complete holds
   013 (10000000) and 014 (6388575), 0 position overlaps, 0 six-field FEN
   mismatches, 17388528 missing authentic game IDs. Obtain authentic IDs and
   bind them to every source/filtered/holdout row before rerunning game-level
   clearance. Do not substitute physical row indexes or invented IDs. The
   supplied training command is a BLOCKED guard, not a ready training recipe;
   a reviewed qualified manifest and fresh seed inventory are still required.
   No training or GPU work is authorized by this handover.

## Job3 exact inputs and completed proof

- Frozen source `d8982bc04d3a828ba440bad250d02fb72526f1a2`, under
  `D:\a10\job3\source`; source manifest
  `78D9904850931712E193B4C280083527F04E964285671F8B951D9D58C66D0933`.
- Six frozen inputs under `D:\a10\job3`, mapped by input manifest
  `4A0B8287C7BF3C1A4666E1F1D723D7B3C15112EAC18E1A4E5E8DE73E809140AF`;
  provenance map `0518B34CEC38D26FEAC7B7D48B3AF8A6987199346534BC681DCAD46ADA0DBC46`.
  Input paths and full hashes are in the sealed pack; the complete six-file
  input collection remains outside Git. Never substitute partial holdouts or
  live trainer data.
- Audit `job3/audit/native-actual01/audit.json`, SHA256
  `353C1DB809BA3DDFAD06725547E2CA41DD5B4FCBA3BC26DB4B96E15EE84E5A1D`.
  Its SQLite is retained outside Git/pack; audit status UNVERIFIED is expected.
- Opt-in full-FEN path preserves castling/EP/counters and unchanged legacy
  output. 19 state fixtures PASS, native 16-row relabel 0 FEN mismatches.
  Native report `A459B3CA75087969E76018E72D0ABE9E662DD177A29A9FA03DC82F4FF3200B78`.
- Real adapter primary proof `D:\a10\job3\resume-proof03`, report
  `30694FBDEA528C084863F06C2152FEFD59AC7E83AF36412A9732687D366CF46C`.
  All three fault points, repeated resume and corrupted-shard refusal PASS;
  uninterrupted/resumed MD5 and SHA256 match. Proof01 mock upstream and
  proof02 rejected load admission remain explicitly auxiliary/rejected.
- Original 73 regression PASS, 0 skips, suite03 result
  `DF6058CB1CA6FE41580056384CE756CD021A744B0F50DE12BAA36E847900338B`.
  Private CPU runtime manifest
  `29F8359847D9FC9E25B4B6166805F71940FD35548F9E222587CF16C422C7230E`;
  Python3.12.10/Torch2.9.1+cpu/NumPy2.5.4. All original assertions preserved.
  Earlier failures/recovery evidence are historical, not instructions to rerun.
- Seeds already used/reserved: parity `3771096103`, state fixture `4803011981`.
  Do not reuse them. No Job2 fit/gate seed was assigned.

Accepted lock remains
`FD3A51903E73DC1FA20263F1DCC7A4EEC506592E9F25E50B8F8739CA36873072`.
The final report and RESULTS contain full outcomes, deviations and review records.
No work is half-done in an active process; unresolved prerequisites above require
new crew evidence or separately scheduled crew qualification.
