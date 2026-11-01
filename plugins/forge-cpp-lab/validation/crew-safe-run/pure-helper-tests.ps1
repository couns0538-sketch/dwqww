$ErrorActionPreference='Stop'
$launcher=$args[0]
. $launcher
$cases=@(
    @('', '""'),
    @('simple', '"simple"'),
    @('a b', '"a b"'),
    @('D:\foo\', '"D:\foo\\"'),
    @('a"b', '"a\"b"')
)
foreach($case in $cases) {
    if ((Quote-SafeArgument $case[0]) -cne $case[1]) {throw 'CRT argument quote mismatch'}
}
$refused=$false;try {Assert-SafeDisk 20000 0} catch {$refused=$true}
if (-not $refused) {throw 'Low floor accepted'}
$refused=$false;try {Quote-SafeArgument ('bad'+[char]0)} catch {$refused=$true}
if (-not $refused) {throw 'NUL accepted'}
$bad=[ordered]@{schema=1;executable='D:\tools\tool.exe';executable_sha256=('0'*64);arguments=@('--threads','4');working_directory='D:\test';output_directory='D:\test\out';read_paths=@('D:\tools\tool.exe');write_paths=@('D:\test\out');logical_cpus=@(0);worker_threads=4;minimum_free_mib=32768;required_bytes=0} | ConvertTo-Json -Depth 5 | ConvertFrom-Json
$refused=$false;try {Test-SafeJob $bad @('D:\npt')} catch {if($_.Exception.Message -notmatch 'worker_threads'){throw};$refused=$true}
if (-not $refused) {throw 'T4 accepted'}
$bad.worker_threads=2;$bad.logical_cpus=@(0,1,2)
$refused=$false;try {Test-SafeJob $bad @('D:\npt')} catch {if($_.Exception.Message -notmatch 'one or two unique'){throw};$refused=$true}
if (-not $refused) {throw 'Three CPUs accepted'}
# Run the production C# drain on ordinary streams, including a failing sink.
$text=Get-Content -LiteralPath $launcher -Raw
$source=[regex]::Match($text,"(?s)Add-Type -TypeDefinition @'\r?\n(?<source>.*?)\r?\n'@").Groups['source'].Value
if (-not $source) {throw 'Production drain source missing'}
Add-Type -TypeDefinition $source
Add-Type -TypeDefinition @'
using System; using System.IO;
public class CrewFailingSink : MemoryStream {
 public override void Write(byte[] buffer,int offset,int count) {throw new IOException("injected sink failure");}
 public override System.Threading.Tasks.Task WriteAsync(byte[] buffer,int offset,int count,System.Threading.CancellationToken token) {throw new IOException("injected sink failure");}
}
'@
foreach($failure in @($false,$true)) {
    $bytes=New-Object byte[] 262144
    $inputStream=[IO.MemoryStream]::new($bytes)
    $outputStream=if($failure){[CrewFailingSink]::new()}else{[IO.MemoryStream]::new()}
    try {
        $errorText=[ForgeCrewSafeDrain]::CopyAsync($inputStream,$outputStream).GetAwaiter().GetResult()
        if ($inputStream.Position -ne $inputStream.Length) {throw 'Drain stopped before EOF'}
        if ($failure -and $errorText -notmatch 'injected sink failure') {throw 'Capture error missing'}
        if (-not $failure -and ($errorText -or $outputStream.Length -ne $bytes.Length)) {throw 'Clean capture mismatch'}
    } finally {$inputStream.Dispose();$outputStream.Dispose()}
}
'PASS: 5 CRT quoting cases; NUL/floor/T4/three-CPU rejection; actual C# clean and failed-sink EOF drain.'
'Linux PowerShell 7/.NET helper tests; not Windows affinity, D-path, native process or PS5.1 qualification.'
