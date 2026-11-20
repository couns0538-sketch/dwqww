#!/usr/bin/env python3
"""Turn a partner row file into a search_set tsv.

Accepts a headerless file whose second column is the node count,
or a tsv that already has a nodes header.
"""
import sys

def main():
    src = sys.argv[1]
    dst = sys.argv[2]
    rows = []
    with open(src, encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            parts = text.split("\t") if "\t" in text else text.split()
            if parts[0] == "index":
                continue
            nodes = parts[1]
            depth = parts[2] if len(parts) > 2 else ""
            best = parts[-1] if len(parts) > 3 else ""
            rows.append((len(rows) + 1, nodes, depth, best))
    with open(dst, "w", encoding="utf-8") as handle:
        handle.write("index\tnodes\tdepth\tbestmove\n")
        for index, nodes, depth, best in rows:
            handle.write(f"{index}\t{nodes}\t{depth}\t{best}\n")
    print("rows", len(rows))

if __name__ == "__main__":
    main()
