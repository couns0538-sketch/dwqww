#include <stdlib.h>
#include <stdio.h>
int main(void) {
    int *a = malloc(4 * sizeof(int));
    for (int i = 0; i <= 4; i++) a[i] = i;      /* heap overflow: index 4 of a 4-int block */
    int x = 2147483647; x = x + 1;               /* signed overflow: UBSan */
    printf("%d %d\n", a[4], x);
    free(a);
    return 0;
}
