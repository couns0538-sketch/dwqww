// O4 positive control: a program whose faults ASan+UBSan must report.
#include <cstdlib>
int main() {
    int* p = static_cast<int*>(std::malloc(4 * sizeof(int)));
    p[4] = 1;            // heap-buffer-overflow (ASan)
    int x = 1 << 31;     // shifts into sign bit... use signed overflow instead
    int big = 2147483647;
    x = big + 1;         // signed integer overflow (UBSan)
    (void)x;
    return p[4];
}
