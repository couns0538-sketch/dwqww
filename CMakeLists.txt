cmake_minimum_required(VERSION 3.16)
project(ChessEngineForge VERSION 6.4.24 LANGUAGES CXX)
find_package(Threads REQUIRED)

option(FORGE_ENABLE_SANITIZERS "Enable AddressSanitizer and UndefinedBehaviorSanitizer" OFF)
option(FORGE_NATIVE "Optimise for the build machine's CPU (-march=native)" OFF)
option(FORGE_EXPOSE_TUNABLES "Advertise search tuning constants as UCI options (development builds)" OFF)

add_library(forge_core
    src/bitboard.cpp
    src/board.cpp
    src/book.cpp
    src/eval.cpp
    src/eval_params.cpp
    src/nnue.cpp
    src/search.cpp
)
target_include_directories(forge_core PUBLIC include)
target_compile_features(forge_core PUBLIC cxx_std_20)

if(MSVC)
    target_compile_options(forge_core PRIVATE /W4 /permissive-)
else()
    target_compile_options(forge_core PRIVATE -Wall -Wextra -Wpedantic -Wconversion -Wshadow)
    # The NNUE accumulators are floats: forbid fused multiply-add contraction so
    # that every build (native, x86-64-v2/v3, Zen 4) searches the same tree.
    target_compile_options(forge_core PUBLIC -ffp-contract=off)
    if(FORGE_NATIVE)
        target_compile_options(forge_core PUBLIC -march=native)
    endif()
    if(FORGE_ENABLE_SANITIZERS)
        target_compile_options(forge_core PUBLIC -fsanitize=address,undefined -fno-omit-frame-pointer)
        target_link_options(forge_core PUBLIC -fsanitize=address,undefined)
    endif()
endif()

add_executable(forge src/uci.cpp)
target_link_libraries(forge PRIVATE forge_core Threads::Threads)
if(FORGE_EXPOSE_TUNABLES)
    target_compile_definitions(forge PRIVATE FORGE_EXPOSE_TUNABLES=1)
endif()

# Test-only engine with the hidden debug hooks (DebugSearchDelayMs) compiled in;
# the release engine above has them only in debug builds (no NDEBUG).
add_executable(forge_debughooks src/uci.cpp)
target_link_libraries(forge_debughooks PRIVATE forge_core Threads::Threads)
target_compile_definitions(forge_debughooks PRIVATE FORGE_DEBUG_HOOKS=1)

add_executable(forge_tests tests/tests.cpp)
target_link_libraries(forge_tests PRIVATE forge_core Threads::Threads)

add_executable(forge_tt_tests tests/tt_coherence_tests.cpp)
target_link_libraries(forge_tt_tests PRIVATE forge_core Threads::Threads)

add_executable(forge_rule50_tests tests/rule50_tests.cpp)
target_link_libraries(forge_rule50_tests PRIVATE forge_core Threads::Threads)

add_executable(forge_legal_witness_tests tests/legal_witness_tests.cpp)
target_link_libraries(forge_legal_witness_tests PRIVATE forge_core Threads::Threads)

add_executable(forge_correction_history_tests tests/correction_history_tests.cpp)
target_link_libraries(forge_correction_history_tests PRIVATE forge_core Threads::Threads)

add_executable(forge_runtime_psqt_tests tests/runtime_psqt_tests.cpp)
target_link_libraries(forge_runtime_psqt_tests PRIVATE forge_core Threads::Threads)

add_executable(forge_pawn_span_tests tests/pawn_span_tests.cpp)
target_link_libraries(forge_pawn_span_tests PRIVATE forge_core Threads::Threads)

add_executable(forge_nearest_pawn_tests tests/nearest_pawn_tests.cpp)
target_link_libraries(forge_nearest_pawn_tests PRIVATE forge_core Threads::Threads)

add_executable(forge_pv_metadata_tests tests/pv_metadata_tests.cpp)
target_link_libraries(forge_pv_metadata_tests PRIVATE forge_core Threads::Threads)

# Search module unit tests (move picker stages, history math, time management).
add_executable(forge_movepicker_tests tests/movepicker_tests.cpp)
target_include_directories(forge_movepicker_tests PRIVATE src)
target_link_libraries(forge_movepicker_tests PRIVATE forge_core Threads::Threads)

add_executable(forge_history_tests tests/history_tests.cpp)
target_link_libraries(forge_history_tests PRIVATE forge_core Threads::Threads)

add_executable(forge_timeman_tests tests/timeman_tests.cpp)
target_include_directories(forge_timeman_tests PRIVATE src)
target_link_libraries(forge_timeman_tests PRIVATE forge_core Threads::Threads)

# Lazy SMP housekeeping and SMP options (O1).
add_executable(forge_smp_tests tests/smp_tests.cpp)
target_link_libraries(forge_smp_tests PRIVATE forge_core Threads::Threads)

