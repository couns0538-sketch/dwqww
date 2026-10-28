cmake_minimum_required(VERSION 3.16)
project(ChessEngineForge VERSION 6.4.24 LANGUAGES CXX)
find_package(Threads REQUIRED)

option(FORGE_ENABLE_SANITIZERS "Enable AddressSanitizer and UndefinedBehaviorSanitizer" OFF)
option(FORGE_NNUE_LAZY_ACC "Enable experimental NnueLazyAcc UCI option (default OFF)" OFF)
option(FORGE_NATIVE "Optimise for the build machine's CPU (-march=native)" OFF)
option(FORGE_EXPOSE_TUNABLES "Advertise search tuning constants as UCI options (development builds)" OFF)
option(FORGE_NOZERO_MOVE_BUFFERS "Leave the MoveList/MovePicker move buffers uninitialised (node-exact speed candidate)" OFF)
option(FORGE_PROF "Build opt-in search-only profiling counters" OFF)

option(FORGE_ATTACKS_INIT_ONCE "Synchronize the first attack-table initialization" OFF)

add_library(forge_core
    src/bitboard.cpp
    src/board.cpp
    src/book.cpp
    src/datagen.cpp
    src/eval.cpp
    src/eval_params.cpp
    src/nnue.cpp
    src/search.cpp
)
target_include_directories(forge_core PUBLIC include)
target_compile_features(forge_core PUBLIC cxx_std_20)
if(FORGE_NOZERO_MOVE_BUFFERS)
    target_compile_definitions(forge_core PUBLIC FORGE_NOZERO_MOVE_BUFFERS=1)
endif()

# R3 stack: the O2 NNUE accumulator kernels (opus-O2; bit-identical output) are a
# build switch, default off. PUBLIC: nnue.hpp's Accumulator alignment depends on it.
option(FORGE_NNUE_O2 "Use the O2 NNUE accumulator kernels (R3 stack build switch)" OFF)
if(FORGE_NNUE_O2)
    target_compile_definitions(forge_core PUBLIC FORGE_NNUE_O2=1)
endif()

option(FORGE_S13_TT_CHILD_PREFETCH "Build the opt-in TtChildPrefetch experiment" OFF)
if(FORGE_S13_TT_CHILD_PREFETCH)
    target_compile_definitions(forge_core PUBLIC FORGE_S13_TT_CHILD_PREFETCH=1)
endif()

# S29 speed stack: the node-exact speed pieces (S11 material-key table, S13 child TT prefetch) behind one
# compile switch, default OFF (the OFF build is the AL1 lock code).
option(FORGE_SPEEDSTACK "Build the node-exact speed stack (S29)" OFF)
if(FORGE_SPEEDSTACK)
    target_compile_definitions(forge_core PUBLIC FORGE_SPEEDSTACK=1)
endif()

# S12 null-edge accumulator alias (compile switch + UCI NnueLazyAcc), default OFF.
if(FORGE_NNUE_LAZY_ACC)
    target_compile_definitions(forge_core PUBLIC FORGE_NNUE_LAZY_ACC=1)
endif()

# S08fix profile counters (compile switch FORGE_PROF), default OFF.
if(FORGE_PROF)
    target_sources(forge_core PRIVATE src/profile.cpp)
    target_compile_definitions(forge_core PUBLIC FORGE_PROF=1)
endif()

# S04fix cold-init probe (compile switch FORGE_ATTACKS_INIT_ONCE), default OFF.
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

# S-A2 NnueInt16 (UCI NnueInt16: integer inference with the compiled-in network's int16 weights, int32
# accumulators) is a build switch, default OFF: the default build is the previous stack binary (compiled in
# unconditionally, the option cost 0.4-0.5% NPS with the option off; opus-offguard). PUBLIC: nnue.hpp's
# Accumulator layout depends on it.
option(FORGE_NNUE_INT16 "Build the NnueInt16 integer NNUE path and its UCI option (S-A2)" OFF)
if(FORGE_NNUE_INT16)
    target_compile_definitions(forge_core PUBLIC FORGE_NNUE_INT16=1)
endif()

# S-A4: another network include file instead of src/nnue_weights.inc (e.g. an H512 net); pass the
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

# Test-only engine with the hidden debug hooks (DebugSearchDelayMs) compiled in;
# the release engine above has them only in debug builds (no NDEBUG).
add_executable(forge_debughooks src/uci.cpp)
target_link_libraries(forge_debughooks PRIVATE forge_core Threads::Threads)
target_compile_definitions(forge_debughooks PRIVATE FORGE_DEBUG_HOOKS=1)

