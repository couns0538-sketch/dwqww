# Isolated NumPy revision — UNPROVEN

Suite02's historical negative test assigns NumPy version1.26.4. The first new
runtime actually used1.26.4, so the deliberate difference disappeared. Preserve
the assertions and use the frozen test's recorded historical NumPy2.5.4 instead.
The former runtime and every failed test/launcher receipt remain unchanged.

[Official PyPI](https://pypi.org/project/numpy/2.5.4/#files) provides the Windows
AMD64 CPython3.12 wheel, SHA256
`a7b1b6353e36a7e50de2973a38d705c88ee93adcf120673cee7f45a4a3fa223a`.
The new script independently checks official JSON metadata and downloaded bytes.

Assemble `D:/a10/job3/runtime312np254` from fixed runtime manifest
`a8d8325cd5d6216477c26da3638fe976b7e784b5ead7277c67692e0211a9b461`,
omitting only old NumPy package, libraries, metadata, marker and f2py launcher.
Copy all other manifest files with consumed-byte and destination SHA checks.
Install only the new NumPy wheel offline into a fresh retained stage and copy
its files exclusively into the new packages directory. No old file is deleted
or overwritten; both runtime revisions remain available.

Reserve1.4 GB, with a fresh total-workspace/C30/D50 check before copying; further
measure copy bytes plus two expanded NumPy copies, download and bounded logs.
All work is Idle CPU3 with one worker after inspected quiet admission. Wait for
the separately owned pytest alias cleanup before any global workspace scan.
Runtime assembly performs no Torch/NPT import, compiler invocation or test run.

The authoritative new `RUNTIME_FILES.json` uses the existing runner schema and
is copied byte-identically into this evidence directory. Existing console
entrypoints other than f2py preserve original source bytes/interpreter paths;
qualification invokes the new python.exe directly and does not use those scripts.
No new regression claim is made by assembly alone.
