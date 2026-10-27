# S35 probe: verify lock semantics and command shadowing on this OS (scratch only, no live paths)
param([Parameter(Mandatory = $true)][string]$OutDir)   # scratch dir for the one test file (never next to this script)
$ErrorActionPreference = 'Stop'
$dir = Join-Path $OutDir 'probe_out'; New-Item -ItemType Directory -Force $dir | Out-Null
$f = Join-Path $dir 'held.log'
$w = [IO.FileStream]::new($f, [IO.FileMode]::Create, [IO.FileAccess]::Write, [IO.FileShare]::Read)
$b = [Text.Encoding]::UTF8.GetBytes("Finished game 1 (a vs b): 0-1 {White loses on time}`n")
$w.Write($b, 0, $b.Length); $w.Flush($true)
try { $t = [IO.File]::ReadAllText($f); "ReadAllText under exclusive writer: OK len $($t.Length) (lock NOT enforced)" } catch { "ReadAllText under exclusive writer: THROWS $($_.Exception.InnerException.GetType().Name): $($_.Exception.InnerException.Message)" }
try { $fs = [IO.File]::Open($f, 'Open', 'Read', 'ReadWrite'); $sr = [IO.StreamReader]::new($fs); $t = $sr.ReadToEnd(); $sr.Close(); "FileShare.ReadWrite reader: OK len $($t.Length)" } catch { "FileShare.ReadWrite reader: THROWS $_" }
try { $t = Get-Content -LiteralPath $f -Raw; "Get-Content -Raw: OK len $($t.Length)" } catch { "Get-Content -Raw: THROWS $_" }
try { $t = Get-Content -LiteralPath $f -Tail 5; "Get-Content -Tail: OK" } catch { "Get-Content -Tail: THROWS $_" }
try { Move-Item -LiteralPath $f -Destination "$f.moved"; "Move-Item while held (writer share Read only): OK" } catch { "Move-Item while held: THROWS $($_.Exception.GetType().Name)" }
$w.Close()
# Start-Process-like writer: ReadWrite access, share Read|Write
$w2 = [IO.FileStream]::new($f, [IO.FileMode]::Create, [IO.FileAccess]::ReadWrite, [IO.FileShare]'Read,Write')
$w2.Write($b, 0, $b.Length); $w2.Flush($true)
try { $t = [IO.File]::ReadAllText($f); "ReadAllText under Start-Process-style writer: OK (lock NOT enforced)" } catch { "ReadAllText under Start-Process-style writer: THROWS IOException" }
try { $fs = [IO.File]::Open($f, 'Open', 'Read', 'ReadWrite'); $fs.Close(); "FileShare.ReadWrite reader under Start-Process-style writer: OK" } catch { "FileShare.ReadWrite reader under Start-Process-style writer: THROWS $_" }
$w2.Close()
# command shadowing: a function named taskkill.exe must win over the external exe
function taskkill.exe { "STUB taskkill.exe called with: $($args -join ' ')" }
& taskkill.exe /T /F /PID 999999
(Get-Command taskkill.exe).CommandType
