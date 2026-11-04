@echo off
rem build_bullet_o30.bat [mock|rocm] [log tag] - Opus 30-h job: build forge-v2-bullet (opus_30h\a\forge_v2_bullet_o30,
rem private trainer library copy D:\o30\bullet with residual_base) on the CPU. mock (default): the mock backend (compiles
rem and runs the CPU-side `rfeatures` check; training needs a GPU). rocm: the ROCm build, environment as R14's
rem build_rocm_r14.bat (vcvars64, read-only HIP SDK of the npt venv, GCN_ARCH_NAME) - building does not touch the GPU.
rem Every write goes to D:\o30 (own CARGO_HOME copy, target dirs, TEMP). Idle, 1 job, CPU mask BULLET_AFFINITY (hex,
rem default 3 = CPUs 0-1). The log is D:\o30\logs\build_bullet_<mock|rocm>[_<tag>].log (a tag keeps older logs).
rem Run as:  cmd /d /c build_bullet_o30.bat [mock|rocm] [tag]
setlocal EnableExtensions
if not exist D:\o30\tmp mkdir D:\o30\tmp
if "%BULLET_AFFINITY%"=="" set BULLET_AFFINITY=3
set LOGTAG=
if not "%~2"=="" set LOGTAG=_%~2
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul || (echo ABORT: vcvars64 failed & exit /b 6)
set TEMP=D:\o30\tmp
set TMP=D:\o30\tmp
set CARGO_HOME=D:\o30\cargo_home
set CARGO_BUILD_JOBS=1
set TC=F:\bullet_hip\rust\rustup\toolchains\stable-x86_64-pc-windows-msvc\bin
set MANIFEST=D:\o30\wt\opus_30h\a\forge_v2_bullet_o30\Cargo.toml
if /i "%~1"=="rocm" goto rocm
set CARGO_TARGET_DIR=D:\o30\target_mock
set PATH=%TC%;%PATH%
set LOG=D:\o30\logs\build_bullet_mock%LOGTAG%.log
if exist %LOG% (echo ABORT: %LOG% exists - pass a new tag & exit /b 2)
start "" /b /wait /low /affinity %BULLET_AFFINITY% "%TC%\cargo.exe" build --release --offline --manifest-path %MANIFEST% > %LOG% 2>&1
set RC=%ERRORLEVEL%
echo cargo mock build exit %RC% (log %LOG%)
exit /b %RC%
:rocm
set CARGO_TARGET_DIR=D:\o30\target_rocm
set SP=F:\nnue_pytorch\venv\Lib\site-packages
set HIP_PATH=%SP%\_rocm_sdk_devel
set PATH=%TC%;%SP%\_rocm_sdk_libraries_gfx110X_all\bin;%SP%\_rocm_sdk_devel\bin;%PATH%
set GCN_ARCH_NAME=gfx1100
set LOG=D:\o30\logs\build_bullet_rocm%LOGTAG%.log
if exist %LOG% (echo ABORT: %LOG% exists - pass a new tag & exit /b 2)
start "" /b /wait /low /affinity %BULLET_AFFINITY% "%TC%\cargo.exe" build --release --offline --features rocm --manifest-path %MANIFEST% > %LOG% 2>&1
set RC=%ERRORLEVEL%
echo cargo rocm build exit %RC% (log %LOG%)
exit /b %RC%
