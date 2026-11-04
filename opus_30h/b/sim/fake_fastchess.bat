@echo off
rem SPSA simulation test only: hands the tuner's fastchess command line to fake_fastchess.py (same folder).
"C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe" -I -B "%~dp0fake_fastchess.py" %*
exit /b %ERRORLEVEL%
