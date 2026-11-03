# R14 permitted regression scope

This is a read-only source inventory, not a collection or test result. No pytest
collection, test execution, protected imports or production workload ran during
this inspection. Static counts below count lines defining names beginning with
test_; parameterization, subtests, fixtures, skip conditions and runtime discovery
mean they are not collected test totals. Recheck candidate hashes after ongoing
implementation finishes.

The complete inherited runner cannot be used unchanged. The permitted R13/R14
regression selection is the 14 direct test_*.py files under D:\a14\tests plus
the two R14 native/qualification files listed below: 16 files and 175 static
test definitions at inspection. This is the full selected R13/R14 regression,
not the entire repository suite. Actual totals must come from its eventual
collection and outcome receipts. Newly added test files require scope review.

## Why inherited full collection is blocked

D:\a14\tools\run_tests.py explicitly selects both astra_r8/datafilter/tests
and tests. It must not be used for this round without a separately reviewed
scope change. Do not suppress the old fixture and describe that altered run as
the complete old suite.

D:\a14\astra_r8\datafilter\tests\conftest.py defines session-autouse
pin_cpu_runtime. Every test in that subtree requires the fixture, which imports
npt_adapter and train, calls the training runtime and hashes its installed files.
This is blocked even for otherwise pure parser tests. The adapter itself changes
sys.path to an installed F: training root and imports torch, data_loader and
model.nnue. train_adapter imports npt_adapter at module level.

Two files also cross this boundary during collection, before any test fixture:
test_input_pin_races.py imports npt_adapter at line 14, and
test_manifest_entry_races.py imports train_adapter at line 10. Merely using
--collect-only on that directory is therefore prohibited. The table of direct
dependency functions below lists the additional explicit adapter/model users;
all remaining functions in the 36-file inherited subtree are still blocked by
the autouse fixture. There are 232 static test definitions in that subtree;
this is not a collected count.

D:\a14\astra_r8\datafilter\evidence\conftest.py explicitly excludes archived
Python execution snapshots. Keep that evidence excluded. Bare repository-root
pytest would also discover unrelated archived/tool tests and is not the selected
R13/R14 suite command.

## Other inherited tests requiring a separate decision

The 24 files under tests/data and tests/data2 have 282 static test definitions.
No protected training import was found in their inspected direct dependencies,
but they are not approved as a group by that observation. They exercise earlier
data tools, native probes and external adapters. They are outside the selected
R13/R14 regression above and are inventoried below rather than silently counted
as passing or included in a full-project claim.

Concrete restrictions found in that group:

- tests/data2/test_converter_disk.py: setup explicitly uses
  TemporaryDirectory(dir='/tmp'), which bypasses the owned TEMP setting on
  Windows. Keep the whole file excluded until fixture paths are adapted.
- tests/data2/test_binpack_adapter.py: external tool opt-in via
  FORGE_BINPACK_ADAPTER, plus the same explicit /tmp fixture path. Do not enable
  it or install its external dependency for this task. An ordinary skipped run
  would not qualify its native behavior.
- tests/data/test_probe_client.py::test_pool_returns_input_order_independent_of_worker_completion
  creates three probe workers. The probe implementation also starts helper
  threads; this does not meet the one-worker regression plan and must not run
  alongside the active scans. The other probe-client tests need separate
  Windows fixture/child-budget review before inclusion.
- tests/data/test_probe.py::ProbeTests requires an explicitly supplied native
  probe and evidence directory. Collection through pytest leaves CONFIG unset
  and skips the native class; that is not native qualification.
- tests/data2/test_external_dependency_policy.py exercises a dependency fetch
  entry point with opt-in arguments in refusal fixtures. No dependency download
  is needed by the selected regression; keep it separate until its refusal-only
  execution boundary is independently checked.
- Legacy converter/holdout tests create SQLite indexes and prune synthetic
  outputs. They need explicit fixture-only scope under this round's RAM-index
  and evidence-preservation rules before being added.

