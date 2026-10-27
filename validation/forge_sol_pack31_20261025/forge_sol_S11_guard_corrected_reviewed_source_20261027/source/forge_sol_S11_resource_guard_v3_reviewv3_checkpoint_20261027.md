# S11 resource-observer v3 source checkpoint, 2026-10-27 UTC

Status: SOURCE-ONLY; native parity remains UNVERIFIED. This observer does not modify the engine or establish speed or Elo gain. Stages1-22 remain closed PASS and are not rerun. The original stage23 ISA-observer FAIL and the later LP observer-v2 capture-timeout FAIL remain FAIL.

## Final source pins

- Resource helper: forge_sol_S11_resource_guard_v3_reviewv3_20261027.py; SHA256 1f963425a0c1deeb13f740d4de4b37a4bc7e48d6364ecd21caa95149469f38cd.
- Consumer: forge_sol_S11_scalar_parity_resource_guard_v3_reviewv3_run_20261027.py; SHA256 3a63b3a0788f659954986a1780df455f3a78b5c90a371f4e4d0c2fa31b1c6cb7.
- Numerical ISA observer stays63aac4e48c5aeacf5254e18a3e08774946b1cda97468b1edf5b812c03cd130cd. C++ oracle, source/build/flags/corpus/retention/math logic are unchanged.
- New LP/B command templates are in forge_sol_S11_resource_guard_v3_reviewv3_preregister_20261027.json. They are not grants. Only replace the authorization placeholder after independent review, publication/readback and a fresh explicit root grant; LP first, B separately held.

## Narrow observer change and limits

The old consumer's per-drain full /proc group scan is replaced by verified cached-group membership. Every loop checks deadline, external stop, controller/active-leader PID birth/group identity and disk floor. Known-PID RSS is sampled every50ms; complete group membership is refreshed every1s, stage change, leader disappearance, finalization and unchanged owned cleanup. The threshold remains4GiB sampled aggregate; new descendants can be invisible until the next1s refresh plus loop/scan latency. This is explicitly sampled enforcement, not a continuous cap. The guard never launches or signals a process.

A zombie leader can still have a live same-Tgid worker with shared memory. Missing RSS on a live leader/task now fails closed. Only a verified Z/X leader can use a bounded64-task fallback: Pid/Tgid, task birth/group and stable task inventory are checked. The maximum shared-MM RSS is counted once. Stable all-dead task inventories may yield0 for normal EOF drain; explicit0kB on a live task is a known value, not missing data. Status reads are capped8192bytes. Original S18 status texts ground the regression fixture; synthesized stat identities are test-only, not native captures.

Budgets remain1800s total,500s per arm,180s scalar build, CPU2 nice19,10000-record gzip1 chunks, original raw stderr/stdout retention and byte comparison. No producer rewrite, flag/corpus/ISA change or timer extension occurred.

## Preserved failed drafts and controls

- Original6eb helper and22de consumer are retained unchanged. Independent review found missingRSS incorrectly mapped to0. The two focused regression cases fail on6eb, as expected; their raw RED logs remain.
- The first repaired draft d35e5793fa12ab394765a1a57fcb98f0987efd22f15566e8b4116fa15ea687fa rejected an explicit live0kB fixture. Its11PASS/1ERROR output remains as an unaccepted draft. The final reviewv3 repair changes that branch only.
- Final controls:12 RSS fixtures PASS;14 membership/clock/stage/EOF policy controls PASS;6 consumer dispatch/pin/read-only actual-arm binding controls PASS. The final-default RSS test is separately runnable without environment overrides. These are Python/source controls; none are native engine validation.
- AST receipts show both reused own S18 parser/inventory helpers identical, only init/_read_rss/snapshot changed for the RSS repair; all original cadence/identity logic is unchanged. Consumer8 binding/helper definitions are AST-identical to v2, and main is identical after exact guard replacement and8 resource pin/metadata statements are normalized.

## Closed evidence and causal limits

The actual LP observer-v2 native failure retained444176 complete records,45 gzip chunks and rawstderr. It timed out under the original500s arm deadline; root is publishing the immutable data-only view separately. The source inspection identified per-read full /proc scanning as an overhead opportunity. A bounded stdlib2MiB pipe diagnostic failed under the old full-scan guard and passed under cached membership, with unchanged bytes and5s deadline. It is a synthetic observation, not proof of the historical timeout's root cause and not an engine performance result. Originals and all failed attempts are retained.

## Exact next action

Independent source reviewer checks the new helper/consumer and controls. Root publishes/readbacks source and failed evidence, then may explicitly grant only the NEW Lprime_three_arm_resource_guard_v3_reviewv3_once_20261027 case using the frozen preregistered command. Preserve all originals. Do not execute B, advisory AA/ABBA, or any native retry from this checkpoint alone. S11 million-position parity is still UNVERIFIED; no job completion/adoption/speed/Elo claim.
