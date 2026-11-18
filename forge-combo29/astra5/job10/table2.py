"""Generate the zero-guard A by changed-node-count tables from job 10's matched D12 rows."""
import csv
from pathlib import Path
import sys

out = Path(sys.argv[1])
with (out/"2x2.tsv").open("x") as table, (out/"summary.txt").open("x") as summary:
    writer = csv.writer(table, delimiter="\t", lineterminator="\n")
    writer.writerow(["suite", "A_zero_counts_equal", "A_zero_counts_differ",
                     "A_nonzero_counts_equal", "A_nonzero_counts_differ"])
    for suite, length in (("O", 200), ("G", 353)):
        datasets = []
        for guard in (0, 1, 2):
            d = out/suite/("Guard"+str(guard))
            msg = (d/"checks.txt").read_text().strip()
            if "STOP" in msg:
                sys.exit(msg)
            print(msg, file=summary)
            with (d/"rows.tsv").open() as f:
                datasets.append(list(csv.DictReader(f, delimiter="\t")))
            assert len(datasets[-1]) == length
        cells = [0, 0, 0, 0]
        for zero, one, two in zip(*datasets):
            assert zero["index"] == one["index"] == two["index"]
            assert zero["fen"] == one["fen"] == two["fen"]
            acts = int(zero["t1"]) != 0
            differ = zero["nodes"] != one["nodes"]
            idx = 2*acts + differ
            cells[idx] += 1
            if idx == 1:
                print(f"STOP {suite} A(zero)=0 with changed nodes, {zero!r} {one!r}", file=summary)
        writer.writerow([suite, *cells])
        if cells[1]:
            sys.exit(1)
