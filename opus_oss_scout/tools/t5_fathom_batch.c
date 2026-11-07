/* t5_fathom_batch.c - OSS scout trial T5 (own code around Fathom, MIT, https://github.com/jdart1/Fathom):
 * probe every FEN of a file with Fathom and print one line per FEN, in the order of the file:
 *   "<wdl> <dtz> <status>"   wdl in -2..2 (loss, blessed loss, draw, cursed win, win) from tb_probe_wdl,
 *                            dtz = signed root DTZ from tb_probe_root (sign from its WDL; 0 for draws),
 *                            status ok | mate | stalemate | failed
 * and to stderr the table count and the timing of a pure WDL-probe pass over all parsed positions (warm, second pass).
 * usage: t5_fathom_batch <tables dir> <fens file> [passes]
 * Build: gcc -O2 -std=c11 -march=x86-64-v3 -I<fathom>/src t5_fathom_batch.c <fathom>/src/tbprobe.c -o t5_fathom_batch.exe
 */
#include "tbprobe.h"

#include <ctype.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef struct {
    uint64_t white, black, kings, queens, rooks, bishops, knights, pawns;
    unsigned rule50, castling, ep;
    int turn;
    int ok;
} Pos;

static int parse_fen(const char *fen, Pos *p) {
    memset(p, 0, sizeof *p);
    int rank = 7, file = 0;
    const char *c = fen;
    for (; *c && *c != ' '; c++) {
        if (*c == '/') { rank--; file = 0; continue; }
        if (isdigit((unsigned char)*c)) { file += *c - '0'; continue; }
        if (rank < 0 || file > 7) return 0;
        uint64_t b = 1ULL << (rank * 8 + file);
        int white = isupper((unsigned char)*c);
        switch (tolower((unsigned char)*c)) {
            case 'k': p->kings |= b; break;
            case 'q': p->queens |= b; break;
            case 'r': p->rooks |= b; break;
            case 'b': p->bishops |= b; break;
            case 'n': p->knights |= b; break;
            case 'p': p->pawns |= b; break;
            default: return 0;
        }
        if (white) p->white |= b; else p->black |= b;
        file++;
    }
    if (*c != ' ') return 0;
    c++;
    p->turn = (*c == 'w');
    while (*c && *c != ' ') c++;
    if (*c == ' ') c++;
    /* castling */
    if (*c && *c != '-') {
        for (; *c && *c != ' '; c++) {
            if (*c == 'K') p->castling |= TB_CASTLING_K;
            else if (*c == 'Q') p->castling |= TB_CASTLING_Q;
            else if (*c == 'k') p->castling |= TB_CASTLING_k;
            else if (*c == 'q') p->castling |= TB_CASTLING_q;
        }
    } else if (*c) c++;
    while (*c == ' ') c++;
    if (*c && *c != '-' && c[1]) {
        int f = c[0] - 'a', r = c[1] - '1';
        if (f >= 0 && f < 8 && r >= 0 && r < 8) p->ep = (unsigned)(r * 8 + f);
        c += 2;
    } else if (*c) c++;
    while (*c == ' ') c++;
    p->rule50 = (unsigned)strtoul(c, NULL, 10);
    p->ok = 1;
    return 1;
}

static double now_sec(void) {
    struct timespec ts;
    timespec_get(&ts, TIME_UTC);
    return (double)ts.tv_sec + ts.tv_nsec * 1e-9;
}

int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: t5_fathom_batch <tables dir> <fens file> [passes]\n"); return 2; }
    int passes = argc > 3 ? atoi(argv[3]) : 2;
    if (!tb_init(argv[1]) || TB_LARGEST == 0) { fprintf(stderr, "tb_init failed or no tables in %s\n", argv[1]); return 2; }
    fprintf(stderr, "Fathom: TB_LARGEST %u\n", TB_LARGEST);
    FILE *f = fopen(argv[2], "r");
    if (!f) { fprintf(stderr, "cannot open %s\n", argv[2]); return 2; }
    size_t cap = 1024, n = 0;
    Pos *pos = malloc(cap * sizeof *pos);
    char line[512];
    while (fgets(line, sizeof line, f)) {
        size_t L = strlen(line);
        while (L && (line[L - 1] == '\n' || line[L - 1] == '\r')) line[--L] = 0;
        if (!L) continue;
        if (n == cap) { cap *= 2; pos = realloc(pos, cap * sizeof *pos); }
        parse_fen(line, &pos[n]);
        n++;
    }
    fclose(f);
    if (n == 0) { fprintf(stderr, "no FENs in %s\n", argv[2]); return 2; }
    /* output pass: WDL + root DTZ per FEN */
    for (size_t i = 0; i < n; i++) {
        Pos *p = &pos[i];
        if (!p->ok) { printf("NA NA failed\n"); continue; }
        unsigned w = tb_probe_wdl(p->white, p->black, p->kings, p->queens, p->rooks, p->bishops, p->knights, p->pawns,
                                  p->rule50, p->castling, p->ep, p->turn);
        unsigned r = tb_probe_root(p->white, p->black, p->kings, p->queens, p->rooks, p->bishops, p->knights, p->pawns,
                                   p->rule50, p->castling, p->ep, p->turn, NULL);
        int wdl = (w == TB_RESULT_FAILED) ? 99 : (int)w - 2;
        if (r == TB_RESULT_FAILED) { printf("%d NA failed\n", wdl); continue; }
        if (r == TB_RESULT_CHECKMATE) { printf("%d 0 mate\n", wdl); continue; }
        if (r == TB_RESULT_STALEMATE) { printf("%d 0 stalemate\n", wdl); continue; }
        int rw = (int)TB_GET_WDL(r) - 2;
        int dtz = (int)TB_GET_DTZ(r);
        int sdtz = rw > 0 ? dtz : (rw < 0 ? -dtz : 0);
        printf("%d %d ok\n", wdl, sdtz);
    }
    /* timing: pure WDL probes, all positions, several passes (the first warms the mapped files) */
    volatile unsigned sink = 0;
    for (int pass = 1; pass <= passes; pass++) {
        double t0 = now_sec();
        for (size_t i = 0; i < n; i++) {
            Pos *p = &pos[i];
            if (!p->ok) continue;
            sink += tb_probe_wdl(p->white, p->black, p->kings, p->queens, p->rooks, p->bishops, p->knights, p->pawns,
                                 p->rule50, p->castling, p->ep, p->turn);
        }
        double t1 = now_sec();
        fprintf(stderr, "pass %d: %zu WDL probes in %.3f s = %.3f us/probe\n", pass, n, t1 - t0, (t1 - t0) * 1e6 / (double)n);
    }
    (void)sink;
    tb_free();
    free(pos);
    return 0;
}
