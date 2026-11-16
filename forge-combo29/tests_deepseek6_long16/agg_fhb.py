import sys
places = ["rfp", "standpat", "qend", "mainend"]
tot = [[0]*4 for _ in range(4)]
n = 0
for line in open(sys.argv[1]):
    line = line.strip()
    if not line.startswith("info string FHB v1"):
        continue
    n += 1
    t = line[len("info string "):].split()
    for i, p in enumerate(places):
        j = t.index(p)
        for k in range(4):
            tot[i][k] += int(t[j + 1 + k])
print(f"searches summed: {n}")
for i, p in enumerate(places):
    print(f"{p:9s} A {tot[i][0]:8d} L {tot[i][1]:8d} R {tot[i][2]:8d} M {tot[i][3]:8d}")
