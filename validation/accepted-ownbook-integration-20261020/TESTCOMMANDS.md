**baseline-release**

`/workspace/.cloud-setup/venv/bin/cmake -S /workspace/.cloud-setup/accepted-ownbook-baseline-source -B /workspace/.cloud-setup/accepted-ownbook-baseline-release -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=/usr/bin/g++-14 -DPython3_EXECUTABLE=/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 -DFORGE_NATIVE=OFF -DFORGE_ENABLE_SANITIZERS=OFF '-DCMAKE_CXX_FLAGS=-fno-fast-math -ffp-contract=off -fno-lto' -DCMAKE_EXPORT_COMPILE_COMMANDS=ON`
`/workspace/.cloud-setup/venv/bin/cmake --build /workspace/.cloud-setup/accepted-ownbook-baseline-release --parallel 2`
`/workspace/.cloud-setup/venv/bin/ctest --test-dir /workspace/.cloud-setup/accepted-ownbook-baseline-release --show-only=json-v1`
`/workspace/.cloud-setup/venv/bin/ctest --test-dir /workspace/.cloud-setup/accepted-ownbook-baseline-release --output-on-failure --parallel 1 --timeout 300`
`/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B /workspace/.cloud-setup/accepted-ownbook-candidate-source/validation/hourly/2026-10-20-ownbook-native/test_ownbook.py /workspace/.cloud-setup/accepted-ownbook-baseline-release/forge --expect-leak yes --out /workspace/dwqww/validation/accepted-ownbook-integration-20261020/baseline-release-attempt1/ownbook-original`

**candidate-release**

`/workspace/.cloud-setup/venv/bin/cmake -S /workspace/.cloud-setup/accepted-ownbook-candidate-source -B /workspace/.cloud-setup/accepted-ownbook-candidate-release -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=/usr/bin/g++-14 -DPython3_EXECUTABLE=/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 -DFORGE_NATIVE=OFF -DFORGE_ENABLE_SANITIZERS=OFF '-DCMAKE_CXX_FLAGS=-fno-fast-math -ffp-contract=off -fno-lto' -DCMAKE_EXPORT_COMPILE_COMMANDS=ON`
`/workspace/.cloud-setup/venv/bin/cmake --build /workspace/.cloud-setup/accepted-ownbook-candidate-release --parallel 2`
`/workspace/.cloud-setup/venv/bin/ctest --test-dir /workspace/.cloud-setup/accepted-ownbook-candidate-release --show-only=json-v1`
`/workspace/.cloud-setup/venv/bin/ctest --test-dir /workspace/.cloud-setup/accepted-ownbook-candidate-release --output-on-failure --parallel 1 --timeout 300`
`/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B /workspace/.cloud-setup/accepted-ownbook-candidate-source/validation/hourly/2026-10-20-ownbook-native/test_ownbook.py /workspace/.cloud-setup/accepted-ownbook-candidate-release/forge --expect-leak no --out /workspace/dwqww/validation/accepted-ownbook-integration-20261020/candidate-release-attempt1/ownbook-original`

**candidate-asan**

`/workspace/.cloud-setup/venv/bin/cmake -S /workspace/.cloud-setup/accepted-ownbook-candidate-source -B /workspace/.cloud-setup/accepted-ownbook-candidate-asan -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=/usr/bin/g++-14 -DPython3_EXECUTABLE=/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 -DFORGE_NATIVE=OFF -DFORGE_ENABLE_SANITIZERS=ON '-DCMAKE_CXX_FLAGS=-fno-fast-math -ffp-contract=off -fno-lto -g -fno-pie' -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_EXE_LINKER_FLAGS=-no-pie`
`/workspace/.cloud-setup/venv/bin/cmake --build /workspace/.cloud-setup/accepted-ownbook-candidate-asan --parallel 2`
`/workspace/.cloud-setup/venv/bin/ctest --test-dir /workspace/.cloud-setup/accepted-ownbook-candidate-asan --show-only=json-v1`
`/workspace/.cloud-setup/venv/bin/ctest --test-dir /workspace/.cloud-setup/accepted-ownbook-candidate-asan --output-on-failure --parallel 1 --timeout 300`
`/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B /workspace/.cloud-setup/accepted-ownbook-candidate-source/validation/hourly/2026-10-20-ownbook-native/test_ownbook.py /workspace/.cloud-setup/accepted-ownbook-candidate-asan/forge --expect-leak no --out /workspace/dwqww/validation/accepted-ownbook-integration-20261020/candidate-asan-attempt1/ownbook-original`
