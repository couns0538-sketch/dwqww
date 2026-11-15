// A tiny planted-fault program for the sanitizer harness itself: it must be
// reported by ASan (heap overflow) and by UBSan (signed overflow). If it is not,
// the sanitizer build proves nothing about the engine.
#include <cstdio>
#include <cstdint>
int main(int argc, char**) {
    int* a = new int[4];
    a[argc + 3] = 7;                       // heap-buffer-overflow
    std::int32_t big = 2147483647;
    big = big + argc;                      // signed overflow
    std::printf("%d %d\n", a[0] > 0 ? 1 : 0, big > 0 ? 1 : 0);
    return 0;
}
