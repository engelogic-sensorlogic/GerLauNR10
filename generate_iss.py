"""
Gera o arquivo .iss para Inno Setup automaticamente.
Execute via: python generate_iss.py
Ou: python build_installer.bat (chama este script automaticamente)
"""
import os
from pathlib import Path
from datetime import datetime

APP_NAME = "GerLauNR10"
APP_VERSION = "1.0.0"
APP_PUBLISHER = "Engelogic Automação e Controle Industrial"
APP_URL = "https://www.engelogic.com.br"
APP_EXE = "GerLauNR10.exe"
DIST_DIR = str(Path(__file__).parent / "dist" / "GerLauNR10")

ISS_CONTENT = f"""; GerLauNR10 Installer Script
; Gerado automaticamente em {datetime.now().strftime('%d/%m/%Y %H:%M')}
; Engelogic Automação e Controle Industrial

#define MyAppName "{APP_NAME}"
#define MyAppVersion "{APP_VERSION}"
#define MyAppPublisher "{APP_PUBLISHER}"
#define MyAppURL "{APP_URL}"
#define MyAppExeName "{APP_EXE}"

[Setup]
AppId={{{{B3A7F2C4-D914-4E8A-B1AC-6F2D09E3C5A7}}}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppVerName={{#MyAppName}} v{{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
AppPublisherURL={{#MyAppURL}}
AppSupportURL={{#MyAppURL}}
AppUpdatesURL={{#MyAppURL}}
DefaultDirName={{autopf}}\\{{#MyAppName}}
DefaultGroupName={{#MyAppName}}
AllowNoIcons=yes
LicenseFile=
OutputDir=Output
OutputBaseFilename=GerLauNR10_Setup_v{APP_VERSION}
SetupIconFile=Icone.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequiredOverridesAllowed=dialog
VersionInfoVersion={APP_VERSION}
VersionInfoCompany={APP_PUBLISHER}
VersionInfoDescription=GerLauNR10 - Gerador de Laudos NR-10

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar ícone na Área de Trabalho"; GroupDescription: "Ícones adicionais:"; Flags: unchecked
Name: "quicklaunchicon"; Description: "Criar ícone na Barra de Tarefas"; GroupDescription: "Ícones adicionais:"; Flags: unchecked

[Files]
Source: "{DIST_DIR}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "Icone.ico"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{group}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; IconFilename: "{{app}}\\Icone.ico"
Name: "{{group}}\\Desinstalar {{#MyAppName}}"; Filename: "{{uninstallexe}}"
Name: "{{commondesktop}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; IconFilename: "{{app}}\\Icone.ico"; Tasks: desktopicon
Name: "{{userappdata}}\\Microsoft\\Internet Explorer\\Quick Launch\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; IconFilename: "{{app}}\\Icone.ico"; Tasks: quicklaunchicon

[Run]
Filename: "{{app}}\\{{#MyAppExeName}}"; Description: "Abrir {{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{{app}}\\data"
Type: filesandordirs; Name: "{{app}}\\Clientes"

[Code]
function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstPath := ExpandConstant('Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{{#SetupSetting("AppId")}}_is1');
  sUnInstallString := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;
"""

output_path = Path(__file__).parent / "GerLauNR10_installer.iss"
output_path.write_text(ISS_CONTENT, encoding="utf-8")
print(f"[OK] Arquivo Inno Setup gerado: {output_path}")
