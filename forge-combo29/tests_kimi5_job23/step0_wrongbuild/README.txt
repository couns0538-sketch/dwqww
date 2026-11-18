step0_wrongbuild/ (kimi5 job 23)

First step-0 attempt of this run: configured with -DFORGE_MATE_ALPHA_GUARD=1
(a CMake variable this CMakeLists does not read). MateAlphaGuard unknown ->
pc20 bench 278016 / 587268 (8 short of 278024 / 587276), the exact wrong-build
signature of job 20. Raw files kept; the corrected build (-DCMAKE_CXX_FLAGS=
-DFORGE_MATE_ALPHA_GUARD=1, swarm file 5's recipe) reran into step0/.
