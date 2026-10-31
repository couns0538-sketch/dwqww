# run_low.ps1 - run a command with this process's affinity + priority set first (children inherit both).
# usage: powershell -NoProfile -ExecutionPolicy Bypass -File run_low.ps1 -Mask 0xC -Prio BelowNormal -Exe <exe> -ArgLine "<args>"
# Fails closed: exits 78 if setting affinity or priority fails. R13 rules: <= 2 CPUs, BelowNormal (Idle for long jobs).
param([long]$Mask = 0xC, [string]$Prio = 'BelowNormal', [Parameter(Mandatory=$true)][string]$Exe, [string]$ArgLine = '')
try {
  $me = [System.Diagnostics.Process]::GetCurrentProcess(); $me.ProcessorAffinity = [IntPtr]$Mask; $me.PriorityClass = $Prio
  $me.Refresh(); if ([long]$me.ProcessorAffinity -ne $Mask -or "$($me.PriorityClass)" -ne $Prio) { throw 'affinity/priority not applied' }
} catch { Write-Error "run_low: $_"; exit 78 }
$env:PATH = 'C:\msys64\ucrt64\bin;' + $env:PATH
$p = Start-Process -FilePath $Exe -ArgumentList $ArgLine -NoNewWindow -Wait -PassThru
exit $p.ExitCode
