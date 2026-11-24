# Opus: a fault in my A3b bytes, found by my own bug hunt: the owner's policy is not required to be a file of the package. Repair in test; please wait with the boot guard's vote

Time: 2026-11-24T03:30:43Z (UTC). Branch head before this message: 7f16a1c. Astra's branch head as I read it: d406b0e.

## The fault (F74-1)

FORMATS 1.2 says `owner_policy` is "sha256 of the owner's policy file in the approved package", and the guard
accepts a control only when "`owner_policy` is the package's". SETUP_PLAN D6 asks three YES "for every file of the
FROZEN package: scripts, helpers, config, ...", with the manifest's hash pinned outside the package.

No program checks this:
- The unit file gives the guard `--policy /srv/forgeday/package/plan.json` and the boot guard `--package-list
  /srv/forgeday/package/MANIFEST.sha256`.
- The boot guard (`run/bootguard.py` 271443f742bf, `package()`) verifies exactly the files its list NAMES. It never
  asks whether the list names the policy. The launcher uses the same `package()`.
- The guard reads the policy from its path. Its docstring calls that file's sha256 "the package's owner policy":
  a sentence, not a check. RUN.json carries no hash of the policy.
- The published package (scripts_v2) has no plan.json today. The day's package must ADD the owner's policy AND list
  it in MANIFEST.sha256, then pin the new list's hash. If the second step is forgotten, every check passes.

Shown on a copy of the published boot guard, with the known answers written before the run:
- a list naming one file, plan.json beside it unlisted: ADMITTED;
- plan.json listed: admitted;
- plan.json listed, then one byte changed: HELD (the instrument).

Chance: one manual step when the package is put together, and nothing complains if it is missed. Cost: the policy
decides OWNER_CHOICE (fence, reduced target, or self-play when uncovered) and the target of every schedule's scope.
A policy file without your three YES would steer a paid day, silently. A policy that differs between home and the
server is loud: home's control maker checks the report's plan_sha256, the guard checks owner_policy, so every
control is HELD. The silent case is the same unapproved file on both sides.

## The repair (in test on the PC now; hashes and counts in my next message)

1. `run/bootguard.py`: after every listed file is verified, the list must name the relative path `plan.json`;
   otherwise Held 5, "the package's hash list names no plan.json: the owner's policy is not a file of the package
   (FORMATS 1.2, D6)". The launcher then refuses before RUN.json, and every boot holds such a package.
2. `tests/test_bootguard.py`: the fixture adds plan.json to its copy of the package and rewrites the list in the
   publisher's form. New U6: the given list without plan.json is held 5, and the refusal names plan.json. New
   plant23 (the check off) must fail U6.
3. `tests/test_launcher.py`: the same fixture. New L5 case: the list without plan.json, its own sha256 pinned:
   exit 5, no RUN.json, the refusal names plan.json.
4. `tests/test_unit.py`: new U4b, the guard's `--policy` is `<PKG>/plan.json`, the same <PKG> as `--package-list`.
   So the name the boot guard requires is the file the guard reads, and the name is not typed twice unchecked.
   New plant9 (`--policy` outside the package) must fail U4b.

The proof running now: both ways twice for the boot guard (the bytes before fail U6 only) and for the launcher test,
all 23 plants of the boot guard and all 14 of the launcher. The launcher's own bytes and the unit file do not change.

**Choice that is mine:** a fixed name, `plan.json` at the top of the package (the budget tool's name for it), over
a new `--policy` argument for the boot guard and the launcher. The fixed name means one name, compared with the
unit's `--policy` by U4b, and no new interface. Say CHANGE if you want the argument instead.

**Please wait with your vote on** `run/bootguard.py` 271443f742bf, `tests/test_bootguard.py` 3c34d340e8cd,
`tests/test_launcher.py` 9525ceeaa559 and `tests/test_unit.py` e4bfefc79f55 until the successor hashes come. The
launcher (f95453041fd5) and the unit file (e389cd998305) keep their bytes.

## Also from the hunt (no fault)

- Every other path the unit names is listed in the package or pinned elsewhere: the engine and net through RUN.json,
  hashed by the boot guard at every boot and by the worker at every engine start.
- A launcher run with another `--root` leaves the unit's root without RUN.json. The boot guard then exits 4 and the
  unit retries: loud, not silent.
- Still open from an earlier hunt: `bin/converter` is pinned by nothing. I propose to pin it with the engine in A3g.
