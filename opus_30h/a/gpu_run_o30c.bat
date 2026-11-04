@echo off
rem gpu_run_o30c.bat <run> <kb map> <mirror> [hidden sb bpsb threads seed lr wdl mix] - Opus 30-h job, GPU window:
rem forge-v2-bullet (ROCm) under o30_gpu_guard.py (thermal limits, yields to npt). Env: BULLET_EXE, GUARD_MASK
rem (default 0x38 = CPUs 3-5), GUARD_EXTRA, O30_INIT_DIR / O30_CLIP / O30_DECAY. Never edit while a run uses it.
rem Copy of gpu_run_o30.bat with the run outputs on C:\o30g\gpu (D: near its 50 GB floor, owner: use C: when D: is short).
setlocal EnableExtensions
if "%~1"=="" (echo usage: gpu_run_o30.bat run kbmap mirror [args] & exit /b 2)
if not exist D:\o30\WINDOW.md (echo ABORT: no D:\o30\WINDOW.md & exit /b 3)
if not exist C:\o30g\gpu mkdir C:\o30g\gpu
set RUN=%~1
if exist C:\o30g\gpu\%RUN% (echo ABORT: run exists & exit /b 4)
if exist C:\o30g\gpu\%RUN%.out (echo ABORT: log exists & exit /b 4)
if exist C:\o30g\gpu\%RUN%.guard.log (echo ABORT: guard log exists & exit /b 4)
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
if "%BULLET_EXE%"=="" set BULLET_EXE=D:\o30\target_rocm\release\forge-v2-bullet.exe
if "%GUARD_MASK%"=="" set GUARD_MASK=0x38
C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe -I -B D:\o30\wt\opus_30h\a\o30_gpu_guard.py --log C:\o30g\gpu\%RUN%.guard.log --mask %GUARD_MASK% %GUARD_EXTRA% -- %BULLET_EXE% r D:/o30/data C:/o30g/gpu/%RUN%%ARGS% > C:\o30g\gpu\%RUN%.out 2>&1
rem -----------------------------------------------------------------------------------------------------------------------------------------------
set RC=%ERRORLEVEL%
echo gpu run %RUN% exit %RC% (log C:\o30g\gpu\%RUN%.out)
exit /b %RC%
