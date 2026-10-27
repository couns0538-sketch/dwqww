cmake_minimum_required(VERSION 3.16)
project(ChessEngineForge VERSION 6.4.24 LANGUAGES CXX)
find_package(Threads REQUIRED)

option(FORGE_ENABLE_SANITIZERS "Enable AddressSanitizer and UndefinedBehaviorSanitizer" OFF)
option(FORGE_NATIVE "Optimise for the build machine's CPU (-march=native)" OFF)
option(FORGE_EXPOSE_TUNABLES "Advertise search tuning constants as UCI options (development builds)" OFF)

option(FORGE_ATTACKS_INIT_ONCE "Synchronize the first attack-table initialization" OFF)

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

if(FORGE_ATTACKS_INIT_ONCE)
    target_compile_definitions(forge_core PRIVATE FORGE_ATTACKS_INIT_ONCE=1)
    # Cold first-Board test: the real Board and attack-table code is compiled into the test itself (not
    # forge_core), so no Board or attacks::init call runs before its eight threads meet at the barrier, and
    # the TSan variant coexists with an ASan/UBSan engine profile.
    # Linux GNU/Clang: ThreadSanitizer variant (Sol's target). Other toolchains (MinGW g++ on the PC, which
    # has no TSan; MSVC): the same source uninstrumented. It still checks every worker's perft/FEN results in
    # each fresh process, so a cold-init race that hands out half-built tables fails it.
    if(CMAKE_SYSTEM_NAME STREQUAL "Linux" AND CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        set(FORGE_S04_COLD_TARGET forge_sol_S04_cold_tsan_test_20261025)
        set(FORGE_S04_COLD_LABELS "cold-init;tsan")
    else()
        set(FORGE_S04_COLD_TARGET forge_sol_S04_cold_test_native)
        set(FORGE_S04_COLD_LABELS "cold-init;native")
    endif()
    add_executable(${FORGE_S04_COLD_TARGET}
        tests/forge_sol_S04_tsan_test_20261025.cpp
        src/bitboard.cpp src/board.cpp)
    target_include_directories(${FORGE_S04_COLD_TARGET} PRIVATE include)
    target_compile_features(${FORGE_S04_COLD_TARGET} PRIVATE cxx_std_20)
    target_compile_definitions(${FORGE_S04_COLD_TARGET} PRIVATE FORGE_ATTACKS_INIT_ONCE=1)
    target_link_libraries(${FORGE_S04_COLD_TARGET} PRIVATE Threads::Threads)
    if(FORGE_S04_COLD_TARGET STREQUAL "forge_sol_S04_cold_tsan_test_20261025")
        target_compile_options(${FORGE_S04_COLD_TARGET} PRIVATE
            -O1 -g1 -fsanitize=thread -fno-omit-frame-pointer)
        target_link_options(${FORGE_S04_COLD_TARGET} PRIVATE -fsanitize=thread)
    endif()
    enable_testing()
    add_test(NAME ${FORGE_S04_COLD_TARGET} COMMAND ${FORGE_S04_COLD_TARGET})
    # S04-2: an explicit TIMEOUT, so a hung first initialization (e.g. a call_once deadlock) fails this test
    # after 120 s instead of blocking ctest until the global --timeout or the CI job cap.
    set_tests_properties(${FORGE_S04_COLD_TARGET} PROPERTIES
        RUN_SERIAL TRUE TIMEOUT 120 LABELS "${FORGE_S04_COLD_LABELS}")
    # S04-1: the 1000-iteration cold-start probe as a ctest target: FORGE_S04_COLD_PROBE_RUNS fresh processes
    # of the cold test (driver tests/forge_sol_S04_cold_probe.cmake, stops at the first failing process).
    # Its TIMEOUT (3 s per process + 120 s) overrides ctest's --timeout default, which would cut it off.
    set(FORGE_S04_COLD_PROBE_RUNS 1000 CACHE STRING "Fresh processes in the S04 cold-start probe test")
    math(EXPR FORGE_S04_COLD_PROBE_TIMEOUT "${FORGE_S04_COLD_PROBE_RUNS} * 3 + 120")
    add_test(NAME forge_sol_S04_cold_probe
        COMMAND ${CMAKE_COMMAND} -DEXE=$<TARGET_FILE:${FORGE_S04_COLD_TARGET}>
                -DRUNS=${FORGE_S04_COLD_PROBE_RUNS}
                -P ${CMAKE_CURRENT_SOURCE_DIR}/tests/forge_sol_S04_cold_probe.cmake)
    set_tests_properties(forge_sol_S04_cold_probe PROPERTIES
        RUN_SERIAL TRUE TIMEOUT ${FORGE_S04_COLD_PROBE_TIMEOUT} LABELS "${FORGE_S04_COLD_LABELS};cold-probe")
endif()

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

add_executable(forge_bench bench/benchmark.cpp)
target_link_libraries(forge_bench PRIVATE forge_core Threads::Threads)

enable_testing()
add_test(NAME forge_tests COMMAND forge_tests)
add_test(NAME forge_correction_history_tests COMMAND forge_correction_history_tests)
add_test(NAME forge_runtime_psqt_tests COMMAND forge_runtime_psqt_tests)
add_test(NAME forge_pawn_span_tests COMMAND forge_pawn_span_tests)
add_test(NAME forge_nearest_pawn_tests COMMAND forge_nearest_pawn_tests)
add_test(NAME forge_pv_metadata_tests COMMAND forge_pv_metadata_tests)
add_test(NAME forge_tt_tests COMMAND forge_tt_tests)
add_test(NAME forge_rule50_tests COMMAND forge_rule50_tests)
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
    add_test(NAME ownbook_regression
        COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tools/ownbook_regression.py
                $<TARGET_FILE:forge> ${CMAKE_CURRENT_BINARY_DIR}/ownbook-regression.json)
endif()