The direct tests/test_runtime_policy.py is different: it imports only the copied
resource_policy module, whose dependencies are standard library modules. Its two
tests check frozen R13 policy expectations and mock disk/tree observations. It
does not import the datafilter conftest or npt adapter. It is allowed in the
selection, but passing it is not evidence of current R14 C:/D: policy compliance.
tests/test_game_hash.py reaches the copied records.py and pgn_input.py parsers;
their inspected imports are the own chess runtime and standard library, without
the training adapter. Normal Python imports do not activate pytest conftest.

## Proposed command, not executed

Save this as an owned .ps1 for execution in a disposable shell after candidate
freeze and independent review. Coordinate an available activity slot first.
It reserves the active overlap scan's CPU 2 and chooses only 0, 1 or 3 after a
fresh admission sample. Runtime, temp files and evidence are all owned. Use a
new Name each attempt, preserve every failed attempt and report skips/failures
honestly. The quick runner disables plugin autoload, bytecode and GPU visibility,
sets all numerical library thread counts to one, and uses the independent
D:\a14\runtime\python\python.exe. No protected-runtime PYTHONPATH is supplied.

```powershell
$ErrorActionPreference='Stop'
$name='r14-permitted-full-01'
$sample=Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor |
    Where-Object Name -in @('0','1','3') |
    Sort-Object PercentProcessorTime | Select-Object -First 1
if (-not $sample -or [int]$sample.PercentProcessorTime -gt 70) { throw 'No spare CPU admitted' }
if ((Get-PSDrive D).Free -lt (50GB+128MB) -or (Get-PSDrive C).Free -lt 30GB) { throw 'Disk floor' }
$used=(Get-ChildItem -LiteralPath D:\a14 -Recurse -File -Force | Measure-Object Length -Sum).Sum
if ([long]$used+128MB -ge 5000000000L) { throw 'Owned storage cap' }
$current=[Diagnostics.Process]::GetCurrentProcess()
$current.PriorityClass='Idle'
$current.ProcessorAffinity=[IntPtr](1 -shl [int]$sample.Name)
Remove-Item Env:ASTRA_R13_CPU,Env:ASTRA_R14_CPU,Env:PYTHONPATH -ErrorAction SilentlyContinue
$env:R14_NATIVE_EXE='D:\a14\tools\r14_native\build\chain_native.exe'
$tests=@(
  'D:\a14\tests\test_game_hash.py',
  'D:\a14\tests\test_p5_audit.py',
  'D:\a14\tests\test_pack.py',
  'D:\a14\tests\test_pack_qualification.py',
  'D:\a14\tests\test_qc_core.py',
  'D:\a14\tests\test_r14_group_map.py',
  'D:\a14\tests\test_r14_launcher.py',
  'D:\a14\tests\test_r14_overlap.py',
  'D:\a14\tests\test_r14_preflight.py',
  'D:\a14\tests\test_r14_qc_fixes.py',
  'D:\a14\tests\test_r14_runtime_setup.py',
  'D:\a14\tests\test_r14_scan.py',
  'D:\a14\tests\test_r14_segments.py',
  'D:\a14\tests\test_runtime_policy.py',
  'D:\a14\tests\r14_native\test_native.py',
  'D:\a14\tests\r14_qualification\test_qualification.py',
  '--confcutdir=D:\a14\tests'
)
& D:\a14\tools\Run-R14QuickTests.ps1 -Name $name -Tests $tests
```

The inherited run_tests.py receipt recorder cannot be used unchanged because of
its blocked directory arguments. The proposed quick command saves output, not
the recorder's per-node JSON. Before final qualification, the parent should
provide an owned recorder for exactly this selection, without broad imports,
and bind actual collected node IDs, outcomes, skips and candidate hashes. This
report does not manufacture a collected total or substitute static definitions
for that missing execution evidence. Launcher/setup tests create only their own
fixture children and require their reviewed wrappers to remain stable; fixture
sleeping descendants and supervision are not additional computation workers.
The old pack_scoped.validate_suite also requires at least 564 collected tests.
Its unchanged synthetic validation tests may pass, but this smaller permitted
selection must not be relabeled as satisfying that historical full-suite gate.

