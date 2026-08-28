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
;      into it, via setup-python.bat. See installer\bootstrap.py's module
;      docstring for why `uv` is used here instead of Python's official
;      embeddable distribution: that distribution ships without `ensurepip`,
;      so it can't bootstrap pip into a fresh venv. `--python-preference
;      only-managed` is verified against uv 0.5.11's real PythonPreference
;      enum (see setup-python.bat) -- not guessed. This step runs from
;      [Code]'s CurStepChanged, not a declarative [Run] entry, specifically
;      so its exit code can be checked -- see RunPythonSetup below. If it
;      fails, Setup stops there: it never runs bootstrap.py, never writes
;      the first-run marker, and never offers to install Claude Code or
;      launch Socials Studio -- see PythonSetupFailed/PythonSetupSucceeded.
;   3. Runs bootstrap.py (using the venv's own freshly-created python, with
;      --skip-python-setup, since step 2 already did that part) to check for
;      Claude Code and Chrome and write the first-run marker -- only if step
;      2 succeeded. Never logs into a platform, never launches a publish
;      flow, never collects a credential.
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
#ifndef MyOutputBaseFilename
  #define MyOutputBaseFilename "Socials-Studio-Setup"
#endif

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
; Overridable via `iscc /DMyOutputBaseFilename=... setup.iss` -- CI uses this
; to build a second, deliberately-broken installer for the dependency-install
; failure-path test without touching the real Socials-Studio-Setup.exe
; artifact. See .github/workflows/build-installers.yml.
OutputBaseFilename={#MyOutputBaseFilename}
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

// Set True only if setup-python.bat (uv venv + uv pip install) fails --
// see RunPythonSetup below. Declarative [Run] entries have no way to
// inspect a previous entry's exit code (Inno's own docs on the [Run]
// section describe only wait-vs-don't-wait behaviour, nothing about
// ResultCode), so the step that MUST gate everything after it -- do not
// run bootstrap.py, do not offer to install Claude Code, do not offer to
// launch Socials Studio -- has to be a real Exec() call in [Code] whose
// ResultCode we can actually read, not a [Run] entry.
var
  PythonSetupFailed: Boolean;

// Runs setup-python.bat (uv venv --python 3.12 --python-preference
// only-managed, then uv pip install -- see that file's own comments) via
// the same cmd.exe /C "path" pattern already proven safe for ClaudeCodeMissing
// above and for the [Run] entries elsewhere in this script: a single quoted
// argument, no redirection at this outer level (setup-python.bat redirects
// its own output to {app}\_setup-python.log internally).
//
// Called from CurStepChanged(ssPostInstall) below, at the same point in
// installation where this used to be a declarative [Run] entry -- but now
// as real Pascal code so PythonSetupFailed can actually reflect whether it
// worked. On failure: shows an error box pointing at _setup-python.log when
// running with a visible wizard (never in a silent/unattended install --
// gated on WizardSilent so this can never block a CI/silent run waiting for
// a click nothing will ever provide), then raises a script exception so
// Setup itself reports a genuine failure (non-zero exit code), not a
// falsely "successful" one. PythonSetupSucceeded() gates both the direct
// call to RunBootstrapPy below and the Check: on the Claude-offer/
// launch-offer [Run] entries -- an independent second line of defense that
// guarantees none of them run after a failure even if that exception
// somehow didn't stop Setup outright.
procedure RunPythonSetup();
var
  ResultCode: Integer;
  ScriptPath: String;
  LogPath: String;
begin
  ScriptPath := ExpandConstant('{app}\setup-python.bat');
  LogPath := ExpandConstant('{app}\_setup-python.log');
  if (not Exec(ExpandConstant('{sys}\cmd.exe'), '/C "' + ScriptPath + '"',
        ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, ResultCode))
     or (ResultCode <> 0) then
  begin
    PythonSetupFailed := True;
    if not WizardSilent() then
      MsgBox(
        'Socials Studio could not finish setting up its Python environment.' + #13#10 +
        'See ' + LogPath + ' for details, then run this installer again.',
        mbCriticalError, MB_OK);
    RaiseException(
      'Socials Studio setup failed: could not create its Python environment ' +
      'or install its dependencies. See ' + LogPath + ' for details.');
  end;
end;

// Used by the [Run] "Install Claude Code" and "Launch Socials Studio now"
// entries' Check: -- both must be skipped if RunPythonSetup above failed.
function PythonSetupSucceeded(): Boolean;
begin
  Result := not PythonSetupFailed;
end;

// Runs bootstrap.py with the venv's own freshly-created python, handling
// the rest (Claude Code / Chrome checks, the profiles/ preservation
// guarantee, and the first-run marker) -- --skip-python-setup because
// RunPythonSetup already did the venv/dependency work via setup-python.bat.
// --no-interactive-claude-offer because this runs hidden with no console a
// human could answer a prompt in -- without it, bootstrap.py's default
// Claude Code offer calls input() and blocks forever (a hidden-but-open
// console never reaches EOF, so the existing EOFError handling never
// triggers). Confirmed live: this hung the CI smoke test for the full step
// timeout, evidenced by Get-CimInstance Win32_Process showing this exact
// python.exe still running. Windows's real opt-in for installing Claude
// Code is the separate finish-page checkbox in [Run] below, not this
// CLI-style prompt -- see bootstrap.py's module docstring and
// installer/README.md's "Offering to install Claude Code".
//
// This used to be a declarative [Run] entry, gated on a Check:
// PythonSetupSucceeded function, on the theory that Check: would simply
// skip it if RunPythonSetup (also run from CurStepChanged(ssPostInstall))
// had already flagged failure. That's wrong: regular (non-postinstall)
// [Run] entries execute automatically as soon as Files are staged --
// *before* CurStepChanged(ssPostInstall) fires, not after. Confirmed live:
// with that design, this entry ran (and could only fail to find
// {app}\.venv\Scripts\python.exe, since RunPythonSetup hadn't created it
// yet) before RunPythonSetup ever got a chance to run, so bootstrap.py
// silently never executed and .first-run-pending was never written, even
// on a fully successful Python setup. Calling it directly from Pascal,
// sequenced explicitly after RunPythonSetup succeeds, is the fix -- see
// CurStepChanged below. bootstrap.py's own exit code (e.g. a normal
// "Claude Code not found yet" outcome) is deliberately not treated as a
// setup failure here -- that's an expected, non-fatal state reported by
// bootstrap.py itself and offered separately via the checkbox below, not
// something this installer aborts over.
procedure RunBootstrapPy();
var
  ResultCode: Integer;
begin
  Exec(ExpandConstant('{app}\.venv\Scripts\python.exe'),
    '"' + ExpandConstant('{app}\installer\bootstrap.py') + '" --project-dir "' +
    ExpandConstant('{app}') + '" --skip-python-setup --no-interactive-claude-offer',
    ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    RunPythonSetup();
    if PythonSetupSucceeded() then
      RunBootstrapPy();
  end;
end;

function ShouldOfferClaudeInstall(): Boolean;
begin
  Result := PythonSetupSucceeded() and ClaudeCodeMissing();
end;

[Run]
; setup-python.bat (via RunPythonSetup) and bootstrap.py (via RunBootstrapPy)
; both run from [Code]'s CurStepChanged(ssPostInstall), not declaratively
; here -- see the comments on both procedures above for why: RunPythonSetup
; needs to inspect a real ResultCode (which a [Run] entry can't expose at
; all), and bootstrap.py's invocation needs to run strictly *after*
; RunPythonSetup succeeds, which a declarative entry's Check: can't
; guarantee -- regular [Run] entries execute automatically as soon as Files
; are staged, before CurStepChanged(ssPostInstall) ever fires, confirmed
; live to silently skip bootstrap.py (unable to find a venv python.exe that
; didn't exist yet) even on a fully successful install.

; Optional, opt-in checkbox on the finish page -- only appears if Claude Code
; isn't already found and Python setup succeeded (Check:
; ShouldOfferClaudeInstall), unchecked by default like "Launch Socials
; Studio now" below, and only runs if the user checks it and clicks Finish.
; Prefers WinGet (a native package-manager install) when available;
; otherwise falls back to Anthropic's official PowerShell installer. Never
; redistributes Claude Code itself -- only invokes Anthropic's own
; installers, and only after this explicit opt-in.
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
    Check: ShouldOfferClaudeInstall

; Check: PythonSetupSucceeded -- never offer to launch Socials Studio after
; a failed Python setup; the app wouldn't work yet.
Filename: "{app}\launch.bat"; Description: "Launch Socials Studio now"; Flags: postinstall nowait skipifsilent unchecked; Check: PythonSetupSucceeded
