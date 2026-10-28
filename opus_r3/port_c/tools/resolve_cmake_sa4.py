"""Resolve the int16/H512 test-target block of CMakeLists.txt in the opus-sol-SA4 merge (R3 port C).

Replaces everything from `add_executable(forge_nnue_int16_tests ...)` up to (not including)
`add_executable(forge_bench ...)` with the union: SA2's two int16 test targets (sources compiled with the
build switch), SA4's FORGE_NNUE_WEIGHTS_FILE propagation to both, SA4's H512 net generator and H512 test
target (same helper, plus its own net and FORGE_NNUE_HIDDEN=512), then the switch-on engine for the UCI
regression.
usage: python -I -B resolve_cmake_sa4.py <CMakeLists.txt>
"""
import pathlib
import sys

NEW_BLOCK = """add_executable(forge_nnue_int16_tests tests/nnue_int16_tests.cpp)
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

"""


def main():
    p = pathlib.Path(sys.argv[1])
    s = p.read_bytes().decode("utf-8")
    assert "\r\n" not in s
    start_marker = "add_executable(forge_nnue_int16_tests tests/nnue_int16_tests.cpp)\n"
    end_marker = "add_executable(forge_bench bench/benchmark.cpp)\n"
    assert s.count(start_marker) == 1 and s.count(end_marker) == 1
    a = s.index(start_marker)
    e = s.index(end_marker)
    old = s[a:e]
    assert "<<<<<<< HEAD" in old and ">>>>>>> origin/opus-sol-SA4" in old
    s = s[:a] + NEW_BLOCK + s[e:]
    assert "<<<<<<<" not in s and ">>>>>>>" not in s and "\n=======\n" not in s
    p.write_bytes(s.encode("utf-8"))
    print("resolved", p)


if __name__ == "__main__":
    main()
