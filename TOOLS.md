# R14 tool inventory

All new tool installations and caches belong below D:/a14/runtime. No training
runtime or its packages are imported. No training is performed.

The independent interpreter is Python 3.12.10, installed from its official
embedded distribution. Dependencies: python-chess as an external chess oracle,
numpy for compact RAM arrays, pytest for checks, psutil for resource observation.
Versions, artifact MD5 and installed-file hashes will be captured after setup.
External dependencies remain separate; their source is not copied into our tools.

| Tool | Purpose | Path | Verification |
|---|---|---|---|
| Runtime setup | isolated CPU-only dependencies | D:/a14/tools/Setup-R14Runtime.ps1 | setup receipt and package inventory |
| Initialization | restore exact review policy | D:/a14/tools/Initialize-R14.ps1 | evidence/r14/initialization.json |

Pending tools and hashes are not claimed verified. Final inventory will enumerate
each runtime/helper artifact with full MD5 and reproducible verification commands.

## Installed runtime identity

Interpreter: D:/a14/runtime/python/python.exe, MD5
0cfdf7db1b81d067d3dad75f6abb312b. Distribution archive:
D:/a14/runtime/downloads/python-3.12.10-embed-amd64.zip, MD5
fe8ef205f2e9c3ba44d0cf9954e1abd3. Bootstrap artifact:
D:/a14/runtime/downloads/get-pip.py, MD5 8bae3e432175fb42da9d41cbe68217b0.

Installed versions: Python3.12.10; python-chess1.999/chess1.11.2; numpy2.5.4;
pytest9.2.0; psutil7.2.2. All versions including build/test transitive dependencies
are pinned in D:/a14/tools/requirements-r14.txt. No protected runtime imports.

Full inventory: D:/a14/evidence/r14/runtime-files.jsonl, MD5
0dee4106b1ab3160fb7f5759ef0ef972;4033 files,125055165 bytes. Runtime metadata and
module search paths: D:/a14/evidence/r14/runtime-identity.json. Verify each listed
file using Get-FileHash -Algorithm MD5; compare the full inventory before reuse.

Existing compiler (read-only, no install): C:/msys64/ucrt64/bin/g++.exe15.2.0,
MD5 9adc799dbc29227b304b84ab2476232c. Original native helper source:
D:/a14/tools/r14_native/chain_native.cpp; build/qualification evidence is recorded
separately per frozen executable. Static linking avoids external runtime loading.

## Qualified native checker

Executable: D:/a14/tools/r14_native/build/chain_native_r03.exe, MD5
91427a99870d6b3775595db55f0a82e8; SHA256
f1827f44d1e10ab503aed1ac9d1fb4bacc23d8a2cc1199d78ac0aea36a6c446a.
Source MD5 e1dc4870316159c4156828e18db99f4e. Purpose: bounded original legal
move generation and exact full-FEN continuation search through eight plies.

Qualification report: D:/a14/sep/qualification-million01/REPORT.json, MD5
b91461a33503289c3025b5723d202d72. One million randomized one-ply foundation
comparisons resolved with zero disagreements. Extra strata resolved2053 pairs;
twenty deep searches hit their node budgets and remain UNKNOWN. Complete legal
successor comparisons covered10011 positions and260282 successors without a
disagreement. This qualifies sampled helper behavior, not authentic game IDs.
Reproduce with D:/a14/tools/Run-R14Qualification.ps1 using a fresh run name and
normal workload/resource admission. Never reuse a previous output directory.

R14 delivery paths use scoped Git byte-preservation attributes. This keeps
committed evidence bytes identical to PC files rather than normalizing newlines;
verify both Get-FileHash MD5 and repository blob identity when sealing delivery.

## Completed identity and source mapping tools

Prepared-row/source/range mapping: D:/a14/tools/r14_joba.py, MD5
813cc79846583b5eef000fed369f3bdd. It binds the completed chain report, all helper
identities and original source pins; checks full parse/mapping coverage; and
reports original identities as UNVERIFIED. Reviewed launcher:
D:/a14/tools/Run-R14JobA.ps1, MD5 22d4eea877a2521942adbe3c55812064.
Completed report: D:/a14/sep/joba-map-complete01/REPORT.json, MD5
13a5a7df60247a3517f7bbc59012eb16.

