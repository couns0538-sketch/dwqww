# Full file read of dwqww commits

GitHub branch: `fable/full-read-20261114`
GitHub branch: `astra/full-read-20261114`

Every listed commit was read from local git objects after `git fetch`. GitHub compare and pull-request file listings were not used, because those APIs stop at 300 files.

One JSON object per commit, one line, under `full-read/slices/`. Commit lists are in `full-read/commit-lists/`. Checkpoints are in `full-read/status/`.

Each path has a byte size or a line count from an actual read of that blob, and a `https://github.com/couns0538-sketch/dwqww/blob/<sha>/<path>` URL. Each commit records its branch names and `https://github.com/couns0538-sketch/dwqww/tree/<branch>`. Text and source files include a summary taken from the contents (purpose, main types, functions, or data). Binary, zip, nnue, and other non-text files record kind, byte size, and that the body is not source text. Identical content hashes share one summary.

| Slice | Commits written | Commits in slice | Files opened | Text files read | Binaries | State |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `01` | 28 | 28 | 69973 | 66923 | 3050 | complete |
| `02` | 29 | 29 | 69973 | 68081 | 1892 | complete |
| `03` | 29 | 29 | 69964 | 68351 | 1613 | complete |
| `04` | 33 | 33 | 69961 | 67868 | 2093 | complete |
| `05` | 30 | 30 | 69962 | 60265 | 9697 | complete |
| `06` | 26 | 29 | 69780 | 67500 | 2280 | partial |
| `08` | 29 | 29 | 69959 | 67763 | 2196 | complete |
| `09` | 30 | 30 | 69959 | 67165 | 2794 | complete |
| `10` | 19 | 33 | 68963 | 66923 | 2040 | partial |
| `11` | 29 | 29 | 69966 | 67852 | 2114 | complete |
| `12` | 30 | 30 | 69960 | 67859 | 2101 | complete |

Slice 07 has no result file yet. Totals below count only the lines in this snapshot: **768420** files opened, **736550** text files read, **31870** binaries classified.

Slices 06 and 10 were still being written when this snapshot was taken, so their commit counts are short of the slice lists.
