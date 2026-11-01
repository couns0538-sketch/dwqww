# Actual-lock source package — UNPROVEN

`package_lock_candidate.py` packages the exact AL1 s198 source at
`294dbed3a15dfd821aaf9d4edc6e5f62832fd460` plus the supplied CR patch SHA256
`ef09b342368efd01876bf771726d58cc84d73ec2960b5a70ead710ff0e88d9e3`.
It leaves `package_evidence.py`, its earlier proof directories, and branch engine
files untouched. It never builds or runs an engine.

The baseline archive contains all75 exact Git blobs read with `git cat-file`,
avoiding checkout/archive newline conversion. The helper runs `git apply --check
-p1` and then `git apply -p1` in a new scratch directory, with `core.autocrlf=false`
and `core.eol=lf`. It verifies every resulting file against the nominated stage.
The candidate archive contains only those77 verified stage files. Stage build
outputs, receipts and other extras are ignored. Both archives sort paths and fix
tar metadata and file modes; source bytes are preserved. No Git index is used.

Run only within the owner's current resource and governor authorization. Both
output and scratch directories must be new. For a source-only draft:

```powershell
python astra_r8/tmfit/package_lock_candidate.py --repo . --patch astra_r8/tmfit/cr_fixes/tmfit_lockport.patch --stage D:/grok-pc-data/dwqww/astra8-scratch/lockport-cr-stage-v1 --scratch D:/grok-pc-data/dwqww/astra8-scratch/lock-package-apply-v1 --output astra_r8/tmfit/evidence/lock-source-draft-v1
```

The installed C++ evidence checker runs automatically. A draft exits1 because
its eight required experimental checks remain `UNVERIFIED`; it is not a
packaging failure if source/artifact checks pass. `execution.json` records
`qualification_status: UNVERIFIED`. Failed or partial directories are retained;
choose new names for a later package instead of overwriting them.

`candidate-identity.json` defines the candidate by base commit, exact patch SHA256
and a canonical JSON source-manifest SHA256. `candidate_id` hashes that triple.
The schema1 checker's mandatory `candidate.commit` contains the base anchor;
`commit_semantics` explicitly states that this is a patched source candidate,
not the branch's Git HEAD. The archives and patch define its actual bytes.

For a later qualification package, supply `--input declarations.json` and new
output/scratch paths. Read `candidate_id` from the source draft. Example shape:

```json
{
  "candidate_id": "copy the full candidate_id from the draft",
  "checks": [
    {
      "name": "1_off_on_bench_and_perft",
      "status": "PASS",
      "scope": "Actual-lock candidate binary; refer to its source/build receipt",
      "evidence": {"path": "native/summary.json", "sha256": "producer-published 64-hex SHA256"}
    }
  ],
  "candidate_artifacts": [
    {"path": "native/build-receipt.json", "sha256": "producer-published 64-hex SHA256"}
  ]
}
```

Evidence paths are relative to the declaration file and use forward slashes.
Producer SHA256 values are checked before files are copied. The declaration file
is read once: its exact parsed bytes are copied to `declarations.json` and that
same retained byte sequence supplies the input SHA256. A later change to the
input path does not change the sealed declaration or receipt.

Native PASS/FAIL declarations must contain this exact candidate ID. This checks
**declared binding only**: the helper does not parse producer build receipts,
authenticate their assertions, or automatically connect source hashes to a
binary and its tests. Before qualifying the package, the main agent and Code
Review must explicitly audit the build source hashes to the binary SHA256 and
then that binary to each test manifest. For CI evidence, they must audit the
exact base and applied patch identity in the build job. `record.json` and
`execution.json` state this limitation in `producer_identity_audit`; even
`DECLARED_PASS` is not automatic verification of those producer links.

Training and fit checks
may describe the earlier data source explicitly; those checks do not qualify a
new engine binary. Missing required checks stay `UNVERIFIED`. PASS/FAIL always
requires evidence, and reserved source checks cannot be overridden. The checker
validates declared statuses and hashes; it does not establish that a transcript
is truthful, rerun its tests, or infer strength. Strength stays **UNPROVEN**.

The required experiment names are `data_50000_iterations`,
`fit_grouped_holdout`, `1_off_on_bench_and_perft`, `2_live_timed`,
`3_average_time_200_games`, `4_hard_limits`, `5_absurd_clamp`, and `6_asan_ubsan`.
Historical fallback-source timing and sanitizer results must not be declared as
actual-lock native results.

Run the tiny source/evidence fixture tests with:

```powershell
python -W error::ResourceWarning -m unittest discover -s astra_r8/tmfit -p test_package_lock_candidate.py -v
```

To include the real75-blob/CR patch/stage comparison, set
`FORGE_TMFIT_REAL_PATCH=1`, `FORGE_TMFIT_CR_STAGE` to the frozen stage, and
optionally `FORGE_TMFIT_CR_PATCH` to the patch path before that command. This
additional test applies source files in a temporary fixture directory and
compares all77 hashes; it runs no builds or engines. The fixture packaging test
uses the installed checker when available and verifies that an incomplete draft
exits1, keeps every experimental check unverified, excludes stage extras, and
rejects output reuse.
The mutation regression rewrites the declaration during checker execution and
verifies that the packaged bytes, input hash, and checker artifact reference
still identify the original parsed bytes.

Reusable lesson: byte identity can change during `git archive` or `git apply`
under host newline settings. Read base blobs directly and pin patch-application
newline configuration before comparing or hashing a source candidate.
