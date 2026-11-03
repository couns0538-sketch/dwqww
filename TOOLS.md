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
