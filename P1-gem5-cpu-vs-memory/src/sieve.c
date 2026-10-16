#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    long n = (argc > 1) ? atol(argv[1]) : 100000000;
    char *is_composite = calloc(n + 1, 1);
    if (!is_composite) return 1;

    long count = 0;
    for (long i = 2; i <= n; i++) {
        if (!is_composite[i]) {
            count++;
            for (long j = i * i; j <= n; j += i)
                is_composite[j] = 1;
        }
    }
    printf("%ld\n", count);
    free(is_composite);
    return 0;
}