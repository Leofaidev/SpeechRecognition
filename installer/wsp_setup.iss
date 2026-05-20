; Speech Recognition Program — Inno Setup 6 installer script
; Spec refs: Section 16 (installer requirements)
;
; Custom wizard pages (in order):
;   1. wpWelcome  (built-in)
;   2. HuggingFace licence acceptance
;   3. wpSelectDir  (installation path + disk-space check)
;   4. Whisper model selection
;   5. wpSelectTasks  (desktop shortcut)
;   6. wpReady  (summary; Next → VLC check + model download)
;   7. wpInstalling  (file copy)
;   8. wpFinished  (built-in)
;
; Required: Inno Setup 6.2 or later.

#define AppName      "Speech Recognition Program"
#define AppVersion   "1.0.0"
#define AppPublisher "Leofaidev"
#define AppExeName   "wsp.exe"
#define VLCVersion   "3.0.21"
#define VLCInstaller "vlc-3.0.21-win64.exe"
#define VLCDownloadURL "https://download.videolan.org/pub/videolan/vlc/3.0.21/win64/vlc-3.0.21-win64.exe"

; ---------------------------------------------------------------------------
; [Setup]
; ---------------------------------------------------------------------------
[Setup]
AppId={{5F2A3C1D-8B4E-4F90-A6D2-7C1E3B9F0A52}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\SpeechRecognitionProgram
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=wsp_setup
SetupIconFile=
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
MinVersion=10.0
ArchitecturesInstallIn64BitMode=x64os
; Require user-level install (no UAC elevation) — data stored in %LOCALAPPDATA%
PrivilegesRequired=lowest
UsedUserAreasWarning=no
DisableDirPage=no
DisableProgramGroupPage=no

; ---------------------------------------------------------------------------
; [Languages]
; ---------------------------------------------------------------------------
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

; ---------------------------------------------------------------------------
; [Tasks]
; ---------------------------------------------------------------------------
[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

; ---------------------------------------------------------------------------
; [Files]
; Source path is relative to the location of this .iss file.
; Run "pyinstaller wsp.spec" from the repo root before building the installer.
; ---------------------------------------------------------------------------
[Files]
Source: "..\dist\wsp\*"; DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

; ---------------------------------------------------------------------------
; [Icons]
; ---------------------------------------------------------------------------
[Icons]
Name: "{group}\{#AppName}";                   Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}";           Filename: "{app}\{#AppExeName}"; \
    Tasks: desktopicon

; ---------------------------------------------------------------------------
; [Run]
; ---------------------------------------------------------------------------
[Run]
Filename: "{app}\{#AppExeName}"; \
    Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; \
    Flags: nowait postinstall skipifsilent

; ---------------------------------------------------------------------------
; [Code]  — Pascal scripting
; ---------------------------------------------------------------------------
[Code]

const
  MIN_DISK_BYTES = 10737418240;  { 10 GB }

  { Whisper model file list (same for all sizes) }
  MODEL_FILES = 'model.bin|config.json|vocabulary.json|tokenizer.json|preprocessor_config.json';

  HF_LICENCE_TEXT =
    'Speaker diarization uses the pyannote/speaker-diarization-3.1 model, which is' + #13#10 +
    'governed by a HuggingFace model licence.' + #13#10 + #13#10 +
    'Licence: https://huggingface.co/pyannote/speaker-diarization-3.1' + #13#10 + #13#10 +
    'Key terms:' + #13#10 +
    '  - You may use the model for personal and commercial purposes.' + #13#10 +
    '  - You must not redistribute the model weights.' + #13#10 +
    '  - You must not use the model to identify real individuals without consent.' + #13#10 + #13#10 +
    'If you ACCEPT, speaker identification features will be available.' + #13#10 +
    'If you DECLINE, speakers will be labelled "Unknown" but all other' + #13#10 +
    'features (transcription, translation, output) will work normally.';

var
  { Custom pages }
  HuggingFacePage:  TWizardPage;
  ModelSelectPage:  TWizardPage;
  DownloadPage:     TDownloadWizardPage;

  { HuggingFace page controls }
  HFLicenceMemo:    TMemo;
  HFAcceptRB:       TRadioButton;
  HFDeclineRB:      TRadioButton;

  { Model selection page controls }
  ModelTinyRB:      TRadioButton;
  ModelBaseRB:      TRadioButton;
  ModelSmallRB:     TRadioButton;
  ModelMediumRB:    TRadioButton;
  ModelLargeRB:     TRadioButton;

  { Installer state }
  LicenceAccepted:  Boolean;
  SelectedModel:    String;   { "tiny"|"base"|"small"|"medium"|"large-v3" }
  VLCWasInstalled:  Boolean;  { True if VLC was already present on entry }

{ =========================================================================
  Helper functions
  ========================================================================= }

function GetModelDisplayName(const Size: String): String;
begin
  if Size = 'tiny'    then Result := 'Tiny    (~75 MB  — fastest, lowest accuracy)'
  else if Size = 'base'    then Result := 'Base    (~145 MB — fast, moderate accuracy)'
  else if Size = 'small'   then Result := 'Small   (~465 MB — balanced)'
  else if Size = 'medium'  then Result := 'Medium  (~1.5 GB — recommended)'
  else                           Result := 'Large v3 (~3.1 GB — slowest, highest accuracy)';
end;

function GetModelURL(const Size, FileName: String): String;
begin
  Result := 'https://huggingface.co/Systran/faster-whisper-' + Size +
            '/resolve/main/' + FileName;
end;

function IsVLCInstalled(): Boolean;
var
  Path: String;
begin
  Result :=
    RegQueryStringValue(HKLM, 'SOFTWARE\VideoLAN\VLC', '', Path) or
    RegQueryStringValue(HKLM, 'SOFTWARE\WOW6432Node\VideoLAN\VLC', '', Path) or
    RegQueryStringValue(HKCU, 'SOFTWARE\VideoLAN\VLC', '', Path);
end;

{ Write a minimal config.json so the app reads the correct model path and
  licence flag on first launch. }
procedure WriteInitialConfig(const AppDir, ModelSize: String;
    AcceptedLicence: Boolean);
var
  Lines:      TStringList;
  ModelPath:  String;
  LicStr:     String;
begin
  ModelPath := AppDir + '\models\faster-whisper-' + ModelSize;
  ModelPath := StringReplace(ModelPath, '\', '\\', [rfReplaceAll]);

  if AcceptedLicence then LicStr := 'true' else LicStr := 'false';

  Lines := TStringList.Create;
  try
    Lines.Add('{');
    Lines.Add('  "whisper_model": "' + ModelSize + '",');
    Lines.Add('  "whisper_model_path": "' + ModelPath + '",');
    Lines.Add('  "licence_accepted": ' + LicStr);
    Lines.Add('}');
    Lines.SaveToFile(AppDir + '\config.json');
  finally
    Lines.Free;
  end;
end;

{ =========================================================================
  Disk space check — called from NextButtonClick on wpSelectDir
  ========================================================================= }

function CheckInstallDirSpace(): Boolean;
var
  FreeAvail, TotalBytes, TotalFree: Int64;
  FreeMB: Double;
  Msg: String;
begin
  Result := True;
  if not GetDiskFreeSpaceEx(WizardDirValue(), FreeAvail, TotalBytes, TotalFree) then
    Exit;  { can't determine — let Inno Setup handle it }

  if FreeAvail < MIN_DISK_BYTES then
  begin
    FreeMB  := FreeAvail  / 1073741824.0;
    Msg := Format(
      'Insufficient disk space on the selected drive.%n%n' +
      'Required:   10.0 GB%n' +
      'Available:  %.1f GB%n%n' +
      'Please choose a different installation path or free up disk space.',
      [FreeMB]);
    MsgBox(Msg, mbError, MB_OK);
    Result := False;
  end;
end;

{ =========================================================================
  VLC installation
  ========================================================================= }

{ Download and silently install VLC if it is not already present. }
function InstallVLC(): Boolean;
var
  TmpInstaller: String;
  ErrorCode:    Integer;
begin
  Result := True;
  TmpInstaller := ExpandConstant('{tmp}\{#VLCInstaller}');

  { Download the VLC installer }
  DownloadPage.Clear;
  DownloadPage.Add('{#VLCDownloadURL}', '{#VLCInstaller}', '');
  DownloadPage.Show;
  try
    try
      DownloadPage.Download;
    except
      DownloadPage.Hide;
      SuppressibleMsgBox(
        'Failed to download VLC media player.' + #13#10 +
        'Please install VLC manually from https://www.videolan.org/ and re-run setup.',
        mbError, MB_OK, IDOK);
      Result := False;
      Exit;
    end;
  finally
    DownloadPage.Hide;
  end;

  { Run VLC installer silently }
  if not ShellExec('', TmpInstaller, '/L=1033 /S', '', SW_HIDE,
      ewWaitUntilTerminated, ErrorCode) then
  begin
    MsgBox(
      'VLC installation failed (error ' + IntToStr(ErrorCode) + ').' + #13#10 +
      'Please install VLC manually and restart the application.',
      mbError, MB_OK);
    Result := False;
  end;

  DeleteFile(TmpInstaller);
end;

{ =========================================================================
  Whisper model download (T-115)
  Retries per file; deletes partial downloads on failure.
  ========================================================================= }

{ Download a single model file with retry.
  Returns True on success, False if user aborts or cancels all retries. }
function DownloadModelFile(const Size, FileName: String): Boolean;
var
  URL:     String;
  TmpFile: String;
  DestDir: String;
  Retry:   Boolean;
begin
  Result  := False;
  URL     := GetModelURL(Size, FileName);
  TmpFile := ExpandConstant('{tmp}\') + FileName;
  DestDir := ExpandConstant('{app}\models\faster-whisper-') + Size;

  Retry := True;
  while Retry do
  begin
    DownloadPage.Clear;
    DownloadPage.Add(URL, FileName, '');
    DownloadPage.Show;
    try
      try
        DownloadPage.Download;
        { Move the downloaded file into the model directory }
        ForceDirectories(DestDir);
        if FileExists(DestDir + '\' + FileName) then
          DeleteFile(DestDir + '\' + FileName);
        if not RenameFile(TmpFile, DestDir + '\' + FileName) then
          FileCopy(TmpFile, DestDir + '\' + FileName, False);
        DeleteFile(TmpFile);
        Result := True;
        Retry  := False;
      except
        { Delete any partial download }
        if FileExists(TmpFile) then
          DeleteFile(TmpFile);

        if DownloadPage.AbortedByUser then
          Retry := False  { user deliberately cancelled }
        else
        begin
          if MsgBox(
              'Download of "' + FileName + '" failed.' + #13#10 +
              'Would you like to retry?',
              mbError, MB_YESNO) = IDNO then
            Retry := False;
        end;
      end;
    finally
      DownloadPage.Hide;
    end;
  end;
end;

{ Download all model files for the selected Whisper model. }
function DownloadWhisperModel(const Size: String): Boolean;
var
  Files: TStringList;
  i:     Integer;
begin
  Result := True;
  Files  := TStringList.Create;
  try
    Files.Delimiter     := '|';
    Files.DelimitedText := MODEL_FILES;

    for i := 0 to Files.Count - 1 do
    begin
      if not DownloadModelFile(Size, Trim(Files[i])) then
      begin
        Result := False;
        Break;
      end;
    end;
  finally
    Files.Free;
  end;
end;

{ =========================================================================
  Wizard: page creation
  ========================================================================= }

procedure CreateHuggingFacePage();
var
  LabelTop: TLabel;
begin
  HuggingFacePage := CreateCustomPage(
    wpWelcome,
    'HuggingFace Licence Agreement',
    'Speaker identification requires a third-party model licence.');

  LabelTop        := TLabel.Create(HuggingFacePage);
  LabelTop.Parent := HuggingFacePage.Surface;
  LabelTop.Left   := 0;
  LabelTop.Top    := 0;
  LabelTop.Width  := HuggingFacePage.SurfaceWidth;
  LabelTop.Caption := 'Please read the licence below, then choose whether to accept or decline.';

  HFLicenceMemo          := TMemo.Create(HuggingFacePage);
  HFLicenceMemo.Parent   := HuggingFacePage.Surface;
  HFLicenceMemo.Left     := 0;
  HFLicenceMemo.Top      := 20;
  HFLicenceMemo.Width    := HuggingFacePage.SurfaceWidth;
  HFLicenceMemo.Height   := HuggingFacePage.SurfaceHeight - 80;
  HFLicenceMemo.ReadOnly := True;
  HFLicenceMemo.ScrollBars := ssVertical;
  HFLicenceMemo.Text     := HF_LICENCE_TEXT;

  HFAcceptRB          := TRadioButton.Create(HuggingFacePage);
  HFAcceptRB.Parent   := HuggingFacePage.Surface;
  HFAcceptRB.Left     := 0;
  HFAcceptRB.Top      := HFLicenceMemo.Top + HFLicenceMemo.Height + 8;
  HFAcceptRB.Width    := HuggingFacePage.SurfaceWidth;
  HFAcceptRB.Caption  := 'I accept the licence terms (speaker identification will be available)';
  HFAcceptRB.Checked  := False;

  HFDeclineRB         := TRadioButton.Create(HuggingFacePage);
  HFDeclineRB.Parent  := HuggingFacePage.Surface;
  HFDeclineRB.Left    := 0;
  HFDeclineRB.Top     := HFAcceptRB.Top + 22;
  HFDeclineRB.Width   := HuggingFacePage.SurfaceWidth;
  HFDeclineRB.Caption := 'I decline (speakers will be labelled "Unknown")';
  HFDeclineRB.Checked := True;
end;

procedure CreateModelSelectPage();
var
  InfoLabel: TLabel;
  TopY:      Integer;

  function AddModelRB(const Caption: String; TopPos: Integer): TRadioButton;
  var R: TRadioButton;
  begin
    R          := TRadioButton.Create(ModelSelectPage);
    R.Parent   := ModelSelectPage.Surface;
    R.Left     := 0;
    R.Top      := TopPos;
    R.Width    := ModelSelectPage.SurfaceWidth;
    R.Caption  := Caption;
    R.Checked  := False;
    Result     := R;
  end;

begin
  ModelSelectPage := CreateCustomPage(
    wpSelectDir,
    'Whisper Speech Recognition Model',
    'Select the model size. Larger models are more accurate but slower and need more disk space.');

  InfoLabel         := TLabel.Create(ModelSelectPage);
  InfoLabel.Parent  := ModelSelectPage.Surface;
  InfoLabel.Left    := 0;
  InfoLabel.Top     := 0;
  InfoLabel.Width   := ModelSelectPage.SurfaceWidth;
  InfoLabel.Caption := 'Choose the Whisper model to download during installation:';

  TopY := 20;
  ModelTinyRB   := AddModelRB('  ' + GetModelDisplayName('tiny'),   TopY);       TopY := TopY + 26;
  ModelBaseRB   := AddModelRB('  ' + GetModelDisplayName('base'),   TopY);       TopY := TopY + 26;
  ModelSmallRB  := AddModelRB('  ' + GetModelDisplayName('small'),  TopY);       TopY := TopY + 26;
  ModelMediumRB := AddModelRB('  ' + GetModelDisplayName('medium'), TopY);       TopY := TopY + 26;
  ModelLargeRB  := AddModelRB('  ' + GetModelDisplayName('large-v3'), TopY);

  ModelMediumRB.Checked := True;   { default: medium }
end;

{ =========================================================================
  Wizard: lifecycle callbacks
  ========================================================================= }

procedure InitializeWizard();
begin
  { Download progress page — shared for VLC and model files }
  DownloadPage := CreateDownloadPage(
    SetupMessage(msgWizardInstalling),
    SetupMessage(msgDiskSpaceDetails),
    nil);

  CreateHuggingFacePage();
  CreateModelSelectPage();

  LicenceAccepted := False;
  SelectedModel   := 'medium';
  VLCWasInstalled := IsVLCInstalled();
end;

{ Resolve which model radio button is checked. }
procedure UpdateSelectedModel();
begin
  if      ModelTinyRB.Checked   then SelectedModel := 'tiny'
  else if ModelBaseRB.Checked   then SelectedModel := 'base'
  else if ModelSmallRB.Checked  then SelectedModel := 'small'
  else if ModelLargeRB.Checked  then SelectedModel := 'large-v3'
  else                               SelectedModel := 'medium';
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;

  { --- HuggingFace licence page --- }
  if CurPageID = HuggingFacePage.ID then
  begin
    LicenceAccepted := HFAcceptRB.Checked;
    { No blocking condition — both choices are valid. }
  end

  { --- Directory selection: enforce disk space --- }
  else if CurPageID = wpSelectDir then
    Result := CheckInstallDirSpace()

  { --- Model selection: capture choice --- }
  else if CurPageID = ModelSelectPage.ID then
    UpdateSelectedModel()

  { --- Ready page: VLC check + model download before file copy --- }
  else if CurPageID = wpReady then
  begin
    { Step 1: VLC }
    if not VLCWasInstalled and not IsVLCInstalled() then
    begin
      if MsgBox(
          'VLC media player is required for audio playback and was not found.' + #13#10 +
          'Download and install VLC now?',
          mbConfirmation, MB_YESNO) = IDYES then
      begin
        if not InstallVLC() then
        begin
          Result := False;
          Exit;
        end;
      end else
      begin
        MsgBox(
          'VLC was not installed. Audio playback will not be available.' + #13#10 +
          'You can install VLC later from https://www.videolan.org/',
          mbInformation, MB_OK);
      end;
    end;

    { Step 2: Whisper model download }
    if not DownloadWhisperModel(SelectedModel) then
    begin
      if MsgBox(
          'Some model files could not be downloaded.' + #13#10 +
          'The application can still start, but transcription will not work until' + #13#10 +
          'the model files are present.' + #13#10 + #13#10 +
          'Continue installation anyway?',
          mbError, MB_YESNO) = IDNO then
      begin
        Result := False;
        Exit;
      end;
    end;
  end;
end;

{ Write initial config.json after all files are in place. }
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    WriteInitialConfig(ExpandConstant('{app}'), SelectedModel, LicenceAccepted);
end;

{ Show total-space requirement on the summary page. }
function UpdateReadyMemo(Space, NewLine, MemoUserInfoInfo, MemoDirInfo,
    MemoTypeInfo, MemoComponentsInfo, MemoGroupInfo, MemoTasksInfo: String): String;
var
  S: String;
begin
  S := '';

  if MemoDirInfo <> '' then
    S := S + MemoDirInfo + NewLine + NewLine;

  if MemoGroupInfo <> '' then
    S := S + MemoGroupInfo + NewLine + NewLine;

  if MemoTasksInfo <> '' then
    S := S + MemoTasksInfo + NewLine + NewLine;

  S := S + 'Whisper model to download: ' + GetModelDisplayName(SelectedModel) + NewLine;

  if LicenceAccepted then
    S := S + 'HuggingFace licence: accepted' + NewLine
  else
    S := S + 'HuggingFace licence: declined (speaker ID disabled)' + NewLine;

  if not VLCWasInstalled then
    S := S + 'VLC media player: will be downloaded and installed' + NewLine;

  S := S + NewLine + 'Minimum disk space required: 10 GB';
  Result := S;
end;

end.
