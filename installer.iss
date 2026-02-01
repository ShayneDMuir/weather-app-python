[Setup]
AppName=Weather App
AppVersion=1.1.8
AppPublisher=Shayne Muir
DefaultDirName={autopf}\WeatherApp
DefaultGroupName=Weather App
OutputDir=installer
OutputBaseFilename=WeatherAppSetup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
SetupIconFile=animated\clear-day.svg
UninstallDisplayIcon={app}\WeatherApp.exe

[Files]
Source: "dist\WeatherApp.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "animated\*"; DestDir: "{app}\animated"; Flags: ignoreversion recursesubdirs
Source: "vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\Weather App"; Filename: "{app}\WeatherApp.exe"
Name: "{autodesktop}\Weather App"; Filename: "{app}\WeatherApp.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/install /quiet /norestart"; StatusMsg: "Installing Visual C++ Runtime..."; Flags: waituntilterminated skipifsilent
Filename: "{app}\WeatherApp.exe"; Description: "Launch Weather App"; Flags: nowait postinstall skipifsilent
