# Step 1 - exact commands (deepseek trial)

All commands were run from `/tmp/ds`; the repository is at
`/agent/repos/dwqww` and the source used is commit `6b98f217`
(tip of `for-fable-and-opus/astra-0017-v3-path`). Nothing under
`forge-combo29/src`, `forge-combo29/include` or `CMakeLists.txt` was modified.

## Compiler choice (a change to the build command, not to the source)

`/usr/bin/c++` on this machine is Clang 18.1.3, and CMake's first configure
failed because Clang could not find `-lstdc++`:

```
/usr/bin/ld: cannot find -lstdc++: No such file or directory
```

That failure is committed as `step1/configure-failed-clang.log`. The build was
therefore configured with `g++-13` explicitly, which finds its own
`libstdc++` (`/usr/lib/gcc/x86_64-linux-gnu/13/libstdc++.so`).

## Configure and build

```
cmake -S /agent/repos/dwqww/forge-combo29 -B /tmp/ds/build-release \
      -DCMAKE_CXX_COMPILER=g++-13 \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_CXX_FLAGS="-DFORGE_NNUE_V3=1"
cmake --build /tmp/ds/build-release -j4
```

`CMakeLists.txt` has no `FORGE_NNUE_V3` option, so the macro is supplied through
`CMAKE_CXX_FLAGS`. The resulting flags are recorded in `step1/flags.make.txt`:

```
CXX_FLAGS = -DFORGE_NNUE_V3=1 -O3 -DNDEBUG -std=c++20 -O3 -ffp-contract=off \
            -fno-fast-math -march=x86-64-v4
```

`march=x86-64-v4` is the CMake default here (`FORGE_MARCH`), and this CPU has
AVX-512F/BW/VL and BMI2, so `FORGE_PORTABLE` was not needed.

## The three runs

Each was run as one engine process. `bench 11` and `bench 13` read only stdin.
`perft` in this engine is a subcommand of `go`, not a top-level command: a bare
`perft 5` is silently ignored (it prints nothing), so the run is `go perft 5`.
The first attempt with a bare `perft 5` is committed as `step1/perft5-bare-attempt.txt`
(0 bytes) so the mistake is visible rather than hidden.

```
printf 'bench 11\nquit\n'  | /tmp/ds/build-release/forge > step1/bench11.txt 2>&1
printf 'bench 13\nquit\n'  | /tmp/ds/build-release/forge > step1/bench13.txt 2>&1
printf 'go perft 5\n'      | /tmp/ds/build-release/forge > step1/perft5.txt  2>&1
```

The `perft` invocation above feeds `quit` on the closed stdin immediately after,
which is safe because `go perft` runs synchronously inside the `go` command
handler before the next line is read (unlike `go depth`, which returns to the
input loop while searching). The command was also run once as
`(echo "go perft 5"; sleep 30; echo quit)` with identical output.

## Results

| run | result | PC value quoted in the job | match |
|---|---|---|---|
| `bench 11` | `nodes 312866` | 312866 | yes |
| `bench 13` | `nodes 862329` | 862329 | yes |
| `go perft 5` | `nodes 4865609` | 4865609 | yes |
