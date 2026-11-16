import random, glob, os

# Job 22 openings: the book minus EVERY opening used in any of my match lists
# (jobs 2..21 and standing 1). The used set comes from GLOBBING every
# gamelist_*.txt in my own tests folders - complete by construction, no
# hand-maintained list to get wrong.

def key(fen):
    return " ".join(fen.split()[:4])

repo = "/agent/repos/dwqww/forge-combo29"
used = set()
files = sorted(glob.glob(f"{repo}/tests_glmflash5_*/gamelist_*.txt"))
for path in files:
    for line in open(path):
        fen = line.rstrip("\n").split("|")[5]
        if fen and fen != "?":
            used.add(key(fen))

book = [l.rstrip("\n") for l in open("/tmp/evid/UHO_Lichess_4852_v1.epd")]
kept = [l for l in book if key(l) not in used]
rng = random.Random(41003)
rng.shuffle(kept)
sel = kept[:5000]
with open("/tmp/evid/openings_queue3.epd", "w") as f:
    f.write("\n".join(sel) + "\n")

print(f"gamelist files read: {len(files)}")
print(f"lines in book: {len(book)}")
print(f"openings used in jobs 2-27, standing 1-2, queue 1-2 (distinct first-4-field FENs): {len(used)}")
print(f"lines left after removing them: {len(kept)}")
print(f"written to openings_queue3.epd: {len(sel)} lines")
