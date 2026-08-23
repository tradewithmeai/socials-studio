; Inno Setup script for Socials-Studio-Setup.exe
;
; Built by CI (see .github/workflows/build-installers.yml), not opaque: this
; installer copies the plain repository source (Markdown skills, Python code,
; everything Claude Code reads) onto disk exactly as it appears in the repo --
; it does not compile, freeze, or obfuscate any of it. A user or an agent can
; open every file after install exactly as they could in a git clone.
;
; What this installer does:
;   1. Copies the repository source to {app} (default: %LOCALAPPDATA%\SocialsStudio),
;      *except* it never overwrites an existing profiles/ directory there --
;      see the [Files] "profiles\*" exclude below. That's what makes a
;      reinstall/upgrade preserve saved logins and OAuth tokens.
;   2. Bundles a minimal embeddable Python (see BUNDLED_PYTHON_DIR below,
;      populated by the CI build step) solely to run installer\bootstrap.py
;      once. Bootstrap creates the project's own .venv and installs
;      requirements.txt into it -- the embeddable Python is not the runtime
;      Socials Studio uses day to day, it only bootstraps that runtime.
;   3. Never logs into a platform, never launches a publish flow, never
;      collects a credential. It only checks whether Claude Code and Chrome
;      are already installed (see bootstrap.py) and reports what to do if not.
;   4. Creates a Start Menu / Desktop shortcut that opens a terminal in {app}
;      and runs `claude` -- see launch.bat.
;
; This script is built with `iscc setup.iss` by CI using the official
; jrsoftware/innosetup toolchain -- see the workflow for exact invocation.
; It has not been compiled or run on a real Windows machine as part of this
; change; that verification is still required before shipping (see PR notes).

#define MyAppName "Socials Studio"
#define MyAppVersion "0.1.0-beta.3"
#define MyAppPublisher "Socials Studio (independent, community project)"
#define MyAppURL "https://github.com/tradewithmeai/socials-studio"

[Setup]
AppId={{B4C6C6F0-9F1B-4B7E-9C1E-5B7A0B3B7B3A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
DefaultDirName={localappdata}\SocialsStudio
DefaultGroupName=Socials Studio
DisableProgramGroupPage=yes
OutputDir=..\..\dist
OutputBaseFilename=Socials-Studio-Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
; No code-signing certificate exists for this project yet -- Windows
; SmartScreen will show an "unrecognized publisher" warning on first run
; until one is added. Documented in the PR, not hidden.

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; The plain repository source, minus profiles/, .git, and anything CI
; excludes when it stages the payload (see the workflow's "Stage repo
; payload" step). profiles/ is excluded here so an existing install's saved
; sessions are never overwritten by a reinstall.
Source: "..\..\payload\*"; DestDir: "{app}"; Excludes: "profiles\*"; Flags: ignoreversion recursesubdirs createallsubdirs
; The embeddable Python CI downloads and stages at build time, used only to
; run bootstrap.py once.
Source: "..\..\payload-python\*"; DestDir: "{app}\_bootstrap-python"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "launch.bat"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
; Created if it doesn't already exist; never touched if it does (see [Files]
; Excludes above -- this entry only guarantees the directory exists for a
; brand-new install, it never runs on top of an existing one).
Name: "{app}\profiles"; Flags: uninsneveruninstall

[Icons]
Name: "{group}\Socials Studio"; Filename: "{app}\launch.bat"; WorkingDir: "{app}"
Name: "{commondesktop}\Socials Studio"; Filename: "{app}\launch.bat"; WorkingDir: "{app}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
; Runs bootstrap.py with the bundled embeddable Python immediately after
; files are copied. This creates {app}\.venv and installs requirements.txt
; into it -- no login, no publish, no platform contact.
Filename: "{app}\_bootstrap-python\python.exe"; \
    Parameters: """{app}\installer\bootstrap.py"" --project-dir ""{app}"""; \
    WorkingDir: "{app}"; \
    StatusMsg: "Setting up Socials Studio's Python environment..."; \
    Flags: runhidden waituntilterminated
Filename: "{app}\launch.bat"; Description: "Launch Socials Studio now"; Flags: postinstall nowait skipifsilent unchecked
