#ifndef Paquete
  #error Falta /DPaquete
#endif
#ifndef Salida
  #define Salida "..\dist"
#endif
#ifndef Version
  #define Version "0.3.1"
#endif
[Setup]
AppId=Telazocraft
AppName=Telazocraft
AppVersion={#Version}
AppPublisher=Adrián Rodríguez Rodríguez
DefaultDirName={localappdata}\Programs\Telazocraft
DefaultGroupName=Telazocraft
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#Salida}
OutputBaseFilename=Telazocraft-{#Version}-windows
Compression=lzma2/fast
SolidCompression=yes
LZMANumBlockThreads=2
WizardStyle=modern dark
SetupIconFile={#Paquete}\Telazocraft.ico
WizardImageFile={#Paquete}\Wizard.bmp
WizardSmallImageFile={#Paquete}\WizardSmall.bmp
UninstallDisplayIcon={app}\Telazocraft.ico
LicenseFile={#Paquete}\LICENSE
DisableProgramGroupPage=yes
CloseApplications=yes
RestartApplications=no
UninstallDisplayName=Telazocraft

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
Source: "{#Paquete}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.pdb,python\Lib\test\*,python\Lib\idlelib\*,python\Lib\tkinter\*,python\tcl\*,python\Lib\site-packages\PySide6\qml\*"

[Icons]
Name: "{autoprograms}\Telazocraft"; Filename: "{app}\Telazocraft.exe"; WorkingDir: "{app}"; IconFilename: "{app}\Telazocraft.ico"; AppUserModelID: "ItsRodryy.Telazocraft"
Name: "{autodesktop}\Telazocraft"; Filename: "{app}\Telazocraft.exe"; WorkingDir: "{app}"; IconFilename: "{app}\Telazocraft.ico"; AppUserModelID: "ItsRodryy.Telazocraft"

[Run]
Filename: "{sys}\ie4uinit.exe"; Parameters: "-show"; Flags: runhidden
Filename: "{app}\Telazocraft.exe"; WorkingDir: "{app}"; Description: "Abrir Telazocraft"; Flags: nowait postinstall skipifsilent
