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
