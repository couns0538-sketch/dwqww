# Checkpoint transport: read-only findings and narrow proposal

This is a proposal for the root agent, not an installed change. No push, repack, garbage collection, build, engine run, branch/ref/config/state/controller edit was performed. Only this scratch directory was written.

## Findings

- The inspected controller is `/workspace/work/all-run/control.mjs`, SHA256 `5222d635077c6364ebb52454f3057f7289b478450ba05b1bdafc20cc4cd03595`.
- Its Git helper at line9 uses `execFileSync('git', ..., timeout:60000)` for every command. The checkpoint push at line45 uses that same helper. A successful push is followed by incrementing pushes, recording lastPush, saving state and printing CHECKPOINT. Keep that success-only accounting unchanged.
- Commit `e983e08e5dc491fd68ae2bd52ae669dbe38137fc` records checkpoint time `2026-11-14T16:00:36.188Z`. The root reported successful completion around16:01:35, about59seconds later. That interval is close to60seconds, but it is not an independently isolated pack/transfer timing measurement: it starts at the commit timestamp and includes subsequent checkpoint work.
- The first match evidence directory contains29 files totaling **253,881,312 bytes**. The largest individual chunks are just under16MiB. Raw text size is not compressed pack size or uploaded-byte count.
- `git count-objects -vH` reports800 loose objects /43.70MiB,14,867 packed objects across9packs /109.33MiB,59 prune-packable objects. These are local-repository statistics, not the new push's wire size. It also reports three linked-worktree metadata paths as garbage; no cleanup is recommended or attempted.
- No matching pack/core-compression/gc/fetch-parallel/transfer overrides were returned by the targeted config read (exit1, empty output). The repository is a promisor clone with `remote.origin.partialclonefilter=blob:none`.
- Cgroup `cpu.max` is `400000 100000`: **four CPU-equivalents**. The effective cpuset is0–4 and nproc returns5. Default thread autodetection can see more CPUs than the quota permits.
- GNU timeout9.7 is available at `/usr/bin/timeout`.
- Point observations at16:05:18 and16:05:57 showed no non-zombie Git/pack process. Old zombie Git processes were excluded from active-process interpretation. A bounded passive observation is retained separately; no CPU/network attribution should be made merely from the earlier59second interval.

## Recommended minimal change

Extend **only the checkpoint push** to a bounded six-minute attempt. Leave the existing60second helper for branch checks, staging, commits and other reads. Preserve the existing branch allowlist at line34, the explicit one-branch refspec and `--no-follow-tags`. Do not add force, tags, mirror or all-branch behavior.

For a process-tree timeout, replace only the `git([...push...])` expression in line45 with this dedicated invocation (root must review/apply it at a safe controller boundary):

```js
cp.execFileSync('/usr/bin/timeout', [
  '--signal=TERM', '--kill-after=10s', '360s',
  'git', 'push', '--no-follow-tags', 'origin',
  'HEAD:refs/heads/' + branch
], {
  cwd: repo,
  encoding: 'utf8',
  timeout: 390000,
  killSignal: 'SIGKILL'
})
```

Keep it within the existing `console.log(...)` and leave the following success-only counter/state updates untouched. GNU timeout supplies the normal360second deadline and a ten-second kill grace; the outer390second exec timeout is a backstop. Both are below the user's eight-minute command ceiling. Do **not** use `--foreground`, which would weaken descendant process timeout coverage. This is safer bounded transport handling, not an engine change or a test rerun. It adds no evidence loss or transformation: Git still transmits the same commit and text objects to the same explicit branch.

A still-smaller source edit is a dedicated push helper with `timeout:360000` while retaining the old helper for other Git commands. However, a Node child timeout alone is less explicit about terminating descendants; the GNU timeout wrapper above is the preferred bounded proposal. Neither alternative has been executed by this reviewer.

## Optional per-push pack settings

If the root chooses to reduce new delta-search work, insert these arguments immediately before `push` in the dedicated Git invocation:

```text
-c pack.window=0 -c pack.threads=4
```

For example, the underlying command would be:

```text
git -c pack.window=0 -c pack.threads=4 push --no-follow-tags origin HEAD:refs/heads/soak/combo29-all
```

