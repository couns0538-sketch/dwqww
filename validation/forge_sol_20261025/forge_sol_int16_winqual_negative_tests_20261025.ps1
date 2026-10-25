# Software-only fixtures. No engine/compiler process or Win32 API is invoked.
[CmdletBinding()]
param([string]$Script = (Join-Path $PSScriptRoot 'forge_sol_int16_winqual_script_20261025.ps1'))
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$tokens = $null; $errors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($Script,[ref]$tokens,[ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
$script:Assertions = 0
$script:Failure = ''
$script:Invariant = [Globalization.CultureInfo]::InvariantCulture
function Assert([bool]$Condition,[string]$Message) {
    if (-not $Condition) { throw "ASSERTION FAILED: $Message" }
    $script:Assertions++
}
function Expect-Failure([scriptblock]$Action,[string]$Code) {
    $failed = $false
    try { & $Action } catch { $failed = $true; Assert ($_.Exception.Message.StartsWith($Code+' ')) "expected $Code, got $($_.Exception.Message)" }
    Assert $failed "expected failure $Code"
}
# Import function definitions, not the executable main block.
foreach ($definition in $ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$false)) {
    Invoke-Expression $definition.Extent.Text
}
function Write-Result([string]$Text) { }
function Run-Child([string]$Exe,[string[]]$Arguments,[string[]]$Commands,[string]$Tag,[bool]$Disassembly=$false) {
    return [pscustomobject]@{Out=[pscustomobject]@{Text=$script:FixtureText}}
}
$sourceAssignment = $ast.Find({param($n)
    $n -is [Management.Automation.Language.AssignmentStatementAst] -and $n.Left.Extent.Text -eq '$script:NativeSource'
},$true)
Assert ($null -ne $sourceAssignment) 'C# source here-string exists'
$native = & ([scriptblock]::Create($sourceAssignment.Right.Extent.Text))
Add-Type -TypeDefinition $native -Language CSharp
Assert ($null -ne ('ForgeSolWinqual20261025.Session' -as [type])) 'C# helper compiles without invoking Win32'
foreach ($layout in @(@('BasicLimits',64),@('ExtendedLimits',144),@('StartupInfo',104),@('ProcessInformation',24),@('SecurityAttributes',24))) {
    $type = [ForgeSolWinqual20261025.Session].GetNestedType($layout[0],[Reflection.BindingFlags]::NonPublic)
    Assert ([Runtime.InteropServices.Marshal]::SizeOf([Activator]::CreateInstance($type)) -eq $layout[1]) "x64 Win32 layout $($layout[0])"
}
$scriptText = [IO.File]::ReadAllText($Script)
Assert (-not [regex]::IsMatch($scriptText,'(?i)\b(?:Stop-Process|TerminateProcess|TerminateJobObject)\b|\.Kill\s*\(')) 'no process termination API'
Assert (-not [regex]::IsMatch($scriptText,"SetEnvironmentVariable\('HOME'")) 'HOME is never changed'

$base = "uciok`nreadyok`ninfo string bench depth 11 nodes 308972 time 100 nps 3089720`n"
$script:FixtureText = $base
$row = Run-Bench 'fixture' $false 11 'good-off' 308972
Assert ($row.Nodes -eq 308972 -and $row.Nps -eq 3089720) 'valid OFF bench parsed'
$script:FixtureText = $base.Replace('nodes 308972','nodes 308971')
Expect-Failure { Run-Bench 'fixture' $false 11 'bad-nodes' 308972 } 'BAD_NODES'
$script:FixtureText = $base + "info string bench depth 11 nodes 308972 time 100 nps 3089720`n"
Expect-Failure { Run-Bench 'fixture' $false 11 'duplicate-bench' 308972 } 'BAD_BENCH'
$script:FixtureText = $base.Replace('depth 11','depth 13')
Expect-Failure { Run-Bench 'fixture' $false 11 'bad-depth' 308972 } 'BAD_BENCH'
$script:FixtureText = $base.Replace('uciok', 'missing')
Expect-Failure { Run-Bench 'fixture' $false 11 'missing-uciok' 308972 } 'BAD_UCI'
$script:FixtureText = $base.Replace('nps 3089720','nps 0')
Expect-Failure { Run-Bench 'fixture' $false 11 'zero-nps' 308972 } 'BAD_BENCH'
$advertisement = "option name NnueInt16 type check default false`n"
$script:FixtureText = $advertisement+$base
Expect-Failure { Run-Bench 'fixture' $true 11 'unacknowledged-on' 308972 } 'BACKEND_INACTIVE'
$script:FixtureText = $advertisement+"info string NnueInt16 active`n"+$base
Assert ((Run-Bench 'fixture' $true 11 'good-on' 308972).Nodes -eq 308972) 'advertised and active ON accepted'
$script:FixtureText = "info string NnueInt16 active`n"+$advertisement+$base
Expect-Failure { Run-Bench 'fixture' $true 11 'early-ack' 308972 } 'BACKEND_INACTIVE'
$script:FixtureText = $advertisement+"info string NnueInt16 active`ninfo string NnueInt16 unavailable; using float`n"+$base
Expect-Failure { Run-Bench 'fixture' $true 11 'fallback' 308972 } 'BACKEND_INACTIVE'
$script:FixtureText = "info string NnueInt16 active`n"+$base
Expect-Failure { Run-Bench 'fixture' $false 11 'unexpected-off-activation' 308972 } 'BAD_OFF_BACKEND'
$script:FixtureText = "uciok`nreadyok`nnodes 4865609`n"
Run-Perft 'fixture' $false 'start' 'position startpos' 5 4865609
$script:FixtureText = "uciok`nreadyok`nnodes 4865608`n"
Expect-Failure { Run-Perft 'fixture' $false 'start' 'position startpos' 5 4865609 } 'BAD_PERFT'

function Parse-Disassembly([string]$Text) {
    $capture = [ForgeSolWinqual20261025.Capture]::new(16384)
    $stream = [IO.MemoryStream]::new([Text.Encoding]::UTF8.GetBytes($Text))
    $capture.Pump($stream,$true)
    return $capture
}
$disassembly = @'
fixture.exe: file format pei-x86-64
[  1](sec  1)(fl 0x00)(ty   20)(scl   2) (nx 0) 0x0000000000000100 forge::nnue::evaluate()
[  2](sec  4)(fl 0x00)(ty    0)(scl   3) (nx 0) 0x0000000000000200 forge::nnue::weights
0000000140000100 <forge::nnue::evaluate()>:
  140000100: vmulps %ymm0,%ymm1,%ymm2
  140000104: ret
0000000140000200 <static_runtime()>:
  140000200: vfmadd132ps %ymm0,%ymm1,%ymm2
  140000204: ret
'@
$capture = Parse-Disassembly $disassembly
Assert $capture.PeX64 'PE x64 recognized'
Assert ($capture.DefinedNnueFunctions.Count -eq 1) 'COFF NNUE functions distinguished from data symbols'
Assert ($capture.Symbols['forge::nnue::evaluate()'].Instructions -eq 2) 'NNUE instructions inventoried'
Assert ($capture.Symbols['forge::nnue::evaluate()'].AllFma -eq 0) 'runtime FMA not attributed to NNUE'
Assert ($capture.Symbols['static_runtime()'].AllFma -eq 1) 'external runtime FMA inventoried separately'
Assert ($capture.UnknownFma -eq 0) 'all FMA has symbol scope'
$capture = Parse-Disassembly ($disassembly.Replace('vmulps','vfmadd132ps'))
Assert ($capture.Symbols['forge::nnue::evaluate()'].Vfmadd -eq 1) 'NNUE vfmadd detected'
$capture = Parse-Disassembly ($disassembly.Replace('vmulps','vfnmsub132ps'))
Assert ($capture.Symbols['forge::nnue::evaluate()'].AllFma -eq 1) 'other NNUE FMA variants detected'
$capture = Parse-Disassembly ($disassembly.Replace('vmulps','(bad)'))
Assert $capture.ParseError 'undecoded NNUE instruction fails closed'
$capture = Parse-Disassembly "fixture.exe: file format pei-x86-64`n  140000100: vfmadd132ps %ymm0,%ymm1,%ymm2`n"
Assert ($capture.UnknownFma -eq 1) 'unattributed FMA detected'
$capture = Parse-Disassembly ('x'*65537)
Assert $capture.ParseError 'oversized disassembly line fails closed'
Assert ((Median @(1.0,4.0,2.0,3.0)) -eq 2.5) 'even median'
Assert ((Median @(1.0,3.0,2.0)) -eq 2.0) 'odd median'
Write-Output "SOFTWARE_FIXTURES PASS assertions=$script:Assertions native_Windows_execution=UNVERIFIED engine_or_performance_jobs=0"
