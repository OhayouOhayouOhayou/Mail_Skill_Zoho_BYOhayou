; Inno Setup script — builds a real "Setup.exe" (like installing Word).
; Requires the free Inno Setup compiler: https://jrsoftware.org/isdl.php
;
; Before compiling this, build the two .exe files first:
;     build_installer.bat   ->  dist\ZohoMailSetup.exe   (config wizard)
;     build_exe.bat         ->  dist\ZohoMailNotifier.exe (tray notifier)
;
; Then open this file in Inno Setup and click Compile. Output:
;     Output\ZohoMail-Setup.exe   <- send THIS single file to users.

#define AppName "Zoho Mail Skill"
#define AppVer  "1.0.0"
#define Pub     "OhayouOhayou"

[Setup]
AppName={#AppName}
AppVersion={#AppVer}
AppPublisher={#Pub}
DefaultDirName={autopf}\ZohoMail
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputBaseFilename=ZohoMail-Setup
OutputDir=Output
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; per-user install: no admin prompt
PrivilegesRequired=lowest

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "สร้างไอคอนบนเดสก์ท็อป"; GroupDescription: "Shortcuts:"
Name: "startupnotifier"; Description: "เปิดตัวแจ้งเตือนเมลอัตโนมัติเมื่อเข้าเครื่อง"; GroupDescription: "Options:"; Flags: unchecked

[Files]
Source: "dist\ZohoMailSetup.exe";    DestDir: "{app}"; Flags: ignoreversion
Source: "dist\ZohoMailNotifier.exe"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "README.md";   DestDir: "{app}"; Flags: ignoreversion
Source: "GUIDE.md";    DestDir: "{app}"; Flags: ignoreversion
Source: "INSTALL.md";  DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\ตั้งค่า Zoho Mail";  Filename: "{app}\ZohoMailSetup.exe"
Name: "{group}\แจ้งเตือนเมล";        Filename: "{app}\ZohoMailNotifier.exe"
Name: "{autodesktop}\Zoho Mail ตั้งค่า"; Filename: "{app}\ZohoMailSetup.exe"; Tasks: desktopicon
; auto-start the notifier at login (optional task)
Name: "{userstartup}\Zoho Mail Notifier"; Filename: "{app}\ZohoMailNotifier.exe"; Tasks: startupnotifier

[Run]
; launch the config wizard right after install
Filename: "{app}\ZohoMailSetup.exe"; Description: "ตั้งค่าเชื่อมต่อ Zoho ตอนนี้"; Flags: postinstall nowait skipifsilent