# S32 self-play datagen v2 ("forge datagen ..."). Default OFF: forge is then the unchanged engine
# (datagen.cpp sits in the static forge_core but is not linked into it). forge_datagen is the same
# engine with the command enabled, always built so CTest/CI exercise the datagen path.
option(FORGE_DATAGEN "Enable the 'forge datagen' self-play command line mode in the forge executable" OFF)
if(FORGE_DATAGEN)
    target_compile_definitions(forge PRIVATE FORGE_DATAGEN=1)
endif()
add_executable(forge_datagen src/uci.cpp)
target_link_libraries(forge_datagen PRIVATE forge_core Threads::Threads)
target_compile_definitions(forge_datagen PRIVATE FORGE_DATAGEN=1)
add_executable(forge_datagen_tests tests/datagen_tests.cpp)
target_link_libraries(forge_datagen_tests PRIVATE forge_core Threads::Threads)

add_executable(forge_tests tests/tests.cpp)
target_link_libraries(forge_tests PRIVATE forge_core Threads::Threads)

add_executable(forge_tt_tests tests/tt_coherence_tests.cpp)
target_link_libraries(forge_tt_tests PRIVATE forge_core Threads::Threads)

add_executable(forge_intended_threefold_tests tests/intended_threefold_tests.cpp)
target_link_libraries(forge_intended_threefold_tests PRIVATE forge_core Threads::Threads)

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
# NNUE parity: current kernels against a verbatim copy of the AL1 s198 code.
add_executable(forge_nnue_parity_tests tests/nnue_parity_tests.cpp)
target_link_libraries(forge_nnue_parity_tests PRIVATE forge_core Threads::Threads)

# S13: includes the actual src/search.cpp with its TT prefetch redirected to a
# counter, so the archive's own search.cpp object is never linked (link map).
add_executable(forge_tt_prefetch_probe tests/tt_prefetch_probe_tests.cpp)
target_link_libraries(forge_tt_prefetch_probe PRIVATE forge_core Threads::Threads)
if(NOT MSVC)
    target_link_options(forge_tt_prefetch_probe PRIVATE "-Wl,-Map=${CMAKE_CURRENT_BINARY_DIR}/forge_tt_prefetch_probe.map")
endif()

add_executable(forge_material_key_tests tests/material_key_tests.cpp)
target_link_libraries(forge_material_key_tests PRIVATE forge_core Threads::Threads)
# S41 NetScale: apply() arithmetic and the actual Worker::static_evaluate path at every scale.
add_executable(forge_net_scale_tests tests/net_scale_tests.cpp)
target_link_libraries(forge_net_scale_tests PRIVATE forge_core Threads::Threads)

# UCI HistRework (Astra A1): helpers, overflow bounds, glue and max-value searches.
add_executable(forge_hist_rework_tests tests/hist_rework_tests.cpp)
target_link_libraries(forge_hist_rework_tests PRIVATE forge_core Threads::Threads)

# S-A2 NnueInt16 (build switch FORGE_NNUE_INT16, UCI NnueInt16). The integer path is compiled only with the
# switch, so its tests compile the NNUE sources themselves with it (and with the core's FORGE_NNUE_O2 state):
# every configuration builds and tests the integer path, and the default forge stays the switch-off binary.
function(forge_nnue_int16_test_sources target)
    target_sources(${target} PRIVATE src/bitboard.cpp src/board.cpp src/nnue.cpp)
    target_include_directories(${target} PRIVATE include)
    target_compile_features(${target} PRIVATE cxx_std_20)
    target_compile_definitions(${target} PRIVATE FORGE_NNUE_INT16=1)
    if(FORGE_NNUE_O2)
        target_compile_definitions(${target} PRIVATE FORGE_NNUE_O2=1)
    endif()
    if(NOT MSVC)
        target_compile_options(${target} PRIVATE -ffp-contract=off)
        if(FORGE_NATIVE)
            target_compile_options(${target} PRIVATE -march=native)
        endif()
        if(FORGE_ENABLE_SANITIZERS)
            target_compile_options(${target} PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer)
            target_link_options(${target} PRIVATE -fsanitize=address,undefined)
        endif()
    endif()
endfunction()

add_executable(forge_nnue_int16_tests tests/nnue_int16_tests.cpp)
forge_nnue_int16_test_sources(forge_nnue_int16_tests)

# The same NnueInt16 tests on the scalar integer kernels: the NNUE sources are
# compiled again without AVX2 (the float path then uses its SSE kernel, which is
# bit-identical by design), so builds for AVX2 targets also cover the fallback.
if(NOT MSVC)
    add_executable(forge_nnue_int16_scalar_tests tests/nnue_int16_tests.cpp)
    forge_nnue_int16_test_sources(forge_nnue_int16_scalar_tests)
    target_compile_options(forge_nnue_int16_scalar_tests PRIVATE -mno-avx2)
