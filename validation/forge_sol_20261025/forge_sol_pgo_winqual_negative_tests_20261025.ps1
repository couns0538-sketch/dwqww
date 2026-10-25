# Software fixtures only. This file is prepared for later execution; it must not
# run during an active engine/NPS CPU lease. No engine compiler or chess engine runs.
# AST-loads three production functions without executing the orchestrator main.
# Add-Type compiles the shared parser on execution, but Session is never created
# and no Win32/resource-control method is called. Synthetic checks prove no
# native Windows, Zen5, arithmetic, speed, CTest or Elo result.
[CmdletBinding()]
param(
    [string]$ScriptPath = (Join-Path $PSScriptRoot 'forge_sol_pgo_winqual_script_20261025.ps1'),
    [string]$NativeSource = (Join-Path $PSScriptRoot 'forge_sol_pgo_native_resource_20261025.cs'),
    [string]$FixtureRoot = (Join-Path $PSScriptRoot ('forge_sol_pgo_winqual_fixtures_20261025_' + [DateTime]::UtcNow.ToString('yyyyMMdd_HHmmss') + '_' + [Guid]::NewGuid().ToString('N'))),
    [switch]$SkipLinuxSubprocess
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:fixtureRows = [Collections.Generic.List[object]]::new()
$script:fixtureMessages = [Collections.Generic.List[string]]::new()
$script:fixtureStatus = 'FAIL'
$script:parserCompiled = $false
$script:log = $null
$script:ownRoot = $null

function Add-FixtureRow([string]$Name,[string]$Outcome,[string]$Detail) {
    $script:fixtureRows.Add([pscustomobject]@{name=$Name;outcome=$Outcome;detail=$Detail})
    Write-Host "$Outcome $Name $Detail"
}
function Expect-Reject([string]$Name,[scriptblock]$Action) {
    $rejected = $false
    $detail = ''
    try { $null = & $Action } catch { $rejected=$true; $detail=$_.Exception.Message }
    if (-not $rejected) { throw "Fixture unexpectedly accepted: $Name" }
    Add-FixtureRow $Name 'PASS_REJECTED' $detail
}
function Expect-Accept([string]$Name,[scriptblock]$Action) {
    $null = & $Action
    Add-FixtureRow $Name 'PASS_ACCEPTED' ''
}
function Check([bool]$Condition,[string]$Message) {
    if (-not $Condition) { throw $Message }
}
function Close-FixtureLog {
    if ($null -ne $script:log) {
        $script:log.Flush()
        $script:log.Dispose()
        $script:log=$null
    }
}
function Log([string]$Text) {
    # Assert-Disassembly uses the real production checker and a harmless log.
    # Initialize-Result is separately verified by writing directly to its log.
    $script:fixtureMessages.Add($Text)
}
function New-SyntheticCapture([string[]]$Defined,[string[]]$Body,[string[]]$BeforeBodies=@()) {
    $lines = [Collections.Generic.List[string]]::new()
    $lines.Add('fixture.exe:     file format pei-x86-64')
    $lines.Add('SYMBOL TABLE:')
    $index=1
    foreach ($name in $Defined) {
        # Exact ordinary AMD64 COFF function-table shape accepted by Capture.
        $lines.Add(('[{0,3}](sec  1)(fl 0x00)(ty   20)(scl   2) (nx 0) 0x0000000000000000 {1}' -f $index,$name))
        $index++
    }
    foreach ($line in $BeforeBodies) { $lines.Add($line) }
    $lines.Add('Disassembly of section .text:')
    foreach ($line in $Body) { $lines.Add($line) }
    $bytes = [Text.Encoding]::UTF8.GetBytes(($lines -join "`n") + "`n")
    $stream = [IO.MemoryStream]::new($bytes,$false)
    try {
        $capture = [ForgeSolWinqual20261025.Capture]::new(262144)
        $capture.Pump($stream,$true)
        return $capture
    } finally { $stream.Dispose() }
}
function Body-For([string[]]$Names,[string]$FmaName='',[switch]$Undecoded) {
    $lines = [Collections.Generic.List[string]]::new()
    $address=[long]0x140001000
    foreach ($name in $Names) {
        $lines.Add(('{0:x16} <{1}>:' -f $address,$name))
        if ($name -eq $FmaName) {
            $lines.Add(('  {0:x}: vfmadd231ps %zmm0,%zmm1,%zmm2' -f $address))
            $address+=4
        }
        if ($Undecoded -and $name -eq 'forge::nnue::evaluate()') {
            $lines.Add(('  {0:x}: (bad)' -f $address))
            $address+=4
        }
        $lines.Add(('  {0:x}: ret' -f $address))
        $address+=16
    }
    return $lines.ToArray()
}

# Refuse to overwrite old fixture evidence and keep every write in this folder.
$fixtureFolder = [IO.Path]::GetFullPath($FixtureRoot)
$packageFolder = [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd([IO.Path]::DirectorySeparatorChar,[IO.Path]::AltDirectorySeparatorChar)
$packagePrefix = $packageFolder + [IO.Path]::DirectorySeparatorChar
$comparison = if ($IsWindows) { [StringComparison]::OrdinalIgnoreCase } else { [StringComparison]::Ordinal }
if (-not $fixtureFolder.StartsWith($packagePrefix,$comparison)) { throw 'FixtureRoot must be a new child of this harness folder' }
if (Test-Path -LiteralPath $fixtureFolder) { throw 'FixtureRoot already exists; preserving earlier evidence' }
[void][IO.Directory]::CreateDirectory($fixtureFolder)
$report = Join-Path $fixtureFolder 'forge_sol_pgo_winqual_negative_tests_20261025.json'

try {
    if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'PowerShell 7 required for software fixtures' }
    $source = (Resolve-Path -LiteralPath $ScriptPath).Path
    $native = (Resolve-Path -LiteralPath $NativeSource).Path
    $tokens=$null; $parseErrors=$null
    $ast = [Management.Automation.Language.Parser]::ParseFile($source,[ref]$tokens,[ref]$parseErrors)
    Check ($parseErrors.Count -eq 0) ('Orchestrator AST syntax failed: ' + ($parseErrors -join '; '))
    $names=@('Resolve-OwnOutput','Initialize-Result','Assert-Disassembly')
    foreach ($name in $names) {
        $found=@($ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $name},$true))
        Check ($found.Count -eq 1) "Expected exactly one AST function definition: $name"
        # Only a validated FunctionDefinitionAst is evaluated, never the script
        # body or any top-level preflight, process, resource or build code.
        . ([scriptblock]::Create($found[0].Extent.Text))
    }
    Add-FixtureRow 'ast_function_loading' 'PASS' 'Only three function definitions loaded; main never executed'

    $script:ownRoot=Join-Path $fixtureFolder 'owned'
    [void][IO.Directory]::CreateDirectory($script:ownRoot)
    $outside=Join-Path $fixtureFolder 'outside-run'
    Expect-Reject 'output_escape_absolute' { Resolve-OwnOutput $outside }
    Check (-not (Test-Path -LiteralPath $outside)) 'Absolute escape fixture wrote outside ownRoot'
    $sibling=Join-Path ($script:ownRoot + '_sibling') 'run'
    Expect-Reject 'output_escape_sibling_prefix' { Resolve-OwnOutput $sibling }
    Check (-not (Test-Path -LiteralPath $sibling)) 'Sibling-prefix escape fixture wrote outside ownRoot'
    $traversal=Join-Path $script:ownRoot (Join-Path '..' 'traversal-run')
    Expect-Reject 'output_escape_dotdot' { Resolve-OwnOutput $traversal }
    Check (-not (Test-Path -LiteralPath (Join-Path $fixtureFolder 'traversal-run'))) 'Traversal escape fixture wrote outside ownRoot'

    $existing=Join-Path $script:ownRoot 'existing-empty-run'
    [void][IO.Directory]::CreateDirectory($existing)
    Expect-Reject 'existing_empty_output_rejected' { Initialize-Result $existing }
    Close-FixtureLog
    Check (@(Get-ChildItem -LiteralPath $existing -Force).Count -eq 0) 'Existing empty output gained files'
    $preserved=Join-Path $script:ownRoot 'existing-report-run'
    [void][IO.Directory]::CreateDirectory($preserved)
    $sentinel=Join-Path $preserved 'forge_sol_pgo_results_20261025.txt'
    [IO.File]::WriteAllText($sentinel,"prior-result-must-survive`n",[Text.UTF8Encoding]::new($false))
    $before=[IO.File]::ReadAllBytes($sentinel)
    Expect-Reject 'existing_report_no_overwrite' { Initialize-Result $preserved }
    Close-FixtureLog
    $after=[IO.File]::ReadAllBytes($sentinel)
    Check ([Convert]::ToBase64String($before) -eq [Convert]::ToBase64String($after)) 'Existing report bytes changed'
    Check (@(Get-ChildItem -LiteralPath $preserved -Force).Count -eq 1) 'Existing report directory gained files'

    $fileParent=Join-Path $script:ownRoot 'regular-file-parent'
    [IO.File]::WriteAllText($fileParent,'not a directory',[Text.UTF8Encoding]::new($false))
    Expect-Reject 'regular_file_parent_rejected' { Initialize-Result (Join-Path $fileParent 'run') }
    Close-FixtureLog
    Check ([IO.File]::ReadAllText($fileParent) -eq 'not a directory') 'Regular parent file changed'

    $externalTarget=Join-Path $fixtureFolder 'reparse-target'
    [void][IO.Directory]::CreateDirectory($externalTarget)
    $link=Join-Path $script:ownRoot 'reparse-parent'
    # A fixture that cannot construct a reparse link fails as UNVERIFIED,
    # instead of silently claiming the rejection case passed.
    if ($IsWindows) {
        $null=New-Item -ItemType Junction -Path $link -Target $externalTarget
    } else {
        $null=New-Item -ItemType SymbolicLink -Path $link -Target $externalTarget
    }
    Check (((Get-Item -LiteralPath $link -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) 'Reparse fixture link was not created'
    Expect-Reject 'reparse_parent_rejected' { Resolve-OwnOutput (Join-Path $link 'escaped-run') }
    Check (-not (Test-Path -LiteralPath (Join-Path $externalTarget 'escaped-run'))) 'Reparse escape fixture wrote through the link'

    $fresh=Join-Path $script:ownRoot 'fresh-report-run'
    Expect-Accept 'new_inroot_report' { Initialize-Result $fresh }
    Check ($null -ne $script:log) 'Initialize-Result did not expose its result writer'
    $script:log.WriteLine('FIXTURE_ONLY UNVERIFIED software fixture; no engine or native evidence')
    Close-FixtureLog
    $newFiles=@(Get-ChildItem -LiteralPath $fresh -File -Recurse -Force)
    Check ($newFiles.Count -eq 1 -and $newFiles[0].Extension -eq '.txt') 'New in-root output must contain exactly one result TXT before OS preflight'
    Check ([IO.File]::ReadAllText($newFiles[0].FullName).Contains('FIXTURE_ONLY UNVERIFIED')) 'New result writer did not retain the fixture line'

    # Compilation is deferred until this harness is explicitly executed later.
    # These declarations are inert; no Session constructor/Win32 method runs.
    if ($null -eq ('ForgeSolWinqual20261025.Capture' -as [type])) {
        Add-Type -TypeDefinition ([IO.File]::ReadAllText($native)) -Language CSharp
        $script:parserCompiled=$true
    }
    $apis=@('forge::nnue::refresh()','forge::nnue::update()','forge::nnue::evaluate()')
    $body=@(Body-For $apis)
    $valid=New-SyntheticCapture $apis $body
    Check ($valid.DefinedNnueFunctions.Count -eq 3 -and $valid.Symbols.Count -eq 3) 'Synthetic COFF definitions/bodies were not parsed'
    Expect-Accept 'disassembly_valid_three_apis' { Assert-Disassembly $valid 'fixture-valid' }
    $emptyDefinitions=New-SyntheticCapture @() $body
    Expect-Reject 'disassembly_empty_definition_table' { Assert-Disassembly $emptyDefinitions 'fixture-empty-definitions' }
    $emptyBodies=New-SyntheticCapture $apis @()
    Expect-Reject 'disassembly_empty_body_table' { Assert-Disassembly $emptyBodies 'fixture-empty-bodies' }
    $missingBody=New-SyntheticCapture $apis @(Body-For $apis[0..1])
    Expect-Reject 'disassembly_missing_defined_body' { Assert-Disassembly $missingBody 'fixture-missing-body' }
    $missingApi=New-SyntheticCapture $apis[0..1] @(Body-For $apis[0..1])
    Expect-Reject 'disassembly_missing_evaluate_api' { Assert-Disassembly $missingApi 'fixture-missing-api' }
    $cloneDefs=$apis+@('forge::nnue::evaluate() [clone .cold]')
    $missingClone=New-SyntheticCapture $cloneDefs $body
    Expect-Reject 'disassembly_missing_defined_clone_body' { Assert-Disassembly $missingClone 'fixture-missing-clone-body' }
    $undecoded=New-SyntheticCapture $apis @(Body-For $apis -Undecoded)
    Check $undecoded.ParseError 'Synthetic undecoded NNUE instruction did not set ParseError'
    Expect-Reject 'disassembly_undecoded_nnue_instruction' { Assert-Disassembly $undecoded 'fixture-undecoded' }
    $evaluateFma=New-SyntheticCapture $apis @(Body-For $apis -FmaName $apis[2])
    Expect-Reject 'disassembly_evaluate_fma' { Assert-Disassembly $evaluateFma 'fixture-evaluate-fma' }
    $updateFma=New-SyntheticCapture $apis @(Body-For $apis -FmaName $apis[1])
    Expect-Reject 'disassembly_update_fma' { Assert-Disassembly $updateFma 'fixture-update-fma' }
    $unknownFma=New-SyntheticCapture $apis $body @('  140000900: vfmadd231ps %xmm0,%xmm1,%xmm2')
    Check ($unknownFma.UnknownFma -eq 1) 'Synthetic unattributed FMA was not parsed'
    Expect-Reject 'disassembly_unattributed_fma' { Assert-Disassembly $unknownFma 'fixture-unknown-fma' }

    if ($IsLinux -and -not $SkipLinuxSubprocess) {
        $linuxRoot=Join-Path $fixtureFolder 'linux-main-rejection'
        [void][IO.Directory]::CreateDirectory($linuxRoot)
        $copied=Join-Path $linuxRoot 'forge_sol_pgo_winqual_script_20261025.ps1'
        [IO.File]::Copy($source,$copied,$false)
        $linuxOut=Join-Path $linuxRoot 'forge_sol_pgo_linux_rejected_run_20261025'
        $missing=Join-Path $linuxRoot 'intentionally-missing-no-native-dependency'
        $pwsh=(Get-Process -Id $PID).MainModule.FileName
        $psi=[Diagnostics.ProcessStartInfo]::new()
        $psi.FileName=$pwsh
        foreach ($arg in @('-NoProfile','-NonInteractive','-File',$copied,'-Out',$linuxOut,
                           '-Source',$missing,'-Recipe',$missing,'-Gpp',$missing,'-Python',$missing,'-Objdump',$missing)) {
            [void]$psi.ArgumentList.Add($arg)
        }
        $psi.UseShellExecute=$false
        $psi.RedirectStandardOutput=$true
        $psi.RedirectStandardError=$true
        $child=[Diagnostics.Process]::new(); $child.StartInfo=$psi
        Check ($child.Start()) 'Could not start Linux-rejection PowerShell fixture'
        $outTask=$child.StandardOutput.ReadToEndAsync()
        $errTask=$child.StandardError.ReadToEndAsync()
        $child.WaitForExit()
        $outText=$outTask.GetAwaiter().GetResult()
        $errText=$errTask.GetAwaiter().GetResult()
        [IO.File]::WriteAllText((Join-Path $linuxRoot 'forge_sol_pgo_linux_rejection_20261025.stdout'),$outText,[Text.UTF8Encoding]::new($false))
        [IO.File]::WriteAllText((Join-Path $linuxRoot 'forge_sol_pgo_linux_rejection_20261025.stderr'),$errText,[Text.UTF8Encoding]::new($false))
        Check ($child.ExitCode -ne 0) 'Linux orchestration main unexpectedly succeeded'
        $rejectionFiles=@(Get-ChildItem -LiteralPath $linuxOut -File -Recurse -Force)
        Check ($rejectionFiles.Count -eq 1 -and $rejectionFiles[0].Extension -eq '.txt') 'Linux rejection must retain exactly one result TXT before source/dependency preflight'
        $rejectionText=[IO.File]::ReadAllText($rejectionFiles[0].FullName)
        Check ($rejectionText.Contains('UNVERIFIED')) 'Linux rejection report lacks UNVERIFIED status'
        Check ($rejectionText -match 'Native.*Windows|Windows.*required') 'Linux rejection report does not identify native-Windows requirement'
        Check (-not (Test-Path -LiteralPath (Join-Path $linuxOut 'build'))) 'Linux rejection created a build directory'
        Check (-not (Test-Path -LiteralPath (Join-Path $linuxOut 'tmp'))) 'Linux rejection created a preflight temporary directory'
        $child.Dispose()
        Add-FixtureRow 'linux_main_retains_one_unverified_report' 'PASS_REJECTED' 'Nonzero exit, one report, no build/tmp or dependencies invoked'
    } elseif ($IsLinux) {
        Add-FixtureRow 'linux_main_retains_one_unverified_report' 'NOT_RUN' 'Explicit -SkipLinuxSubprocess; overall harness remains UNVERIFIED'
    } else {
        Add-FixtureRow 'linux_main_retains_one_unverified_report' 'NOT_APPLICABLE' 'This host is not Linux'
    }
    $script:fixtureStatus=if ($IsLinux -and $SkipLinuxSubprocess) { 'UNVERIFIED_SKIPPED_LINUX_MAIN_FIXTURE' } else { 'PASS_SOFTWARE_FIXTURES_ONLY' }
} catch {
    Add-FixtureRow 'harness_failure' 'FAIL' $_.Exception.Message
    $script:fixtureStatus='FAIL'
} finally {
    Close-FixtureLog
    $summary=[ordered]@{kind='forge_sol_pgo_software_fixtures';status=$script:fixtureStatus;
                      native_windows_verified=$false;engine_run=$false;engine_compiler_run=$false;
                      csharp_parser_compiled_this_invocation=$script:parserCompiled;
                      session_constructed=$false;fixtures=$script:fixtureRows.ToArray();
                      production_checker_messages=$script:fixtureMessages.ToArray()}
    $bytes=[Text.Encoding]::UTF8.GetBytes(($summary | ConvertTo-Json -Depth 8) + "`n")
    $reportStream=[IO.FileStream]::new($report,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
    try { $reportStream.Write($bytes,0,$bytes.Length) } finally { $reportStream.Dispose() }
    Write-Host "SOFTWARE_FIXTURE_STATUS $($script:fixtureStatus) report=$report"
}
if ($script:fixtureStatus -ne 'PASS_SOFTWARE_FIXTURES_ONLY') { exit 1 }
