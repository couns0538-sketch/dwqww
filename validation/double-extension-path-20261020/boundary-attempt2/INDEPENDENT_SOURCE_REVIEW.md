# Independent synthetic boundary-fixture source review

No blocking defect found in the fixture's seed mechanism or independent path
counter. This is a static source review, not a build or runtime result. Only
this file was written; no engine, compiler, Git mutation or production edit ran.

The frozen baseline is cecf0b9e3af5602053bcaf5c5d16ffc09f58850d. Both exported
boundary search files match SOURCE-PROVENANCE.json: baseline SHA256
7076a5032cdd3afe58bba611fa57f567dbaa9fafeacd97511a52be70b4ad2f35,
proposal ff49a18e938371f8846ed0dda1ab0b6299b7dd842048b2efc4872e35445490ca.
The additions/removals in the two boundary-only patches are mechanically
identical (29 lines; hunk locations differ). Their complete tuning namespaces
are byte-identical. The <=6 eligibility threshold and singular score margins
are not changed by this boundary decorator.

At each actual Worker search, all stack counts are initialized as before. The
fixture then overrides only stack_[3], the root frame's parent sentinel, with
an environment-selected6 or7. The independent shadow starts at that same
ancestral value. Unset environment preserves zero; other values abort. Extra
maximum/counter fields and stderr traces are diagnostic observations, not search
inputs. This is an artificial already-consumed ancestry, not a legal normal-root
initialization or evidence of a naturally occurring overflow.

The shadow advances from its own prior path count plus the actual extension
choice. It never reads the production double_extensions field to derive its
expected value. Null and ProbCut edges copy the independent incoming count;
ordinary child edges add one only for extension==2. Same-ply verification keeps
the same shadow index. Production fields are read only for comparisons/traces
and the separate actual maximum. This tests bookkeeping consistency; it does
not independently decide whether a chess extension is desirable.

At seed6, a nonzero double-extension count and maximum true/actual count7
exercise permission for one additional double extension per path. At seed7,
zero double extensions plus zero mismatches/limit breaches support denial along
all traversed paths. These are meaningful only with a nontrivial workload.
The inherited run-boundary.py assertions do not explicitly require nonzero
children or singular attempts in the seeded cases; require/report those counts
when executing. More narrowly, max7 is initialized by seed7, so max7 plus zero
doubles alone could pass without any margin-qualified double-extension
opportunity. An independent opportunity counter would strengthen that specific
coverage claim. This is a test-coverage limit, not a production defect found.

Keep seed0's established419798-node control, original commands/hashes and all
failed/interrupted attempts. Any baseline seed7 overflow observed by this fixture
must be labelled synthetic inherited-state coverage. No natural-root overflow,
changed move decision, speed, Elo or target-hardware conclusion follows.
