# A3 bundle validation — 2026-10-29

`tools/check_bundle_opts.py` runs the supplied executable with `uci`/`quit`, requires `uciok` and successful exit within a finite timeout, and checks a JSON option specification or repeated `--require` names. Names/types/ranges/defaults supplied in the spec are exact requirements; additional advertised options are permitted. Malformed and duplicate advertisements/spec fields fail. Native Windows executables are supported when run on Windows with Python; this session exercised Linux only.

Example:

```sh
python3 tools/check_bundle_opts.py /path/to/forge --spec astra_evidence/A3/expected_options.json
bash tests/bundle_off_identity.sh /path/to/exact-base /path/to/candidate \
  --off SmpProtectProvenScore=false --output /new/evidence/directory
```

The OFF comparator uses fresh processes with Threads=1, Hash=16 and OwnBook=false, defaults to d11/13/16/20/22, and applies optional `--off NAME=false|0` settings only to the candidate. Other settings retain fresh-process defaults; the caller supplies any extra bundle-specific OFF settings. It checks both handshakes, exactly one bench record of the requested depth, positive node count, clean exit, timeout, option errors, identical nodes, and unchanged executable hashes. Output directories must be new. Raw stdin/stdout/stderr bytes and hashes are retained; timings/NPS are evidence only, not a speed claim.

Native reference is `opus-r3-stack` da15814975e224e770f4d25195e0551d02afae48; candidate binary is the qualified A2 build. A3 changes tools/tests only. `expected_options.json` accepts the candidate and correctly rejects the base because it lacks SmpProtectProvenScore.

Tests: 17 option-checker tests and 10 OFF-comparator tests pass. Both are registered with CTest and pass. The earlier full 54-suite A2 run is retained in A2 evidence, including its known and overshoot failures; it is not relabelled green. Independent review findings for byte preservation, readiness and malformed duplicates were reproduced and fixed; RED/GREEN logs are retained. The option checker's whitespace regression is likewise retained.

IDEA_SOURCE: Owner A3, public UCI protocol, and Forge's own bench interface. No engine code was copied from another project.

Final native OFF comparison: **PASS**, all five depths on both real executables. Full per-run numbers (including the pre-review native run) are in the tables below; no timing comparison is inferred.

## Initial script

| Mode | Depth | Nodes | Time ms | NPS |
|---|---:|---:|---:|---:|
| base | 11 | 312866 | 475 | 658665 |
| candidate | 11 | 312866 | 327 | 956776 |
| base | 13 | 862329 | 894 | 964573 |
| candidate | 13 | 862329 | 852 | 1012123 |
| base | 16 | 3024920 | 2883 | 1049226 |
| candidate | 16 | 3024920 | 4397 | 687950 |
| base | 20 | 12389307 | 24013 | 515941 |
| candidate | 20 | 12389307 | 12216 | 1014186 |
| base | 22 | 34048354 | 33892 | 1004613 |
| candidate | 22 | 34048354 | 38291 | 889199 |

## Final reviewed script

| Mode | Depth | Nodes | Time ms | NPS |
|---|---:|---:|---:|---:|
| base | 11 | 312866 | 304 | 1029164 |
| candidate | 11 | 312866 | 308 | 1015798 |
| base | 13 | 862329 | 841 | 1025361 |
| candidate | 13 | 862329 | 905 | 952849 |
| base | 16 | 3024920 | 2782 | 1087318 |
| candidate | 16 | 3024920 | 3180 | 951232 |
| base | 20 | 12389307 | 24529 | 505088 |
| candidate | 20 | 12389307 | 11184 | 1107770 |
| base | 22 | 34048354 | 31215 | 1090768 |
| candidate | 22 | 34048354 | 41959 | 811467 |
