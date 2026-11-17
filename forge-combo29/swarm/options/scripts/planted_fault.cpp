// Planted faults, compiled ONLY into the sanitizer control binary.
//
// This file exists for one reason: a sanitizer run that reports nothing proves
// nothing unless the same sanitizer setup is shown to catch a fault. Each
// function below is a deliberate defect, reachable only through a test-only
// environment variable, so the audited binary never contains them: this file is
// never added to the audited target's source list.
//
//   FORGE_PLANT_ASAN=1    heap buffer overflow
//   FORGE_PLANT_UBSAN=1   signed integer overflow
#include <cstdlib>
#include <iostream>

namespace forge::plant {

namespace {

volatile int sink = 0;

__attribute__((noinline)) void heap_overflow() {
    auto* buffer = new int[4];
    for (int i = 0; i <= 4; ++i) buffer[i] = i;   // one past the end
    sink = buffer[0];
    delete[] buffer;
}

__attribute__((noinline)) void signed_overflow() {
    int value = 2147483640;
    for (int i = 0; i < 4; ++i) value += 100;     // overflows int
    sink = value;
}

} // namespace

// Returns true when a fault was planted, so the caller can exit non-zero and
// the harness can tell a caught fault from a binary that never ran the fault.
bool maybe_run_planted_fault() {
    if (const char* asan = std::getenv("FORGE_PLANT_ASAN"); asan != nullptr && *asan == '1') {
        heap_overflow();
        std::cerr << "plant: asan fault returned normally\n";
        return true;
    }
    if (const char* ubsan = std::getenv("FORGE_PLANT_UBSAN"); ubsan != nullptr && *ubsan == '1') {
        signed_overflow();
        std::cerr << "plant: ubsan fault returned normally\n";
        return true;
    }
    return false;
}

namespace {

// Run before main(), so linking this file into the control binary is the only
// change needed: the audited sources stay byte-identical to the binary under
// test, and no test hook has to be threaded through them.
struct PlantedFaultLauncher {
    PlantedFaultLauncher() {
        if (maybe_run_planted_fault()) {
            std::cerr << "plant: fault did not trap; the sanitizer is not live\n";
            std::_Exit(3);
        }
    }
};

const PlantedFaultLauncher launcher{};

} // namespace

} // namespace forge::plant
