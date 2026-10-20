Prepared commands, to be executed only after ROOT-CLEARANCE.json contains the exact frozen source SHA, final runtime-test SUMMARY count and explicit root authorization. Each invocation uses PYTHONDONTWRITEBYTECODE=1 and /workspace/.cloud-setup/venv/bin/python -B from /workspace/dwqww. Existing attempt/build paths are preserved and refused, never reused for retries.

1. run-frozen-validation.py release
2. run-release-parity.py (one defaultbench321912 plus56 fixed-depth cold/warm searches across frozen18/candidate, defaultNNUE/NNUEoff)
3. run-frozen-validation.py asan
4. run-frozen-validation.py tsan
5. run-active-validation.py (one eight-edge default-TSan active session)

All scripts are in validation/lazy-runtime-psqt-native-20261020/. All compiler builds are j2 and all phases are serial. No command from this list has been executed during preparation. The final independent audit and exact full-originals snapshot/manifest follow completed execution without starting engines. All failures stop dependent phases and retain raw process/source/artifact facts; no gate repeats, suppressions or waivers are planned.
