#include <cstdio>
#include <cstring>
int main() {
    char* buf = new char[8];
    std::memset(buf, 0x41, 9);          // heap overflow: ASan must report
    int x = 1;
    int* p = &x;
    delete[] buf;
    std::printf("%d\n", *p + (int)buf[0]);  // heap-use-after-free: ASan must report
    return 0;
}
