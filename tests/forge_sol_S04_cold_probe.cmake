# S04-1 cold-start probe as a CTest target (registered by CMakeLists.txt when FORGE_ATTACKS_INIT_ONCE=ON).
# Runs the S04 cold first-Board test in RUNS fresh processes; every process constructs its first Board on
# eight threads released together by a barrier, so every iteration exercises a cold attack-table init.
# Port of Sol's forge_sol_S04_cold_runs_20261025.py (17aa0cae) to CMake script mode, so the probe needs no
# Python and runs wherever ctest runs (Linux TSan build in CI, MinGW on the PC).
# A run fails on a nonzero exit (TSan: halt_on_error=1, exit code 66), on stdout other than the one expected
# line, or on any stderr output. The probe stops at the first failing run and prints its streams.
# usage: cmake -DEXE=<cold test exe> [-DRUNS=1000] -P forge_sol_S04_cold_probe.cmake
cmake_minimum_required(VERSION 3.16)
if(NOT DEFINED EXE OR NOT EXISTS "${EXE}")
    message(FATAL_ERROR "COLD_PROBE_ERROR: -DEXE=<cold test executable> is required (got '${EXE}')")
endif()
if(NOT DEFINED RUNS)
    set(RUNS 1000)
endif()
if(NOT RUNS MATCHES "^[1-9][0-9]*$")
    message(FATAL_ERROR "COLD_PROBE_ERROR: RUNS must be a positive integer (got '${RUNS}')")
endif()
set(expected "COLD_FIRST_BOARD_PASS workers=8 startpos_d3=8902 kiwipete_d2=2039")
# Keep a caller's TSAN_OPTIONS (CI sends reports to its sanitizer log directory); otherwise halt on the
# first report with exit code 66 like Sol's probe. No suppressions are used.
if("$ENV{TSAN_OPTIONS}" STREQUAL "")
    set(ENV{TSAN_OPTIONS} "halt_on_error=1:exitcode=66")
endif()
file(SHA256 "${EXE}" exe_sha256)
message("COLD_PROBE start: runs=${RUNS} exe=${EXE} sha256=${exe_sha256} TSAN_OPTIONS=$ENV{TSAN_OPTIONS}")
string(TIMESTAMP t_start "%s" UTC)
foreach(run RANGE 1 ${RUNS})
    execute_process(COMMAND "${EXE}" RESULT_VARIABLE rc OUTPUT_VARIABLE out ERROR_VARIABLE err)
    # MinGW's text-mode stdout ends the line with CRLF; compare the stripped line.
    string(STRIP "${out}" out_line)
    if(NOT rc STREQUAL "0" OR NOT out_line STREQUAL expected OR NOT err STREQUAL "")
        message(FATAL_ERROR "COLD_PROBE_FAIL run ${run}/${RUNS}: exit=${rc}\n--- stdout ---\n${out}\n--- stderr ---\n${err}")
    endif()
    math(EXPR every100 "${run} % 100")
    if(every100 EQUAL 0)
        string(TIMESTAMP t_now "%s" UTC)
        math(EXPR elapsed "${t_now} - ${t_start}")
        message("COLD_PROBE progress ${run}/${RUNS} elapsed_s=${elapsed}")
    endif()
endforeach()
string(TIMESTAMP t_end "%s" UTC)
math(EXPR elapsed "${t_end} - ${t_start}")
message("COLD_PROBE_PASS runs=${RUNS} fresh_processes=${RUNS} workers_per_process=8 elapsed_s=${elapsed}")
