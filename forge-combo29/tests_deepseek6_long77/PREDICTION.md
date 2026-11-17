long 77 prediction -- written after the mechanism runs had already started, so it is in arrears; the honest note: the item's spec (file 17) has no prediction-first line and I treated it as a proof-of-mechanics, but my session rule asks for this file before the first counted run; I missed that. Recorded as it is.

1. The two planted faults fire at the planted lines only: the FEN with fullmove 4242 gives an
   ASan heap-buffer-overflow at board.cpp:355 (inside set_fen); `go depth 77` gives a UBSan
   signed-integer-overflow at uci.cpp:107 and the search continues. Kill: either fault fires
   on ordinary input.
2. The four honesty numbers of the planted sanitizer build equal the unplanted sanitizer
   build's: `go bench 11` = 312,866, `go bench 13` = 862,329, `go bench 16` = 3,024,920
   (the bench argument is DEPTH, not hash -- uci.cpp:592-595), and startpos perft 5 =
   4,865,609. Kill: any difference.
3. The same runner (fuzzuci78.py, updated to capture stderr and count sanitizer lines in a
   san_count column) counts both planted faults: the 4242 row san_count > 0 with
   AddressSanitizer, the depth-77 row san_count = 1 with the runtime error; the control row
   san_count = 0. Kill: a fault the runner does not count.
4. The updated runner reproduces the long 78 plant exactly: 200/200 illegal, san_count 0 on
   all 200 (the fake engine prints nothing to stderr).
