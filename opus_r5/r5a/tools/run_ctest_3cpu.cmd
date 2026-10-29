@echo off
rem R5A: run the CTest list of one CMake build dir at BelowNormal on a 3-CPU affinity mask (job rule: at most 3
rem threads). Children inherit the mask and the priority class. forge_tests is excluded (two of its checks search
rem with 4 threads); GitHub CI (opus-ci) runs it with the known-failure check.
rem usage: run_ctest_3cpu.cmd <build dir> <log file>
set "VSCM=C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake"
set "PATH=C:\msys64\ucrt64\bin;%VSCM%\CMake\bin;%VSCM%\Ninja;%PATH%"
cd /d "%~1"
start "" /b /wait /belownormal /affinity 700 ctest -E "^forge_tests$" --output-on-failure --timeout 900 > "%~2" 2>&1
echo ctest exit %ERRORLEVEL% >> "%~2"
