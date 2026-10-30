# R8 baseline: the live self-play pipeline (forge_selfplay.py + Forge 6.2.0, unchanged files, read only) run beside the
# live workers: 1 worker on CPUs 8-9 (the script sets the worker and engine to Idle and pins them), own output folder,
# a games cap so that it ends by itself after ~25 minutes. Started BelowNormal.
$py = 'C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe'
$script = 'C:\Users\Administrator\grok-pc\nnue\forge-nnue-tools\forge_selfplay.py'
$out = 'F:\opus_scratch\r8\baseline\out'
$args = @('-B', $script, '--engine', 'F:\opus_scratch\r8\engine\forge_live_copy.exe', '--workers', '1', '--cpus', '8-9',
          '--nodes', '5000', '--engine-timeout', '180', '--out', $out, '--progress-seconds', '60',
          '--games-per-worker', '2500', '--seed', '20261029')
$p = Start-Process -FilePath $py -ArgumentList $args -WorkingDirectory 'F:\opus_scratch\r8\baseline' `
     -RedirectStandardOutput 'F:\opus_scratch\r8\baseline\selfplay.out' -RedirectStandardError 'F:\opus_scratch\r8\baseline\selfplay.err' -PassThru -NoNewWindow
try { $p.PriorityClass = 'BelowNormal' } catch {}
"started pid=" + $p.Id + " at " + (Get-Date -Format "HH:mm:ss")
$p.Id | Out-File -FilePath 'F:\opus_scratch\r8\baseline\root.pid' -Encoding ascii
