#Requires -Version 5.1
# Checks and configures the Windows 11 VM for WSP installer testing.
# Run once in the VM before taking the baseline snapshot.
# Writes results to Desktop\vm_setup_log.txt and the shared wsp_tools folder.

Set-StrictMode -Off
$ErrorActionPreference = "SilentlyContinue"

$LogFile   = "$env:USERPROFILE\Desktop\vm_setup_log.txt"
$ShareLog  = "\\vmware-host\Shared Folders\wsp_tools\vm_setup_log.txt"
$Changes   = 0
$Problems  = 0

"" | Out-File $LogFile -Encoding ASCII

function Log {
    param([string]$msg, [string]$level = "INFO")
    $entry = "[$(Get-Date -Format 'HH:mm:ss')] [$level] $msg"
    Write-Host $entry
    Add-Content $LogFile $entry -Encoding ASCII
    try { Add-Content $ShareLog $entry -Encoding ASCII } catch {}
    if ($level -eq "CHANGE") { $script:Changes++ }
    if ($level -eq "FAIL")   { $script:Problems++ }
}

Log "=== WSP VM Setup Check  ($env:COMPUTERNAME  $env:USERNAME) ==="

# ---------------------------------------------------------------------------
# 1. UAC -- EnableLUA = 0
# ---------------------------------------------------------------------------
Log "--- 1. UAC ---"
$uacKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
$uac = (Get-ItemProperty $uacKey -Name EnableLUA -ErrorAction SilentlyContinue).EnableLUA
if ($uac -eq 0) {
    Log "UAC: already disabled (EnableLUA=0)"
} else {
    Log "UAC: enabling disable (EnableLUA=0)" "CHANGE"
    Set-ItemProperty $uacKey -Name EnableLUA -Value 0 -Type DWord -Force
    Log "UAC: set EnableLUA=0 -- reboot required to take effect"
}

# ---------------------------------------------------------------------------
# 2. Windows Defender real-time protection -- disable
# ---------------------------------------------------------------------------
Log "--- 2. Windows Defender ---"
try {
    $defStatus = (Get-MpPreference -ErrorAction Stop).DisableRealtimeMonitoring
    if ($defStatus -eq $true) {
        Log "Defender real-time protection: already disabled"
    } else {
        Set-MpPreference -DisableRealtimeMonitoring $true -ErrorAction Stop
        Log "Defender real-time protection: disabled" "CHANGE"
    }
} catch {
    Log "Defender: could not check/set ($_ ) -- may need manual disable" "FAIL"
}

# ---------------------------------------------------------------------------
# 3. SmartScreen -- disable
# ---------------------------------------------------------------------------
Log "--- 3. SmartScreen ---"
$ssKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer"
$ss = (Get-ItemProperty $ssKey -Name SmartScreenEnabled -ErrorAction SilentlyContinue).SmartScreenEnabled
if ($ss -eq "Off" -or $ss -eq "") {
    Log "SmartScreen: already off"
} else {
    Set-ItemProperty $ssKey -Name SmartScreenEnabled -Value "Off" -Type String -Force
    Log "SmartScreen: set to Off" "CHANGE"
}
# Also disable via policy key
$ssPol = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\System"
if (-not (Test-Path $ssPol)) { New-Item $ssPol -Force | Out-Null }
$ssPolVal = (Get-ItemProperty $ssPol -Name EnableSmartScreen -ErrorAction SilentlyContinue).EnableSmartScreen
if ($ssPolVal -eq 0) {
    Log "SmartScreen policy: already 0"
} else {
    Set-ItemProperty $ssPol -Name EnableSmartScreen -Value 0 -Type DWord -Force
    Log "SmartScreen policy: set EnableSmartScreen=0" "CHANGE"
}

# ---------------------------------------------------------------------------
# 4. Display scaling -- check (cannot set programmatically without reboot)
# ---------------------------------------------------------------------------
Log "--- 4. Display scaling ---"
try {
    Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class DpiHelper {
    [DllImport("shcore.dll")]
    public static extern int GetDpiForMonitor(IntPtr hmonitor, int dpiType, out uint dpiX, out uint dpiY);
    [DllImport("user32.dll")]
    public static extern IntPtr MonitorFromWindow(IntPtr hwnd, uint dwFlags);
    [DllImport("user32.dll")]
    public static extern IntPtr GetDesktopWindow();
}
"@ -ErrorAction Stop
    $hmon = [DpiHelper]::MonitorFromWindow([DpiHelper]::GetDesktopWindow(), 0)
    $dpiX = 0; $dpiY = 0
    [DpiHelper]::GetDpiForMonitor($hmon, 0, [ref]$dpiX, [ref]$dpiY) | Out-Null
    $scale = [int]([math]::Round($dpiX / 96.0 * 100))
    if ($scale -eq 100) {
        Log "Display scaling: ${scale}% (OK)"
    } else {
        Log "Display scaling: ${scale}% -- must be set to 100% manually (Settings -> Display -> Scale)" "FAIL"
    }
} catch {
    Log "Display scaling: could not detect ($_)" "FAIL"
}

