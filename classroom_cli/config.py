"""
config.py

This module provides configuration management for the classroom_cli tool.

"""

import json
import os
import shutil
import sys
from pathlib import Path

import click

IS_WINDOWS = sys.platform == "win32"

# Cross-platform config location:
#   Windows: %APPDATA%\classroom-cli   Linux: ~/.config/classroom-cli
CONFIG_DIR = Path(click.get_app_dir("classroom-cli"))
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> dict:
    """Load the config.json file. Returns empty dict if missing or invalid."""
    try:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        # If the user mangles the file manually, don't explode.
        pass
    return {}


def save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    fd = os.open(CONFIG_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    if not IS_WINDOWS:
        os.chmod(CONFIG_FILE, 0o600)  # also fixes pre-existing files


def update_config(**kwargs) -> dict:
    """Merge updates into existing config and save."""
    cfg = load_config()
    cfg.update({k: v for k, v in kwargs.items() if v is not None})
    save_config(cfg)
    return cfg


ENV_OVERRIDES = {"github_token": "GITHUB_TOKEN"}
PATH_FALLBACKS = {"gh_path": "gh", "pio_path": "pio"}


def get_config(key):
    if (env_name := ENV_OVERRIDES.get(key)) and (value := os.environ.get(env_name)):
        return value

    value = load_config().get(key)
    if not value and key in PATH_FALLBACKS:
        value = shutil.which(PATH_FALLBACKS[key])

    if not value:
        raise click.UsageError(
            f"Missing configuration value '{key}'. Run: classroom-cli configure"
        )
    return value


# Config Wizard

# Default Path Helpers


# default detection for specific tools
def _first_file(*candidates) -> str:
    for c in candidates:
        if c and Path(c).is_file():
            return str(c)
    return ""


def default_gh_path() -> str:
    # shutil.which searches PATH and handles .exe on Windows automatically
    if found := shutil.which("gh"):
        return found
    if IS_WINDOWS:
        roots = [os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")]
        local = os.environ.get("LOCALAPPDATA")
        if local:
            roots.append(str(Path(local) / "Programs"))
        return _first_file(*(Path(r) / "GitHub CLI" / "gh.exe" for r in roots if r))
    return _first_file("/usr/bin/gh", "/usr/local/bin/gh", "/snap/bin/gh")


def default_pio_path() -> str:
    if found := shutil.which("pio") or shutil.which("platformio"):
        return found
    # PlatformIO's standard installer puts its virtualenv here
    penv = Path.home() / ".platformio" / "penv"
    if IS_WINDOWS:
        return _first_file(penv / "Scripts" / "pio.exe")
    return _first_file(penv / "bin" / "pio")


def default_editor() -> str:
    for name in ("code", "codium"):
        if shutil.which(name):
            return name
    return "notepad" if IS_WINDOWS else "nano"


# Prompt Helpers


def _clean_path(value: str) -> str:
    # Windows "Copy as path" wraps paths in quotes; also expand ~ and %VARS%
    value = value.strip().strip('"').strip("'")
    return os.path.expandvars(os.path.expanduser(value)) if value else ""


def prompt_file(text: str, default: str, required: bool = True) -> str:
    """Prompt the user for a file path, with optional default and required flag."""

    def check(value: str) -> str:
        path = _clean_path(value)
        if not path and not required:
            return ""
        if not Path(path).is_file():
            raise click.BadParameter(f"File not found: {path or '(empty)'}")
        return path

    suffix = "" if required else " (Enter to skip)"
    return click.prompt(
        text + suffix, default=default, show_default=bool(default), value_proc=check
    )


def check_token(token: str, org: str) -> tuple[bool, str]:
    """Verify the token works and can see the org."""
    from github import Auth, Github, GithubException

    try:
        Github(auth=Auth.Token(token), timeout=10).get_organization(org)
        return True, ""
    except GithubException as e:
        if e.status == 401:
            return False, "GitHub rejected the token (typo, expired, or revoked)."
        if e.status in (403, 404):
            return False, (
                f"Could not access organization '{org}'. Check the org name, and that the "
                "token's Resource owner is the organization (not your personal account)."
            )
        return False, f"GitHub error {e.status}."
    except Exception as e:  # offline, DNS, timeout...
        return False, f"Could not reach GitHub ({type(e).__name__})."


def prompt_token(existing: str, org: str) -> str:
    """Prompt the user for a GitHub token, with optional existing value and org check."""
    if os.environ.get("GITHUB_TOKEN"):
        click.echo(
            "Note: GITHUB_TOKEN is set in your environment and will override the saved value."
        )
    hint = f" [current: ...{existing[-4:]}]" if existing else ""

    while True:
        token = click.prompt(
            f"GitHub token (input hidden){hint}",
            default=existing,
            hide_input=True,
            show_default=False,
        ).strip()
        if not token:
            click.echo("A token is required.")
            continue
        if not token.startswith("github_pat_"):
            click.echo(
                "Warning: fine-grained tokens start with 'github_pat_'. Did you copy the right one?"
            )
        ok, msg = check_token(token, org)
        if ok:
            click.echo("Token verified.")
            return token
        click.echo(msg)
        if click.confirm("Save this token anyway?", default=False):
            return token


# Called from cli.py
def config_wizard():
    """This function is called by the CLI to prompt user to configure CLI tool."""
    existing = load_config()

    click.echo("Configuring Classroom CLI...")
    click.echo("See readme.md for how to find these values.")
    click.echo("Press Enter to keep the value shown in [brackets].\n")

    # Organization
    github_org = click.prompt(
        "GitHub organization name",
        default=existing.get("github_org", ""),
        show_default=True,
    ).strip()

    # Token
    github_token = prompt_token(existing.get("github_token", ""), github_org)

    # Term Code
    term_code = (
        click.prompt(
            "Term code (e.g., AY2026S1)",
            default=existing.get("term_code", ""),
            show_default=True,
        )
        .strip()
        .upper()
    )

    # Class roster CSV path
    roster_path = prompt_file(
        "Path to your class roster CSV",
        existing.get("roster_path", ""),
    )

    # GitHub CLI path
    gh_path = prompt_file(
        "Path to GitHub CLI (gh)",
        existing.get("gh_path") or default_gh_path(),
        required=False,
    )

    # PlatformIO CLI path
    pio_path = prompt_file(
        "Path to PlatformIO CLI (pio)",
        existing.get("pio_path") or default_pio_path(),
        required=False,
    )

    # Editor command
    editor = click.prompt(
        "Editor command for the 'open' command",
        default=existing.get("editor") or default_editor(),
        show_default=True,
    ).strip()

    update_config(
        github_token=github_token,
        github_org=github_org,
        term_code=term_code,
        roster_path=roster_path,
        gh_path=gh_path,
        pio_path=pio_path,
        editor=editor,
    )
    click.echo(f"\nSaved configuration to {CONFIG_FILE}")