## File identities and static definitions

Inventory snapshot: 2026-11-03 13:52:05 Vienna.

### Selected R13/R14 files

| Full PC path | MD5 | Static test definitions |
| --- | --- | ---: |
| D:\a14\tests\r14_native\test_native.py | ad08286c17f278ca1ca7debf2ba51950 | 15 |
| D:\a14\tests\r14_qualification\test_qualification.py | 947c1a4f43e5aefe131c3c2f7cab92fc | 25 |
| D:\a14\tests\test_game_hash.py | 2c8f4bb3828b5a0012ba7a27837d232d | 5 |
| D:\a14\tests\test_p5_audit.py | 4830d39513906db7e1b78e264104f9ae | 10 |
| D:\a14\tests\test_pack_qualification.py | d33f165ad7e9e283083ec7d8fa18d0db | 3 |
| D:\a14\tests\test_pack.py | b9d0acb30013d17178a1a615787868b6 | 4 |
| D:\a14\tests\test_qc_core.py | 3fb391d8504348a77eda310bccdd6938 | 15 |
| D:\a14\tests\test_r14_group_map.py | f26a62a10680d1e8c42175fcc0027b0f | 14 |
| D:\a14\tests\test_r14_launcher.py | 05f9092dd5b9120df88ffd784a4da629 | 5 |
| D:\a14\tests\test_r14_overlap.py | b4888c52eef4ec4a9e9adb48b34adf2f | 17 |
| D:\a14\tests\test_r14_preflight.py | abb6be63083824b00aa69d31a1116af9 | 2 |
| D:\a14\tests\test_r14_qc_fixes.py | 6d15bd5a2411de8b7858a0a10a8d7da5 | 18 |
| D:\a14\tests\test_r14_runtime_setup.py | b0bd4395040f7dd12f75d86bd4dc2943 | 6 |
| D:\a14\tests\test_r14_scan.py | fce1afad9baabba7a47b3d1098d6c74d | 13 |
| D:\a14\tests\test_r14_segments.py | c7418e247a4615fd1a29c25d74513efd | 21 |
| D:\a14\tests\test_runtime_policy.py | ecac934eda898d4b555e163d83b71ff5 | 2 |

Files: 16. Static test definitions: 175. No collection was performed.

### Blocked inherited datafilter tests