# Multi-thread TT stress (O1-LTT, UCI LocklessTT).
add_executable(forge_tt_stress_tests tests/tt_stress_tests.cpp)
target_link_libraries(forge_tt_stress_tests PRIVATE forge_core Threads::Threads)
# Syzygy tablebase tests (job C1). Tablebase files are not in the repository:
# pass a folder with FORGE_SYZYGY_PATH (cache variable or environment variable),
# otherwise only the checks that need no table files run.
set(FORGE_SYZYGY_PATH "" CACHE PATH "Syzygy tablebase folder used by forge_syzygy_tests (optional)")
add_executable(forge_syzygy_tests tests/syzygy_tests.cpp)
target_link_libraries(forge_syzygy_tests PRIVATE forge_core Threads::Threads)

# v2 networks (king buckets): bucket map / mirroring, loader, lock replicas, incremental == refresh.
add_executable(forge_nnue_v2_tests tests/nnue_v2_tests.cpp)
target_include_directories(forge_nnue_v2_tests PRIVATE src)
target_link_libraries(forge_nnue_v2_tests PRIVATE forge_core Threads::Threads)

# UCI-level fail-loud checks of the v2 options (drives the forge executable through stdin).
add_executable(forge_nnue_v2_uci_tests tests/nnue_v2_uci_tests.cpp)
target_link_libraries(forge_nnue_v2_uci_tests PRIVATE forge_core Threads::Threads)
add_dependencies(forge_nnue_v2_uci_tests forge)

# Export parity helper for v2 nets (tools/nnue/v2_parity.py): position generator and engine-side evaluator.
add_executable(forge_nnue_v2_tool tools/nnue/nnue_v2_tool.cpp)
target_link_libraries(forge_nnue_v2_tool PRIVATE forge_core Threads::Threads)

# O6 (UCI NNUEThreats): threat pairs vs brute force, features, loader, rules, zero-threat lock replicas,
# incremental == refresh on 102k plies, UCI checks (drives the forge executable).
add_executable(forge_nnue_threat_tests tests/nnue_threat_tests.cpp)
target_include_directories(forge_nnue_threat_tests PRIVATE src)
target_link_libraries(forge_nnue_threat_tests PRIVATE forge_core Threads::Threads)
add_dependencies(forge_nnue_threat_tests forge)

# O7 (UCI NNUEPawnPairs): pawn pairs vs brute force, symmetry, loader, rules, zero-pawn-pair lock replicas,
# incremental == refresh on 102k plies (also with threats), UCI checks (drives the forge executable).
add_executable(forge_nnue_pawn_pair_tests tests/nnue_pawn_pair_tests.cpp)
target_include_directories(forge_nnue_pawn_pair_tests PRIVATE src)
target_link_libraries(forge_nnue_pawn_pair_tests PRIVATE forge_core Threads::Threads)
add_dependencies(forge_nnue_pawn_pair_tests forge)

# O4 (UCI PureNnue): selection / fail-loud rules, the network-only evaluation path, search and UCI checks
# (drives the forge executable), and the engine-level evaluator of the PyTorch -> engine parity chain.
add_executable(forge_pure_nnue_tests tests/pure_nnue_tests.cpp)
target_link_libraries(forge_pure_nnue_tests PRIVATE forge_core Threads::Threads)
add_dependencies(forge_pure_nnue_tests forge)
add_executable(forge_nnue_engine_eval tools/nnue/nnue_engine_eval.cpp)
target_link_libraries(forge_nnue_engine_eval PRIVATE forge_core Threads::Threads)
# UCI CorrMargins: correction-size pruning margins (margin functions, node decisions, whole searches).
add_executable(forge_corr_margins_tests tests/corr_margins_tests.cpp)
target_link_libraries(forge_corr_margins_tests PRIVATE forge_core Threads::Threads)
# UCI CorrExt: correction-history extensions (decision rule, per-path budget, node decisions, whole searches).
add_executable(forge_corr_ext_tests tests/corr_ext_tests.cpp)
target_link_libraries(forge_corr_ext_tests PRIVATE forge_core Threads::Threads)
# C6 CuckooRep: cuckoo table, upcoming-repetition detector vs brute force, search bound.
add_executable(forge_cuckoo_tests tests/cuckoo_tests.cpp)
target_link_libraries(forge_cuckoo_tests PRIVATE forge_core Threads::Threads)

add_executable(forge_bench bench/benchmark.cpp)
target_link_libraries(forge_bench PRIVATE forge_core Threads::Threads)

