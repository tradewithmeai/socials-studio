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
;      build step) to create {app}\.venv from a uv-*managed* Python 3.12 --
;      not the machine's own Python, if any -- and install requirements.txt
;      into it. See installer\bootstrap.py's module docstring for why `uv`
;      is used here instead of Python's official embeddable distribution:
;      that distribution ships without `ensurepip`, so it can't bootstrap
;      pip into a fresh venv. `--python-preference only-managed` is verified
;      against uv 0.5.11's real PythonPreference enum (see the [Run] comment
;      below) -- not guessed.
;   3. Runs bootstrap.py (using the venv's own freshly-created python, with
;      --skip-python-setup, since uv already did that part) to check for
;      Claude Code and Chrome and write the first-run marker. Never logs
;      into a platform, never launches a publish flow, never collects a
;      credential.
;   4. If Claude Code isn't already on PATH, offers an *opt-in checkbox* on
;      the finish page (unchecked by default, exactly like "Launch Socials
;      Studio now") to install it via WinGet, or Anthropic's official
;      PowerShell installer if WinGet isn't available. This never runs
;      without the user explicitly checking the box and clicking Finish --
;      see [Code] and the [Run] "Install Claude Code" entry below. This
;      project never bundles or redistributes Claude Code itself.
;   5. Creates a Start Menu / Desktop shortcut that opens a terminal in {app}
;      and runs `claude` -- see launch.bat.
;
; This script is built with `iscc setup.iss` by CI using the official
; jrsoftware/innosetup toolchain -- see the workflow for exact invocation.
; The workflow also runs a smoke test: silent install, verify the venv was
; built from a uv-managed Python (not the runner's own), verify a dependency
; imports, verify the launcher/marker exist, verify a reinstall doesn't
; touch profiles/. See the PR for the actual run's result -- an artifact
; isn't claimed "built" here, only described; whether the build actually
; succeeded is reported from the real CI run, not asserted in this comment.

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
Source: "setup-python.bat"; DestDir: "{app}"; Flags: ignoreversion

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

[Code]
// Used only by the [Run] "Install Claude Code" entry's Check: -- this is a
// read-only PATH lookup (same idea as `where claude` from a command
// prompt), never an install action itself. Returns True (offer the
// checkbox) only when Claude Code genuinely isn't already found.
function ClaudeCodeMissing(): Boolean;
var
  ResultCode: Integer;
begin
  Result := not Exec('cmd.exe', '/C where claude >nul 2>nul', '', SW_HIDE,
    ewWaitUntilTerminated, ResultCode) or (ResultCode <> 0);
end;

[Run]
; Steps 1-2: setup-python.bat provisions {app}\.venv from uv's own *managed*
; Python 3.12 (--python-preference only-managed forces this rather than
; opportunistically picking up whatever Python, if any, is already on the
; machine -- verified against uv 0.5.11's real PythonPreference enum:
; https://github.com/astral-sh/uv/blob/0.5.11/crates/uv-python/src/discovery.rs,
; "only-managed": "Only use managed Python installations; never use system
; Python installations." -- not guessed, no system Python required), then
; installs requirements.txt into that same venv. Both uv calls and their
; output redirection live inside setup-python.bat itself, run as a plain
; script rather than assembled as a cmd.exe /C Parameters string.
;
; That distinction matters and was hard-won: uv writes a live-updating
; progress display while downloading, and Inno Setup's plain Exec doesn't
; drain a child process's output pipes, so calling uv directly with no
; redirection at all hung the CI job indefinitely once the OS pipe buffer
; filled. Redirecting output removed that hang -- but redirecting via an
; inline `cmd.exe /C "..." >"...log" 2>&1` Parameters string introduced a
; second, different failure: cmd.exe's /C argument parser mishandles a
; command line that both starts with a quoted path and contains a `>`
; redirection, and fails instantly with "The filename, directory name, or
; volume label syntax is incorrect" -- before uv ever runs, and without
; Inno surfacing that error anywhere. Confirmed live, reproduced locally.
; Moving the redirection inside a real .bat file removed that quoting
; hazard, but invoking the .bat as this entry's bare Filename introduced a
; *third* failure: CreateProcess (which Inno's plain Exec calls) does not
; support a .bat/.cmd file as the application image directly -- only APIs
; with their own .bat special-casing (e.g. .NET's Process.Start, which is
; why local testing looked fine) handle that. Confirmed live: this exact
; setup hung the CI job for the full 8-minute step timeout with zero
; output. The fix below is the standard, documented-safe way to launch a
; batch file from a raw CreateProcess-based API: wrap it in `cmd.exe /C
; "path"` with a single quoted argument and no redirection at this outer
; level -- the redirection stays inside the .bat, so there's still no pipe
; for Inno's Exec to fail to drain. See {app}\_setup-python.log if Socials
; Studio doesn't work after install.
Filename: "{sys}\cmd.exe"; \
    Parameters: "/C ""{app}\setup-python.bat"""; \
    WorkingDir: "{app}"; \
    StatusMsg: "Setting up Socials Studio's Python environment..."; \
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

; Optional, opt-in checkbox on the finish page -- only appears if Claude Code
; isn't already found (Check: ClaudeCodeMissing), unchecked by default like
; "Launch Socials Studio now" below, and only runs if the user checks it and
; clicks Finish. Prefers WinGet (a native package-manager install) when
; available; otherwise falls back to Anthropic's official PowerShell
; installer. Never redistributes Claude Code itself -- only invokes
; Anthropic's own installers, and only after this explicit opt-in.
; `skipifsilent` guarantees this never runs during a silent/unattended
; install (e.g. the CI smoke test's /VERYSILENT run) -- confirmed live: an
; earlier version without this flag caused the CI job to hang, consistent
; with Inno Setup running a "postinstall" entry by default in silent mode
; unless skipifsilent says otherwise. CI must never attempt a real Claude
; Code install; this flag is what enforces that, not just documentation.
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; \
    Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""if (Get-Command winget -ErrorAction SilentlyContinue) {{ winget install --id Anthropic.ClaudeCode -e --accept-source-agreements --accept-package-agreements }} else {{ irm https://claude.ai/install.ps1 | iex }}"""; \
    Description: "Install Claude Code now (via WinGet, or Anthropic's official installer if WinGet isn't available) -- required to use Socials Studio"; \
    Flags: postinstall shellexec unchecked skipifsilent; \
    Check: ClaudeCodeMissing

Filename: "{app}\launch.bat"; Description: "Launch Socials Studio now"; Flags: postinstall nowait skipifsilent unchecked
