// Planted fault for the sanitizer check: a heap-buffer-overflow WRITE that
// AddressSanitizer must report. Not part of the engine.
#include <new>
int main() {
    int* a = new int[4];
    a[7] = 42;
    int r = a[0];
    delete[] a;
    return r;
}