| Full PC path | MD5 | Static test definitions |
| --- | --- | ---: |
| D:\a14\astra_r8\datafilter\tests\test_adapter.py | 7d982dcb4487118472c6dfa1855c3d89 | 13 |
| D:\a14\astra_r8\datafilter\tests\test_admission_union.py | e8192e505d6a1bf05305652f1ee483b8 | 16 |
| D:\a14\astra_r8\datafilter\tests\test_audit_optimization.py | df0bbfe66f16d7c1e000dc21505e174f | 2 |
| D:\a14\astra_r8\datafilter\tests\test_capture_cohort.py | c3f9a3216681c5b9c7eff044077c718d | 8 |
| D:\a14\astra_r8\datafilter\tests\test_converter_admission.py | 73dafd2d442b3216acefe6ba7fb1a4d0 | 6 |
| D:\a14\astra_r8\datafilter\tests\test_converter.py | 3c44dcd8c84dbd8d64bd45216ef87520 | 4 |
| D:\a14\astra_r8\datafilter\tests\test_corpus_profile.py | 771ad9689a9000dddca129eb920b6fc5 | 11 |
| D:\a14\astra_r8\datafilter\tests\test_corpus_report.py | 6d82db695ee2c471062a2aa512bfb3d0 | 5 |
| D:\a14\astra_r8\datafilter\tests\test_entrypoint_admission.py | 521ae4cdabd7fed6c67deb13ea700612 | 13 |
| D:\a14\astra_r8\datafilter\tests\test_filter_cpu_budget.py | 8062913f09c80e1bb54dfa7e784209ed | 1 |
| D:\a14\astra_r8\datafilter\tests\test_filter_interruption.py | 4267be16f0a548b3e74ae494ee4d5fb9 | 2 |
| D:\a14\astra_r8\datafilter\tests\test_filter.py | d615ac89496392257b9f9e1957664620 | 6 |
| D:\a14\astra_r8\datafilter\tests\test_forge_material_admission.py | a230b762205e6153da55940c51493274 | 3 |
| D:\a14\astra_r8\datafilter\tests\test_handoff_adversarial.py | 5489a638d1a3c72aab681e9bf165ea74 | 5 |
| D:\a14\astra_r8\datafilter\tests\test_handoff_completeness.py | 74bacb8c244e39e4958274832c8df639 | 4 |
| D:\a14\astra_r8\datafilter\tests\test_handoff.py | c16f1f6ecef7a8d3b48914a6df0615aa | 1 |
| D:\a14\astra_r8\datafilter\tests\test_holdout.py | d46b31ca125db890c92391c766b2e069 | 3 |
| D:\a14\astra_r8\datafilter\tests\test_input_pin_races.py | 5fa4d8853e051197ff59cb4b3f2aac4d | 8 |
| D:\a14\astra_r8\datafilter\tests\test_integration.py | 911155f950b7bc25f416022a64fa3593 | 2 |
| D:\a14\astra_r8\datafilter\tests\test_integrity_regressions.py | 49d424bcb67d37b118d67d1047b96260 | 9 |
| D:\a14\astra_r8\datafilter\tests\test_lichess_selection.py | fc55d72d7a620a60965e087b27b3fd67 | 14 |
| D:\a14\astra_r8\datafilter\tests\test_lock_correction_receipt.py | f9524800af8eb2c4efa2ebe99c788f03 | 4 |
| D:\a14\astra_r8\datafilter\tests\test_manifest_entry_races.py | 9e3117c1b3c65b494e1c4be07c9a8781 | 6 |
| D:\a14\astra_r8\datafilter\tests\test_metadata_contract.py | 3ea9b664232e976f3666b0712d9cc2a4 | 10 |
| D:\a14\astra_r8\datafilter\tests\test_native_fen_boundary.py | 3e8a035e14aabe006cf62bc185c24231 | 5 |
| D:\a14\astra_r8\datafilter\tests\test_native_smoke.py | cbdb314381d4031bc6714db91bb26904 | 5 |
| D:\a14\astra_r8\datafilter\tests\test_pgn_original_fen.py | 5840890ee303177f003723540d3f7dbb | 7 |
| D:\a14\astra_r8\datafilter\tests\test_profile_reservoir.py | 20302b43f4661df2b265bfce92a3baf7 | 2 |
| D:\a14\astra_r8\datafilter\tests\test_receipt_byte_identity.py | e98e58ea8e398a7cd88ca6fe802ee718 | 2 |
| D:\a14\astra_r8\datafilter\tests\test_records.py | 423c39aec3e1e9c4219a5c74f79f7aa5 | 5 |
| D:\a14\astra_r8\datafilter\tests\test_refresh_handoff.py | 2620e29e9e4bb50a6b763e5a0dcd3f1e | 7 |
| D:\a14\astra_r8\datafilter\tests\test_resources.py | 7e046cffe1b49ff18c5da1784c8cdf2d | 12 |
| D:\a14\astra_r8\datafilter\tests\test_result_codec.py | dd0fbbb0c779199afed08ff4c2e2e9f7 | 3 |
| D:\a14\astra_r8\datafilter\tests\test_runtime_proof.py | 502bbe6ef787f0662fe7a5bbba2f3529 | 3 |
| D:\a14\astra_r8\datafilter\tests\test_strict_corpus_admission.py | 33023775d55a0f5745db67cb42679ebd | 16 |
| D:\a14\astra_r8\datafilter\tests\test_strict_pgn.py | 550a268621821b172f80bb8102571ca3 | 9 |

Files: 36. Static test definitions: 232. No collection was performed.

### Deferred earlier data suites

