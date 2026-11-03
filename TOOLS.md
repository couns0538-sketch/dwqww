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
