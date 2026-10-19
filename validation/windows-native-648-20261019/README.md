# Offline native Windows 6.4.8 comparison bundle

[Download the bundle](../../releases/forge-6.4.8-windows-validation-bundle.zip). ZIP SHA256: `253f33c129c0f5d4301354f755e03e876c7a76c6da18e13307facaceba7b4e73` (30,272,872 bytes;2,354 files).

This is a new manifest-verified bundle for candidate `7125b3379a850de34041d42529cf95993607f93c`, engine SHA256 `e39a240e3f7380e84c4e585013c2d602cba379f15e9e23d7a036a9712c415644`. It compares that exact tested Windows6.4.8 executable with the unmodified original6.4.0 release PE from the user's ZIP. The original reference, pinned Fastchess60d7a7a, Python3.14.8, safety runner, licenses, disjoint opening selections and stopping rules are unchanged from the immutable6.4.2 bundle; its SHA256 remains `27022666ef6e9eb14ce5b84109810be3f6caa1d97a25066409f915dd0029367c`.

Native A/A, timed pilot and paired SPRT are **pending**. No games were run for this bundle. Seven earlier standalone6.4.8 Wine checks are correctness/signature evidence only; old bundle A/A results are not results for this candidate or bundle. No equal-clock, physical-Ryzen, native Windows, Stockfish or Elo gain is established.

Extract the complete ZIP to an ASCII-only Windows path; spaces are supported. `run-validation.cmd` performs a fresh four-pair original-vs-original A/A, eight-pair10+0.1 candidate/original pilot, then serial10+0.1 paired SPRT0/5 (alpha=beta=.05, max5,000pairs) if the earlier phases pass. `run-readiness.cmd` runs A/A only. All original safety settings and strict no-resume/retry/pooling rules are unchanged. There is no installation, credential, upload or reporting setup.

`manifest.json`, candidate provenance, source snapshot hashes and bundle verification are retained here. Every bundle file except only its root manifest is listed, including both nested source opening manifests. Linux `load_bundle`, exact full inventory/hashes, ZIP CRC/member checks and source Git identity passed. Bundled Windows Python isolated imports and validator `--help` passed under Wine with all manifest bytes unchanged; those checks launch no engine or games. Detailed logs/commands are retained alongside this note.
