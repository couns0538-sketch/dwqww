# Isolated CPU regression runtime — UNPROVEN

Use official NuGet `python`3.12.10 instead of the embeddable distribution. The
[Python Windows documentation](https://docs.python.org/3.12/using/windows.html#the-nuget-org-packages)
describes NuGet as a build/CI runtime with headers and import libraries. The
[official package page](https://www.nuget.org/packages/python/3.12.10) identifies
CPython ownership and a 13.84 MB package. Before using it, inspect the actual
archive for Python.h, python312.lib, the interpreter and licence.

Required versions: Torch2.9.1+cpu, NumPy1.26.4, plus actual CPU/test dependencies
tyro, torchmetrics>=1.8.2, tensorboard, pytest, chess and psutil. Transitive
requirements are resolved and frozen by the new interpreter before installation;
their exact URLs, SHA256 and licence metadata are retained. No CUDA/ROCm/DirectML
wheel or NPT source is installed/copied into Forge. Existing NPT stays an external
read-only dependency. Third-party runtime packages and their notices remain
outside the Git source tree; GPL runtime dependency use is not engine vendoring.

[PyTorch's Windows CPU guide](https://docs.pytorch.org/tutorials/unstable/inductor_windows.html)
requires a C++ compiler and Torch2.5 or later. The existing MSVC14.51/Windows SDK
will be accessed through separately reviewed read-only allowlists. No compiler
installation, backend bypass, training step, optimizer update or GPU use occurs.

All new interpreter, dependency, download, cache and temporary bytes belong under
`D:/a10/job3/runtime312`. The old runtime remains unchanged. The reviewed bootstrap
first downloads only the official NuGet archive, NuGet metadata and pip25.3's
official PyPI wheel; it uses a 500 MB conservative reservation and refuses more
than64 MB of downloaded bootstrap bytes or256 MB expanded archives. It verifies
the NuGet SHA512 from official package metadata and the pip SHA256 from PyPI.

After bootstrap, resolve exact compatible dependencies with the new interpreter.
Retain every downloaded archive. Inspect wheel expanded sizes before installing.
The provisional ceiling is4 GB including retained wheels, final files and
temporary install expansion; tighten it using measured archive sizes. Before
any stage that could write over1 GB, freshly check total D:/a10 usage plus the
entire reservation <=15,000,000,000 bytes and C>=30 GiB/D>=50 GiB floors. Stop if
the reservation does not fit; do not delete old evidence to make room.

Each CPU workload requires Idle, one worker, CPU3 and two separately inspected
3-second load observations below30% CPU3 and95% host mean. Coordinate with the
other agent before workspace scans or package writes. Full2-worker regression
waits until the installer releases its CPU slot. The installer and bootstrap
are reviewed before execution; no global config, registry, PATH or C: files are
changed. Process-local environment variables redirect every writable cache/tmp
location under the new runtime.

Next: reviewer inspects bounded bootstrap, run it after admission, report actual
Python archive layout and storage, then prepare the exact wheel lock/size plan
and bounded dependency installer. No large dependency install is authorized
solely by this provisional size estimate.

Completed assembly: see REVIEW.md and ASSEMBLY_RECEIPT.json. All stages above
were independently reviewed and run within measured bounds. The authoritative
manifest is `D:/a10/job3/runtime312/RUNTIME_FILES.json`, SHA256
`a8d8325cd5d6216477c26da3638fe976b7e784b5ead7277c67692e0211a9b461`.
The next step is the separately reviewed native regression runner with fresh
load admission, the exact runtime-manifest hash, and bound read-only MSVC/NPT
inputs. Do not rerun assembly or alter any frozen runtime file.
