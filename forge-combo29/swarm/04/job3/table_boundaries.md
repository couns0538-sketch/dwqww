# iteration boundaries — the node count at the END of each finished depth
# measured with: python3 job3/boundaries.py <exe> /tmp/bnd <tag> --settings pc20 --depth D --fen FEN
# PC r15 / PC20 / Threads 1 / Hash 16; BOTH runs identical at every depth (checked in the script)
# these are the numbers to use, with the position named — they are position-specific, not universal

## startpos rnbqkbnr/... (opening)  (pc20, 18 iterations)

| depth | nodes at end of depth | score |
|---|---|---|
| 1 | 26 | 1 |
| 2 | 59 | 39 |
| 3 | 133 | 10 |
| 4 | 412 | 8 |
| 5 | 971 | 9 |
| 6 | 1740 | 18 |
| 7 | 4121 | 32 |
| 8 | 6170 | 22 |
| 9 | 7131 | 20 |
| 10 | 8569 | 20 |
| 11 | 13604 | 16 |
| 12 | 21600 | 25 |
| 13 | 28565 | 19 |
| 14 | 46854 | 14 |
| 15 | 78579 | 21 |
| 16 | 104892 | 20 |
| 17 | 166281 | 13 |
| 18 | 377485 | 15 |

boundaries: 26, 59, 133, 412, 971, 1740, 4121, 6170, 7131, 8569, 13604, 21600, 28565, 46854, 78579, 104892, 166281, 377485

## ordinary middlegame G 1r6/2k2pp1/...  (pc20, 17 iterations)

| depth | nodes at end of depth | score |
|---|---|---|
| 1 | 67 | -336 |
| 2 | 171 | -324 |
| 3 | 286 | -293 |
| 4 | 626 | -317 |
| 5 | 775 | -317 |
| 6 | 1574 | -303 |
| 7 | 2671 | -306 |
| 8 | 3891 | -306 |
| 9 | 5852 | -299 |
| 10 | 9155 | -304 |
| 11 | 19832 | -287 |
| 12 | 31779 | -293 |
| 13 | 52904 | -272 |
| 14 | 97289 | -292 |
| 15 | 121306 | -283 |
| 16 | 170070 | -273 |
| 17 | 288912 | -292 |

boundaries: 67, 171, 286, 626, 775, 1574, 2671, 3891, 5852, 9155, 19832, 31779, 52904, 97289, 121306, 170070, 288912