endif()
# S-A4: both use the core's network include file when FORGE_NNUE_WEIGHTS_FILE is set.
if(FORGE_NNUE_WEIGHTS_FILE)
    target_compile_definitions(forge_nnue_int16_tests PRIVATE FORGE_NNUE_WEIGHTS="${FORGE_NNUE_WEIGHTS_FILE}")
    if(NOT MSVC)
        target_compile_definitions(forge_nnue_int16_scalar_tests PRIVATE FORGE_NNUE_WEIGHTS="${FORGE_NNUE_WEIGHTS_FILE}")
    endif()
endif()

if(NOT MSVC)
    # H512 (S-A4): the same tests on a generated synthetic 512-unit network (not a playing net),
    # with the NNUE sources compiled for FORGE_NNUE_HIDDEN=512; the default build keeps H256.
    add_executable(forge_nnue_gen_net tests/nnue_gen_net.cpp)
    set(FORGE_H512_TEST_NET ${CMAKE_CURRENT_BINARY_DIR}/nnue_test_h512.inc)
    add_custom_command(OUTPUT ${FORGE_H512_TEST_NET}
        COMMAND forge_nnue_gen_net 512 20261027 ${FORGE_H512_TEST_NET}
        DEPENDS forge_nnue_gen_net VERBATIM)
    add_custom_target(forge_nnue_test_h512_net DEPENDS ${FORGE_H512_TEST_NET})
    add_executable(forge_nnue_h512_tests tests/nnue_int16_tests.cpp)
    forge_nnue_int16_test_sources(forge_nnue_h512_tests)
    add_dependencies(forge_nnue_h512_tests forge_nnue_test_h512_net)
    target_compile_definitions(forge_nnue_h512_tests PRIVATE FORGE_NNUE_WEIGHTS="${FORGE_H512_TEST_NET}")
    target_compile_options(forge_nnue_h512_tests PRIVATE -UFORGE_NNUE_HIDDEN -DFORGE_NNUE_HIDDEN=512)
endif()

# The engine for the NnueInt16 UCI regression: forge itself in a FORGE_NNUE_INT16 build, else forge_int16 =
# the core's sources and settings plus FORGE_NNUE_INT16=1 (built in every configuration, never released).
if(FORGE_NNUE_INT16)
    set(FORGE_NNUE_INT16_ENGINE forge)
else()
    get_target_property(FORGE_CORE_SOURCES forge_core SOURCES)
    add_library(forge_core_int16 STATIC ${FORGE_CORE_SOURCES})
    target_include_directories(forge_core_int16 PUBLIC include)
    target_compile_features(forge_core_int16 PUBLIC cxx_std_20)
    target_compile_definitions(forge_core_int16 PUBLIC FORGE_NNUE_INT16=1
        $<TARGET_PROPERTY:forge_core,INTERFACE_COMPILE_DEFINITIONS>)
    target_compile_options(forge_core_int16 PRIVATE $<TARGET_PROPERTY:forge_core,COMPILE_OPTIONS>
        INTERFACE $<TARGET_PROPERTY:forge_core,INTERFACE_COMPILE_OPTIONS>)
    target_link_options(forge_core_int16 INTERFACE $<TARGET_PROPERTY:forge_core,INTERFACE_LINK_OPTIONS>)
    add_executable(forge_int16 src/uci.cpp)
    target_link_libraries(forge_int16 PRIVATE forge_core_int16 Threads::Threads)
    if(FORGE_EXPOSE_TUNABLES)
        target_compile_definitions(forge_int16 PRIVATE FORGE_EXPOSE_TUNABLES=1)
    endif()
    set(FORGE_NNUE_INT16_ENGINE forge_int16)
endif()

add_executable(forge_bench bench/benchmark.cpp)
target_link_libraries(forge_bench PRIVATE forge_core Threads::Threads)

# S37: NNUE inference microbench (its own target; the forge executable is unchanged). CTest runs the
# consistency checks only (replica == engine output, incremental == refresh, whole eval == HCE + net).
add_executable(forge_nnue_microbench tools/nnue_microbench.cpp)
target_link_libraries(forge_nnue_microbench PRIVATE forge_core Threads::Threads)

enable_testing()
if(FORGE_PROF)
    add_executable(forge_prof_tests tests/prof_tests.cpp)
    target_link_libraries(forge_prof_tests PRIVATE forge_core Threads::Threads)
    add_test(NAME forge_prof_tests COMMAND forge_prof_tests)
    # S08-2: the test runs Threads 1/2/4 profiled searches; bound it explicitly (TSan builds are slow).
    set_tests_properties(forge_prof_tests PROPERTIES TIMEOUT 600)
