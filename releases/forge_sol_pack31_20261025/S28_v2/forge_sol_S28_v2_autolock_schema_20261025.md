# Authoritative AUTOLOCK checklist checker, 20261025

Authority: the user's verbatim11-point clarification and later additions, SHA256 `56b36813b2fc791d0c8c2676188ca56a31eb59b32c6a269d14f6e084405d3160`, source `forge_sol_S28_v2_user_autolock_rules_20261025.md`. This replaces the earlier derived11-item grouping as S47's authority. Historical `forge_sol_S28_v2_audit_checks_20261025.py` remains a generic qualification/tree helper; its derived checklist is not the user checklist.

API: `audit_autolock(packet=None)` in `forge_sol_S28_v2_autolock_checklist_20261025.py`. Output has exactly11 numbered checks and3 later-addition checks, each PASS/FAIL/UNVERIFIED with individual missing facts and contradictions. FAIL outranks missing facts. Booleans are not integer counts. Complete hexadecimal hashes compare without case sensitivity; original input files and dictionaries are not changed.

This is a read-only consistency audit of exported metadata/artifacts. It never calls a PC, runs an engine or script, simulates promotion scheduling, edits pointers/state, writes CR_PASS, or impersonates Code Review. `live_pc_verified` and `writes_cr_pass` are alwaysfalse. PASS here is evidence consistency, not approval or a claim that current PC state was observed. Caller/reviewer retains responsibility for provenance and completeness of exported observations. Artifact paths/source_snapshot refer to local read-only exported evidence; `lock.path` records the observed PC directory.

The known F41CF92F and896663B0 script prefixes have user-supplied review authority. A complete measured64-hex live hash must equal an actual supplied script snapshot hash; a prefix alone stays UNVERIFIED. No fresh review is requested for an identified known successor. An unlisted full hash needs an existing external successor-review artifact. This checker cannot invent the missing full896663B0 identity or prove that any exported snapshot is still live on the PC.

## Packet fields

Hashes are fullSHA256 unless statedMD5. An artifact object contains `{path,sha256}`; bytes must exist as a regular nonsymlink file and hash-match. External review objects additionally contain `external:true,decision:"PASS"` and the covered identity. The actual first meaningful header must say PASS and bind that identity as an exact token, such as `PASS <full-script-sha256>` or `PASS AUTOLOCK_1_tag`. A FAIL header contradicts PASS metadata; an ambiguous/unbound header yields UNVERIFIED. Historical FAIL controls in the body are permitted. This conservative recognizer does not guess an unknown document format.

|Point|Required evidence fields|
|---|---|
|1|`script.live_sha256`, `script.snapshot` artifact, `script.no_autopromote_absent:true`; unknown successor additionally `script.review` artifact with external/decision/script_sha256 binding|
|2|`winner.parent` and `winner.confirm`, each `{void_file_exists:false,result_md,options_check,candidate_sha256}`; no **VOID**, final meaningful options-check line PASS|
|3|`race.{g104c,cap_expired,winner_id,winner_tag,rework_list,g120_rebase_gates,g104_rebase_gates,mode}` plus branch facts below|
|4|`lock.{n,tag,path,directory_new,orphan_lower_n_dirs,exe_sha256,parent_tag,kind,tree_diff,net_md5,net_manifest_md5,gate_id,gate_tag,chain_id}`; `event:"first"` or `"later_cap_late"`; f006 additionally attached-only pins fields below|
|5|`checks.{perft5,kiwipete5,fma,bench_reference_source,bench_reference,bench_first,bench_repeat}`; oracle source exactly `gate.prebench.cand_off`; maps exactly depths11/13/16/20/22 with positive integer nodes; reference and both runs equal. `checks.nps_ratio` is optional advisory only|
|6|`old_lock.{exe_before_sha256,exe_after_sha256,sources_before,sources_after,source_snapshot,read_only_attributes_only,pointer_backup,steps}`; full old exe identities equal and e3df99cd-prefixed; complete raw file/SHA maps equal actual supplied old source snapshot; backup filename `CURRENT_LOCK.json.bak_pre_<ltag>_*`; CREATE then POINTER for current tag, hashes mutually equal and exe/net bindings match new lock|
|7|`state.{promotes_last_tag,pointer_tag,seen,datagen_pending,combine_list}`; tags equal lock tag, seen indexed by actual full `lock.gate_tag` says PROMOTED, pending true, lock.chain_id absent from COMBINE_LIST|
|8|`gates.{manifest_backup,started_before,started_after,rebuilt_net,search_option}`; backup filename `forge_gates.json.bak_rebuild_<n>_*`, actual JSON has `gates:[{tag,...}]`; each complete started_before row equals its actual backup row and started_after. Rebuilt records and search labels below|
|9|`high2.{all_chains_inspected:true,chains}`; each chain has `{id,double_h1,seen_status,seen_reason}`; no double-H1 INELIGIBLE caused by missing FORGE_RESULTS/RUN_INFO. If `was_high2_ineligible:true`, require nonempty `crew_visible_clear_note`|
|10|`datagen.{switch_completed,file_boundary,nps_ratio,trainer_before_sha256,trainer_after_sha256}`; completed switch at file boundary, ratio0.9..1.1, trainer unchanged. A pending switch remains UNVERIFIED|
|11|`cr.chained_without_cr` integer0..2 plus `cr.external_pass` artifact with `{external:true,decision:"PASS",lock_tag,record_name:"CR_PASS_AUTOLOCK_<n>.txt"}` and actual covered PASS header. Missing external CR_PASS remains UNVERIFIED even when operationally within the two-chain allowance|