The actual controller must continue using its validated `branch` variable so the destination remains exactly the already authorized current branch.

`pack.window=0` disables new delta search for this command. Git can still compress objects and reuse applicable existing packed representations. It can reduce CPU spent comparing large log chunks, but may create a larger pack and increase network time. No measurement here establishes that it improves this push. `pack.threads=4` aligns the delta-search thread setting with the CPU quota; it is not a hard CPU limiter and may have little effect when delta search is disabled. These options are command-local: no repository/global config mutation, object rewrite, ref change or text-byte loss is needed.

The **required immediate correction is timeout headroom**. Pack tuning is optional and should not be represented as a proven speed improvement. Do not change compression levels, HTTP buffer settings, existing object packs, evidence chunking/content, or Git configuration merely to address a59second observation.

## Outcome handling

If a bounded push exits nonzero, preserve its stdout/stderr and exit/signal, and do not count it as successful. A transport timeout can occur after the remote accepted the commit but before local confirmation. At the controller boundary, use a separately bounded read-only `git ls-remote --heads origin refs/heads/<validated-branch>` and compare the exact expected local SHA before deciding whether the same-commit push needs retrying. Do not rewrite commits, force-push, delete refs or recount completed native work because delivery was uncertain. These are root-owned recovery steps, not actions performed here.

Before the next active Git operation, recording UTC plus PID/PPID/status/CPU samples can separate an observed pack process from a remote-transfer wait. Process averages alone do not identify the bottleneck. Full transport metrics were not enabled or retroactively recovered in this review.

## Evidence

`initial-reads.txt`, `controller-discovery.txt`, `helper-and-process.txt`, `object-and-process-read.txt`, and `live-observation.txt` retain exact read commands and actual output. The discovery glob included a nonexistent `*.js` path and rg reported that inspection-path error; the controller was successfully found as `control.mjs`. It was not an engine or push failure. No native performance, strength, data-loss or universal reliability claim is made.

## Root-applied variant and read-only verification

After the initial proposal, the root agent independently applied a narrower180second push variant while idle, before the next native batch. This reviewer did not install it. The active controller is now SHA256 `c471c0287c542defcbaac4ba05a0173fc1f9550ad8224f88a55d35d5bf6c82dc`.

Readback at16:08 confirms:

- The general Git helper remains60seconds.
- The original current-branch allowlist and single explicit refspec remain unchanged.
- The push command is `/usr/bin/timeout -k 5s 180s git -c pack.window=0 -c pack.threads=4 push --no-follow-tags origin HEAD:refs/heads/<validated-branch>`.
- Its Node parent timeout is195000ms. Normal termination is180seconds plus a five-second kill grace, well below eight minutes. No `--foreground`, force, tag or multi-ref behavior was added.
- Push-command provenance is appended to PROGRESS; success-only push count/state updates remain after successful command completion.
- The root states that it now schedules checkpoint uploads separately before each native batch. This scheduling arrangement is root-owned; the diff does not silently add an engine clock or change native search semantics.

The retained before/after diff changes only push command construction, provenance logging and the dedicated invocation. Root's `CHANGE.txt` is retained as a read-only observation in `root-applied-diff.txt`.

The next commit was `2ff0a916bec7bbe9187a40d7862f9cb46e49f087` at16:07:39.049Z. The read-only state snapshot records `lastPush=2026-11-14T16:07:49.220Z`, pushes52 and active=null. This records about10seconds between that commit timestamp and the controller's success timestamp for this different checkpoint. It is **not a controlled before/after benchmark or a speed conclusion**, and this reviewer did not independently query the remote branch. The root owns the actual push command result.

The passive observer ended at16:07:24.968Z, before the root's reported16:07:34 push-session start. At16:08:03 no active Git process remained. Therefore no active packing or transfer CPU sample was captured for this successful attempt; no CPU-versus-network bottleneck attribution is justified.

Applied-source/output evidence: `applied-readback.txt`, `applied-outcome-read.txt`, `root-applied-diff.txt`. The initial six-minute suggestion above remains historical advice; the actual selected limit is180+5seconds with195second parent backstop. No further change is proposed or applied by this reviewer.
