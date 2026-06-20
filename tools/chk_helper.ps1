# chk_helper.ps1 — shared helpers for CHK automation
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System; using System.Runtime.InteropServices; using System.Text;
public class WH {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern void mouse_event(uint f,int x,int y,int d,int e);
    [DllImport("user32.dll")] public static extern void keybd_event(byte vk,byte sc,uint f,int ei);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc cb, IntPtr lp);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L,T,R,B; }
    public delegate bool EnumWindowsProc(IntPtr h, IntPtr lp);
}
"@

$script:WinL = 553; $script:WinT = 200
$script:HWND = [IntPtr]3279272

# Nav item absolute Y positions (window top=200)
$script:Nav = @{
    Home=297; Settings=335; VoiceProfiles=373; AIConfig=411
    SubDict=449; BatchQueue=487; OutputConfig=525; Hotkeys=562
    SessionHistory=601; BackupRestore=638; About=676
}

function Click([int]$ax, [int]$ay, [int]$ms=150) {
    [WH]::SetForegroundWindow($script:HWND) | Out-Null
    Start-Sleep -Milliseconds 100
    [WH]::SetCursorPos($ax, $ay) | Out-Null
    Start-Sleep -Milliseconds 80
    [WH]::mouse_event(0x0002,0,0,0,0)
    [WH]::mouse_event(0x0004,0,0,0,0)
    Start-Sleep -Milliseconds $ms
}

function NavTo([string]$panel) {
    $y = $script:Nav[$panel]
    Click 653 $y 700
}

function Shot([string]$name) {
    $bmp = New-Object System.Drawing.Bitmap(1143,659)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($script:WinL, $script:WinT, 0, 0, $bmp.Size)
    $path = "H:\Users\Leo1\SpeechRecognition\screens\chk_$name.png"
    $bmp.Save($path); $g.Dispose(); $bmp.Dispose()
    return $path
}

function Log([string]$id, [string]$status, [string]$note="") {
    $line = "$(Get-Date -Format 'HH:mm:ss')  $id  $status  $note"
    Add-Content "H:\Users\Leo1\SpeechRecognition\tools\chk_results.txt" $line
    Write-Host $line
}
