# Windows24 root verifier preparation

`verify-windows.py` is prepared for root execution only. Preparation parsed its Python AST and independently inspected genuine source/data schemas; it did not import or execute the verifier, Git, engines, tests, compilers or archive producers. The qualified23 root verifier is a historical reference only; actual24 counts and field names come from closed24 receipts.

From `/workspace/dwqww`, root invocation:

```sh
PYTHONDONTWRITEBYTECODE=1 /workspace/.cloud-setup/venv/bin/python -B validation/see-proof-reuse-candidate-20261021/root-verification/verify-windows.py > validation/see-proof-reuse-candidate-20261021/root-verification/windows.stdout 2> validation/see-proof-reuse-candidate-20261021/root-verification/windows.stderr
```

Root should retain actual command and return code. Only after every check passes, the verifier exclusively creates `WINDOWS.json`; an existing file blocks execution. It does not overwrite previous proof or modify originals/source/Git. Frozen `git ls-tree` and `git cat-file --batch` reads are the only child commands, solely to check actual candidate77/parent77 blobs and exactly four changes. No engine/test/build/archive reruns occur.

Scope: genuine final status and287-entry namespace seal; actual13 named Wine checks/SEE504/TT12/PV56; first same-platform334752 signature; Git77 versus source74 after3pyc exclusions; all seven outside roots including the new2-file outer-package supervisor;597 parent originals; built11/shipped10 PE and static core bytes; raw271/272 ZIP; release23 members/22 checksums; strict Windows flags and actual7 outer group/stream receipts. Standalone file entries in the outside map use absolute keys; directory entries use relative keys. No schema fallback, retry waiver, invented per-PE historical PID, Windows/Ryzen runtime, speed or Elo claim.

Source/evidence/outside hashes are checked again before final output. The old23 checker and all Windows/native originals remain unchanged. Pending complete24 recovery archive is outside this verifier's scope.
