# Verification commands and artifact provenance — 2026-10-19 21:45 CEST

Accepted engine SHA: `9108d012526be80c6d163f7cab684e6acd9abf8d`.
Candidate source commit: `ed06daf99875b99c9b73749b6c00bc796f8089e7`. Source blob hashes are embedded in the resulting Git commit.
Container: Debian x86_64, GCC 14.2.0, Clang 17.0.0. The complete Forge checkout and binaries were unavailable because direct GitHub DNS resolution failed. **Every executed test below is a standalone model**, not a full-engine test.

Reproduced the 21:00 bug investigator's unchanged model from original `tt_rule50_guard_model.cpp` (SHA256 `e5424f8a5bf87c265f5abe237a58277bb945ae1195eccc8cbfbae615b2b3d6bd`) with:
```bash
g++ -std=c++20 -O2 -Wall -Wextra -Wpedantic -o prior/repro_rebuilt prior/tt_rule50_guard_model.cpp
./prior/repro_rebuilt
g++ -std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -o prior/repro_asan_rebuilt prior/tt_rule50_guard_model.cpp
ASAN_OPTIONS=detect_leaks=0 ./prior/repro_asan_rebuilt
```
The outputs are in `raw/baseline_regression.log` and `raw/baseline_regression_sanitizer.log`. These reproduce **guard asymmetry**; they do not establish an incorrect chess score.

The candidate's exact `rule50_consumer_model.cpp` was downloaded via GitHub connector and locally compiled with:
```bash
g++ -std=c++20 -O2 -Wall -Wextra -Wpedantic -Wconversion -Wshadow -o rule50_model_gcc rule50_consumer_model.cpp && ./rule50_model_gcc
clang++ -std=c++20 -O2 -Wall -Wextra -Wpedantic -Wconversion -Wshadow -o rule50_model_clang rule50_consumer_model.cpp && ./rule50_model_clang
g++ -std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -o rule50_model_asan rule50_consumer_model.cpp && ASAN_OPTIONS=detect_leaks=0 ./rule50_model_asan
```
PASS three model runs. Three original outputs saved as `raw/candidate_*.log`. `raw/SHA256SUMS.txt` includes source, binaries, and logs. Local model Git blob SHA `57e241043006e661306d16190b4e118fd3eda260` equals published GitHub model blob SHA.

No full engine CMake/CTest/perft/UCI/bench, full-engine ASan/UBSan, or fastchess games were run. A proposed GitHub Actions CI workflow was rejected by GitHub tool safety restrictions; do not claim that CI was triggered or passed.

Next: independent build + FEN-based reproduction and full validation before considering integration. **DO NOT MERGE.**
