# R8 "after" benchmark: forge_selfplay_fast with the unchanged live engine copy, same conditions as the baseline
# (1 worker, CPUs 8-9, engine at Idle priority, 5000 nodes, Hash 16, random 8-ply openings, de-duplication on),
# 25 minutes, text + direct .pos output. Started BelowNormal; ends by itself (--max-minutes).
$exe = 'F:\opus_scratch\r8\driver\forge_selfplay_fast.exe'
$args = @('--engine', 'F:\opus_scratch\r8\engine\forge_live_copy.exe', '--out', 'F:\opus_scratch\r8\after1\out',
          '--workers', '1', '--cpus', '8-9', '--nodes', '5000', '--hash', '16', '--max-minutes', '25',
          '--seed', '20261029', '--pos', '--progress-seconds', '60', '--priority', 'idle')
$p = Start-Process -FilePath $exe -ArgumentList $args -WorkingDirectory 'F:\opus_scratch\r8\after1' `
     -RedirectStandardOutput 'F:\opus_scratch\r8\after1\driver.out' -RedirectStandardError 'F:\opus_scratch\r8\after1\driver.err' -PassThru -NoNewWindow
try { $p.PriorityClass = 'BelowNormal' } catch {}
"started pid=" + $p.Id + " at " + (Get-Date -Format "HH:mm:ss")
$p.Id | Out-File -FilePath 'F:\opus_scratch\r8\after1\root.pid' -Encoding ascii
$s = Start-Process -FilePath powershell -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','D:\grok-pc-data\dwqww\.claude\worktrees\opus-r8-datagen\r8\tools\sample_tree.ps1','-RootPid',"$($p.Id)",'-Seconds','30','-Out','F:\opus_scratch\r8\after1\tree_samples.csv' -WindowStyle Hidden -PassThru
"sampler pid=" + $s.Id
