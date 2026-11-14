// Proof for Finding 11 (LOW / UB):
// src/eval_params.cpp:22-32 — `forge::params::name(int index)` checks `if (index < KnightMobility)`
// without checking `index < 0`. Passing a negative index such as `-64` evaluates `index / 64 == -1`,
// casts `-1` to `std::size_t` (`SIZE_MAX`), and indexes the 6-element `pieces` array out of bounds
// (caught by UndefinedBehaviorSanitizer / AddressSanitizer / SIGSEGV).
//
// Build & run (ASan + UBSan):
//   g++ -std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
//     -Iforge-combo29/include forge-combo29/tests_audit/proof_eval_param_name_oob.cpp \
//     forge-combo29/src/eval_params.cpp -o /tmp/proof_eval_param_name_oob
//   /tmp/proof_eval_param_name_oob

#include "forge/eval_params.hpp"

#include <iostream>

int main() {
    volatile int idx = -64;
    const char* s = forge::params::name(idx);
    std::cout << (s != nullptr ? s : "(null)") << "\n";
    return 0;
}
