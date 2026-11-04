@echo off
rem gpu_run_o30.bat <run name> <trainer r-mode args after the out dir> - Opus 30-h job: run the ROCm build of
rem forge-v2-bullet in GPU window (D:\o30\WINDOW.md) under o30_gpu_guard.py (thermal limits + yield to npt-like
rem trainers; Idle, CPUs 4-5). Runtime environment = build_bullet_o30.bat rocm (read-only HIP SDK of the npt venv).
rem Output D:\o30\gpu\<run>\, trainer log D:\o30\gpu\<run>.out, guard log D:\o30\gpu\<run>.guard.log.
rem Example (smoke): cmd /d /c gpu_run_o30.bat smoke01 one 0 256 6 256 2 30001 0.001 0.4 8
setlocal EnableExtensions
if "%~1"=="" (echo usage: gpu_run_o30.bat ^<run^> ^<kb map^> ^<mirror^> [hidden sb bpsb threads seed lr wdl mix] & exit /b 2)
if not exist D:\o30\WINDOW.md (echo ABORT: no GPU window record D:\o30\WINDOW.md & exit /b 3)
if not exist D:\o30\gpu mkdir D:\o30\gpu
set RUN=%~1
if exist D:\o30\gpu\%RUN% (echo ABORT: D:\o30\gpu\%RUN% exists & exit /b 4)
if exist D:\o30\gpu\%RUN%.out (echo ABORT: D:\o30\gpu\%RUN%.out exists & exit /b 4)
shift
set ARGS=
:collect
if "%~1"=="" goto run
set ARGS=%ARGS% %1
shift
goto collect
:run
set SP=F:\nnue_pytorch\venv\Lib\site-packages
set HIP_PATH=%SP%\_rocm_sdk_devel
set PATH=%SP%\_rocm_sdk_libraries_gfx110X_all\bin;%SP%\_rocm_sdk_devel\bin;%PATH%
set GCN_ARCH_NAME=gfx1100
set TEMP=D:\o30\tmp
set TMP=D:\o30\tmp
if "%GUARD_EXTRA%"=="" set GUARD_EXTRA=
C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe -I -B D:\o30\wt\opus_30h\a\o30_gpu_guard.py --log D:\o30\gpu\%RUN%.guard.log --mask 0x30 %GUARD_EXTRA% -- D:\o30\target_rocm\release\forge-v2-bullet.exe r D:/o30/data D:/o30/gpu/%RUN%%ARGS% > D:\o30\gpu\%RUN%.out 2>&1
set RC=%ERRORLEVEL%
echo gpu run %RUN% exit %RC% (log D:\o30\gpu\%RUN%.out)
exit /b %RC%
