#ifndef Paquete
  #error Falta /DPaquete
#endif
#ifndef Salida
  #define Salida "..\dist"
#endif
#ifndef Version
  #define Version "0.2.1"
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
Name: "{autoprograms}\Telazocraft"; Filename: "{app}\python\pythonw.exe"; Parameters: "-B -m telazocraft"; WorkingDir: "{app}"; IconFilename: "{app}\Telazocraft.ico"
Name: "{autodesktop}\Telazocraft"; Filename: "{app}\python\pythonw.exe"; Parameters: "-B -m telazocraft"; WorkingDir: "{app}"; IconFilename: "{app}\Telazocraft.ico"

[Run]
Filename: "{app}\python\pythonw.exe"; Parameters: "-B -m telazocraft"; WorkingDir: "{app}"; Description: "Abrir Telazocraft"; Flags: nowait postinstall skipifsilent
