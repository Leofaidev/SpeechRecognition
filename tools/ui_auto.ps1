# ui_auto.ps1 — self-contained GUI automation helpers
# Usage: . .\ui_auto.ps1 ; then call Clk, Ss, ScrollAt, Log
param([IntPtr]$Hwnd = [IntPtr]656756)

Add-Type -AssemblyName System.Windows.Forms, System.Drawing
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public static class UA {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern void mouse_event(uint f,int x,int y,int d,int e);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int sw);
    // SW_RESTORE=9, SW_MINIMIZE=6, SW_HIDE=0
    public struct SINPUT {
        public uint type;
        public ushort wVk, wScan;
        public uint dwFlags, time;
        public IntPtr extra;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst=8)]
        public byte[] pad;
    }
    [DllImport("user32.dll")] public static extern uint SendInput(uint n,[In] SINPUT[] i, int sz);
    public static void SendKey(ushort vk, bool up) {
        SINPUT i = new SINPUT();
        i.type = 1; i.wVk = vk;
        if (up) i.dwFlags = 2;
        int sz = System.Runtime.InteropServices.Marshal.SizeOf(typeof(SINPUT));
        SendInput(1, new SINPUT[]{i}, sz);
    }
}
"@ -ErrorAction SilentlyContinue

$script:HWND = $Hwnd
$script:WinL = 553; $script:WinT = 200

# Nav item absolute screen Y values (window top = 200)
$script:Nav = @{
    Home=297; Settings=335; VoiceProfiles=373; AIConfig=411
    SubDict=449; BatchQueue=487; OutputConfig=525; Hotkeys=562
    SessionHistory=601; BackupRestore=638; About=676
}

function Clk([int]$ax, [int]$ay, [int]$ms=200) {
    [UA]::SetForegroundWindow($script:HWND) | Out-Null
    Start-Sleep -Milliseconds 100
    [UA]::SetCursorPos($ax, $ay) | Out-Null
    Start-Sleep -Milliseconds 60
    [UA]::mouse_event(0x0002,0,0,0,0)
    [UA]::mouse_event(0x0004,0,0,0,0)
    Start-Sleep -Milliseconds $ms
}

function NavTo([string]$panel) {
    Clk 653 $script:Nav[$panel] 800
}

function ScrollAt([int]$ax, [int]$ay, [int]$delta) {
    # delta: negative = down, positive = up (120 per notch)
    [UA]::SetCursorPos($ax, $ay) | Out-Null
    [UA]::mouse_event(0x0800, 0, 0, $delta, 0)
    Start-Sleep -Milliseconds 300
}

function Ss([string]$name) {
    $b = New-Object System.Drawing.Bitmap(1143,659)
    $g = [System.Drawing.Graphics]::FromImage($b)
    $g.CopyFromScreen($script:WinL, $script:WinT, 0, 0, $b.Size)
    $p = "H:\Users\Leo1\SpeechRecognition\screens\chk_$name.png"
    $b.Save($p); $g.Dispose(); $b.Dispose()
    return $p
}

function Log([string]$id, [string]$status, [string]$note="") {
    $line = "$(Get-Date -Format 'HH:mm:ss')  $id  [$status]  $note"
    Add-Content "H:\Users\Leo1\SpeechRecognition\tools\chk_results.txt" $line
    Write-Host $line
}

Write-Host "ui_auto.ps1 loaded - HWND=$script:HWND"
