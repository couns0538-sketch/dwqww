[Diagnostics.Process]::GetCurrentProcess().PriorityClass='Idle'
& 'D:\a14\tools\Invoke-R13.ps1' -Script 'D:\a14\evidence\test_logs\r14\qc\launcher-cap-green03\pytest\test_exited_child_cannot_leave0\pipe_probe.py' -RunName 'pipes-d8f760a26d54' -TimeoutSeconds 2
exit $LASTEXITCODE