`old_lock.steps` records are `{action:"CREATE"|"POINTER",tag,hashes:{exe_sha256,...}}`; supplied net_md5 is bound to lock.net_md5 too. Full hashes compare case-insensitively. Prefix-only log hashes cannot establish complete evidence. Extra unrelated stages may exist, but the selected current-tag CREATE/POINTER sequence must be in order.

`gates.rebuilt_net` records contain `{id,notes,before_srand,srand,base_override,ag_prev}`: note contains `REBUILT on `, nonnegative seed changes, new lock override and stored ag_prev. `gates.search_option` records contain `{id,kind:"search"|"option",label}` with `vs h256_e12`. `started_before/after` maps use actual full gate tags and complete manifest rows; partial rows cannot pass comparison to the actual backup.

## Race and CAP-LATE branches

`race.g104c` describes the status AT THE INITIAL RACE DECISION, not a later update; values H1/H0/CAPPED/PENDING. `race.cap_expired` describes the same decision. A terminal status and expired wait-cap together are conflicting branch facts, not a reason to guess event precedence. Later G104c status belongs in `cap_late.g104c_current`.

- H1: winner_id G104, winner_tag gate104_e48f006; g120_status PARKED-E32; G120 in rework_list and no G120 rebase gates.
- H0/CAPPED without wait-cap expiry: winner_id G120, gate120_* tag, G104 in rework_list and no G104 re-gate.
- Expired wait cap: G120 wins; gate104_e48f006_rebase_vs_AL1 queued with a fresh nonnegative srand, exempt24 true and crew-visible INFO alert. No policy scheduler is inferred.
- First event parent is exactly h256_e12; first lock's canonical gate_id and full gate_tag equal the race winner. Later CAP-LATE event is explicitly different: parent AUTOLOCK_1[_tag], kind net, promoted gate exactly the queued gate104_e48f006_rebase_vs_AL1. It does not reapply the first-event parent rule.

Three additions are checked separately:

1. `post_promote.inflight:null`, `post_promote.alerts_lines` contains no inflight_* lines.
2. For cap/later-cap events, `cap_late.{z2_enabled,queued_gate,ag_rebase_exempt24,srand,original_srand,conc,g104c_current,queue_status,crew_alert}`. Queued name is exact, seeds differ, conc5, exempt24 true; once Z2 is enabled it is HELD while G104c is not H1. `crew_alert:{level:"INFO",visible:true}`. Later event requires G104c H1 and `{later_promote_logged:true,log_kind:"net",log_parent_tag:"AUTOLOCK_1[_tag]"}` matching actual parent.
3. If race.mode is RH-Q1 FALLBACK and G120 wins, `fallback.crew_visible_note` must be nonempty. Default mode is explicit RH-Q1.

## Actual f006 lock versus isolated post-pin qualification

The named gate104_e48f006 and its AL1 rebase bind BOTH net and MD5-sidecar to `0fae54a4c0c437432ddb5da85512b5f4`, require actual kind net and Tree-Diff exactly src/nnue_weights.inc. Applied tests/helper/docs changes cannot pass as the real net-only lock.

`lock.pins_applied:false`; `lock.pins_refs` maps the original3AECB403 and5A4ED675 references to `attached`. Keys may be case-insensitive prefixes or the exact measured full originalMD5; a different fullMD5 is rejected. Known originals are:

|MD5|SHA256|
|---|---|
|3aecb403afebae7a5046e9e4bd3f8f97|692b164b2601cf84411a7ea8c4b7892b255a219b2a07e5bdf7167b2cad77a35e|
|5a4ed6758d7778e26d2d4c504f3a47bb|5685e836373afaecafba0e284f35d62402df478beedda7b0f3f40564ef2ccbca|

Optional supplied `lock.pin_attachment_sha256` maps measured fullMD5→SHA256 and is checked against those originals. The rebased7fea candidate-qualification patch is never substituted as an original real-lock attachment. The separate isolated qualification is not a real AUTOLOCK/source adoption.

## Running and evidence limits

From this kit, `python3 -B forge_sol_S28_v2_autolock_tests_20261025.py` runs60 pure fixtures. `python3 -B forge_sol_S28_v2_autolock_checklist_20261025.py` with no packet returns UNVERIFIED/exit1: eleven points plus three additions lack actual PC evidence. Use `--packet <exported.json>` only with genuine externally supplied observations/artifacts. Redirect stdout to an ordinary dated review report; never a CR_PASS filename.

`forge_sol_S28_v2_autolock_synthetic_packet_20261025.json` and its named fixture directory contain ONLY SYNTHETIC metadata, dummy source/script text, neutral fake external-review files and fabricated candidate identity references for logic tests. They are not PC, gate or review evidence and must never be submitted as a promotion packet. The sample retains a known old reference hash as a test reference only; it does not measure an old executable.

The first60-fixture GREEN and each prior RED/failing approach are retained. Independent read-only peer review is in `forge_sol_S28_v2_authoritative_peer_review_20261025.md`; that report is not CR_PASS. The referenced14:35 bundle lacked the cited original CR file and16:15 prompt, but the user's exact supplied clarification is sufficient authority here; no missing-rule approval flow is invented.
