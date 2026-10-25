# S28 v2 S47-derived audit schema, 20261025

Pure Python, read-only snapshots/metadata only. No live AUTO-LOCK decision, PC-script execution, native test, promotion rule, missing numbered11-point list or CAP-LATE rule is inferred. `PASS` means the stated S47-derived checks on the supplied evidence inputs passed; input provenance/review authenticity remains the caller/reviewer responsibility.

API: `netonly_tree(lock_dir, candidate_dir, expected_net_md5)` and `audit_packet(packet)` in `forge_sol_S28_v2_audit_checks_20261025.py`.

Strict Part A hashes EVERY regular file of the caller-defined snapshots after CRLF->LF; no build/docs/tests/helper exclusions. It rejects links, nonregular entries, added/removed file/directory paths, unrelated changes, unchanged net and a wrong expected normalized MD5. Raw and normalized net MD5 are both reported. Supply only already-frozen snapshot input roots if a live checkout has build output; the tool never hides it.

| Derived check | Packet fields |
|---|---|
|1 old source unchanged|`old_before`, `old_after`: complete relative-file→raw-SHA256 maps; must equal each other AND complete current raw old_lock_dir snapshot|
|2 separate new directory|`old_lock_dir`, `new_lock_dir`: separate non-nested snapshot paths; `new_dir_existed_before:false`: supplied historical evidence, not inferred from current existence|
|3 gated net identity|`candidate_net_md5`, `gated_net_md5`: lowercase32hex|
|4 gated executable/flavour|`candidate_exe_sha256`, `gated_exe_sha256`: lowercase64hex; `candidate_build_flavour`, `gated_build_flavour`: equal explicit labels|
|5 repeated fixed bench|`bench_expected`, `bench_first`, `bench_repeat`: exactly string keys11/13/16/20/22 to nonnegative integer nodes; `bench_reference_sha256`: identity of external fixed-reference source, never derived from candidate|
|6 perfts|`perft5:4865609`, `kiwipete5:193690690`|
|7 FMA|`whole_executable_fma:0`, integer not Boolean|
|8 UCI metadata|`uci_before`, `uci_after`: equal objects `{build_flavour,options:[exact option metadata strings]}` matching candidate flavour|
|9 fresh confirm|`gate`, `confirm`: objects with integer `srand` and `start`; BOTH values must differ|
|10 reviewed pin delta|`pins_before`, `pins_after`: nonempty mappings with identical keys; optional reviewed file/patch evidence below|
|11 strict net-only|Actual old_lock_dir/new_lock_dir snapshots and candidate_net_md5 passed to Part A; no allow-list weakens this check|

Booleans cannot masquerade as integer counts/seeds; pin scalar comparison is type-sensitive JSON. Present contradictions yield FAIL even when other inputs are missing. Missing evidence yields UNVERIFIED. Exit0 is only for strict overall PASS.

For ANY changed semantic pins or file deltas, require `file_changes:[{path,before_sha256,after_sha256}]`, `applied_pin_patch_sha256`, and `reviewed_pin_diff:{review_sha256,patch_sha256,changes:[{key,before,after}],expected_file_changes:[{path,before_sha256,after_sha256}]}`. The actual applied patch hash must equal the externally reviewed patch hash; actual file changes must equal the reviewed list exactly, with safe relative paths, no duplicates/extras, and complete before/after hashes. Semantic pin changes must equal reviewed before/after values exactly. No-change pins/files need no review metadata. A matching claimed review hash is consistency proof, not independent proof that the review happened.

Output `status` reduces ALL11 checks with FAIL > UNVERIFIED > PASS. `part_b_status` independently reduces checks01..10; `strict_netonly_status` exposes11. A fully evidenced reviewed delta can have `classification:REVIEWED_DELTA` and part_b_status PASS while strict_netonly_status/status remain FAIL on raw pin/docs changes. Never call that strict net-only PASS. Capture the strict net-only snapshot BEFORE separate reviewed pin metadata changes.

The provided sample packet/trees/CR packet are entirely SYNTHETIC: dummy net text, fabricated executable identities, dummy fixed-node values1..5, no native game/gate proof. They test schema/logic only. The real numbered11-point checklist and CAP-LATE specification remain missing and live_autoLock_verified is alwaysfalse.

Run from this kit: `python3 -B forge_sol_S28_v2_audit_tests_20261025.py`; sample: `python3 -B forge_sol_S28_v2_audit_checks_20261025.py packet forge_sol_S28_v2_audit_sample_packet_20261025.json`.
