[Setup]
AppName=Lumina Photo Organizer
AppVersion=1.0.0
AppPublisher=Tarun Nichwani
AppPublisherURL=https://github.com/tar7nic/lumina
DefaultDirName={autopf}\Lumina
DefaultGroupName=Lumina
OutputBaseFilename=LuminaSetup
OutputDir=Output
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\Lumina.exe
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\Lumina\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Lumina Photo Organizer"; Filename: "{app}\Lumina.exe"
Name: "{commondesktop}\Lumina Photo Organizer"; Filename: "{app}\Lumina.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\Lumina.exe"; Description: "Launch Lumina"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