Synthetic identity ambiguity: D:/a14/tools/r14_identity_ambiguity.py, MD5
0b95e213be4941cc98a67a8f3a7cfa43. It independently replays legal histories and
simulates the documented buffered first-four-field dedup rule. No real shard
history is asserted. Verification: its seven tests and the sealed proof manifest
D:/a14/sep/identity-ambiguity/MANIFEST.json, MD5
0451c24a9ab8c18a183f7c59f5afeb95. Hash sets remain in RAM.

## R14 finish helper tools (Opus, branch opus-astra-r14-finish)

Own code under D:/a14/tools (licence-clean; python-chess appears only as a test oracle). Run with the R14 runtime at Idle on CPU 2 via opus_lowrun.py.

| Tool (full path) | md5 | Purpose | How to verify |
|---|---|---|---|
| D:\a14\tools\opus_lowrun.py | 0787fcaa38297f6df4c0fb8ae59b74bb | Run a program at Idle priority on a CPU mask (read back; exit 78 if not confirmed) with CUDA/HIP_VISIBLE_DEVICES=-1; children inherit both. | `D:\a14\runtime\python\python.exe -I -B D:\a14\tools\opus_lowrun.py --mask 0x4 -- <python> -c "..." (prints the child mask/priority)` |
| D:\a14\tools\opus_seal.py | 6742803a4cb4908bee3e266768b02823 | Seal/verify tool: verify-report (every {path, md5, bytes} of a REPORT, exact file set with --dir), seal (hash list of a directory), verify-seal. | `D:\a14\runtime\python\python.exe -I -B D:\a14\tools\opus_seal.py verify-seal D:\a14\sep\segments-production02\MAPS_SEAL.json` |
| D:\a14\tools\opus_prod_separation.py | 17ffcc20834142754443853db772e752 | Writes sep/PROD_SEPARATION.json from the two final scan reports and the mandatory BOARDSTM_TRIAGE.json (md5-pinned; no typed numbers; the raw 4-field "0 keys" is labelled as the en-passant artifact, the EP-normalised 4,088-key FAIL is the verdict); output via <out>.part (mode x) + rename, an existing output is refused; --replace-committed only for the git-tracked record unchanged since HEAD. | `D:\a14\runtime\python\python.exe -I -B D:\a14\tools\opus_prod_separation.py --out <new file under D:\a14\tmp> (compare with the committed record: only updated_vienna differs); a second run into the same --out must refuse` |
| D:\a14\tools\opus_ep.py | 1b142bc9941e0b8c791c65adbfb472db | EP normaliser: legal-capture-only en-passant status / FEN normalisation; invalid EP fails closed. | `D:\a14\runtime\python\python.exe -I -B -m pytest D:\a14\tests\test_opus_ep.py -q -p no:cacheprovider; D:\a14\runtime\python\python.exe -I -B D:\a14\tools\opus_ep.py --oracle D:\grok-pc-data\selfplay_out\forge_selfplay_013.txt --limit 300000` |
| D:\a14\tools\opus_boardstm_probe.py | ab989d17cca0b703b9b281855a71a81d | Independent fast board+stm overlap probe (raw FEN prefix, RAM hash index, exact resolution, md5 of every byte vs pins, EP census per file). | `D:\a14\runtime\python\python.exe -I -B -m pytest D:\a14\tests\test_opus_boardstm_probe.py -q -p no:cacheprovider` |
| D:\a14\tools\opus_boardstm_triage.py | 63e82e3a820a5495c258fa25efcd2b8f | Triage classifier: ep_format_diff / real_ep_diff / other per shared key and pair, EP-normalised 4-field recount, per class / holdout file / piece count, listing cross-check. | `D:\a14\runtime\python\python.exe -I -B -m pytest D:\a14\tests\test_opus_boardstm_triage.py -q -p no:cacheprovider` |
| D:\a14\tools\opus_guardband.py | bf2afb3de7bd5f6632a95c708b68bc4f | Guard-band builder: contiguous jobA split cut at an UNREACHABLE link, K-ply guards, holdout-key / val-key / mate drops, every dropped row by id; stages candidate rows. | `proved by opus_guardband_proof.py (sep/GUARDBAND_SEPARATION.json)` |
| D:\a14\tools\opus_guardband_proof.py | 6c974b2e446182ba875a74a4a32fb334 | Independent proof of a guard-band split: accounting, payload, three-key holdout check, train/val keys, chain cut, npt-data-holdout-check audit. | `read checks in sep/GUARDBAND_SEPARATION.json; re-run with a new --out / --big-dir` |
| D:\a14\tools\opus_silent_sweep.py | b1571a0557a427c2319b0140c23647d6 | Lists silent error handling: Python except bodies of only pass/.../continue (ast), PowerShell empty catch, SilentlyContinue/Ignore, trap continue; --changed-list limits it to a git diff list. | `D:\a14\runtime\python\python.exe -I -B D:\a14\tools\opus_silent_sweep.py --root D:\a14 --changed-list D:\a14\evidence\r14\r14_changed_files_11d38208_7636122b.txt (expect 0 findings)` |
| D:\a14\tools\opus_pypi_hashes.py | 50e32a68a8dd5b832d128c1c69ca137b | Hash-pins a requirements file for this interpreter from PyPI metadata (sys_tags-compatible wheels, else sdist); makes tools/requirements-r14-hashes.txt. | `D:\a14\runtime\python\python.exe -I -B -m pip download --require-hashes --no-deps --no-build-isolation -r D:\a14\tools\requirements-r14-hashes.txt -d <new folder under D:\a14\tmp>` |
| D:\a14\tools\opus_inventory.py | 1b63d0c0b6e7573942709c63d2aa17a7 | File inventory for the report: full PC path, bytes and md5 of every file changed on the branch plus extra output folders. | `D:\a14\runtime\python\python.exe -I -B D:\a14\tools\opus_inventory.py --base 7636122b71ff27a5b4b781b6775757f926f8fdc4 --out <new file>` |
| D:\a14\tools\opus_step0_verify.py | 473259754c6149b865cb8d8f5fb09c4b | Re-checks the seven Step 0 input md5s from the committed blobs (aa78a56, 7636122b) after later commits changed two of the files on purpose. | `D:\a14\runtime\python\python.exe -I -B D:\a14\tools\opus_step0_verify.py (expect "step 0 re-check PASS: 7 files")` |
| D:\a14\tools\opus_guardband_record.py | 1b8c9e77bb99ee13c0966c32653199b3 | Writes sep/GUARDBAND_SEPARATION.json from SPLIT.json + PROOF.json with the repository rule final_verdict (no typed numbers). | `compare its output with the committed record` |
| D:\a14\tools\opus_promote_export.py | 0bc94d4267529aec152a8ad92927c7db | Owner-only: turns the staged guard-band candidate into the export (refuses without --confirm-owner-decision, a non-PASS proof, audit failure counters (check_proof, F-014) or changed md5s). | `D:\a14\runtime\python\python.exe -I -B -m pytest D:\a14\tests\test_opus_promote_export.py -q -p no:cacheprovider (refusal rules on fixtures; the command itself is the owner\'s call); tool test of 2026-11-04 10:24: C:\a14x\promote_tooltest01` |
| D:\a14\.agents\skills\boardstm-overlap-triage\SKILL.md | 9f93465b3bb1bbfaf4fa207930bb890b | Skill (by the reviewer agent): probe, EP normaliser, triage - commands and how to read the records. | `read it; every command in it was checked by its author` |
| D:\a14\.agents\skills\guardband-split-proof\SKILL.md | b7f7728af02b22e7b88e34d24fa8dfdb | Skill (by the reviewer agent): build -> proof -> record flow, what each check proves, owner-only promotion. | `read it` |
| D:\a14\.agents\skills\r14-finish-helpers\SKILL.md | 3edfb1a6d982a0c8b803dde9ab26c52f | Skill (by the reviewer agent): the small helpers and the pitfalls of this job. | `read it` |
| D:\a14\tools\opus_tools_md.py | c11122cf13259758266bd526384df5e0 | Prints this section; --check compares every md5 in TOOLS.md with the files. | `D:\a14\runtime\python\python.exe -I -B D:\a14\tools\opus_tools_md.py --check` |
