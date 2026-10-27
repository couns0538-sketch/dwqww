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
# Another network include file instead of src/nnue_weights.inc (e.g. an H512 net); pass the
# matching -DFORGE_NNUE_HIDDEN in CMAKE_CXX_FLAGS. Unset (default) = the lock's H256 net.
set(FORGE_NNUE_WEIGHTS_FILE "" CACHE FILEPATH "Network include file (default: src/nnue_weights.inc)")
if(FORGE_NNUE_WEIGHTS_FILE)
    target_compile_definitions(forge_core PUBLIC FORGE_NNUE_WEIGHTS="${FORGE_NNUE_WEIGHTS_FILE}")
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

add_executable(forge_nnue_int16_tests tests/nnue_int16_tests.cpp)
target_link_libraries(forge_nnue_int16_tests PRIVATE forge_core Threads::Threads)

# The same NnueInt16 tests on the scalar integer kernels: the NNUE sources are
# compiled again without AVX2 (the float path then uses its SSE kernel, which is
# bit-identical by design), so builds for AVX2 targets also cover the fallback.
if(NOT MSVC)
    add_executable(forge_nnue_int16_scalar_tests tests/nnue_int16_tests.cpp src/bitboard.cpp src/board.cpp src/nnue.cpp)
    target_include_directories(forge_nnue_int16_scalar_tests PRIVATE include)
    target_compile_features(forge_nnue_int16_scalar_tests PRIVATE cxx_std_20)
    target_compile_options(forge_nnue_int16_scalar_tests PRIVATE -ffp-contract=off -mno-avx2)
    if(FORGE_ENABLE_SANITIZERS)
        target_compile_options(forge_nnue_int16_scalar_tests PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer)
        target_link_options(forge_nnue_int16_scalar_tests PRIVATE -fsanitize=address,undefined)
    endif()
    if(FORGE_NNUE_WEIGHTS_FILE)
        target_compile_definitions(forge_nnue_int16_scalar_tests PRIVATE FORGE_NNUE_WEIGHTS="${FORGE_NNUE_WEIGHTS_FILE}")
    endif()

    # H512 (S-A4): the same tests on a generated synthetic 512-unit network (not a playing net),
    # with the NNUE sources compiled for FORGE_NNUE_HIDDEN=512; the default build keeps H256.
    add_executable(forge_nnue_gen_net tests/nnue_gen_net.cpp)
    set(FORGE_H512_TEST_NET ${CMAKE_CURRENT_BINARY_DIR}/nnue_test_h512.inc)
    add_custom_command(OUTPUT ${FORGE_H512_TEST_NET}
        COMMAND forge_nnue_gen_net 512 20261027 ${FORGE_H512_TEST_NET}
        DEPENDS forge_nnue_gen_net VERBATIM)
    add_custom_target(forge_nnue_test_h512_net DEPENDS ${FORGE_H512_TEST_NET})
    add_executable(forge_nnue_h512_tests tests/nnue_int16_tests.cpp src/bitboard.cpp src/board.cpp src/nnue.cpp)
    add_dependencies(forge_nnue_h512_tests forge_nnue_test_h512_net)
    target_include_directories(forge_nnue_h512_tests PRIVATE include)
    target_compile_features(forge_nnue_h512_tests PRIVATE cxx_std_20)
    target_compile_definitions(forge_nnue_h512_tests PRIVATE FORGE_NNUE_WEIGHTS="${FORGE_H512_TEST_NET}")
    target_compile_options(forge_nnue_h512_tests PRIVATE -ffp-contract=off -UFORGE_NNUE_HIDDEN -DFORGE_NNUE_HIDDEN=512)
    if(FORGE_ENABLE_SANITIZERS)
        target_compile_options(forge_nnue_h512_tests PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer)
        target_link_options(forge_nnue_h512_tests PRIVATE -fsanitize=address,undefined)
    endif()
endif()

add_executable(forge_bench bench/benchmark.cpp)
target_link_libraries(forge_bench PRIVATE forge_core Threads::Threads)

enable_testing()
add_test(NAME forge_tests COMMAND forge_tests)
add_test(NAME forge_correction_history_tests COMMAND forge_correction_history_tests)
add_test(NAME forge_runtime_psqt_tests COMMAND forge_runtime_psqt_tests)
add_test(NAME forge_pawn_span_tests COMMAND forge_pawn_span_tests)
add_test(NAME forge_nearest_pawn_tests COMMAND forge_nearest_pawn_tests)
add_test(NAME forge_pv_metadata_tests COMMAND forge_pv_metadata_tests)
add_test(NAME forge_nnue_int16_tests COMMAND forge_nnue_int16_tests)
if(NOT MSVC)
    add_test(NAME forge_nnue_int16_scalar_tests COMMAND forge_nnue_int16_scalar_tests)
    add_test(NAME forge_nnue_h512_tests COMMAND forge_nnue_h512_tests)
endif()
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
    add_test(NAME nnue_int16_uci_regression
        COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tools/nnue_int16_regression.py
                $<TARGET_FILE:forge>)
endif()
