# CR prerequisite verification

Base: e6868fd56ebb3991ee197af6be29f3dd14a4d1c2. Applied requested sets in order: abcbb9c9, 0e91e02e, b25b207d, 31481475. All 22 copy receipts match staged bytes. git diff --check passes. No sealed-pack paths changed; no staged script executed.

The first two MD5SUMS.txt manifests cover all nine supplied payloads each; other manifest-listed review/test artifacts are absent. The last two directories contain no MD5SUMS. Couns explicitly chose recording measured hashes for them during plan review. CRFIX_APPLIED.json labels manifest_verified=false rather than claiming an authoritative comparison.

The exact staged scripts still contain D:/a10 paths. They are preserved for prerequisite identity only and MUST NOT run unchanged. The staged regression runner lacks the later R10 runtime312np254/pytest_alias_guard behavior. R11 must combine that behavior with the staged safety changes in separate reviewed files. No training, GPU, engine, or data job ran.