| Full PC path | MD5 | Static test definitions |
| --- | --- | ---: |
| D:\a14\tests\data\test_build_probe.py | a6fcfe17747dfc59422487d16d473381 | 6 |
| D:\a14\tests\data\test_check_data_bundle.py | bf1900b306951a48b8b95a11187adbc9 | 13 |
| D:\a14\tests\data\test_filter_positions.py | f71511b230bd6a373a04c33a9a4e61ca | 19 |
| D:\a14\tests\data\test_forge_pos.py | e8cb5ce0916ec06df34228ad54c0f79c | 16 |
| D:\a14\tests\data\test_generate_openings.py | 73a87bc24bc6fdc7e7336ff7aad6a2c4 | 14 |
| D:\a14\tests\data\test_idle_launcher_static.py | 9c316472237299f8484c5f9a5e9e3715 | 4 |
| D:\a14\tests\data\test_package_results.py | 8b71d4aaf6b023fc147f5a86420d5214 | 25 |
| D:\a14\tests\data\test_probe_client.py | 1928244b9b809d6d897c81d64c4afd6a | 8 |
| D:\a14\tests\data\test_probe.py | 69627e24b69d24588138819ae9a1689e | 9 |
| D:\a14\tests\data\test_relabel_positions.py | f8e7bbafb858212a88e8b3d7d521e9ab | 14 |
| D:\a14\tests\data\test_transport_parts.py | 0727eb3cac6a97ea100e514787acac60 | 15 |
| D:\a14\tests\data2\test_audit_stat_portability.py | 4c7d0b4ed0ff5aef47ba33e30db9ed0e | 3 |
| D:\a14\tests\data2\test_binpack_adapter.py | 2347f63c54de4f52d2ed48efea155c30 | 13 |
| D:\a14\tests\data2\test_converter_disk.py | 7fe68b312b5bd89243ac219d245593b8 | 23 |
| D:\a14\tests\data2\test_converter.py | 50c9306dca0caa120efda767accf740d | 32 |
| D:\a14\tests\data2\test_external_dependency_policy.py | 11a2bfeb195140a2d41651754f50b099 | 4 |
| D:\a14\tests\data2\test_holdout_clearance.py | 7b32a1588a8b12d79dfd17472240e346 | 25 |
| D:\a14\tests\data2\test_plan_shard_batches.py | 56e68a75140f665207869633f9c2e804 | 12 |
| D:\a14\tests\data2\test_probe_budget.py | bf03a47399d4423c322e4bcb40ddafb5 | 1 |
| D:\a14\tests\data2\test_reserve_defaults.py | a872130f3955a421edbf5e216263dc22 | 3 |
| D:\a14\tests\data2\test_roundtrip_policy.py | e0bb4c0de1cadd4615cdf144fd4f8d6f | 4 |
| D:\a14\tests\data2\test_runtime_policy.py | 988956f0b47310c5180d66a3ff1ec569 | 13 |
| D:\a14\tests\data2\test_shard_runbook_contract.py | 1f02716568aa8045e4f7c4790f0bf4b1 | 5 |
| D:\a14\tests\data2\test_windows_fsync.py | d10b0e176071408fa1cf3daacadac04c | 1 |

Files: 24. Static test definitions: 282. No collection was performed.

### Inspected collection/dependency boundaries

| Full PC path | MD5 |
| --- | --- |
| D:\a14\tools\run_tests.py | 2ddecd628b9a929558da849a50648cef |
| D:\a14\tools\Run-R14QuickTests.ps1 | e78acc11306c01e51dbf3540c8b99335 |
| D:\a14\tools\game_hash.py | d3d40b9602def71fcc2ead7ee815862d |
| D:\a14\astra_r8\datafilter\tests\conftest.py | e1a8357098cb94a5827ddf6f6503b688 |
| D:\a14\astra_r8\datafilter\evidence\conftest.py | 072b12d9146d8b351ae62c2985b058a9 |
| D:\a14\astra_r8\datafilter\npt_adapter.py | 3afa5ebd7b2aaf0bb9e60e8f9bb38ff7 |
| D:\a14\astra_r8\datafilter\train_adapter.py | 9af3948f3047da31647c4726f05ef92d |
| D:\a14\astra_r8\datafilter\resource_policy.py | 2fca425c8c2bcad355f683fa13b0f740 |
| D:\a14\astra_r8\datafilter\records.py | 082c76ece3e0592ab79fee3d9a7a36d0 |
| D:\a14\astra_r8\datafilter\pgn_input.py | 20f9555354e048b0f378a817f64cb2ea |
| D:\a14\tools\data\forge_probe.py | a5c2cd56d4f478509d63eb746bc11ae3 |
| D:\a14\tools\data2\convert_dataset.py | db8aa8381a2b61b3d90833bce8d4cf9a |
| D:\a14\tools\r14_native\build\chain_native.exe | f70d041d304556d8f8b0bf24c40ecdea |

