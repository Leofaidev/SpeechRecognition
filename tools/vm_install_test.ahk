#NoEnv
#SingleInstance Force
SetTitleMatchMode, 2
SetWorkingDir, %A_Desktop%

; ---------------------------------------------------------------------------
; WSP Installer Automation - AutoHotkey backup method
; Clicks through the Inno Setup wizard using keyboard + ControlClick.
; Run from the VM Desktop after wsp_setup*.exe is present.
; Log written to Desktop\ahk_install_log.txt
; ---------------------------------------------------------------------------

LogFile := A_Desktop . "\ahk_install_log.txt"
FileDelete, %LogFile%
AHKLog("=== AHK Installer Automation Started ===")
AHKLog("User: " . A_UserName . "  Computer: " . A_ComputerName)

; ---------------------------------------------------------------------------
; Find and launch installer
; ---------------------------------------------------------------------------
installer := ""
Loop, Files, %A_Desktop%\wsp_setup*.exe, F
{
    installer := A_LoopFilePath
    break
}
if (installer = "") {
    AHKLog("ERROR: No wsp_setup*.exe found on Desktop")
    MsgBox, ERROR: No wsp_setup*.exe found on Desktop
    ExitApp
}
AHKLog("Launching: " . installer)
Run, %installer%

AHKLog("Waiting for Setup window...")
WinWait, Setup, , 60
if (ErrorLevel) {
    AHKLog("ERROR: Setup window did not appear after 60s")
    ExitApp
}
WinActivate, Setup
Sleep, 2500
AHKLog("Setup window ready")

; ---------------------------------------------------------------------------
; Page 1: Welcome
; ---------------------------------------------------------------------------
AHKLog("Page 1: Welcome")
WinActivate, Setup
Sleep, 500
; "Next >" is the default button - Enter activates it
ControlFocus, , Setup  ; focus the window
Send, {Enter}
AHKLog("Sent Enter (Next)")
Sleep, 1500

; ---------------------------------------------------------------------------
; Page 2: HuggingFace Licence
; ---------------------------------------------------------------------------
AHKLog("Page 2: HuggingFace Licence - selecting Accept")
WinActivate, Setup
Sleep, 1000
; First radio = Accept; click it by partial text match (TitleMatchMode=2)
ControlClick, I accept the licence terms, Setup
Sleep, 300
if (ErrorLevel) {
    ; Fallback: Tab to first radio and Space to select
    AHKLog("ControlClick failed - using Tab+Space")
    Send, {Tab}{Tab}{Tab}{Space}
    Sleep, 300
}
AHKLog("Clicking Next on HF page")
Send, {Enter}
Sleep, 1500

; ---------------------------------------------------------------------------
; Page 3: Install Directory (default path - just click Next)
; ---------------------------------------------------------------------------
AHKLog("Page 3: Install Directory")
WinActivate, Setup
Sleep, 500
Send, {Enter}
AHKLog("Sent Enter (Next)")
Sleep, 1500

; ---------------------------------------------------------------------------
; Page 4: Whisper Model - select Tiny (first radio), then Next
; ---------------------------------------------------------------------------
AHKLog("Page 4: Whisper Model - selecting Tiny")
WinActivate, Setup
Sleep, 1000
ControlClick, Tiny, Setup
Sleep, 300
if (ErrorLevel) {
    AHKLog("ControlClick Tiny failed - using Tab+Space")
    Send, {Tab}{Tab}{Tab}{Space}
    Sleep, 300
}
AHKLog("Clicking Next on model page")
Send, {Enter}
Sleep, 1500

; ---------------------------------------------------------------------------
; Page 5: Additional Tasks (desktop shortcut)
; ---------------------------------------------------------------------------
AHKLog("Page 5: Additional Tasks")
WinActivate, Setup
Sleep, 500
Send, {Enter}
AHKLog("Sent Enter (Next)")
Sleep, 1500

; ---------------------------------------------------------------------------
; Page 6: Ready to Install - click Install button
; ---------------------------------------------------------------------------
AHKLog("Page 6: Ready to Install")
WinActivate, Setup
Sleep, 500
; Install is NOT the default button here - need to click it explicitly
ControlClick, Install, Setup
Sleep, 300
if (ErrorLevel) {
    AHKLog("ControlClick Install failed - trying Alt+I")
    Send, !i
}
AHKLog("Install clicked - waiting for downloads...")
Sleep, 2000

; ---------------------------------------------------------------------------
; Dialog loop: handle VLC + model download prompts (up to 30 min)
; ---------------------------------------------------------------------------
AHKLog("Entering dialog loop (30 min timeout)...")
startTime := A_TickCount

Loop {
    elapsed := A_TickCount - startTime
    if (elapsed > 1800000) {
        AHKLog("TIMEOUT: 30 minutes elapsed without reaching Finish")
        break
    }

    ; --- MessageBox dialogs (#32770) ---
    IfWinExist, ahk_class #32770
    {
        WinActivate, ahk_class #32770
        ControlGetText, dlgText, Static1, ahk_class #32770
        AHKLog("Dialog: " . dlgText)

        ; Click Yes if present; otherwise OK
        ControlClick, &Yes, ahk_class #32770
        if (ErrorLevel) {
            ControlClick, Button1, ahk_class #32770
            AHKLog("Clicked Button1 (OK/Yes)")
        } else {
            AHKLog("Clicked Yes")
        }
        Sleep, 800
        continue
    }

    ; --- Finish button on the Setup window ---
    IfWinExist, Setup
    {
        ControlGetText, b1Text, Button1, Setup
        if (InStr(b1Text, "Finish")) {
            AHKLog("Finish button found - installation complete!")
            ControlClick, Button1, Setup
            Sleep, 1000
            break
        }
    }

    Sleep, 1000
}

; ---------------------------------------------------------------------------
; Verify installation
; ---------------------------------------------------------------------------
AHKLog("=== Verifying installation ===")

wspExe := A_LocalAppData . "\SpeechRecognitionProgram\wsp.exe"
if FileExist(wspExe)
    AHKLog("PASS: wsp.exe found at " . wspExe)
else
    AHKLog("FAIL: wsp.exe NOT found at " . wspExe)

cfgFile := A_LocalAppData . "\SpeechRecognitionProgram\config.json"
if FileExist(cfgFile)
    AHKLog("PASS: config.json found")
else
    AHKLog("FAIL: config.json NOT found")

lnkFile := A_Desktop . "\Speech Recognition Program.lnk"
if FileExist(lnkFile)
    AHKLog("PASS: Desktop shortcut found")
else
    AHKLog("FAIL: Desktop shortcut missing")

AHKLog("=== Done ===")
ExitApp

; ---------------------------------------------------------------------------
; Helper
; ---------------------------------------------------------------------------
AHKLog(msg) {
    global LogFile
    FormatTime, ts,, HH:mm:ss
    line := "[" . ts . "] " . msg
    FileAppend, %line%`n, %LogFile%
}
