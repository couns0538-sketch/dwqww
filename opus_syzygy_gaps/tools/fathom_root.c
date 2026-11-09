/* fathom_root.c - own test tool around Fathom (MIT, https://github.com/jdart1/Fathom, see THIRD_PARTY_NOTICES.md):
 * one line per FEN: "<root wdl with the FEN's clock> <dtz> <status> <uci:wdl:dtz ...>", from tb_probe_root.
 * wdl in -2..2 (loss, blessed loss, draw, cursed win, win). status ok | mate | stalemate | failed.
 * Not linked into the engine. Build: gcc -O2 -std=c11 -march=x86-64-v3 -I<fathom> fathom_root.c <fathom>/tbprobe.c -static
 */
#include "tbprobe.h"

#include <ctype.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    uint64_t white, black, kings, queens, rooks, bishops, knights, pawns;
    unsigned rule50, castling, ep;
    int turn;
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
    while (*c == ' ') c++;
    if (*c == '-') c++;
    else for (; *c && *c != ' '; c++) {
        if (*c == 'K') p->castling |= TB_CASTLING_K;
        else if (*c == 'Q') p->castling |= TB_CASTLING_Q;
        else if (*c == 'k') p->castling |= TB_CASTLING_k;
        else if (*c == 'q') p->castling |= TB_CASTLING_q;
    }
    while (*c == ' ') c++;
    if (*c && *c != '-' && c[1]) {
        int f = c[0] - 'a', r = c[1] - '1';
        if (f >= 0 && f < 8 && r >= 0 && r < 8) p->ep = (unsigned)(r * 8 + f);
        c += 2;
    } else if (*c) c++;
    while (*c == ' ') c++;
    p->rule50 = (unsigned)strtoul(c, NULL, 10);
    return 1;
}

int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: fathom_root <tables dir> <fens file>\n"); return 2; }
    if (!tb_init(argv[1]) || TB_LARGEST == 0) { fprintf(stderr, "tb_init failed\n"); return 2; }
    fprintf(stderr, "Fathom: TB_LARGEST %u\n", TB_LARGEST);
    FILE *f = fopen(argv[2], "r");
    if (!f) { fprintf(stderr, "cannot open %s\n", argv[2]); return 2; }
    static unsigned results[TB_MAX_MOVES];
    static const char promo[] = { 0, 'q', 'r', 'b', 'n' };
    char line[512];
    while (fgets(line, sizeof line, f)) {
        size_t L = strlen(line);
        while (L && (line[L - 1] == '\n' || line[L - 1] == '\r')) line[--L] = 0;
        if (!L || line[0] == '#') continue;
        Pos p;
        if (!parse_fen(line, &p)) { printf("NA NA failed\n"); continue; }
        unsigned r = tb_probe_root(p.white, p.black, p.kings, p.queens, p.rooks, p.bishops, p.knights, p.pawns,
                                   p.rule50, p.castling, p.ep, p.turn, results);
        if (r == TB_RESULT_FAILED) { printf("NA NA failed\n"); continue; }
        if (r == TB_RESULT_CHECKMATE) { printf("-2 0 mate\n"); continue; }
        if (r == TB_RESULT_STALEMATE) { printf("0 0 stalemate\n"); continue; }
        int rw = (int)TB_GET_WDL(r) - 2;
        printf("%d %d ok", rw, (int)TB_GET_DTZ(r));
        for (unsigned i = 0; i < TB_MAX_MOVES && results[i] != TB_RESULT_FAILED; i++) {
            unsigned m = results[i];
            unsigned from = TB_GET_FROM(m), to = TB_GET_TO(m), pr = TB_GET_PROMOTES(m);
            printf(" %c%c%c%c", 'a' + (from & 7), '1' + (from >> 3), 'a' + (to & 7), '1' + (to >> 3));
            if (pr && pr < 5) printf("%c", promo[pr]);
            printf(":%d:%d", (int)TB_GET_WDL(m) - 2, (int)TB_GET_DTZ(m));
        }
        printf("\n");
    }
    fclose(f);
    tb_free();
    return 0;
}
