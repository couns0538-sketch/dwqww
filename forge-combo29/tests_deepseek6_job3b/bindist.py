#!/usr/bin/env python3
"""bindist.py -- the deficit distribution for one L, from a counters file.

Usage: bindist.py COUNTERSFILE L
Prints one line per non-empty bin: "bin <label> <count>", then the total.
Bin 0 is "e < 0", bin k (1..30) is "(k-1)*100 .. (k-1)*100+99", bin 32 is ">= 3000".
"""
import re, sys
BIN=re.compile(r"\bb(\d+)((?:\s+\d+)+)")
def main():
    path, L = sys.argv[1], int(sys.argv[2])
    tot=[0]*33
    for line in open(path):
        if "cfp" not in line: continue
        for idx, vals in BIN.findall(line):
            if int(idx)!=L: continue
            for k,v in enumerate(vals.split()):
                if k<33: tot[k]+=int(v)
    n=0
    for k,c in enumerate(tot):
        if c:
            lab = "e<0" if k==0 else (">=3000" if k==32 else "%d..%d"%((k-1)*100,(k-1)*100+99))
            print("bin %-9s %6d"% (lab,c)); n+=c
    print("total %d"%n)
if __name__=="__main__": main()
