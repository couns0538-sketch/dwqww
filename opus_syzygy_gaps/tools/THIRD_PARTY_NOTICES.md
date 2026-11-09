# Third-party notices (test tools only; nothing here is linked into the engine)

## Fathom (jdart1/Fathom, commit c9c6fef0dddc05d2e242c183acf5833149ab676d)
Used as an independent test oracle (`tools/fathom_root.c` and the OSS scout's `t5_fathom_batch.c` are compiled against its
`src/tbprobe.c`). The sources are read from a local checkout at build time and not committed in this pack. Its LICENSE file
is an MIT licence ("The MIT License (MIT)"); the file stays with the checkout and is copied to `out/oracle/fathom_src/LICENSE`
next to the build. Copyright lines as in that file: Ronald de Man (2013-2018), Basil Falcinelli (2015), Jon Dart (2015-2020).

## python-chess 1.11.2 (chess.syzygy)
GPL-3.0, run as a separate program for expected values only, as in R13 P6. No code from it is copied.
