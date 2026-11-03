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
