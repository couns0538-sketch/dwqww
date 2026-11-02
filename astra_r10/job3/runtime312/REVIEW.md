# Isolated CPU runtime assembly — UNPROVEN

Independent reviewer: `proof_contract`. This record covers interpreter/package
assembly only; it does not qualify the original 73-test suite, training, an
engine candidate or the data holdout audit.

The official NuGet Python3.12.10 bootstrap was reviewed at
`816de0307ac3a7896ff49b3f8fd3a72dbdb0242d05c8d7016900b7ae417de255`.
The reviewed source validates the official NuGet SHA512, PyPI pip SHA256,
archive paths, Python.h, python312.lib and licence. Bootstrap completed with
16,309,737 downloaded bytes and44,619,813 expanded bytes. Its original receipt
is `BOOTSTRAP.json`, SHA256
`f9bba4329df2c6e99e1e65c6170b2683248ef86c1d1767901d71746fca2c4b3e`.
The interpreter SHA256 is
`4d6f5f81a4bca11191c4c7c6b43632694d0a4ce74e068619d8fdc161d469859a`.

Collection review found and fixed two concrete provenance gaps before execution:
inherited PIP_EXTRA_INDEX_URL/FIND_LINKS could override the intended source scope,
and a final Torch hash was not compared against its original official receipt.
All inherited PIP_* variables are now cleared before adding explicit controls;
Torch's final SHA256 and byte count must match the verified CPU-index receipt.
Four narrow fixtures passed, with no skips.

The first actual download retained31 wheels successfully, then metadata
inspection failed once because setuptools contains legitimate nested vendored
dist-info metadata. The corrected inspector selects exactly one root-level
dist-info/METADATA; both nested-metadata and missing-root controls were added.
Six fixtures passed, with no skips. The used pre-fix source and original failure
remain under `reviewed-before-metadata-fix/` and `collect-launch/`.

The metadata-only recovery fetched fresh official metadata and rehashed all
retained wheels, without redownloading archives. Reviewed candidates:

- Collector: `7ecb18f419fd7203203ba96ad3b6d8674961b3a17e79ee83a2e12ad844a6439e`.
- Finalizer: `4cb3cbdfdf9076bcaa5843d1a64c08d6fe8ced801527af8ee95063e7f2cd3880`.
- Installer: `0f2c2020cab94a83d8b16574ac4aaef79ffd9367b04aee794136decd9d3da171`.

`WHEEL_LOCK.json`, SHA256
`ef9dcb6af1e3e64b9d2bbdbcf2eeac7480f9864a56b5bd96cad1741c50ac9a90`,
records31 official CPU/test wheels, their URLs, hashes, licences and metadata.
Compressed total159,399,842 bytes; expanded total566,772,910 bytes. The reviewer
independently checked these sums and source receipt identities. The measured
installation reservation is1,233,545,820 bytes (two expanded copies plus100 MB),
against a recorded workspace4,851,673,257 bytes, below the15 GB cap.

Installer review also caught a publication-path mismatch. It now publishes the
authoritative manifest at `D:/a10/job3/runtime312/RUNTIME_FILES.json` and an
identical branch evidence copy. Only hash-pinned local wheels are installed,
using no-index/no-deps/require-hashes/no-compile. The only old-runtime dependency
copied is pure-Python chess1.11.2 plus its licence, bound to current-D receipt
`c20358958646d3ccf6372fda39548c9c9840626f8dfd93fcc531219d2d16bba6`;
this does not recreate a lost historical upstream receipt. No old binary-package
directory is added to the new interpreter's import path.

Every executed phase used Idle CPU3, one worker and the full protected-root
launcher. Load sampler receipts are under sibling `packaging/`:

| Phase | Sampler suffix | CPU3 pair | Host mean pair |
|---|---|---|---|
| Bootstrap | runtime312load04 |8.3,11.5|85.98125,86.925|
| Initial4 fixtures | runtime312load05 |7.8,13.0|86.88125,86.70625|
| Wheel collection | runtime312load06 |13.5,13.5|86.4875,87.2125|
| Corrected6 fixtures | runtime312load07 |9.8,7.3|84.6625,83.30625|
| Metadata finalization | runtime312load08 |7.3,7.3|85.80625,85.8375|
| Offline installation | runtime312load09 |23.7,8.9|87.54375,86.49375|

Earlier WAIT observations are preserved. No loader was launched from a failed
admission pair. Original launcher stdout/stderr/result files remain unmodified.
The assembly does not import Torch/NPT, invoke a compiler, execute training or
use a GPU. The separate regression runner owns those later CPU correctness
checks and their read-only compiler bindings.

Assembly completed at2026-11-02T08:42:21.1278054Z. The installer launcher returned
native0, Idle CPU3, one worker, no capture errors and no disk-floor breach. Its
stdout records18,686 runtime files totaling613,012,961 bytes. The authoritative
and branch manifests are byte-identical, SHA256
`a8d8325cd5d6216477c26da3638fe976b7e784b5ead7277c67692e0211a9b461`.
All runtime input files are now frozen. CPU3 was released to the independent
regression runner. Assembly PASS is not a substitute for native import/compiler
compatibility or the73-test result; those checks were not run by this adapter.
