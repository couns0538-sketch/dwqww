cmake_minimum_required(VERSION 3.16)
project(forge_hlm_root_oracle LANGUAGES CXX)

set(FORGE_PROBE_TREE "" CACHE PATH "Scratch k12 probe or control tree")
if(NOT EXISTS "${FORGE_PROBE_TREE}/include/forge/hlm_probe.hpp")
  message(FATAL_ERROR "FORGE_PROBE_TREE must contain include/forge/hlm_probe.hpp")
endif()

set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)
add_subdirectory("${FORGE_PROBE_TREE}" forge-config EXCLUDE_FROM_ALL)

add_executable(hlm_roots hlm_roots.cpp
  "${FORGE_PROBE_TREE}/src/bitboard.cpp"
  "${FORGE_PROBE_TREE}/src/board.cpp")
set_target_properties(hlm_roots PROPERTIES
  CXX_STANDARD 20 CXX_STANDARD_REQUIRED ON CXX_EXTENSIONS OFF)
target_include_directories(hlm_roots PRIVATE "$<TARGET_PROPERTY:forge,INCLUDE_DIRECTORIES>")
target_compile_definitions(hlm_roots PRIVATE "$<TARGET_PROPERTY:forge,COMPILE_DEFINITIONS>")
target_compile_options(hlm_roots PRIVATE "$<TARGET_PROPERTY:forge,COMPILE_OPTIONS>")
target_link_libraries(hlm_roots PRIVATE Threads::Threads)