endif()
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
add_test(NAME forge_nnue_parity_tests COMMAND forge_nnue_parity_tests
    --fens ${CMAKE_CURRENT_SOURCE_DIR}/tests/data/nnue_selfplay_sample_916.txt)
add_test(NAME forge_hist_rework_tests COMMAND forge_hist_rework_tests)
add_test(NAME forge_nnue_int16_tests COMMAND forge_nnue_int16_tests)
if(NOT MSVC)
    add_test(NAME forge_nnue_int16_scalar_tests COMMAND forge_nnue_int16_scalar_tests)
    add_test(NAME forge_nnue_h512_tests COMMAND forge_nnue_h512_tests)
endif()
add_test(NAME forge_tt_tests COMMAND forge_tt_tests)
add_test(NAME forge_tt_stress_lockless COMMAND forge_tt_stress_tests --threads 2 --ops 2000000 --mode lockless)
add_test(NAME forge_tt_stress_locked COMMAND forge_tt_stress_tests --threads 2 --ops 2000000 --mode locked)
add_test(NAME forge_intended_threefold_tests COMMAND forge_intended_threefold_tests)
add_test(NAME forge_rule50_tests COMMAND forge_rule50_tests)
add_test(NAME forge_syzygy_tests COMMAND forge_syzygy_tests
    ${CMAKE_CURRENT_SOURCE_DIR}/tests/syzygy_fixtures.tsv ${CMAKE_CURRENT_SOURCE_DIR}/tests/syzygy_reference.tsv
    ${FORGE_SYZYGY_PATH})
add_test(NAME forge_tt_prefetch_probe COMMAND forge_tt_prefetch_probe)
add_test(NAME forge_material_key_tests COMMAND forge_material_key_tests
    ${CMAKE_CURRENT_SOURCE_DIR}/tools/openings/forge-10000.epd)
add_test(NAME forge_net_scale_tests COMMAND forge_net_scale_tests)
add_test(NAME forge_datagen_tests COMMAND forge_datagen_tests ${CMAKE_CURRENT_BINARY_DIR}/datagen_unit)
add_test(NAME forge_nnue_microbench_check COMMAND forge_nnue_microbench --check-only --positions 2000
    --wac ${CMAKE_CURRENT_SOURCE_DIR}/tools/nnue_microbench_wac300.epd)
add_test(NAME forge_legal_witness_tests COMMAND forge_legal_witness_tests
    ${CMAKE_CURRENT_SOURCE_DIR}/tests/legal_witness_fixtures.tsv
    ${CMAKE_CURRENT_SOURCE_DIR}/tools/openings/forge-10000.epd)
# Sol's null-edge accumulator alias regression test (S12, v2); only builds with the alias compiled in.
if(FORGE_NNUE_LAZY_ACC)
    add_executable(forge_s12_lazyacc_tests tests/forge_sol_S12_lazyacc_native_regression_v2_20261027.cpp)
    target_link_libraries(forge_s12_lazyacc_tests PRIVATE forge_core Threads::Threads)
    add_test(NAME forge_s12_lazyacc_tests COMMAND forge_s12_lazyacc_tests)
    add_executable(forge_s12_lazyacc_extra_tests tests/s12_lazyacc_extra_tests.cpp)
    target_link_libraries(forge_s12_lazyacc_extra_tests PRIVATE forge_core Threads::Threads)
    add_test(NAME forge_s12_lazyacc_extra_tests COMMAND forge_s12_lazyacc_extra_tests)
endif()

# S29 speed stack: checks for the stack's pieces, built and run in both configurations. Kept in its own block
# so the speed-stack patch also applies on top of Sol's node-identical buffix (base B), which adds a test next
# to forge_pv_metadata_tests.
add_executable(forge_speedstack_tests tests/speedstack_tests.cpp)
target_link_libraries(forge_speedstack_tests PRIVATE forge_core Threads::Threads)
add_test(NAME forge_speedstack_tests COMMAND forge_speedstack_tests
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
    add_test(NAME datagen_cli_tests
        COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tests/datagen_cli_tests.py
                $<TARGET_FILE:forge_datagen> ${CMAKE_CURRENT_BINARY_DIR}/datagen_cli)
    # S-A2: the NnueInt16 option on a switch-on engine; the default forge (switch off) must not list it.
    add_test(NAME nnue_int16_uci_regression
        COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tools/nnue_int16_regression.py
                $<TARGET_FILE:${FORGE_NNUE_INT16_ENGINE}>)
    if(NOT FORGE_NNUE_INT16)
        add_test(NAME nnue_int16_uci_absent
            COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tools/nnue_int16_regression.py
                    --absent $<TARGET_FILE:forge>)
    endif()
endif()
