"""
config.py

This module provides configuration management for the classroom_cli tool.

"""

import json
from pathlib import Path

import click

CONFIG_DIR = Path.home() / ".classroom_cli"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> dict:
    """Load the config.json file. Returns empty dict if missing or invalid."""
    try:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text())
    except json.JSONDecodeError:
        # If the user mangles the file manually, don't explode.
        pass
    return {}


def save_config(cfg: dict) -> None:
    """Create the config directory if needed and save the JSON config."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


def update_config(**kwargs) -> dict:
    """Merge updates into existing config and save."""
    cfg = load_config()
    cfg.update({k: v for k, v in kwargs.items() if v is not None})
    save_config(cfg)
    return cfg


def get_config(key):
    cfg = load_config()
    value = cfg.get(key)
    if not value:
        raise click.UsageError(
            f"Missing configuration value '{key}'. Run: classroom-cli configure"
        )
    return value


# Called from cli.py
def config_wizard():
    """This function is called by the CLI to prompt user to configure CLI tool."""
    existing = load_config()

    click.echo("Configuring Classroom CLI...")
    click.echo("See readme.md for how to find values for this configuration.")
    click.echo("Press Enter to keep the existing value.\n")

    github_token = click.prompt(
        "Enter your GitHub token (input hidden)",
        default=existing.get("github_token", ""),
        hide_input=True,
        show_default=False,
    )

    roster_path = click.prompt(
        "Enter the path to your class roster CSV from GitHub Classroom",
        default=existing.get("roster_path", ""),
        show_default=True,
    )

    gh_path = click.prompt(
        "Enter your path to GitHub CLI",
        default=existing.get("gh_path", "C:\\Program Files\\GitHub CLI\\gh.exe"),
        show_default=True,
    )

    pio_path = click.prompt(
        "Enter the path to PlatformIO CLI",
        default=existing.get(
            "pio_path", "C:\\Users\\YourUsername\\.platformio\\penv\\Scripts\\pio.exe"
        ),
        show_default=True,
    )

    editor = click.prompt(
        "Select the default code editor for the 'open' command",
        default=existing.get("editor", "code"),
        show_default=True,
    )

    cfg = {
        "github_token": github_token,
        "roster_path": roster_path,
        "gh_path": gh_path,
        "pio_path": pio_path,
        "editor": editor,
    }

    save_config(cfg)
    click.echo(f"\nSaved configuration to {CONFIG_FILE}")
