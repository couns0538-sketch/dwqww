The performance packet is stable and disabled, ready for root publication and
final metadata review. No engines, builds, matches, Git writes or hosted jobs
were executed by this preparer. Root supplied the actual five-command captures.

The comparison is18 fc51e43 versus19 61f5980: one CPU, fresh matched GCC14 builds,
complete baseline10/candidate11 CTests, five canonical321912-node bench commands
per fresh process, one excluded warmup block,15 baseline A/A blocks and31 A/B
blocks. Both CPU and wall must pass calibration and have bootstrap lower limits
above1; all faults invalidate. This measures the specified whole-process Linux
workload, with no Elo or Ryzen/native-Windows claim. No local performance trial
was run.

The original de13 capture helper is preserved byte for byte. Future461a adds
owned cleanup for owner-construction and evidence-write failures. Meaningful
RED/GREEN controls, prior source bytes, failed controls and original streams are
retained. Astra closed the concrete cleanup finding independently. The actual
source/binary/stream/process provenance for both captured positives is mandatory;
swapping the baseline capture into the candidate label is rejected.

Individual offline groups passed49 checks:12 analysis,14 orchestration/proof
checks,10 build guards,4 collector checks and9 benign process checks. An extra
combined wrapper hit its arbitrary60-second offline budget after45 completed
checks during synthetic188-sample file writes. It is retained as FAIL/incomplete,
including the final unchanged-input rehash. Follow-up found no remaining owned
process group; its exact post-cleanup child exit code was not recorded. Four
runner checks were interrupted or pending. Only the synthetic fixture's redundant
physical writes were replaced by an in-memory mapping of376 distinct raw paths
and188 facts; the unchanged parser/hash/sample validator still runs. The targeted
14 checks then passed in0.527s. Hosted60-second/3600-second deadlines did not change.

The package inventory has21 sorted entries plus its manifest (22 paths), SHA256
`e255c744dcb03449adbfbe694c9f522ef9a2ee24e98ec6100e43121abcd5f66c`.
All27 consumed root/capture proofs and package inputs rehash unchanged. Root's
native19 proof covers33 CTests,8 active UCI edges,56 exact searches and2298 audit
checks; its Windows proof covers10 Wine checks and1184 artifact checks. The
workflow still has `on: []` and job `if: false`; final authorization, enabled
workflow hash and READY metadata review remain pending.

`Integrity.test_draft_intentionally_blocked_before_any_child` intentionally
asserts the current draft is BLOCKED and must be explicitly updated when root
authorizes READY. Other reusable tests do not require draft status. The
metadata-only READY fixture is synthetic; actual proof bytes and missing/mutated
proofs are checked separately. `WORKFLOW-STATIC-VERIFY.json` describes this
disabled phase only. The retained `run_offline.py` is the executed attempt1
driver with fixed original output names; do not rerun it over those originals.

Root and independent reviewers may now freeze enabled metadata and run the
targeted current-gate checks. No performance gain has been measured or accepted.
