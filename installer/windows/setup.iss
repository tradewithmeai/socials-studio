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
;   2. Bundles a pinned `uv` binary (see payload-uv\, populated by the CI
;      build step) to create {app}\.venv and install requirements.txt into
;      it -- see installer\bootstrap.py's module docstring for why `uv` is
;      used here instead of Python's official embeddable distribution: the
;      embeddable distribution ships without `ensurepip`, so it can't
;      bootstrap pip into a fresh venv. `uv` doesn't have that dependency.
;   3. Runs bootstrap.py (using the venv's own freshly-created python, with
;      --skip-python-setup, since uv already did that part) to check for
;      Claude Code and Chrome and write the first-run marker. Never logs
;      into a platform, never launches a publish flow, never collects a
;      credential.
;   4. Creates a Start Menu / Desktop shortcut that opens a terminal in {app}
;      and runs `claude` -- see launch.bat.
;
; This script is built with `iscc setup.iss` by CI using the official
; jrsoftware/innosetup toolchain -- see the workflow for exact invocation.
; The workflow also runs a smoke test: silent install, verify the venv/
; launcher/marker exist, verify a reinstall doesn't touch profiles/. See
; the PR for the actual run's result -- an artifact isn't claimed "built"
; here, only described; whether the build actually succeeded is reported
; from the real CI run, not asserted in this comment.

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
; The pinned uv binary CI stages at build time -- see the workflow's
; "Stage uv for bundling" step. Used only to provision {app}\.venv.
Source: "..\..\payload-uv\*"; DestDir: "{app}\_bootstrap-uv"; Flags: ignoreversion recursesubdirs createallsubdirs
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
; Step 1: uv provisions {app}\.venv (creating or finding a suitable Python
; itself -- no system Python required). No login, no publish, no platform
; contact.
Filename: "{app}\_bootstrap-uv\uv.exe"; \
    Parameters: "venv ""{app}\.venv"""; \
    WorkingDir: "{app}"; \
    StatusMsg: "Setting up Socials Studio's Python environment..."; \
    Flags: runhidden waituntilterminated

; Step 2: uv installs requirements.txt into that venv.
Filename: "{app}\_bootstrap-uv\uv.exe"; \
    Parameters: "pip install --python ""{app}\.venv\Scripts\python.exe"" -r ""{app}\requirements.txt"""; \
    WorkingDir: "{app}"; \
    StatusMsg: "Installing dependencies..."; \
    Flags: runhidden waituntilterminated

; Step 3: bootstrap.py, run with the venv's own python, handles the rest
; (Claude Code / Chrome checks, the profiles/ preservation guarantee, and
; the first-run marker) -- --skip-python-setup because steps 1-2 already
; did the venv/dependency work.
Filename: "{app}\.venv\Scripts\python.exe"; \
    Parameters: """{app}\installer\bootstrap.py"" --project-dir ""{app}"" --skip-python-setup"; \
    WorkingDir: "{app}"; \
    StatusMsg: "Checking for Claude Code and Chrome..."; \
    Flags: runhidden waituntilterminated

Filename: "{app}\launch.bat"; Description: "Launch Socials Studio now"; Flags: postinstall nowait skipifsilent unchecked
