; Inno Setup script — builds a branded "ASEFA-Mail-Setup.exe" (installs like Word).
; Requires the free Inno Setup compiler: https://jrsoftware.org/isdl.php
;
; Build the app .exe FIRST:
;     build_app.bat        ->  dist\ASEFAMail.exe   (main app: dashboard/realtime/backup/settings)
;     build_exe.bat        ->  dist\ZohoMailNotifier.exe  (optional tray notifier)
;
; Then open this file in Inno Setup -> Compile. Output:
;     Output\ASEFA-Mail-Setup.exe   <- distribute THIS single file to staff.

#define AppName "ASEFA Mail"
#define AppVer  "1.0.0"
#define Pub     "ASEFA Public Company Limited"
#define ExeName "ASEFAMail.exe"

[Setup]
AppName={#AppName}
AppVersion={#AppVer}
AppPublisher={#Pub}
AppPublisherURL=https://www.asefa.co.th/
DefaultDirName={autopf}\ASEFA Mail
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputBaseFilename=ASEFA-Mail-Setup
OutputDir=Output
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#ExeName}

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "สร้างไอคอนบนเดสก์ท็อป"; GroupDescription: "Shortcuts:"
Name: "startupapp"; Description: "เปิด ASEFA Mail อัตโนมัติเมื่อเข้าเครื่อง"; GroupDescription: "Options:"; Flags: unchecked

[Files]
Source: "dist\ASEFAMail.exe";        DestDir: "{app}"; Flags: ignoreversion
Source: "dist\ZohoMailNotifier.exe"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "assets\icon.ico";           DestDir: "{app}\assets"; Flags: ignoreversion
Source: "INSTALL.md";                DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "DEPLOY.md";                 DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{group}\{#AppName}";            Filename: "{app}\{#ExeName}"
Name: "{group}\แจ้งเตือนเมล (Tray)";  Filename: "{app}\ZohoMailNotifier.exe"; Check: FileExists(ExpandConstant('{app}\ZohoMailNotifier.exe'))
Name: "{autodesktop}\{#AppName}";     Filename: "{app}\{#ExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#AppName}";     Filename: "{app}\{#ExeName}"; Tasks: startupapp

[Run]
Filename: "{app}\{#ExeName}"; Description: "เปิด ASEFA Mail ตอนนี้"; Flags: postinstall nowait skipifsilent
