#include <stdio.h>
#include <stdlib.h>
/* Planted fault: heap buffer overflow, one byte past a 4-byte allocation.
   Positive control for the sanitizer build: this must produce an AddressSanitizer
   report on stderr, or the sanitizer run of the engine proves nothing. */
int main(void) {
    char* p = (char*)malloc(4);
    p[7] = 'x';
    printf("%c\n", p[7]);
    free(p);
    return 0;
}
