# Forge S27 patch-hygiene pre-check — 2026-10-26

This standalone Python 3.10+ tool checks an exact patch or ZIP against explicitly
named source trees. It changes no accepted engine. Static mode runs Git and GNU
patch only; it never runs an engine, compiler, training job or PC script.

## Files and normal use

Keep `forge_sol_S27_hygiene_20261026.py` and
`forge_sol_S27_known_hashes_20261026.json` together. Native comparison additionally
uses the sibling `forge_sol_S27_buildcompare_20261026.py`.

```sh
python3 -B forge_sol_S27_hygiene_20261026.py candidate.patch \
  --base Lp=/path/to/current_Lprime --base B=/path/to/current_B \
  --out /path/to/NEW_OUTPUT_FOLDER
```

Without a history argument the bundled catalogue of prior submissions is used.
Use `--history FILE.json` for an explicit list or the typed catalogue schema.
`--empty-history` is deliberate: use it for controlled tests of already-known
patches, not as evidence that a candidate has passed the ordinary duplicate gate.
All history values are full SHA256 strings. The result records the selected role,
entries and canonical history digest. Exact raw-input, contained-patch and ZIP
member-content hashes are checked; renaming or wrapping a reviewed patch does
not conceal its hash.

Exit 0 means the requested checks passed, exit 1 means findings were recorded,
and exit 2 means invalid invocation/output/history. Static FAIL includes an
explicit unverified guard/configuration finding rather than calling unsupported
source constructs safe. The new output contains a dated result and lossless
base64 command records with argv, cwd, exit, byte lengths and stream SHA256s.
Findings and the static signature are deterministic for identical input bytes,
source inventories, history and tool behavior. Raw execution paths are separate.

## Input and apply policy

* Output must be new, canonical, outside every input tree and outside protected
  baseline, lock, distribution and Git metadata directories.
* Input paths are conservative POSIX repository paths. Quoted/space-containing
  patch paths and ambiguous formats fail rather than being guessed. The output
  folder itself may contain spaces.
* Traversals, absolute/drive/backslash/NUL paths, protected targets, Git metadata,
  symlinks, special files, renames, gitlinks, binary changes, duplicate/casefold
  ZIP entries, encrypted members and resource-limit violations are rejected.
* ZIP input is either one patch with explicitly ignored `.md`, `.txt` or `.rst`
  attachments, or a source overlay. Mixed patch/source layouts are rejected.
  An overlay is converted into a checked unified patch; applied bytes must equal
  the requested member bytes. Omission from an overlay does not delete a file.
* Every declared base is frozen, copied to private reference/candidate trees,
  checked by `git apply --check`, dry-run/applied with GNU `patch -p1 -F0`, and
  rehashed. The actual changed-file set must equal the parsed patch targets.
  Accepted input trees and their Git metadata are not edited.
* Limits are 8 MiB input/member, 32 MiB per base source tree, 64 MiB expanded ZIP,
  2,048 files and 200:1 compression above 1 MiB. These are limits, not claims that
  arbitrarily large repositories were tested. Pass the engine source export,
  not a checkout containing large archives or build products.

The notice/vendor checks examine added text and changed files. Identical inherited
source files are not relabelled as new licensing. Hostile notice fixtures are
created at test runtime from fragments; their literal payloads are not delivered.
Documentation with abbreviated prefix/ellipsis/suffix digests is rejected.

## Default-build and option checks

The source checker tracks simple compile guards, literal CMake OFF options,
visible macro definitions and commented/string-contained false guards. Unknown
preprocessor values fail closed. New default instrumentation, advertised runtime
options and bench statistics have distinct findings. Runtime setters are checked
against literal typed Forge UCI advertisements using case-insensitive names.
CMake-only test switches are reported separately and do not require UCI options.

This is a heuristic over Forge's literal registration style. It is not a complete
C++/CMake interpreter, include resolver, semantic-equivalence proof or general
sandbox. Bracket CMake forms and multiline quoted constructs are explicitly
unsupported when they could bless production/configuration changes. Global or
engine-target compile configuration changes and option overrides require review
unless guarded out in the supported form. Unsupported dynamic registries or
complex macro/include behavior need independent source/native review.

The optional build-and-compare helper is requested explicitly:

```sh
python3 -B forge_sol_S27_hygiene_20261026.py known_test_only.patch \
  --base Lp=/path/to/current_Lprime --empty-history \
  --build-compare --cmake /path/to/cmake --out /path/to/NEW_NATIVE_OUTPUT
```

It is blocked by static findings. It receives private trees only, records actual
source/build/runtime evidence and compares default symbols, typed UCI metadata
and strict fixed-node bench output. Time and NPS fields are not speed evidence.
Executing supplied CMake/C++ is opt-in and is not made into an arbitrary-code
sandbox by the source-path checks. Native test execution and its verdict are
reported separately from the static tests; no speed or Elo claim follows.

## Historical required controls

The buffer repair and Job C are already present in the merged current trees.
Their positive controls therefore use explicitly historical pre-patch scratch
bases, never a reset or replacement of current accepted Lprime/B. Unit controls
use exact complete bytes of the real patch-target files and are labelled as
file views, not full source/build qualification.

The sole storage-correctness control exemption requires all of: exact supplied
buffer-patch SHA256, the supplied same-diff review bytes with their authenticated
SHA256, explicit `--control-role approved_buffix_control`, and exactly its three
expected paths. It exempts only that `src/search.cpp` guard finding. It does not
bypass content, paths, application, history or any other rule. No arbitrary
approval label or changed patch can acquire this exemption.

```sh
python3 -B forge_sol_S27_hygiene_20261026.py exact_buffer.patch \
  --base historical_L=/path/to/pristine_L --empty-history \
  --control-role approved_buffix_control --review-record exact_review.txt \
  --out /path/to/NEW_CONTROL_OUTPUT
```

The independent repeat-hash control inserts that same patch hash into history
and must fail. Job C runs with empty history against historical L and L+buffix
before Job C. Job A's actual unguarded counters, runtime option and bench stats
must each be detected even if other findings also exist. No shelved backend is
compiled, activated or adopted for the static controls.

## Idea sources and validation

Idea sources only: the user's S27 specification and reviewed Forge handoffs;
existing original Forge S25 strict UCI/bench-contract test design; GNU patch and
Git apply behavior; Python standard-library ZIP/path/process APIs. All new
implementation and rule values are written for this task. No foreign engine
code or tuned chess constants are used. The fixed engine-node oracle is the
user's supplied lock reference, not a value inferred from candidate output.

Run the full tool suite:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_*.py'
```

The completed core test run is 47/47; the then-current combined core/helper suite
is 58/58. The actual supplied historical controls, original RED observations and
corrected GREEN runs are retained in dated logs and JSONL control captures. The
final root native qualification/report decides whether the helper mode was
actually exercised. Native Windows, PC speed, Elo and S27 engine-strength changes
are not claimed by this source/tool delivery.