# ---------------------------------------------------------------------------
# 5. Autologon
# ---------------------------------------------------------------------------
Log "--- 5. Autologon ---"
$alKey = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
$al = (Get-ItemProperty $alKey -Name AutoAdminLogon -ErrorAction SilentlyContinue).AutoAdminLogon
$alUser = (Get-ItemProperty $alKey -Name DefaultUserName -ErrorAction SilentlyContinue).DefaultUserName
if ($al -eq "1" -and $alUser -eq "claude") {
    Log "Autologon: enabled for '$alUser'"
} else {
    Set-ItemProperty $alKey -Name AutoAdminLogon   -Value "1"      -Type String -Force
    Set-ItemProperty $alKey -Name DefaultUserName  -Value "claude" -Type String -Force
    Set-ItemProperty $alKey -Name DefaultPassword  -Value "1"      -Type String -Force
    Set-ItemProperty $alKey -Name DefaultDomainName -Value ""      -Type String -Force
    Log "Autologon: configured for claude/1" "CHANGE"
}

# ---------------------------------------------------------------------------
# 6. PowerShell execution policy
# ---------------------------------------------------------------------------
Log "--- 6. PowerShell execution policy ---"
$pol = (Get-ExecutionPolicy -Scope LocalMachine)
if ($pol -in @("Unrestricted","Bypass")) {
    Log "Execution policy: $pol (OK)"
} else {
    Set-ExecutionPolicy Unrestricted -Scope LocalMachine -Force
    Log "Execution policy: set to Unrestricted" "CHANGE"
}

# ---------------------------------------------------------------------------
# 7. WSP-Run-Watcher task
# ---------------------------------------------------------------------------
Log "--- 7. WSP-Run-Watcher task ---"
$task = Get-ScheduledTask -TaskName "WSP-Run-Watcher" -ErrorAction SilentlyContinue
if ($task) {
    Log "WSP-Run-Watcher: installed (state=$($task.State))"
    if ($task.State -ne "Running") {
        Start-ScheduledTask -TaskName "WSP-Run-Watcher" -ErrorAction SilentlyContinue
        Log "WSP-Run-Watcher: started" "CHANGE"
    }
} else {
    Log "WSP-Run-Watcher: NOT installed -- will install now" "CHANGE"
    $watcherInstaller = "\\vmware-host\Shared Folders\wsp_tools\install_vm_watcher.ps1"
    if (Test-Path $watcherInstaller) {
        & powershell.exe -ExecutionPolicy Bypass -File $watcherInstaller
        $task2 = Get-ScheduledTask -TaskName "WSP-Run-Watcher" -ErrorAction SilentlyContinue
        if ($task2) {
            Log "WSP-Run-Watcher: installed successfully (state=$($task2.State))"
        } else {
            Log "WSP-Run-Watcher: install FAILED" "FAIL"
        }
    } else {
        Log "WSP-Run-Watcher: installer not found at $watcherInstaller" "FAIL"
    }
}

# ---------------------------------------------------------------------------
# 8. Clean state -- no Python, no VLC, no WSP
# ---------------------------------------------------------------------------
Log "--- 8. Clean state ---"
$python = (Get-Command python -ErrorAction SilentlyContinue)
if ($python) {
    Log "Python: FOUND at $($python.Source) -- should NOT be installed on a clean test VM" "FAIL"
} else {
    Log "Python: not found (OK -- clean)"
}

$vlc = "C:\Program Files\VideoLAN\VLC\vlc.exe"
if (Test-Path $vlc) {
    Log "VLC: FOUND at $vlc -- should NOT be pre-installed (installer handles it)" "FAIL"
} else {
    Log "VLC: not found (OK -- clean)"
}

$wsp = "$env:LOCALAPPDATA\SpeechRecognitionProgram\wsp.exe"
if (Test-Path $wsp) {
    Log "WSP: FOUND at $wsp -- should NOT be pre-installed" "FAIL"
} else {
    Log "WSP: not found (OK -- clean)"
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
Log "=== Summary: $Changes change(s) applied, $Problems item(s) need manual attention ==="
if ($Problems -gt 0) {
    Log "ACTION REQUIRED: fix the items marked [FAIL] before taking the snapshot"
} else {
    Log "All checks passed -- VM is ready for snapshot"
}
