step0_wrongbuild/ (kimi5 job 20)

My FIRST base/A4 builds of this run configured with `-DFORGE_MATE_ALPHA_GUARD=1`
(a CMake variable the project's CMakeLists does not read; CMake warns "not used").
The option MateAlphaGuard does not exist in such a build, PC20's
`setoption name MateAlphaGuard value true` is answered `info string unknown option
MateAlphaGuard`, and PC20 bench comes out 278016 / 587268 instead of 278024 / 587276.
Swarm file 5's recipe is `-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1`.

The raw files of that first step-0 run were deleted by me (`rm -rf step0`) before the
rerun — my mistake, against the job-17 lesson (keep a failed attempt under its own
name). The two files here are a REGENERATION at 15:1xZ of the same faulty
configuration (same source tree 6b98f217 + pc_r15, same wrong cmake invocation, on
the plain base without the A4 patch), which reproduces the same two numbers. The
diagnosis itself is proven by them: `unknown option MateAlphaGuard` in each file.
