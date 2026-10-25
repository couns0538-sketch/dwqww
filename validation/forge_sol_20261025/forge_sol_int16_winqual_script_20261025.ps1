# Forge Sol native Windows/Zen5 qualification, frozen 2026-10-25.
# Run in a dedicated PowerShell 7 process with -NoProfile -File. Never dot-source.
# Runtime output: exactly one new forge_sol_int16_winqual_results_20261025.txt.
# No matches/Elo assertion. A Linux/Wine/syntax test is never native evidence.
# See forge_sol_winqual_notes_20261025.md for the safety contract and test plan.
[CmdletBinding()]
param(
    [string]$GppExe = 'C:\msys64\ucrt64\bin\g++.exe',
    [string]$ObjdumpExe = 'C:\msys64\ucrt64\bin\objdump.exe',
    # Two frozen source trees and their complete hashes are supplied in-folder.
    [string]$BuildManifest = (Join-Path $PSScriptRoot 'forge_sol_int16_build_manifest_20261025.json'),
    [ValidateRange(8,16)][int]$Pairs = 8,
    [ValidateRange(30,300)][int]$ChildTimeoutSeconds = 300
)
if ($MyInvocation.InvocationName -eq '.') { throw 'Run in a dedicated pwsh -NoProfile -File process; do not dot-source.' }
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:Clock = [Diagnostics.Stopwatch]::StartNew()
$script:Folder = [IO.Path]::GetFullPath($PSScriptRoot)
$script:Result = Join-Path $script:Folder 'forge_sol_int16_winqual_results_20261025.txt'
$script:Output = $null
$script:Controls = $null
$script:WorkSeconds = 2580.0 # 43 minutes: reserve the final 2 minutes for cleanup.
$script:TotalSeconds = 2700.0
$script:Failure = 'UNVERIFIED'
$script:SpeedVerdict = 'UNVERIFIED'
$script:ActivePids = @()
$script:Off = @{11=[long]308972;13=[long]745494;16=[long]2460422;20=[long]11901452;22=[long]31111774}
$script:LinuxOnUnverified = @{11=[long]335382;13=[long]850773;16=[long]3130100;20=[long]10757244;22=[long]27884195}
$script:On = @{}
$script:Invariant = [Globalization.CultureInfo]::InvariantCulture
$script:Identity = @{}
$script:SavedTemp = [Environment]::GetEnvironmentVariable('TEMP','Process')
$script:SavedTmp = [Environment]::GetEnvironmentVariable('TMP','Process')
$script:SavedTmpdir = [Environment]::GetEnvironmentVariable('TMPDIR','Process')
$script:SavedPath = [Environment]::GetEnvironmentVariable('PATH','Process')
$script:SavedModuleCache = [Environment]::GetEnvironmentVariable('PSModuleAnalysisCachePath','Process')
$script:SavedBundleCache = [Environment]::GetEnvironmentVariable('DOTNET_BUNDLE_EXTRACT_BASE_DIR','Process')