### Direct adapter/model dependency function inventory

The following named test definitions also depend on the adapter through their body, a module import or a local fixture. Every other function in the blocked subtree remains excluded by pin_cpu_runtime. These are source names, not collected node IDs.


#### D:\a14\astra_r8\datafilter\tests\test_adapter.py

- test_native_batch_lifetime_and_mask
- test_sampler_resume
- test_masked_loss_parity_and_reset
- test_row_lambda_shape_rejection
- test_native_cleanup_on_conversion_exception
- test_distributed_rejected
- test_actual_feature_and_model_forward_contract
- test_command_contract
- test_native_black_result_and_mirror_features
- test_validation_does_not_advance_training_sampler
- test_checkpoint_identity_and_epoch_boundary
- test_native_logger_interface
- test_nonzero_device_rank_rejected

#### D:\a14\astra_r8\datafilter\tests\test_entrypoint_admission.py

- test_check_verifies_handoff_before_context_and_pass
- test_failed_handoff_never_constructs_context_or_reports_pass
- test_existing_output_rejected_before_preflight_or_training
- test_dangling_output_entry_rejected
- test_missing_resume_rejected_before_preflight_or_training
- test_actual_output_policy_rejects_F_destination
- test_resource_failure_blocks_preflight
- test_partial_manifest_cannot_enter_training
- test_cpu_check_accepts_staged_manifest_after_verification
- test_partial_target_captured_after_early_path_guard_cannot_delegate
- test_cpu_check_accepts_partial_target_captured_after_early_path_guard
- test_seeding_precedes_delegation
- test_same_seed_repeats_actual_small_cpu_model_initialization

#### D:\a14\astra_r8\datafilter\tests\test_input_pin_races.py

- test_change_after_successful_hash_cannot_become_index_baseline
- test_index_handle_must_be_the_hashed_file_even_if_path_is_stable
- test_fetch_handle_redirection_cannot_return_rows_from_another_file
- test_in_place_change_during_fetch_never_returns_a_batch
- test_windows_handle_change_time_is_not_compared_as_path_creation_time
- test_manifest_bytes_must_match_verified_identity_before_row_files
- test_manifest_change_during_context_initialization_is_rejected
- test_valid_context_retains_exact_byte_digest_and_checks_later_mutation

#### D:\a14\astra_r8\datafilter\tests\test_integration.py

- test_installed_entrypoint_constructs_without_training
- test_real_checkpoint_sampler_lr_restore

#### D:\a14\astra_r8\datafilter\tests\test_manifest_entry_races.py

- test_manifest_replacement_after_verification_never_constructs_context
- test_manifest_replacement_during_runtime_check_never_reports_or_delegates
- test_manifest_replacement_in_last_initialization_step_never_delegates
- test_verifier_digest_must_match_the_original_manifest_before_context
- test_unchanged_verified_manifest_allows_cpu_check_or_stub_delegation
- test_command_uses_verified_target_after_transient_alias_resolution

#### D:\a14\astra_r8\datafilter\tests\test_native_fen_boundary.py

- test_native_features_match_canonical_fen_without_changing_metadata
- test_native_argument_canonicalizes_spacing_and_decimal_clocks
- test_unrepresentable_native_clocks_rejected_before_allocation
- test_maximum_representable_native_clocks_pass_admission
- test_later_invalid_row_prevents_the_whole_native_batch
