@echo off
rem build_rocm_r14.bat - R14 Main item 1: CPU-only ROCm build of forge-v2-bullet (no GPU use). Same per-process environment as
rem Engine NNUE's F:\bullet_hip\launch_smoke.bat "build" (vcvars64, read-only HIP SDK of the npt venv, GCN_ARCH_NAME), but
rem every write goes to D:\o14a (F: is write-forbidden in R14): own CARGO_HOME copy, target dir and TEMP on D:.
rem Run ONLY as:  cmd /d /c build_rocm_r14.bat      (Idle, CPUs 2-3, 2 jobs). Nothing is set machine- or user-wide.
setlocal EnableExtensions
if not exist D:\o14a\tmp mkdir D:\o14a\tmp
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul || (echo ABORT: vcvars64 failed & exit /b 6)
set TEMP=D:\o14a\tmp
set TMP=D:\o14a\tmp
set CARGO_HOME=C:\o13\p4\cargo_home
set CARGO_TARGET_DIR=D:\o14a\p4\target_rocm
rem 1 job while another own 1-thread job runs (R14 budget: <= 2 threads in total)
set CARGO_BUILD_JOBS=1
set SP=F:\nnue_pytorch\venv\Lib\site-packages
set HIP_PATH=%SP%\_rocm_sdk_devel
set TC=F:\bullet_hip\rust\rustup\toolchains\stable-x86_64-pc-windows-msvc\bin
set PATH=%TC%;%SP%\_rocm_sdk_libraries_gfx110X_all\bin;%SP%\_rocm_sdk_devel\bin;%PATH%
set GCN_ARCH_NAME=gfx1100
start "" /b /wait /low /affinity C "%TC%\cargo.exe" build --release --offline --features rocm --manifest-path D:\grok-pc-data\dwqww\.claude\worktrees\o13-p4\opus_r13\p4\forge_v2_bullet\Cargo.toml > D:\o14a\p4\build_rocm.log 2>&1
set RC=%ERRORLEVEL%
echo cargo rocm build exit %RC% (log D:\o14a\p4\build_rocm.log)
exit /b %RC%