function Write-Result([string]$Text) {
    if ($null -ne $script:Output) { $script:Output.WriteLine($Text); $script:Output.Flush() }
    Write-Host $Text
}
function Stop-Qualification([string]$Code, [string]$Message) {
    $script:Failure = $Code
    throw "$Code $Message"
}
function Hash-File([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Existing-File([string]$Path) {
    $item = Get-Item -LiteralPath $Path -ErrorAction Stop
    if ($item.PSIsContainer) { Stop-Qualification 'BAD_INPUT' "Expected file: $Path" }
    return $item.FullName
}
function Number([double]$Value) { return $Value.ToString('0.000000',$script:Invariant) }
function Median([double[]]$Values) {
    $sorted = @($Values | Sort-Object)
    if ($sorted.Count -eq 0) { Stop-Qualification 'INTERNAL_ERROR' 'Empty median' }
    $i = [int][Math]::Floor($sorted.Count/2)
    if (($sorted.Count % 2) -eq 1) { return [double]$sorted[$i] }
    return ([double]$sorted[$i-1] + [double]$sorted[$i])/2.0
}
function Require-Properties($Object, [string[]]$Names, [string]$Context) {
    foreach ($name in $Names) {
        if ($null -eq $Object -or $Object.PSObject.Properties.Name -notcontains $name) {
            Stop-Qualification 'BAD_DATA' "$Context missing $name"
        }
    }
}
function Check-WorkBudget {
    if ($script:Clock.Elapsed.TotalSeconds -ge $script:WorkSeconds) {
        Stop-Qualification 'INCOMPLETE_TIME_BUDGET' 'No further work admitted after 43 minutes; cleanup time reserved.'
    }
}
function Own-Path([string]$Relative) {
    if ([IO.Path]::IsPathRooted($Relative) -or $Relative -match '(^|[/\\])\.\.([/\\]|$)') { Stop-Qualification 'BAD_INPUT' "Expected in-folder relative path: $Relative" }
    $full = [IO.Path]::GetFullPath((Join-Path $script:Folder $Relative))
    $prefix = $script:Folder.TrimEnd([IO.Path]::DirectorySeparatorChar)+[IO.Path]::DirectorySeparatorChar
    if (-not $full.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)) { Stop-Qualification 'BAD_INPUT' "Path escapes own folder: $Relative" }
    return $full
}
function Check-SourceTree($Tree,[string]$Label) {
    Require-Properties $Tree @('directory','files','network_sha256') "source tree $Label"
    $folder = Own-Path $Tree.directory
    $root = Get-Item -LiteralPath $folder
    if (-not $root.PSIsContainer -or ($root.Attributes -band [IO.FileAttributes]::ReparsePoint)) { Stop-Qualification 'BAD_SOURCE' "$Label source root must be a real directory" }
    $expected = [Collections.Generic.Dictionary[string,string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($record in @($Tree.files)) {
        Require-Properties $record @('path','sha256') "source file $Label"
        $relative = ([string]$record.path).Replace('\','/')
        if ($relative -match '^(?:/|[A-Za-z]:)|(^|/)\.\.(/|$)' -or [string]$record.sha256 -notmatch '^[0-9a-fA-F]{64}$' -or $expected.ContainsKey($relative)) { Stop-Qualification 'BAD_SOURCE' "$Label invalid/duplicate manifest path or SHA256: $relative" }
        $expected.Add($relative,([string]$record.sha256).ToLowerInvariant())
    }
    if ($expected.Count -lt 20) { Stop-Qualification 'BAD_SOURCE' "$Label incomplete source manifest" }
    $files = @(Get-ChildItem -LiteralPath $folder -Force -Recurse)
    $actual = [Collections.Generic.Dictionary[string,string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($item in $files) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { Stop-Qualification 'BAD_SOURCE' "$Label reparse point forbidden: $($item.FullName)" }
        if ($item.PSIsContainer) { continue }
        $relative = $item.FullName.Substring($folder.Length+1).Replace('\','/')
        $hash = Hash-File $item.FullName
        if (-not $expected.ContainsKey($relative) -or $expected[$relative] -ne $hash) { Stop-Qualification 'BAD_SOURCE' "$Label missing/mismatching manifest entry: $relative" }
        $actual.Add($relative,$hash)
    }
    if ($actual.Count -ne $expected.Count) { Stop-Qualification 'BAD_SOURCE' "$Label source file count mismatch" }
    $lines = [Collections.Generic.List[string]]::new()
    $keys = [string[]]@($actual.Keys); [Array]::Sort($keys,[StringComparer]::Ordinal)
    foreach ($relative in $keys) { $lines.Add("$($actual[$relative])  $relative`n") }
    $sha = [Security.Cryptography.SHA256]::Create()
    try { $treeHash = [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes(($lines -join '')))).Replace('-','').ToLowerInvariant() } finally { $sha.Dispose() }
    $network = Join-Path $folder 'src/nnue_weights.inc'
    $networkHash = Hash-File $network
    if ($networkHash -ne ([string]$Tree.network_sha256).ToLowerInvariant() -or $networkHash -ne '74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b') { Stop-Qualification 'BAD_NETWORK' "$Label exact H256 e12 network required" }
    Write-Result "SOURCE PASS build=$Label files=$($actual.Count) sorted_sha256_manifest=$treeHash network_sha256=$networkHash directory=$folder"
    return [pscustomobject]@{Folder=$folder;Hash=$treeHash;Network=$networkHash}
}

# Win32 is used so that no child executes even one instruction before the job,
# CPU mask and Idle priority apply. No termination API and no kill-on-close flag.
$script:NativeSource = @'
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Win32.SafeHandles;

namespace ForgeSolWinqual20261025 {
  public sealed class SymbolInfo {
    public long Instructions, Vfmadd, AllFma;
  }
  public sealed class Capture {
    readonly object gate = new object();
    readonly StringBuilder text = new StringBuilder();
    readonly StringBuilder tail = new StringBuilder();
    readonly int cap;
    public long Characters;
    public bool Truncated, ParseError, PeX64;
    public long UnknownFma;
    public readonly SortedDictionary<string,SymbolInfo> Symbols = new SortedDictionary<string,SymbolInfo>(StringComparer.Ordinal);
    public readonly HashSet<string> DefinedNnueFunctions = new HashSet<string>(StringComparer.Ordinal);
    static readonly Regex header = new Regex(@"^\s*[0-9a-fA-F]+\s+<(.+)>:\s*$",RegexOptions.Compiled);
    static readonly Regex function = new Regex(@"^\[\s*\d+\]\(sec\s+(\d+)\)\(fl 0x[0-9a-fA-F]+\)\(ty\s+20\)\(scl\s+\d+\)\s+\(nx\s+\d+\)\s+0x[0-9a-fA-F]+\s+(.+)$",RegexOptions.Compiled);
    static readonly Regex insn = new Regex(@"^\s*[0-9a-fA-F]+:\s+([A-Za-z][A-Za-z0-9.]*)\b",RegexOptions.Compiled);
    static readonly Regex addressLine = new Regex(@"^\s*[0-9a-fA-F]+:\s*\S",RegexOptions.Compiled);
    static readonly Regex fma = new Regex(@"^v?f(?:madd|msub|nmadd|nmsub)",RegexOptions.Compiled|RegexOptions.IgnoreCase);
    public Capture(int limit) { cap=limit; }
    public string Text { get { lock(gate) return text.ToString(); } }
    public string Tail { get { lock(gate) return tail.ToString(); } }
    void Keep(char[] buffer,int length) {
      lock(gate) {
        Characters+=length;
        int n=Math.Min(length,Math.Max(0,cap-text.Length));
        if(n>0) text.Append(buffer,0,n);
        if(n<length) Truncated=true;
        tail.Append(buffer,0,length);
        if(tail.Length>8192) tail.Remove(0,tail.Length-8192);
      }
    }
    public void Pump(Stream stream,bool disassembly) {
      string current=null;
      StringBuilder line=new StringBuilder();
      using(var reader=new StreamReader(stream,Encoding.UTF8,true,4096)) {
        char[] buffer=new char[4096]; int count;
        while((count=reader.Read(buffer,0,buffer.Length))>0) {
          Keep(buffer,count);
          if(!disassembly) continue;
          for(int i=0;i<count;i++) {
            char c=buffer[i];
            if(c=='\n') { Parse(line.ToString().TrimEnd('\r'),ref current); line.Clear(); }
            else if(line.Length<65536) line.Append(c);
            else ParseError=true;
          }
        }
        if(disassembly && line.Length>0) Parse(line.ToString().TrimEnd('\r'),ref current);
      }
    }
    void Parse(string line,ref string current) {
      if(line.IndexOf("file format pei-x86-64",StringComparison.Ordinal)>=0) PeX64=true;
      Match f=function.Match(line);
      if(f.Success && f.Groups[1].Value!="0" && f.Groups[2].Value.Contains("forge::nnue::")) DefinedNnueFunctions.Add(f.Groups[2].Value);
      Match h=header.Match(line);
      if(h.Success) {
        current=h.Groups[1].Value;
        if(!Symbols.ContainsKey(current)) Symbols.Add(current,new SymbolInfo());
        return;
      }
      Match m=insn.Match(line);
      if(!m.Success) {
        if(current!=null && current.Contains("forge::nnue::") && addressLine.IsMatch(line)) ParseError=true;
        return;
      }
      string op=m.Groups[1].Value;
      if(current==null) { if(fma.IsMatch(op)) UnknownFma++; return; }
      var s=Symbols[current]; s.Instructions++;
      if(op.StartsWith("vfmadd",StringComparison.OrdinalIgnoreCase)) s.Vfmadd++;
      if(fma.IsMatch(op)) s.AllFma++;
    }
  }
  public sealed class Child {
    public int Pid;
    public IntPtr Handle,Thread;
    public StreamWriter Input;
    public Capture Out,Err;
    public Task OutTask,ErrTask;
    public bool Resumed,InputClosed,Exited,TimedOut,DrainComplete;
    public uint ExitCode;
    public double Seconds;
    public string ControlError;
    public readonly List<string> CommandsSent=new List<string>();
  }
  public sealed class Session : IDisposable {
    [StructLayout(LayoutKind.Sequential)] struct BasicLimits {
      public long PerProcessUserTimeLimit,PerJobUserTimeLimit;
      public uint LimitFlags;
      public UIntPtr MinimumWorkingSetSize,MaximumWorkingSetSize;
      public uint ActiveProcessLimit;
      public UIntPtr Affinity;
      public uint PriorityClass,SchedulingClass;
    }
    [StructLayout(LayoutKind.Sequential)] struct IoCounters {
      public ulong ReadOperationCount,WriteOperationCount,OtherOperationCount,ReadTransferCount,WriteTransferCount,OtherTransferCount;
    }
    [StructLayout(LayoutKind.Sequential)] struct ExtendedLimits {
      public BasicLimits BasicLimitInformation;
      public IoCounters IoInfo;
      public UIntPtr ProcessMemoryLimit,JobMemoryLimit,PeakProcessMemoryUsed,PeakJobMemoryUsed;
    }
    [StructLayout(LayoutKind.Sequential)] struct SecurityAttributes {
      public int Length; public IntPtr Descriptor;
      [MarshalAs(UnmanagedType.Bool)] public bool Inherit;
    }
    [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)] struct StartupInfo {
      public int Size; public string Reserved,Desktop,Title;
      public int X,Y,XSize,YSize,XCountChars,YCountChars,FillAttribute,Flags;
      public short ShowWindow,Reserved2; public IntPtr ReservedPtr,StdInput,StdOutput,StdError;
    }
    [StructLayout(LayoutKind.Sequential)] struct ProcessInformation {
      public IntPtr Process,Thread; public int ProcessId,ThreadId;
    }
    [DllImport("kernel32.dll",SetLastError=true,CharSet=CharSet.Unicode)] static extern IntPtr CreateJobObject(IntPtr attributes,string name);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool SetInformationJobObject(IntPtr job,int info,ref ExtendedLimits limits,uint size);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool QueryInformationJobObject(IntPtr job,int info,out ExtendedLimits limits,uint size,IntPtr length);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool AssignProcessToJobObject(IntPtr job,IntPtr process);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool IsProcessInJob(IntPtr process,IntPtr job,out bool result);
    [DllImport("kernel32.dll")] static extern IntPtr GetCurrentProcess();
    [DllImport("kernel32.dll")] static extern ushort GetActiveProcessorGroupCount();
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool CreatePipe(out IntPtr read,out IntPtr write,ref SecurityAttributes security,int size);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool SetHandleInformation(IntPtr handle,uint mask,uint flags);
    [DllImport("kernel32.dll",SetLastError=true,CharSet=CharSet.Unicode)] static extern bool CreateProcessW(string application,StringBuilder command,IntPtr pa,IntPtr ta,bool inherit,uint flags,IntPtr environment,string folder,ref StartupInfo startup,out ProcessInformation result);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool SetProcessAffinityMask(IntPtr process,UIntPtr mask);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetProcessAffinityMask(IntPtr process,out UIntPtr processMask,out UIntPtr systemMask);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool SetPriorityClass(IntPtr process,uint priority);
    [DllImport("kernel32.dll",SetLastError=true)] static extern uint GetPriorityClass(IntPtr process);
    [DllImport("kernel32.dll",SetLastError=true)] static extern uint ResumeThread(IntPtr thread);
    [DllImport("kernel32.dll",SetLastError=true)] static extern uint WaitForSingleObject(IntPtr handle,uint milliseconds);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetExitCodeProcess(IntPtr process,out uint code);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool CloseHandle(IntPtr handle);
    [DllImport("kernel32.dll",CharSet=CharSet.Unicode)] static extern IntPtr GetModuleHandle(string name);
    [DllImport("kernel32.dll",CharSet=CharSet.Ansi)] static extern IntPtr GetProcAddress(IntPtr module,string name);
    IntPtr job;
    public readonly List<Child> Children=new List<Child>();
    public static bool IsWine { get { return GetProcAddress(GetModuleHandle("ntdll.dll"),"wine_get_version")!=IntPtr.Zero; } }
    static void Check(bool good,string action) { if(!good) throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error(),action); }
    public Session() {
      Check(GetActiveProcessorGroupCount()==1,"A single Windows processor group is required for global CPUs 0-3");
      job=CreateJobObject(IntPtr.Zero,null); Check(job!=IntPtr.Zero,"CreateJobObject");
      var limits=new ExtendedLimits();
      // JOB_MEMORY | AFFINITY | PRIORITY_CLASS; deliberately no KILL_ON_JOB_CLOSE.
      limits.BasicLimitInformation.LimitFlags=0x200|0x10|0x20;
      limits.BasicLimitInformation.Affinity=new UIntPtr(15);
      limits.BasicLimitInformation.PriorityClass=0x40;
      limits.JobMemoryLimit=new UIntPtr(3UL*1024UL*1024UL*1024UL);
      Check(SetInformationJobObject(job,9,ref limits,(uint)Marshal.SizeOf(typeof(ExtendedLimits))),"SetInformationJobObject");
      // Dedicated pwsh host belongs to the same memory/CPU/priority job.
      Check(AssignProcessToJobObject(job,GetCurrentProcess()),"Assign dedicated pwsh host to bounded job");
      Verify(GetCurrentProcess());
    }
    void Verify(IntPtr process) {
      bool member; UIntPtr mask,system;
      Check(IsProcessInJob(process,job,out member)&&member,"Verify job membership");
      Check(GetProcessAffinityMask(process,out mask,out system)&&mask.ToUInt64()==15,"Verify CPU affinity 0xF");
      Check(GetPriorityClass(process)==0x40,"Verify Idle priority");
      ExtendedLimits applied;
      Check(QueryInformationJobObject(job,9,out applied,(uint)Marshal.SizeOf(typeof(ExtendedLimits)),IntPtr.Zero),"Verify job limits readback");
      Check(applied.JobMemoryLimit.ToUInt64()==3UL*1024UL*1024UL*1024UL && applied.BasicLimitInformation.LimitFlags==0x230,"Verify 3 GiB memory/affinity/priority limits and absence of kill flags");
    }
    public ulong PeakCommittedBytes {
      get { ExtendedLimits limits; Check(QueryInformationJobObject(job,9,out limits,(uint)Marshal.SizeOf(typeof(ExtendedLimits)),IntPtr.Zero),"Query job memory"); return limits.PeakJobMemoryUsed.ToUInt64(); }
    }
    static string Quote(string s) {
      if(s.IndexOf('\0')>=0 || s.IndexOf('\r')>=0 || s.IndexOf('\n')>=0) throw new ArgumentException("Invalid command argument");
      var b=new StringBuilder("\""); int slashes=0;
      foreach(char c in s) {
        if(c=='\\') { slashes++; continue; }
        if(c=='\"') { b.Append('\\',slashes*2+1); b.Append(c); slashes=0; continue; }
        b.Append('\\',slashes); slashes=0; b.Append(c);
      }
      b.Append('\\',slashes*2); b.Append('\"'); return b.ToString();
    }
    public Child Start(string exe,string[] args,string folder,bool disassembly) {
      var sa=new SecurityAttributes { Length=Marshal.SizeOf(typeof(SecurityAttributes)),Inherit=true };
      IntPtr inputRead=IntPtr.Zero,inputWrite=IntPtr.Zero,outputRead=IntPtr.Zero,outputWrite=IntPtr.Zero,errorRead=IntPtr.Zero,errorWrite=IntPtr.Zero;
      Child c=null;
      try {
        Check(CreatePipe(out inputRead,out inputWrite,ref sa,4096),"stdin pipe");
        Check(CreatePipe(out outputRead,out outputWrite,ref sa,4096),"stdout pipe");
        Check(CreatePipe(out errorRead,out errorWrite,ref sa,4096),"stderr pipe");
        Check(SetHandleInformation(inputWrite,1,0),"non-inheritable parent stdin");
        Check(SetHandleInformation(outputRead,1,0),"non-inheritable parent stdout");
        Check(SetHandleInformation(errorRead,1,0),"non-inheritable parent stderr");
        var si=new StartupInfo { Size=Marshal.SizeOf(typeof(StartupInfo)),Flags=0x100,StdInput=inputRead,StdOutput=outputWrite,StdError=errorWrite };
        var command=new StringBuilder(Quote(exe)); foreach(string arg in args) command.Append(' ').Append(Quote(arg));
        ProcessInformation pi;
        Check(CreateProcessW(exe,command,IntPtr.Zero,IntPtr.Zero,true,0x4|0x40|0x08000000,IntPtr.Zero,folder,ref si,out pi),"CreateProcess suspended");
        c=new Child { Pid=pi.ProcessId,Handle=pi.Process,Thread=pi.Thread,Out=new Capture(disassembly?16384:2097152),Err=new Capture(65536) };
        Children.Add(c); // Account for the child even if subsequent controls fail.
        CloseHandle(inputRead); inputRead=IntPtr.Zero;
        CloseHandle(outputWrite); outputWrite=IntPtr.Zero;
        CloseHandle(errorWrite); errorWrite=IntPtr.Zero;
        c.Input=new StreamWriter(new FileStream(new SafeFileHandle(inputWrite,true),FileAccess.Write,4096,false),new UTF8Encoding(false));
        inputWrite=IntPtr.Zero; c.Input.AutoFlush=true;
        var output=new FileStream(new SafeFileHandle(outputRead,true),FileAccess.Read,4096,false); outputRead=IntPtr.Zero;
        var error=new FileStream(new SafeFileHandle(errorRead,true),FileAccess.Read,4096,false); errorRead=IntPtr.Zero;
        c.OutTask=Task.Run(()=>c.Out.Pump(output,disassembly));
        c.ErrTask=Task.Run(()=>c.Err.Pump(error,false));
        bool member; Check(IsProcessInJob(c.Handle,job,out member),"Check child inherited job");
        if(!member) Check(AssignProcessToJobObject(job,c.Handle),"Assign suspended child to job");
        Check(SetProcessAffinityMask(c.Handle,new UIntPtr(15)),"Pin suspended child");
        Check(SetPriorityClass(c.Handle,0x40),"Set suspended child Idle");
        Verify(c.Handle);
        Check(ResumeThread(c.Thread)!=UInt32.MaxValue,"Resume constrained child"); c.Resumed=true;
        CloseHandle(c.Thread); c.Thread=IntPtr.Zero;
        return c;
      } catch(Exception e) {
        if(c!=null) { c.ControlError=e.Message; CloseInput(c); }
        throw;
      } finally {
        foreach(IntPtr h in new[]{inputRead,inputWrite,outputRead,outputWrite,errorRead,errorWrite}) if(h!=IntPtr.Zero) CloseHandle(h);
      }
    }
    public void Send(Child c,string[] lines) {
      int bytes=0; foreach(string line in lines) bytes+=Encoding.UTF8.GetByteCount(line)+2;
      if(bytes>3000) throw new ArgumentException("Input exceeds bounded pipe budget");
      foreach(string line in lines) { if(line.IndexOf('\n')>=0 || line.IndexOf('\r')>=0) throw new ArgumentException("Multiline command"); c.Input.WriteLine(line); c.CommandsSent.Add(line); }
    }
    public void CloseInput(Child c) {
      if(c.InputClosed) return; c.InputClosed=true;
      try { if(c.Input!=null) c.Input.Dispose(); } catch(IOException) { }
      c.CommandsSent.Add("<EOF>");
    }
    public bool Poll(Child c,int ms) {
      if(c.Exited) return true;
      uint state=WaitForSingleObject(c.Handle,(uint)Math.Max(0,ms));
      if(state==0) { c.Exited=true; uint code; Check(GetExitCodeProcess(c.Handle,out code),"Exit code"); c.ExitCode=code; return true; }
      if(state!=258) throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error(),"Wait child");
      return false;
    }
    public bool Drain(Child c,int milliseconds) {
      if(c.OutTask==null||c.ErrTask==null) return false;
      c.DrainComplete=Task.WaitAll(new[]{c.OutTask,c.ErrTask},Math.Max(0,milliseconds));
      return c.DrainComplete;
    }
    public void RequestStop(Child c) {
      if(Poll(c,0)) return;
      if(c.Resumed&&!c.InputClosed) {
        try { Send(c,new[]{"stop","quit"}); } catch(IOException) { } catch(ObjectDisposedException) { }
      }
      CloseInput(c); // EOF is also supplied to non-UCI helpers.
    }
    [DllImport("kernel32.dll",EntryPoint="QueryInformationJobObject",SetLastError=true)] static extern bool QueryJobIds(IntPtr job,int info,IntPtr data,uint size,out uint length);
    public int[] LivingPids() {
      // Include compiler grandchildren, not just directly created children.
      IntPtr data=Marshal.AllocHGlobal(131072);
      try {
        uint length; Check(QueryJobIds(job,3,data,131072,out length),"Query all job PIDs");
        uint assigned=(uint)Marshal.ReadInt32(data,0),listed=(uint)Marshal.ReadInt32(data,4);
        if(assigned!=listed||listed>16383) throw new InvalidOperationException("Incomplete job PID inventory");
        int host=Process.GetCurrentProcess().Id; var pids=new List<int>();
        for(int i=0;i<listed;i++) { int pid=checked((int)Marshal.ReadInt64(data,8+i*8)); if(pid!=host) pids.Add(pid); }
        foreach(var c in Children) Poll(c,0);
        return pids.ToArray();
      } finally { Marshal.FreeHGlobal(data); }
    }
    public void Dispose() {
      foreach(var c in Children) {
        CloseInput(c);
        if(c.Thread!=IntPtr.Zero) { CloseHandle(c.Thread); c.Thread=IntPtr.Zero; }
        if(c.Handle!=IntPtr.Zero) { CloseHandle(c.Handle); c.Handle=IntPtr.Zero; }
      }
      if(job!=IntPtr.Zero) { CloseHandle(job); job=IntPtr.Zero; }
    }
  }
}
'@

function Run-Child([string]$Exe,[string[]]$Arguments,[string[]]$Commands,[string]$Tag,[bool]$Disassembly=$false) {
    Check-WorkBudget
    $previousPids = @($script:Controls.LivingPids())
    if ($previousPids.Count -ne 0) { Stop-Qualification 'UNVERIFIED_DESCENDANT_REMAINS' "No concurrent child admitted; existing job PIDs=$($previousPids -join ',')" }
    if ((Hash-File $Exe) -ne $script:Identity[$Exe]) { Stop-Qualification 'IDENTITY_CHANGED' $Exe }
    $available = $script:WorkSeconds - $script:Clock.Elapsed.TotalSeconds
    $timeout = [Math]::Min([double]$ChildTimeoutSeconds,$available)
    if ($timeout -lt 1) { Stop-Qualification 'INCOMPLETE_TIME_BUDGET' 'Insufficient child admission budget' }
    Write-Result "RUN BEGIN tag=$Tag exe=$Exe arguments=$($Arguments -join ' ') timeout_seconds=$(Number $timeout) affinity=0xF priority=Idle"
    $child = $script:Controls.Start($Exe,[string[]]$Arguments,$script:Folder,$Disassembly)
    Write-Result "RUN CHILD tag=$Tag pid=$($child.Pid) suspended_controls_verified=true resumed=true"
    $watch = [Diagnostics.Stopwatch]::StartNew()
    try {
        if ($Commands.Count) {
            Write-Result "STDIN BEGIN tag=$Tag"
            foreach ($line in $Commands) { Write-Result $line }
            Write-Result "STDIN END tag=$Tag"
            $script:Controls.Send($child,[string[]]$Commands)
        }
        # Keep UCI stdin open until normal quit is consumed or graceful recovery.
        # Non-UCI tools get EOF immediately and cannot await unbounded input.
        if (-not $Commands.Count) { $script:Controls.CloseInput($child) }
        while (-not $script:Controls.Poll($child,100)) {
            if ($watch.Elapsed.TotalSeconds -ge $timeout) {
                $child.TimedOut = $true
                $script:Controls.RequestStop($child)
                break
            }
        }
        if ($child.Exited) {
            $script:Controls.CloseInput($child)
            if (-not $script:Controls.Drain($child,2000)) { Stop-Qualification 'OUTPUT_DRAIN_TIMEOUT' "tag=$Tag pid=$($child.Pid)" }
        }
    } finally {
        $child.Seconds = $watch.Elapsed.TotalSeconds
        Write-Result "STDOUT BEGIN tag=$Tag total_chars=$($child.Out.Characters) truncated=$($child.Out.Truncated)"
        Write-Result $child.Out.Text
        Write-Result "STDOUT END tag=$Tag"
        Write-Result "STDERR BEGIN tag=$Tag total_chars=$($child.Err.Characters) truncated=$($child.Err.Truncated)"
        Write-Result $child.Err.Text
        Write-Result "STDERR END tag=$Tag"
        Write-Result "RUN END tag=$Tag pid=$($child.Pid) exited=$($child.Exited) exit_code=$($child.ExitCode) timed_out=$($child.TimedOut) seconds=$(Number $child.Seconds)"
    }
    if ($child.TimedOut) { Stop-Qualification 'CHILD_TIMEOUT_UNVERIFIED' "tag=$Tag pid=$($child.Pid); stop/quit/EOF requested; no later work" }
    if ($child.ExitCode -ne 0) { Stop-Qualification 'CHILD_FAILED' "tag=$Tag exit=$($child.ExitCode)" }
    if ($child.Err.Truncated -or ($child.Out.Truncated -and -not $Disassembly)) { Stop-Qualification 'OUTPUT_LIMIT' "tag=$Tag bounded capture overflow" }
    $remainingPids = @($script:Controls.LivingPids())
    if ($remainingPids.Count -ne 0) { Stop-Qualification 'UNVERIFIED_DESCENDANT_REMAINS' "tag=$Tag compiler/helper descendant PIDs=$($remainingPids -join ',')" }
    return $child
}

function Uci-Setup([bool]$On) {
    return @('uci','setoption name Threads value 1','setoption name Hash value 16',
        'setoption name OwnBook value false','setoption name UseNNUE value true',
        'setoption name SingTtPv value false','setoption name RefutLmr value false',
        "setoption name NnueInt16 value $($On.ToString().ToLowerInvariant())",'isready')
}
function Check-Backend([string]$Text,[bool]$On) {
    if ($Text -notmatch '(?m)^uciok\r?$' -or $Text -notmatch '(?m)^readyok\r?$') { Stop-Qualification 'BAD_UCI' 'Missing uciok/readyok' }
    if ($On) {
        $option = [regex]::Match($Text,'(?m)^option name NnueInt16 type check default false\r?$')
        $active = [regex]::Match($Text,'(?m)^info string NnueInt16 active\r?$')
        if (-not $option.Success -or -not $active.Success -or $active.Index -le $option.Index -or $Text -match 'NnueInt16 unavailable|invalid value for option NnueInt16') {
            Stop-Qualification 'BACKEND_INACTIVE' 'NnueInt16 ON needs OFF-default advertisement and subsequent active acknowledgement without fallback'
        }
    } elseif ($Text -match '(?m)^info string NnueInt16 active\r?$') { Stop-Qualification 'BAD_OFF_BACKEND' 'Unexpected int16 activation in OFF mode' }
}
function Run-Bench([string]$Exe,[bool]$On,[int]$Depth,[string]$Tag,[long]$Expected=0) {
    $commands = @(Uci-Setup $On) + @("bench $Depth",'quit')
    $child = Run-Child $Exe @() $commands $Tag
    $text = $child.Out.Text
    Check-Backend $text $On
    $rows = [regex]::Matches($text,'(?m)^info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)\r?$')
    if ($rows.Count -ne 1) { Stop-Qualification 'BAD_BENCH' "$Tag requires exactly one bench line" }
    $row = $rows[0]
    $nodes = [long]$row.Groups[2].Value
    $nps = [double]$row.Groups[4].Value
    if ([int]$row.Groups[1].Value -ne $Depth -or $nodes -le 0 -or $nps -le 0) { Stop-Qualification 'BAD_BENCH' "$Tag invalid depth/nodes/NPS" }
    if ($Expected -gt 0 -and $nodes -ne $Expected) { Stop-Qualification 'BAD_NODES' "$Tag nodes=$nodes expected=$Expected; no later test/timing" }
    return [pscustomobject]@{Nodes=$nodes;Nps=$nps;Ms=[long]$row.Groups[3].Value}
}
function Run-Perft([string]$Exe,[bool]$On,[string]$Label,[string]$Position,[int]$Depth,[long]$Expected) {
    $child = Run-Child $Exe @() (@(Uci-Setup $On)+@($Position,"go perft $Depth",'quit')) "perft-$Label-$On-d$Depth"
    Check-Backend $child.Out.Text $On
    $rows = [regex]::Matches($child.Out.Text,'(?m)^nodes (\d+)\r?$')
    if ($rows.Count -ne 1 -or [long]$rows[0].Groups[1].Value -ne $Expected) { Stop-Qualification 'BAD_PERFT' "$Label ON=$On depth=$Depth expected=$Expected" }
    Write-Result "PERFT PASS build=$Label NnueInt16=$On depth=$Depth nodes=$Expected"
}
function Run-Disassembly([string]$Exe,[string]$Label) {
    $child = Run-Child $ObjdumpExe @('-d','-t','-C','--no-show-raw-insn',$Exe) @() "objdump-$Label" $true
    if (-not $child.Out.PeX64 -or $child.Out.ParseError -or $child.Out.UnknownFma -ne 0) { Stop-Qualification 'BAD_DISASSEMBLY' "$Label unknown format/parser/FMA scope" }
    $found = 0; $nnueFma = [long]0; $externalFma = [long]0
    if ($child.Out.DefinedNnueFunctions.Count -eq 0) { Stop-Qualification 'BAD_DISASSEMBLY' "$Label no defined NNUE function symbols in COFF table" }
    foreach ($symbol in $child.Out.DefinedNnueFunctions) {
        if (-not $child.Out.Symbols.ContainsKey($symbol) -or $child.Out.Symbols[$symbol].Instructions -le 0) { Stop-Qualification 'BAD_DISASSEMBLY' "$Label symbol table function missing from disassembly: $symbol" }
    }
    foreach ($entry in $child.Out.Symbols.GetEnumerator()) {
        $symbol = $entry.Key; $stats = $entry.Value
        if ($symbol.Contains('forge::nnue::')) {
            if ($stats.Instructions -le 0) { Stop-Qualification 'BAD_DISASSEMBLY' "$Label empty NNUE symbol $symbol" }
            $found++; $nnueFma += $stats.AllFma
            Write-Result "NNUE_SYMBOL build=$Label instructions=$($stats.Instructions) vfmadd=$($stats.Vfmadd) all_fma=$($stats.AllFma) symbol=$symbol"
        } elseif ($stats.AllFma -gt 0) {
            $externalFma += $stats.AllFma
            Write-Result "EXTERNAL_FMA build=$Label instructions=$($stats.Instructions) vfmadd=$($stats.Vfmadd) all_fma=$($stats.AllFma) symbol=$symbol"
        }
    }
    if ($found -eq 0 -or $nnueFma -ne 0) { Stop-Qualification 'NNUE_FMA_FAIL' "$Label NNUE_symbols=$found NNUE_all_fma=$nnueFma" }
    Write-Result "DISASSEMBLY PASS build=$Label defined_NNUE_function_symbols=$($child.Out.DefinedNnueFunctions.Count) all_demangled_forge_nnue_symbols=$found nnue_vfmadd=0 nnue_all_fma=0 external_runtime_all_fma=$externalFma scope=emitted_named_functions_no_LTO"
}
function Build-Executable([string]$Source,[string[]]$RelativeSources,[string]$Output,[string]$Label,[string[]]$Flags) {
    if (Test-Path -LiteralPath $Output) { Stop-Qualification 'OUTPUT_EXISTS' "Refusing to overwrite existing executable: $Output" }
    $arguments = @($Flags) + @('-I',(Join-Path $Source 'include'))
    foreach ($relative in $RelativeSources) { $arguments += Join-Path $Source $relative }
    $arguments += @('-o',$Output)
    [void](Run-Child $GppExe $arguments @() "compile-$Label")
    $Output = Existing-File $Output
    $script:Identity[$Output] = Hash-File $Output
    Write-Result "BUILT build=$Label sha256=$($script:Identity[$Output]) file=$Output"
    $imports = Run-Child $ObjdumpExe @('-p',$Output) @() "imports-$Label"
    if ($imports.Out.Text -notmatch 'file format pei-x86-64' -or $imports.Out.Text -match '(?im)DLL Name:\s*(?:libgcc|libstdc\+\+|libwinpthread)') { Stop-Qualification 'BAD_STATIC_BUILD' "$Label wrong PE format or dynamic GCC/C++/pthread dependency" }
}

try {
    # CreateNew prevents overwriting a previous/partial report, including failure evidence.
    $stream = [IO.File]::Open($script:Result,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
    $script:Output = [IO.StreamWriter]::new($stream,[Text.UTF8Encoding]::new($false))
    Write-Result 'FORGE_SOL_INT16_WINQUAL protocol_date=20261025 STATUS=RUNNING native_result=UNVERIFIED'
    Write-Result "CONTRACT affinity=0xF CPUs=0,1,2,3 priority=Idle threads=1 hash_mib=16 OwnBook=false UseNNUE=true work_admission_limit_seconds=2580 total_target_seconds=2700 ABAB_blocks=$Pairs"
    Write-Result 'LIMITATION no process is terminated; uncooperative stop/quit/EOF children can survive the 45-minute target. A hard completion deadline and guaranteed cleanup cannot both be promised under kill-nothing.'
    Write-Result 'MEMORY_CONTRACT shared_JobObject_includes_dedicated_pwsh_and_children hard_private_committed_limit_bytes=3221225472 headroom_below_4GiB_bytes=1073741824 no_kill_on_close=true allocation_denial_may_cause_application_OOM_or_exit aggregate_RSS_is_not_a_Windows_job_hard_limit'
    Write-Result 'SCOPE correctness_and_search_NPS_only matches=0 Elo=UNPROVEN 3_percent_gain=UNVERIFIED'
    Write-Result "FROZEN_STATISTICS primary=median_of_all_adjacent_B_over_A_ratios adjacent_pairs=$($Pairs*2) ABAB_blocks=$Pairs fresh_timed_processes=$($Pairs*4) threshold_ratio=1.03 supplemental=median_block_geometric_ratio no_outlier_rejection=true"
    if ($PSVersionTable.PSVersion.Major -lt 7) { Stop-Qualification 'UNSUPPORTED_HOST' 'PowerShell 7 required' }
    if (-not [Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([Runtime.InteropServices.OSPlatform]::Windows)) { Stop-Qualification 'NATIVE_WINDOWS_REQUIRED' 'Linux is rejected; no synthetic or Wine mode exists' }
    if ([Runtime.InteropServices.RuntimeInformation]::ProcessArchitecture.ToString() -ne 'X64' -or [Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString() -ne 'X64') { Stop-Qualification 'UNSUPPORTED_HOST' 'Native x64 Windows and x64 PowerShell required' }
    # Redirect .NET/compiler/helper temporary writes into this script's own folder.
    [Environment]::SetEnvironmentVariable('TEMP',$script:Folder,'Process')
    [Environment]::SetEnvironmentVariable('TMP',$script:Folder,'Process')
    [Environment]::SetEnvironmentVariable('TMPDIR',$script:Folder,'Process')
    [Environment]::SetEnvironmentVariable('PSModuleAnalysisCachePath',(Join-Path $script:Folder 'forge_sol_psmodule_cache_20261025.bin'),'Process')
    [Environment]::SetEnvironmentVariable('DOTNET_BUNDLE_EXTRACT_BASE_DIR',$script:Folder,'Process')
    Add-Type -TypeDefinition $script:NativeSource -Language CSharp
    if ([ForgeSolWinqual20261025.Session]::IsWine -or (Test-Path 'HKCU:\Software\Wine') -or (Test-Path 'HKLM:\SOFTWARE\Wine')) { Stop-Qualification 'NATIVE_WINDOWS_REQUIRED' 'Wine detected' }
    $cpu = Get-ItemProperty -LiteralPath 'HKLM:\HARDWARE\DESCRIPTION\System\CentralProcessor\0'
    Write-Result "HOST OS=$([Runtime.InteropServices.RuntimeInformation]::OSDescription) PowerShell=$($PSVersionTable.PSVersion) cpu_name=$($cpu.ProcessorNameString.Trim()) identifier=$($cpu.Identifier) vendor=$($cpu.VendorIdentifier)"
    if ($cpu.VendorIdentifier -ne 'AuthenticAMD' -or $cpu.Identifier -notmatch '\bFamily 26\b') { Stop-Qualification 'ZEN5_REQUIRED' 'AMD family 0x1A (26) required; CPU identity retained' }
    $script:Controls = [ForgeSolWinqual20261025.Session]::new()
    Write-Result 'PROCESS_CONTROLS PASS shared_job=true host_and_descendants=true affinity=0xF priority=Idle suspended_launch=true'
    $GppExe = Existing-File $GppExe; $ObjdumpExe = Existing-File $ObjdumpExe
    $BuildManifest = Existing-File $BuildManifest
    [Environment]::SetEnvironmentVariable('PATH',([IO.Path]::GetDirectoryName($GppExe)+';'+$script:SavedPath),'Process')
    foreach ($path in @($GppExe,$ObjdumpExe,$BuildManifest)) {
        $script:Identity[$path] = Hash-File $path
        Write-Result "IDENTITY sha256=$($script:Identity[$path]) file=$path"
    }
    $manifestText = [IO.File]::ReadAllText($BuildManifest)
    Write-Result "BUILD_MANIFEST BEGIN`n$manifestText`nBUILD_MANIFEST END"
    $manifest = $manifestText | ConvertFrom-Json
    Require-Properties $manifest @('protocol','compiler','flags','source_trees') 'build manifest'
    Require-Properties $manifest.compiler @('version','target','distribution') 'compiler'
    if ($manifest.protocol -ne 'forge_sol_int16_winqual_20261025' -or $manifest.compiler.version -ne '15.2.0' -or $manifest.compiler.target -ne 'x86_64-w64-mingw32' -or $manifest.compiler.distribution -ne 'MSYS2') { Stop-Qualification 'BAD_BUILD_MANIFEST' 'Exact MSYS2 Windows GCC 15.2.0 manifest required' }
    # Exact recovered recipe: no AVX512/alignment defines or extra tuning flags.
    $requiredFlags = @('-std=c++20','-O3','-DNDEBUG','-DFORGE_NNUE_HIDDEN=256','-ffp-contract=off','-fno-fast-math','-march=znver5','-static','-pthread')
    if (@($manifest.flags).Count -ne $requiredFlags.Count) { Stop-Qualification 'BAD_BUILD_MANIFEST' 'Exact nine recovered flags required' }
    for ($i=0;$i -lt $requiredFlags.Count;$i++) { if ($manifest.flags[$i] -cne $requiredFlags[$i]) { Stop-Qualification 'BAD_BUILD_MANIFEST' "Flag/order mismatch at $i" } }
    Require-Properties $manifest.source_trees @('buffer','int16') 'source trees'
    $bufferTree = Check-SourceTree $manifest.source_trees.buffer 'buffer'
    $int16Tree = Check-SourceTree $manifest.source_trees.int16 'int16'
    if ($bufferTree.Hash -eq $int16Tree.Hash -or $bufferTree.Folder -eq $int16Tree.Folder) { Stop-Qualification 'BAD_SOURCE' 'Distinct buffer-only and buffer+int16 trees required' }
    $version = Run-Child $GppExe @('--version') @() 'g++-version'
    $fullVersion = Run-Child $GppExe @('-dumpfullversion') @() 'g++-fullversion'
    $target = Run-Child $GppExe @('-dumpmachine') @() 'g++-target'
    if ($version.Out.Text -notmatch '(?i)MSYS2' -or $fullVersion.Out.Text.Trim() -cne '15.2.0' -or $target.Out.Text.Trim() -cne 'x86_64-w64-mingw32') { Stop-Qualification 'WRONG_COMPILER' 'Exact MSYS2 GCC 15.2.0 x86_64-w64-mingw32 required' }
    $BufferExe = Own-Path 'forge_sol_buffer_only_20261025.exe'
    $Int16Exe = Own-Path 'forge_sol_int16_20261025.exe'
    $ParityExe = Own-Path 'forge_sol_int16_parity_20261025.exe'
    $engineSources = @('src/bitboard.cpp','src/board.cpp','src/book.cpp','src/eval.cpp','src/eval_params.cpp','src/nnue.cpp','src/search.cpp','src/uci.cpp')
    Build-Executable $bufferTree.Folder $engineSources $BufferExe 'buffer' $requiredFlags
    Build-Executable $int16Tree.Folder $engineSources $Int16Exe 'int16' $requiredFlags
    $paritySources = @($engineSources | Where-Object { $_ -ne 'src/uci.cpp' }) + @('tools/nnue_int16_parity.cpp')
    Build-Executable $int16Tree.Folder $paritySources $ParityExe 'actual-api-parity' $requiredFlags
    [void](Check-SourceTree $manifest.source_trees.buffer 'buffer-after-build')
    [void](Check-SourceTree $manifest.source_trees.int16 'int16-after-build')
    Write-Result 'BUILD PASS source_manifests_match=true compiler=MSYS2_GCC_15.2.0 target=znver5 static=true exact_recovered_recipe=true LTO=false'
    # Each engine's FIRST engine command/test is its mandatory OFF bench11.
    foreach ($build in @(@{Label='buffer';Exe=$BufferExe},@{Label='int16';Exe=$Int16Exe})) {
        foreach ($depth in @(11,13,16,20,22)) {
            $bench = Run-Bench $build.Exe $false $depth "off-$($build.Label)-d$depth" $script:Off[$depth]
            Write-Result "OFF_NODES PASS build=$($build.Label) depth=$depth nodes=$($bench.Nodes) all_experimental_options=OFF"
        }
    }
    # Native ON counts are measurements, frozen before any timing; the Linux
    # vector is explicitly unverified across platforms and is never a pass gate.
    foreach ($depth in @(11,13,16,20,22)) {
        $bench = Run-Bench $Int16Exe $true $depth "on-native-measure-d$depth"
        $script:On[$depth] = [long]$bench.Nodes
        Write-Result "ON_NODES NATIVE_MEASURED depth=$depth nodes=$($bench.Nodes) linux_reference_unverified=$($script:LinuxOnUnverified[$depth]) same_as_linux_reference=$($bench.Nodes -eq $script:LinuxOnUnverified[$depth])"
    }
    Write-Result "ON_NODE_CONTRACT FROZEN_NATIVE depths=11,13,16,20,22 nodes=$(@(11,13,16,20,22).ForEach({$script:On[$_]}) -join ',')"
    $kiwi = 'position fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'
    foreach ($build in @(@{Label='buffer';Exe=$BufferExe;On=$false},@{Label='int16-off';Exe=$Int16Exe;On=$false},@{Label='int16-on';Exe=$Int16Exe;On=$true})) {
        Run-Perft $build.Exe $build.On $build.Label 'position startpos' 5 4865609
        Run-Perft $build.Exe $build.On $build.Label $kiwi 5 193690690
    }
    $version = Run-Child $ObjdumpExe @('--version') @() 'objdump-version'
    if ($version.Out.Text -notmatch 'GNU objdump') { Stop-Qualification 'BAD_OBJDUMP' 'GNU objdump required' }
    Run-Disassembly $BufferExe 'buffer'
    Run-Disassembly $Int16Exe 'int16'
    $parityRun = Run-Child $ParityExe @('10000','20261025') @() 'actual-api-parity-10000'
    try { $parity = $parityRun.Out.Text | ConvertFrom-Json } catch { Stop-Qualification 'BAD_PARITY' 'Actual API driver must emit one JSON object' }
    $zeroFields = @('fresh_lane_mismatches','incremental_lane_mismatches','output_oracle_mismatches','state_mismatches','parent_mismatches','in_place_mismatches')
    Require-Properties $parity (@('result','seed','unique_four_field_positions','state_checks','transitions','mean_abs_cp','max_abs_cp','p99_abs_cp','different','raw_net_strict_sign_flips','full_static_strict_sign_flips','raw_net_zero_vs_nonzero','full_static_zero_vs_nonzero','castles','en_passant','quiet_promotions','capture_promotions','null_moves','coverage_pass','fen_stream_fnv1a64','first_failure') + $zeroFields) 'parity JSON'
    foreach ($field in $zeroFields) { if ([long]$parity.$field -ne 0) { Stop-Qualification 'PARITY_FAIL' "Nonzero $field" } }
    $mean = [double]$parity.mean_abs_cp
    if ($parity.result -ne 'PASS' -or $parity.seed -ne 20261025 -or $parity.unique_four_field_positions -ne 10000 -or $parity.coverage_pass -ne $true -or -not [double]::IsFinite($mean) -or $mean -lt 0 -or $mean -gt 2 -or $parity.max_abs_cp -gt 30 -or $parity.max_abs_cp -lt 0 -or $parity.state_checks -lt 10000 -or $parity.transitions -le 0 -or $parity.castles -lt 4 -or $parity.en_passant -lt 2 -or $parity.quiet_promotions -lt 8 -or $parity.capture_promotions -lt 8 -or $parity.null_moves -lt 2 -or $parity.first_failure -ne '' -or $parity.fen_stream_fnv1a64 -notmatch '^[0-9a-fA-F]{1,16}$') { Stop-Qualification 'PARITY_FAIL' 'Wrong corpus/count/coverage/state/error bounds' }
    Write-Result "PARITY PASS actual_core_api=true unique_four_field_FENs=10000 seed=20261025 mean_abs_cp=$(Number $mean) max_abs_cp=$($parity.max_abs_cp) p99_abs_cp=$($parity.p99_abs_cp) corpus_fnv1a64=$($parity.fen_stream_fnv1a64) numerical_tolerance_only=true bit_exact=false"
    # Primary: median of all adjacent B/A ratios. Supplementary: per-block
    # geometric means. Keep every sample; no rejection or early gain stop.
    $ratios = [Collections.Generic.List[double]]::new()
    $adjacentRatios = [Collections.Generic.List[double]]::new()
    $aSamples = [Collections.Generic.List[double]]::new()
    $bSamples = [Collections.Generic.List[double]]::new()
    for ($pair=1;$pair -le $Pairs;$pair++) {
        $a1 = Run-Bench $BufferExe $false 20 "ABAB-$pair-A1" $script:Off[20]
        $b1 = Run-Bench $Int16Exe $true 20 "ABAB-$pair-B1" $script:On[20]
        $a2 = Run-Bench $BufferExe $false 20 "ABAB-$pair-A2" $script:Off[20]
        $b2 = Run-Bench $Int16Exe $true 20 "ABAB-$pair-B2" $script:On[20]
        $r1 = $b1.Nps/$a1.Nps; $r2 = $b2.Nps/$a2.Nps
        $ratio = [Math]::Sqrt($r1*$r2)
        if (-not [double]::IsFinite($ratio) -or $ratio -le 0) { Stop-Qualification 'BAD_TIMING' 'Nonfinite/nonpositive ratio' }
        $ratios.Add($ratio); $adjacentRatios.Add($r1); $adjacentRatios.Add($r2)
        $aSamples.Add($a1.Nps); $aSamples.Add($a2.Nps); $bSamples.Add($b1.Nps); $bSamples.Add($b2.Nps)
        Write-Result "ABAB_BLOCK block=$pair/$Pairs depth=20 A1_nps=$(Number $a1.Nps) B1_nps=$(Number $b1.Nps) A2_nps=$(Number $a2.Nps) B2_nps=$(Number $b2.Nps) ratio_B1_A1=$(Number $r1) ratio_B2_A2=$(Number $r2) geometric_mean_ratio=$(Number $ratio) A_nodes=$($script:Off[20]) B_nodes=$($script:On[20])"
    }
    $median = Median $adjacentRatios.ToArray()
    $blockMedian = Median $ratios.ToArray()
    $script:SpeedVerdict = if ($median -ge 1.03) { 'PASS_3PCT_NATIVE_NPS_SCREEN' } else { 'FAIL_3PCT_NATIVE_NPS_SCREEN' }
    Write-Result "NPS_RESULT NATIVE_MEASURED blocks=$Pairs adjacent_AB_pairs=$($Pairs*2) samples_per_side=$($Pairs*2) order=ABAB depth=20 PRIMARY_median_adjacent_B_over_A_ratio=$(Number $median) primary_change_pct=$(Number (100*($median-1))) threshold_ratio=1.03 supplemental_median_block_geometric_ratio=$(Number $blockMedian) A_median_nps=$(Number (Median $aSamples.ToArray())) B_median_nps=$(Number (Median $bSamples.ToArray())) adjacent_ratios=$($adjacentRatios.ToArray().ForEach({Number $_}) -join ',') block_geometric_ratios=$($ratios.ToArray().ForEach({Number $_}) -join ',') provisional_until_final_clean_status=true"
    Write-Result 'INTERPRETATION descriptive_native_search_NPS_only no_AA_noise_gate no_confidence_interval no_Elo_or_strength_acceptance quantized_ON_and_float_OFF_have_different_search_nodes'
    foreach ($path in $script:Identity.Keys) { if ((Hash-File $path) -ne $script:Identity[$path]) { Stop-Qualification 'IDENTITY_CHANGED' "Final identity changed: $path" } }
    if ($script:Clock.Elapsed.TotalSeconds -ge $script:TotalSeconds) { Stop-Qualification 'INCOMPLETE_TIME_BUDGET' '45-minute target exceeded' }
    $script:Failure = 'QUALIFICATION_CHECKS_PASSED'
} catch {
    if ($script:Failure -eq 'UNVERIFIED') { $script:Failure = 'ERROR_UNVERIFIED' }
    Write-Result "STOP status=$script:Failure error=$($_.Exception.Message)"
} finally {
    try {
      if ($null -ne $script:Controls) {
        # No further benchmark is admitted. Graceful requests only, globally
        # bounded by the original 45-minute clock, even for a hung helper.
        foreach ($child in $script:Controls.Children) {
            try { $script:Controls.RequestStop($child) } catch { $script:Failure = 'UNVERIFIED_CLEANUP_ERROR'; Write-Result "CLEANUP_REQUEST_ERROR pid=$($child.Pid) error=$($_.Exception.Message)" }
        }
        $cleanupDeadline = [Math]::Min($script:TotalSeconds,$script:Clock.Elapsed.TotalSeconds+120.0)
        do {
            $script:ActivePids = @($script:Controls.LivingPids())
            if ($script:ActivePids.Count -eq 0 -or $script:Clock.Elapsed.TotalSeconds -ge $cleanupDeadline) { break }
            [Threading.Thread]::Sleep(100)
        } while ($true)
        foreach ($child in $script:Controls.Children) {
            if ($child.Exited) {
                try { [void]$script:Controls.Drain($child,100) } catch { Write-Result "CLEANUP_DRAIN_ERROR pid=$($child.Pid) error=$($_.Exception.Message)" }
            }
            if (-not $child.Resumed) { Write-Result "CONTROL_FAILURE_SUSPENDED_CHILD pid=$($child.Pid) error=$($child.ControlError) no_termination_attempted=true" }
            if ($child.TimedOut -or -not $child.Exited -or -not $child.DrainComplete -or $null -ne $child.ControlError) {
                Write-Result "POST_CLEANUP_STDIN pid=$($child.Pid) sent=$($child.CommandsSent -join ' | ')"
                Write-Result "POST_CLEANUP_STDOUT_TAIL BEGIN pid=$($child.Pid) total_chars=$($child.Out.Characters) tail_limit=8192"
                Write-Result $child.Out.Tail
                Write-Result "POST_CLEANUP_STDOUT_TAIL END pid=$($child.Pid)"
                Write-Result "POST_CLEANUP_STDERR_TAIL BEGIN pid=$($child.Pid) total_chars=$($child.Err.Characters) tail_limit=8192"
                Write-Result $child.Err.Tail
                Write-Result "POST_CLEANUP_STDERR_TAIL END pid=$($child.Pid)"
            }
        }
        Write-Result "RESOURCE_RESULT peak_job_private_committed_bytes=$($script:Controls.PeakCommittedBytes) limit_bytes=3221225472 remaining_child_pids=$($script:ActivePids -join ',')"
        if ($script:ActivePids.Count -gt 0) { $script:Failure = 'UNVERIFIED_UNCOOPERATIVE_CHILD_REMAINS' }
      }
    } catch {
        $script:Failure = 'UNVERIFIED_CLEANUP_ERROR'
        try { Write-Result "CLEANUP ERROR error=$($_.Exception.Message) remaining_child_pids=UNKNOWN no_termination_attempted=true" } catch { Write-Host 'CLEANUP ERROR report write failed' }
    } finally {
        if ($null -ne $script:Controls) {
            try { $script:Controls.Dispose() } catch {
                $script:Failure = 'UNVERIFIED_CLEANUP_ERROR'
                Write-Host "CLEANUP DISPOSE ERROR $($_.Exception.Message)"
            }
        }
        try {
            [Environment]::SetEnvironmentVariable('TEMP',$script:SavedTemp,'Process')
            [Environment]::SetEnvironmentVariable('TMP',$script:SavedTmp,'Process')
            [Environment]::SetEnvironmentVariable('TMPDIR',$script:SavedTmpdir,'Process')
            [Environment]::SetEnvironmentVariable('PATH',$script:SavedPath,'Process')
            [Environment]::SetEnvironmentVariable('PSModuleAnalysisCachePath',$script:SavedModuleCache,'Process')
            [Environment]::SetEnvironmentVariable('DOTNET_BUNDLE_EXTRACT_BASE_DIR',$script:SavedBundleCache,'Process')
        } catch { $script:Failure = 'UNVERIFIED_ENVIRONMENT_RESTORE_ERROR'; Write-Host $_.Exception.Message }
        if ($script:Failure -eq 'QUALIFICATION_CHECKS_PASSED' -and $script:Clock.Elapsed.TotalSeconds -ge $script:TotalSeconds) { $script:Failure = 'INCOMPLETE_TIME_BUDGET' }
        if ($script:Failure -ne 'QUALIFICATION_CHECKS_PASSED') { $script:SpeedVerdict = 'UNVERIFIED' }
        try { Write-Result "FINAL STATUS=$script:Failure NPS_SCREEN=$script:SpeedVerdict primary=median_adjacent_B_over_A threshold_ratio=1.03 elapsed_seconds=$(Number $script:Clock.Elapsed.TotalSeconds) native_measurements_valid=$($script:Failure -eq 'QUALIFICATION_CHECKS_PASSED') matches=0 Elo=UNPROVEN" } catch {
            $script:Failure = 'UNVERIFIED_REPORT_WRITE_ERROR'
            Write-Host "FINAL STATUS=$script:Failure"
        }
        if ($null -ne $script:Output) { try { $script:Output.Dispose() } catch { $script:Failure = 'UNVERIFIED_REPORT_WRITE_ERROR'; Write-Host 'Report disposal failed' } }
    }
}
if ($script:Failure -eq 'QUALIFICATION_CHECKS_PASSED') { exit 0 }
exit 1
