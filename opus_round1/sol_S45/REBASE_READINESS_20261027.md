# REBASE READINESS 2026-10-27 (S45) — speed and search candidates on a new lock base

**Question (S45).** When a new lock net confirms, can the queued search candidates (P23b, P27R, buffix; timepack4
from the archive's rebase inputs) and the speed patches (S11-S14, S29) be rebuilt on it? Their OFF bench must equal
the new base at all 5 depths, every tunable option must still change the search (d16 ON != OFF), and the table
must say which queued gates become void.

**Answer: yes, on every base tried.**
- **Bases.** AL1 s198 is the base that confirmed (G120 H1 + G120c H1), so it gets the real run. e48f006 (the spec's
  dry-run base) and e48f029 get dry runs.
- **Spec candidates.** All 7 are READY on all 3 bases:
  - both patch tools apply every patch with 0 offsets;
  - every build has FMA 0;
  - OFF bench = base at d11/13/16/20/22.
- **ON prechecks.**
  - P23b and P27R: ON != OFF at d16 on every base.
  - S11, S13, S29: ON = base at all 5 depths (node-exact on every base).
  - buffix: node-identical.
  - timepack4: by design inert at fixed depth (time management only). Its effect needs a timed test (UNVERIFIED).
  - S12 and S14: nothing left to rebase.
- **Extra.** The 9 Opus O/C candidates are READY on e48f006 too (C1 needs Syzygy tables; not run).

## Findings
- **A net-only lock change is fully modelled by swapping `src/nnue_weights.inc` on the AL1 tree.**
  - The e48f006 base reproduces the spec's refs, which are also the PC prebench of the gated
    `forge_h256_f006.exe` (G104/G104c).
  - The e48f029 base reproduces the PC prebench of the gated `forge_h256_auto_e48f029.exe` (A-e48f029)
    exactly: 395885/1101387/2983425/9988472/19376304.
- **The tunable options stay live on every base, but they change the search differently per net.** That is why a
  gate run on one base says nothing about another.

  | d16 nodes with the option ON | h256_e12 (pack record) | AL1 s198 | e48f006 | e48f029 |
  |---|---:|---:|---:|---:|
  | P23b `RefutLmr=1` | 2594099 | 3160733 | 2957682 | 2793391 |
  | P27R `QsEvasionSeeNonPv=1` | 2061742 | 2830435 | 3037089 | 3086416 |

- **The queue under AL1.**
  - 19 queued gates are VALID: net-only candidates rebuilt on AL1, playing against AL1.
  - 49 queued or held gates play against h256_e12 under QA's explicit policy ("keeps old opponent; an H1 goes to
    COMBINE_LIST"). These include P23b (G121), P27R (G118), the speed build G84 and int16 G113.
  - Their verdicts cannot promote anything over AL1. The rebuilt AL1 versions of P23b and P27R are READY (table
    below); re-gating them against AL1 needs new srands (QA's decision).
  - When checked (about 14:25 and 15:30 PC time; read-only process listing), the live fastchess ran `forge_packb_h256` vs `forge_h256_e12`, i.e. one of the COMBINE-route
    packb gates (G40/G41).
- **If e48f006 or e48f029 were locked,** all 19 VALID gates would become VOID_OPPONENT (their opponent would no
  longer be the lock), and the 49 COMBINE-route gates keep their class.
- No PC file was written. The manifest and results were read through copies; machine exclusive: no; everything
  ran at nice 19 / Idle, one compiler or engine process at a time.

## Summary

| base | net md5 | base bench d11/13/16/20/22 | identity vs refs | candidates |
|---|---|---|---|---|
| AL1 s198 (lock, confirmed) | `22b4b9e2` | 312866/862329/3024920/12389307/34048354 | PASS | 7/7 READY |
| e48f006 on the AL1 tree (dry run) | `0fae54a4` | 328459/945640/3024381/9162399/20421972 | PASS | 7/7 READY |
| e48f029 on the AL1 tree (dry run) | `652f7bcf` | 395885/1101387/2983425/9988472/19376304 | n/a | 7/7 READY |
| e48f006 on the AL1 tree (dry run, Opus candidates) | `0fae54a4` | 328459/945640/3024381/9162399/20421972 | PASS | 9/9 READY |

## AL1 s198 — the base that confirmed (G120 H1 + G120c H1): **real run**

### Base `AL1 s198 (lock, confirmed)` (net md5 `22b4b9e2c61b37c0450f13a3a92c19b3`)

- base bench d11/13/16/20/22: 312866/862329/3024920/12389307/34048354; reference 312866/862329/3024920/12389307/34048354 -> identity PASS; base build FMA 0

| candidate | kind | gate | git apply --check | patch -p1 -F0 | build OFF (FMA) | OFF bench = base (d11/d13/d16/d20/d22) | ON precheck | verdict |
|---|---|---|---|---|---|---|---|---|
| P23b_RefutLmr | tunable | 121 | PASS | PASS | OK (0) | = base | d16 ON 3160733 vs OFF 3024920: ON != OFF | READY |
| P27R_QsEvasionSeeNonPv | tunable | 118 | PASS | PASS | OK (0) | = base | d16 ON 2830435 vs OFF 3024920: ON != OFF | READY |
| buffix | bugfix_node_identical | - | PASS | PASS | OK (0) | = base | no option (fix always on): OFF bench == base is the check | READY |
| timepack4_TmDecisiveWinStable | fixed_depth_inert | - | PASS | PASS | OK (0) | = base | d16 ON 3024920 vs OFF 3024920: ON == OFF as designed (effect needs a timed test, UNVERIFIED) | READY |
| S11_MaterialKeyTable | node_exact | - | PASS | PASS | OK (0) | = base | ON == base at all depths | READY |
| S12_lazy_updates | none | - | - | - | - | - | nothing to rebase: already in AL1 (opus-sol-S12 d0574f53: lazy accumulator updates are part of the lock); no patch | N/A |
| S13_TtChildPrefetch | node_exact | - | PASS | PASS | OK (0) | = base | ON == base at all depths | READY |
| S14_movepicker_mailbox | none | - | - | - | - | - | nothing to rebase: nothing left in AL1 (opus-sol-S14 9dca2a54: fixed picker + squares_ mailbox already in the lock); no patch | N/A |
| S29_speedstack | node_exact | - | PASS | PASS | OK (0) | = base | ON == base at all depths | READY |

## e48f006 net on the AL1 tree — **dry run** (spec's dry-run base; G104 H1, G104c cap no decision)

### Base `e48f006 on the AL1 tree (dry run)` (net md5 `0fae54a4c0c437432ddb5da85512b5f4`)

- base bench d11/13/16/20/22: 328459/945640/3024381/9162399/20421972; reference 328459/945640/3024381/9162399/20421972 -> identity PASS; base build FMA 0

| candidate | kind | gate | git apply --check | patch -p1 -F0 | build OFF (FMA) | OFF bench = base (d11/d13/d16/d20/d22) | ON precheck | verdict |
|---|---|---|---|---|---|---|---|---|
| P23b_RefutLmr | tunable | 121 | PASS | PASS | OK (0) | = base | d16 ON 2957682 vs OFF 3024381: ON != OFF | READY |
| P27R_QsEvasionSeeNonPv | tunable | 118 | PASS | PASS | OK (0) | = base | d16 ON 3037089 vs OFF 3024381: ON != OFF | READY |
| buffix | bugfix_node_identical | - | PASS | PASS | OK (0) | = base | no option (fix always on): OFF bench == base is the check | READY |
| timepack4_TmDecisiveWinStable | fixed_depth_inert | - | PASS | PASS | OK (0) | = base | d16 ON 3024381 vs OFF 3024381: ON == OFF as designed (effect needs a timed test, UNVERIFIED) | READY |
| S11_MaterialKeyTable | node_exact | - | PASS | PASS | OK (0) | = base | ON == base at all depths | READY |
| S12_lazy_updates | none | - | - | - | - | - | nothing to rebase: already in AL1 (opus-sol-S12 d0574f53: lazy accumulator updates are part of the lock); no patch | N/A |
| S13_TtChildPrefetch | node_exact | - | PASS | PASS | OK (0) | = base | ON == base at all depths | READY |
| S14_movepicker_mailbox | none | - | - | - | - | - | nothing to rebase: nothing left in AL1 (opus-sol-S14 9dca2a54: fixed picker + squares_ mailbox already in the lock); no patch | N/A |
| S29_speedstack | node_exact | - | PASS | PASS | OK (0) | = base | ON == base at all depths | READY |

## e48f029 net on the AL1 tree — **dry run** (A-e48f029 H1 + confirm H1 vs h256_e12; never locked)

### Base `e48f029 on the AL1 tree (dry run)` (net md5 `652f7bcf51ca4eda560e0fb2b1747c72`)

- base bench d11/13/16/20/22: 395885/1101387/2983425/9988472/19376304; base build FMA 0

| candidate | kind | gate | git apply --check | patch -p1 -F0 | build OFF (FMA) | OFF bench = base (d11/d13/d16/d20/d22) | ON precheck | verdict |
|---|---|---|---|---|---|---|---|---|
| P23b_RefutLmr | tunable | 121 | PASS | PASS | OK (0) | = base | d16 ON 2793391 vs OFF 2983425: ON != OFF | READY |
| P27R_QsEvasionSeeNonPv | tunable | 118 | PASS | PASS | OK (0) | = base | d16 ON 3086416 vs OFF 2983425: ON != OFF | READY |
| buffix | bugfix_node_identical | - | PASS | PASS | OK (0) | = base | no option (fix always on): OFF bench == base is the check | READY |
| timepack4_TmDecisiveWinStable | fixed_depth_inert | - | PASS | PASS | OK (0) | = base | d16 ON 2983425 vs OFF 2983425: ON == OFF as designed (effect needs a timed test, UNVERIFIED) | READY |
| S11_MaterialKeyTable | node_exact | - | PASS | PASS | OK (0) | = base | ON == base at all depths | READY |
| S12_lazy_updates | none | - | - | - | - | - | nothing to rebase: already in AL1 (opus-sol-S12 d0574f53: lazy accumulator updates are part of the lock); no patch | N/A |
| S13_TtChildPrefetch | node_exact | - | PASS | PASS | OK (0) | = base | ON == base at all depths | READY |
| S14_movepicker_mailbox | none | - | - | - | - | - | nothing to rebase: nothing left in AL1 (opus-sol-S14 9dca2a54: fixed picker + squares_ mailbox already in the lock); no patch | N/A |
| S29_speedstack | node_exact | - | PASS | PASS | OK (0) | = base | ON == base at all depths | READY |

## Extra: Opus O/C candidates rebuilt on the e48f006 base — **dry run**

### Base `e48f006 on the AL1 tree (dry run, Opus candidates)` (net md5 `0fae54a4c0c437432ddb5da85512b5f4`)

- base bench d11/13/16/20/22: 328459/945640/3024381/9162399/20421972; reference 328459/945640/3024381/9162399/20421972 -> identity PASS; base build FMA 0

| candidate | kind | gate | git apply --check | patch -p1 -F0 | build OFF (FMA) | OFF bench = base (d11/d13/d16/d20/d22) | ON precheck | verdict |
|---|---|---|---|---|---|---|---|---|
| O1_SmpExactNodes_SmpBestThread | fixed_depth_inert | G-? SmpExactNodes / SmpBestThread (SMP 10+0.1) | PASS | PASS | OK (0) | = base | d16 ON 3024381 vs OFF 3024381: ON == OFF as designed (effect needs a timed test, UNVERIFIED) | READY |
| O1LTT_LocklessTT | node_exact | G-B5 LocklessTT (SMP-only) | PASS | PASS | OK (0) | = base | ON == base at all depths | READY |
| O2_nnue_kernels | bugfix_node_identical | none (speed) | PASS | PASS | OK (0) | = base | no option (fix always on): OFF bench == base is the check | READY |
| O3_search_modules | bugfix_node_identical | none | PASS | PASS | OK (0) | = base | no option (fix always on): OFF bench == base is the check | READY |
| O5_CorrMargins | tunable | G-B3 CorrMargins=1 | PASS | PASS | OK (0) | = base | d16 ON 3607051 vs OFF 3024381: ON != OFF | READY |
| O8_CorrExt | tunable | G-C5 CorrExt=1 | PASS | PASS | OK (0) | = base | d16 ON 3542788 vs OFF 3024381: ON != OFF | READY |
| C2_CorrHistPlus | tunable | G-B1 CorrHistPlus=1 | PASS | PASS | OK (0) | = base | d16 ON 2816649 vs OFF 3024381: ON != OFF | READY |
| C3_HardDeadline | fixed_depth_inert | HardDeadline=10 | PASS | PASS | OK (0) | = base | d16 ON 3024381 vs OFF 3024381: ON == OFF as designed (effect needs a timed test, UNVERIFIED) | READY |
| C6_CuckooRep | tunable | CuckooRep=true | PASS | PASS | OK (0) | = base | d16 ON 2540396 vs OFF 3024381: ON != OFF | READY |
| C1_Syzygy | none | G-B6 SyzygyPath | - | - | - | - | nothing to rebase: needs Syzygy tables for any ON check; not part of this dry run | N/A |

## Queued gates that become void (live manifest copy sha256 `09c995b6…`, FORGE_RESULTS.csv copy `0864d96d…`)

- **lock = AL1 s198 (now)**: DONE 52, DROPPED 8, OLD_OPPONENT_COMBINE 49, VALID 19
- **if e48f006 were locked (dry run)**: DONE 52, DROPPED 8, OLD_OPPONENT_COMBINE 49, VOID_OPPONENT 19
- **if e48f029 were locked (dry run)**: DONE 52, DROPPED 8, OLD_OPPONENT_COMBINE 49, VOID_OPPONENT 19

Per-gate table for the current lock (queued and held gates only):

| gate | tag | state | opponent | candidate built on | class |
|---|---|---|---|---|---|
| 40 | gate40_packb_fs10_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 41 | gate41_packb_fs40_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 42 | gate42_p11r_k16_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 43 | gate43_packa_w50_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 44 | gate44_pawnhist_div1_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 47 | gate47_packf2_c80_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 48 | gate48_packf2_c120_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 49 | gate49_packe2r_v1_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 50 | gate50_packe2r_v2_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 51 | gate51_packd_l1_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 52 | gate52_packd_l3_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 53 | gate53_packd_l4_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 54 | gate54_packd_l2_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 55 | gate55_h256e20i_vs_h256e12 | QUEUED | base_AUTOLOCK_1_gate120_e32f003rec_s198 (833C47F3) | AUTOLOCK_1_gate120_e32f003rec_s198 | VALID |
| 56 | gate56_h256auto000_vs_h256e12 | QUEUED | base_AUTOLOCK_1_gate120_e32f003rec_s198 (833C47F3) | AUTOLOCK_1_gate120_e32f003rec_s198 | VALID |
| 58 | gate58_gcx_qsqpromo_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 59 | gate59_gcx_chkcap8_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 60 | gate60_gcx_lmpoffkp_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 62 | gate62_omnis_s11b_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 63 | gate63_omnis_s1a_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 64 | gate64_omnis_s3b_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 65 | gate65_omnis_s13c_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 66 | gate66_omnis_s15a_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 67 | gate67_omnis_s12b_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 68 | gate68_omnis_s1c_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 69 | gate69_omnis_s10a_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 70 | gate70_omnis_s6a_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 71 | gate71_omnis_s11a_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 72 | gate72_omnis_s12c_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 73 | gate73_omnis_s15b_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 74 | gate74_omnis_s10b_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 75 | gate75_omnig_p20a_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 76 | gate76_omnig_p21b_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 77 | gate77_omnig_p24c_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 79 | gate79_omnieval_mcw100_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 83 | gate83_omnig_p27a_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 85 | gate85_buckets8_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 121 | gate121_p23b_refutlmr_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 84 | g84_c_ptype_pext_nnuemem3b | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 118 | gate118_p27r_qsevnonpv_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 91b | gate91b_tp3_dwin60_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 45 | gate45_timepack_v1_vs_h256e12 | HELD | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 46 | gate46_timepack_inc90_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 57 | gate57_tmdiv18_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 80 | gate80_omnitm_nip75_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 81 | gate81_omnitm_fall_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 82 | gate82_omnitm_fall50_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 96 | gate96_e16p_vs_h256e12 | QUEUED | base_AUTOLOCK_1_gate120_e32f003rec_s198 (833C47F3) | AUTOLOCK_1_gate120_e32f003rec_s198 | VALID |
| 99 | gate99_f001_vs_h256e12 | QUEUED | base_AUTOLOCK_1_gate120_e32f003rec_s198 (833C47F3) | AUTOLOCK_1_gate120_e32f003rec_s198 | VALID |
| 93 | gate93_e24n_vs_h256e12 | QUEUED | base_AUTOLOCK_1_gate120_e32f003rec_s198 (833C47F3) | AUTOLOCK_1_gate120_e32f003rec_s198 | VALID |
| 94 | gate94_e16o_vs_h256e12 | QUEUED | base_AUTOLOCK_1_gate120_e32f003rec_s198 (833C47F3) | AUTOLOCK_1_gate120_e32f003rec_s198 | VALID |
| 97 | gate97_e16q_vs_h256e12 | QUEUED | base_AUTOLOCK_1_gate120_e32f003rec_s198 (833C47F3) | AUTOLOCK_1_gate120_e32f003rec_s198 | VALID |
| 92 | gate92_tp2_fd6_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 61 | gate61_h256kep16_vs_h256e12 | QUEUED | base_AUTOLOCK_1_gate120_e32f003rec_s198 (833C47F3) | AUTOLOCK_1_gate120_e32f003rec_s198 | VALID |
| 108 | gate108_e20f011_vs_h256e12 | QUEUED | base_AUTOLOCK_1_gate120_e32f003rec_s198 (833C47F3) | AUTOLOCK_1_gate120_e32f003rec_s198 | VALID |
| 110 | gate110_e20f013_vs_h256e12 | QUEUED | base_AUTOLOCK_1_gate120_e32f003rec_s198 (833C47F3) | AUTOLOCK_1_gate120_e32f003rec_s198 | VALID |
| 113 | gate113_int16sol_vs_h256e12 | QUEUED | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 114 | gate114_e16f015_vs_h256e12 | QUEUED | base_AUTOLOCK_1_gate120_e32f003rec_s198 (833C47F3) | AUTOLOCK_1_gate120_e32f003rec_s198 | VALID |
| 115 | gate115_e16f017_vs_h256e12 | QUEUED | base_AUTOLOCK_1_gate120_e32f003rec_s198 (833C47F3) | AUTOLOCK_1_gate120_e32f003rec_s198 | VALID |
| 116 | gate116_e16f018_vs_h256e12 | QUEUED | base_AUTOLOCK_1_gate120_e32f003rec_s198 (833C47F3) | AUTOLOCK_1_gate120_e32f003rec_s198 | VALID |
| 117 | gate117_e20f016_vs_h256e12 | QUEUED | base_AUTOLOCK_1_gate120_e32f003rec_s198 (833C47F3) | AUTOLOCK_1_gate120_e32f003rec_s198 | VALID |
| 91 | gate91_tp2_dec70_vs_h256e12 | HELD | base_h256_e12 (456743D9) | h256_e12 tree (exe name) | OLD_OPPONENT_COMBINE |
| 88r | gate88r_e16g90_vs_h256e12 | QUEUED | base_AUTOLOCK_1_gate120_e32f003rec_s198 (833C47F3) | AUTOLOCK_1_gate120_e32f003rec_s198 | VALID |
| 102r | gate102r_e24f005_vs_h256e12 | QUEUED | base_AUTOLOCK_1_gate120_e32f003rec_s198 (833C47F3) | AUTOLOCK_1_gate120_e32f003rec_s198 | VALID |
| 95r | gate95r_e12f_vs_h256e12 | QUEUED | base_AUTOLOCK_1_gate120_e32f003rec_s198 (833C47F3) | AUTOLOCK_1_gate120_e32f003rec_s198 | VALID |
| 26r | gate26r_h256e16h_vs_h256e12 | QUEUED | base_AUTOLOCK_1_gate120_e32f003rec_s198 (833C47F3) | AUTOLOCK_1_gate120_e32f003rec_s198 | VALID |
| 89r | gate89r_e16s_sol_vs_h256e12 | QUEUED | base_AUTOLOCK_1_gate120_e32f003rec_s198 (833C47F3) | AUTOLOCK_1_gate120_e32f003rec_s198 | VALID |
| e32c | gate_e32c_e32f003_cond_vs_h256e12 | HELD | base_h256_e12 (456743D9) | h256_e12 code tree + own net (exe name; net-only candidate) | OLD_OPPONENT_COMBINE |

For a new lock (e48f006 or e48f029) the 19 VALID gates above become VOID_OPPONENT (their opponent is AL1);
the 49 OLD_OPPONENT_COMBINE gates keep that class (`logs/voids_e48f006.json`, `logs/voids_e48f029.json`).

