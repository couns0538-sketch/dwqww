cmake_minimum_required(VERSION 3.16)
project(ChessEngineForge VERSION 6.4.18 LANGUAGES CXX)
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

add_executable(forge_bench bench/benchmark.cpp)
target_link_libraries(forge_bench PRIVATE forge_core Threads::Threads)

enable_testing()
add_test(NAME forge_tests COMMAND forge_tests)
add_test(NAME forge_correction_history_tests COMMAND forge_correction_history_tests)
add_test(NAME forge_runtime_psqt_tests COMMAND forge_runtime_psqt_tests)
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
