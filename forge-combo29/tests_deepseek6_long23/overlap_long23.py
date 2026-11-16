import sys, os, itertools

# deepseek6 long 23, part 2: opening overlap between matches.
# Key = the first four FEN fields (piece placement, side to move, castling, ep) — the same
# identity glmflash5's own generator used. Also reported separately for the full FEN, so a
# reader can see the key choice does not hide a difference.

D = sys.argv[1]
MATCHES = sorted(f[9:-4] for f in os.listdir(D) if f.startswith("gamelist_M") and f.endswith(".txt"))


def keys(m, full=False):
    out = set()
    for line in open(os.path.join(D, "gamelist_%s.txt" % m)):
        line = line.rstrip("\n")
        if not line:
            continue
        fen = line.split("|")[5]
        out.add(fen.strip() if full else " ".join(fen.split()[:4]))
    return out


print("matches found: %d (%s)" % (len(MATCHES), " ".join(MATCHES)))
for m in MATCHES:
    print("%s distinct openings (4-field key) = %d" % (m, len(keys(m))))

print()
print("== PAIRWISE OPENING SHARE, 4-field key (rows = matches, columns = matches)")
hdr = "      " + " ".join("%6s" % m for m in MATCHES)
print(hdr)
K = {m: keys(m) for m in MATCHES}
for a in MATCHES:
    row = ["%6d" % (len(K[a] & K[b]) if a != b else -1) for b in MATCHES]
    print("%6s" % a + " ".join(row))

print()
print("== PAIRS WITH A NON-ZERO SHARE")
nonzero = 0
for a, b in itertools.combinations(MATCHES, 2):
    n = len(K[a] & K[b])
    if n:
        nonzero += 1
        print("  %s & %s share %d of %d/%d" % (a, b, n, len(K[a]), len(K[b])))
print("nonzero pairs: %d of %d" % (nonzero, len(MATCHES) * (len(MATCHES) - 1) // 2))

print()
print("== SAME CHECK ON FULL FENs (to show the key choice does not hide a difference)")
KF = {m: keys(m, full=True) for m in MATCHES}
for a, b in itertools.combinations(MATCHES, 2):
    n = len(KF[a] & KF[b])
    if n:
        print("  %s & %s share %d full FEN(s)" % (a, b, n))
print("full-FEN nonzero pairs: %d" % sum(1 for a, b in itertools.combinations(MATCHES, 2) if KF[a] & KF[b]))