enable_testing()
add_test(NAME forge_tests COMMAND forge_tests)
add_test(NAME forge_correction_history_tests COMMAND forge_correction_history_tests)
add_test(NAME forge_runtime_psqt_tests COMMAND forge_runtime_psqt_tests)
add_test(NAME forge_pawn_span_tests COMMAND forge_pawn_span_tests)
add_test(NAME forge_nearest_pawn_tests COMMAND forge_nearest_pawn_tests)
add_test(NAME forge_pv_metadata_tests COMMAND forge_pv_metadata_tests)
add_test(NAME forge_movepicker_tests COMMAND forge_movepicker_tests)
add_test(NAME forge_history_tests COMMAND forge_history_tests)
add_test(NAME forge_timeman_tests COMMAND forge_timeman_tests)
add_test(NAME forge_smp_tests COMMAND forge_smp_tests)
add_test(NAME forge_nnue_v2_tests COMMAND forge_nnue_v2_tests)
add_test(NAME forge_nnue_v2_uci_tests COMMAND forge_nnue_v2_uci_tests $<TARGET_FILE:forge>)
add_test(NAME forge_nnue_threat_tests COMMAND forge_nnue_threat_tests $<TARGET_FILE:forge>)
add_test(NAME forge_nnue_pawn_pair_tests COMMAND forge_nnue_pawn_pair_tests $<TARGET_FILE:forge>)
add_test(NAME forge_pure_nnue_tests COMMAND forge_pure_nnue_tests $<TARGET_FILE:forge>)
add_test(NAME forge_corr_margins_tests COMMAND forge_corr_margins_tests)
add_test(NAME forge_corr_ext_tests COMMAND forge_corr_ext_tests)
add_test(NAME forge_cuckoo_tests COMMAND forge_cuckoo_tests)
add_test(NAME forge_tt_tests COMMAND forge_tt_tests)
add_test(NAME forge_tt_stress_lockless COMMAND forge_tt_stress_tests --threads 2 --ops 2000000 --mode lockless)
add_test(NAME forge_tt_stress_locked COMMAND forge_tt_stress_tests --threads 2 --ops 2000000 --mode locked)
add_test(NAME forge_rule50_tests COMMAND forge_rule50_tests)
add_test(NAME forge_syzygy_tests COMMAND forge_syzygy_tests
    ${CMAKE_CURRENT_SOURCE_DIR}/tests/syzygy_fixtures.tsv ${CMAKE_CURRENT_SOURCE_DIR}/tests/syzygy_reference.tsv
    ${FORGE_SYZYGY_PATH})
add_test(NAME forge_legal_witness_tests COMMAND forge_legal_witness_tests
    ${CMAKE_CURRENT_SOURCE_DIR}/tests/legal_witness_fixtures.tsv
    ${CMAKE_CURRENT_SOURCE_DIR}/tools/openings/forge-10000.epd)

# Support tooling does not change engine behavior or add runtime dependencies.
option(FORGE_BUILD_VALIDATION_TOOLS "Build the original opening corpus generator" OFF)
if(FORGE_BUILD_VALIDATION_TOOLS)
    add_executable(forge_openings tools/generate_openings.cpp)
    target_link_libraries(forge_openings PRIVATE forge_core)
endif()
option(FORGE_BUILD_TUNING_TOOLS "Build the evaluation tuning tools (position extractor and Texel tuner)" OFF)
if(FORGE_BUILD_TUNING_TOOLS)
    add_executable(forge_extract tools/tune/extract.cpp)
    target_link_libraries(forge_extract PRIVATE forge_core)
    add_executable(forge_texel tools/tune/texel.cpp)
    target_link_libraries(forge_texel PRIVATE forge_core Threads::Threads)
    add_executable(forge_nnue_train tools/tune/nnue_train.cpp)
    target_link_libraries(forge_nnue_train PRIVATE forge_core Threads::Threads)
    add_executable(forge_bookgen tools/book/bookgen.cpp)
    target_link_libraries(forge_bookgen PRIVATE forge_core Threads::Threads)
endif()
find_package(Python3 3.10 COMPONENTS Interpreter QUIET)
if(Python3_Interpreter_FOUND)
    add_test(NAME match_tool_tests
        COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tools/match/test_match_tools.py)
    add_test(NAME windows_validation_tests
        COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tools/match/tests/test_windows_validate.py)
    add_test(NAME uci_regression
        COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tools/uci_regression.py
                $<TARGET_FILE:forge> --log ${CMAKE_CURRENT_BINARY_DIR}/uci-regression.log)
    add_test(NAME ponder_regression
        COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tools/ponder_regression.py
                $<TARGET_FILE:forge>)
    # HardDeadline watchdog: exactly one legal bestmove per go when the watchdog races the search (C3);
    # starved searches need the DebugSearchDelayMs hook, so the test engine is forge_debughooks.
    add_test(NAME hard_deadline_regression
        COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tools/hard_deadline_regression.py
                $<TARGET_FILE:forge_debughooks> --iterations 60 --threads 1 --grace 1 --reference $<TARGET_FILE:forge>)
    add_test(NAME ownbook_regression
        COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tools/ownbook_regression.py
                $<TARGET_FILE:forge> ${CMAKE_CURRENT_BINARY_DIR}/ownbook-regression.json)
endif()
