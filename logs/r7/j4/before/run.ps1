$a = @('-engine','name=a','cmd=F:/opus_scratch/r7/j4/forge_r7_base_gate.exe','option.Threads=1','option.Hash=16','option.OwnBook=false',
       '-engine','name=b','cmd=F:/opus_scratch/r7/j4/forge_r7_base_gate.exe','option.Threads=1','option.Hash=16','option.OwnBook=false',
       '-each','tc=10+0.1','timemargin=1000','proto=uci',
       '-openings','file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn','format=pgn','order=random','start=1',
       '-srand','1100276691','-games','2','-repeat','-rounds','20','-concurrency','3','-recover',
       '-pgnout','file=F:/opus_scratch/r7/j4/before/games.pgn','timeleft=true') + @('-log','file=F:/opus_scratch/r7/j4/before/engine_io.log','level=warn','engine=true','append=false')
$sw = [Diagnostics.Stopwatch]::StartNew()
$p = Start-Process -FilePath 'C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe' -ArgumentList $a -WorkingDirectory 'F:/opus_scratch/r7/j4/before' -RedirectStandardOutput 'F:/opus_scratch/r7/j4/before/fastchess.out' -RedirectStandardError 'F:/opus_scratch/r7/j4/before/fastchess.err' -PassThru -NoNewWindow
try { $p.PriorityClass = 'BelowNormal' } catch {}
$p.WaitForExit()
$cpu = $p.TotalProcessorTime.TotalSeconds
"wall_s=" + $sw.Elapsed.TotalSeconds + " fastchess_cpu_s=" + $cpu + " exit=" + $p.ExitCode
