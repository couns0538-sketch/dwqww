import random

def key(fen):
    return " ".join(fen.split()[:4])

used = set()
for path in ["gamelist_K0.txt", "gamelist_K1.txt", "gamelist_M1.txt", "gamelist_M3.txt", "gamelist_M4.txt", "gamelist_M5.txt", "gamelist_S1.txt", "gamelist_S2.txt", "gamelist_S3.txt", "gamelist_M2b.txt", "gamelist_M9.txt", "gamelist_M10.txt", "gamelist_M11.txt", "gamelist_M2j9.txt",
             "gamelist_K0b.txt", "gamelist_M1b.txt", "gamelist_M2.txt",
             "gamelist_S1.txt", "gamelist_T1.txt", "gamelist_M1.txt", "gamelist_M3.txt", "gamelist_M4.txt", "gamelist_M5.txt", "gamelist_S1.txt", "gamelist_S2.txt", "gamelist_S3.txt", "gamelist_M2b.txt", "gamelist_M9.txt", "gamelist_M10.txt", "gamelist_M11.txt", "gamelist_M2j9.txt", "gamelist_M1.txt"]:
    for line in open(path):
        fen = line.rstrip("\n").split("|")[5]
        used.add(key(fen))

book = [l.rstrip("\n") for l in open("UHO_Lichess_4852_v1.epd")]
kept = [l for l in book if key(l) not in used]
rng = random.Random(9990)
rng.shuffle(kept)
sel = kept[:5000]
with open("openings_job13.epd", "w") as f:
    f.write("\n".join(sel) + "\n")

print(f"lines in book: {len(book)}")
print(f"openings used in jobs 2+3+5+6+7+8+9+10+11+12 (distinct first-4-field FENs): {len(used)}")
print(f"lines left after removing them: {len(kept)}")
print(f"written to openings_job13.epd: {len(sel)} lines")
