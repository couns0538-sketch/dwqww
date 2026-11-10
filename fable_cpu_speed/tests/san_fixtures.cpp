// san_fixtures.cpp - isolated fault fixtures for the sanitizer set-up check. One fault per -DFIXTURE value.
// They have nothing to do with the engine: they only show that the same compiler, flags and runtime that
// instrument the engine do report a fault of each kind, and stay silent on clean code.
#include <climits>
#include <cstdio>
#include <vector>

#ifndef FIXTURE
#define FIXTURE 0
#endif

int main() {
#if FIXTURE == 1    // ASan: heap-buffer-overflow (read one element past a heap array)
    volatile int n = 8;
    int* p = new int[n];
    for (int i = 0; i < n; ++i) p[i] = i;
    volatile int k = n;
    int v = p[k];
    delete[] p;
    std::printf("fixture 1 read %d\n", v);
#elif FIXTURE == 2  // ASan: stack-buffer-overflow
    int a[8];
    for (int i = 0; i < 8; ++i) a[i] = i;
    volatile int k = 10;
    std::printf("fixture 2 read %d\n", a[k]);
#elif FIXTURE == 3  // ASan: heap-use-after-free
    int* p = new int[4];
    p[0] = 7;
    delete[] p;
    volatile int k = 0;
    std::printf("fixture 3 read %d\n", p[k]);
#elif FIXTURE == 4  // UBSan: signed integer overflow
    volatile int x = INT_MAX;
    int y = x + 1;
    std::printf("fixture 4 value %d\n", y);
#elif FIXTURE == 5  // UBSan: shift exponent too large
    volatile int s = 40;
    int v = 1 << s;
    std::printf("fixture 5 value %d\n", v);
#elif FIXTURE == 6  // UBSan: array index out of bounds
    int a[4] = {1, 2, 3, 4};
    volatile int k = 6;
    std::printf("fixture 6 value %d\n", a[k]);
#else               // clean
    std::vector<int> v(8, 1);
    long s = 0;
    for (int x : v) s += x;
    std::printf("clean fixture sum %ld\n", s);
    return s == 8 ? 0 : 1;
#endif
    return 0;
}
