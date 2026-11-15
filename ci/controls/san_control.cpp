// Positive control for the sanitizer jobs of the Fable/Opus checks: each mode has a deliberate fault that the tool
// must report. Taken from Fable's forge/tools/san_control.cpp (2026-11-15) and given one more mode, "race", for the
// ThreadSanitizer build (Opus, 2026-11-15). A sanitizer job counts only if, built with the same compiler and flags
// as the engine, "none" prints "clean run" and exits 0 and every planted fault is reported (else the job fails).
//   AddressSanitizer + UBSan build: none | heap | stack | uaf | signed | shift
//   ThreadSanitizer build:          none | race
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <climits>
#include <thread>
#include <vector>

static int shared_counter = 0;   // written by two threads without a lock in mode "race"

int main(int argc, char** argv) {
    const char* mode = argc > 1 ? argv[1] : "none";
    if (!std::strcmp(mode, "heap")) {           // AddressSanitizer: read one element past a heap block
        std::vector<int> v(8, 1);
        volatile int i = 8;
        std::printf("%d\n", v.data()[i]);
    } else if (!std::strcmp(mode, "stack")) {   // AddressSanitizer: write past a stack array
        volatile int i = 12;
        int a[8];
        a[i] = 7;
        std::printf("%d\n", a[0]);
    } else if (!std::strcmp(mode, "uaf")) {     // AddressSanitizer: use after free
        int* p = new int[4];
        delete[] p;
        volatile int i = 1;
        std::printf("%d\n", p[i]);
    } else if (!std::strcmp(mode, "signed")) {  // UBSan: signed overflow
        volatile int x = INT_MAX;
        int y = x + 1;
        std::printf("%d\n", y);
    } else if (!std::strcmp(mode, "shift")) {   // UBSan: shift by more than the width
        volatile int s = 40;
        int y = 1 << s;
        std::printf("%d\n", y);
    } else if (!std::strcmp(mode, "race")) {    // ThreadSanitizer: two threads write one int without a lock
        std::thread a([] { for (int k = 0; k < 100000; ++k) shared_counter = k; });
        std::thread b([] { for (int k = 0; k < 100000; ++k) shared_counter = -k; });
        a.join();
        b.join();
        std::printf("%d\n", shared_counter);
    } else {
        std::printf("clean run\n");
    }
    return 0;
}
