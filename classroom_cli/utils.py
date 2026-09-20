import os
import subprocess

import click
import pandas as pd

from .config import get_config

# TODO: Change CSV shape to email and username


def load_roster(csv_path):
    """Load CSV mapping student email-prefixes to GitHub usernames."""
    df = pd.read_csv(csv_path)
    email_prefixes = df["email"].str.split("@").str[0]
    return dict(zip(email_prefixes, df["github_username"], strict=False))


def getRepoPaths(submission_dir):
    """Returns a list of directories (repos) for an assignment."""
    repo_paths = [
        os.path.join(submission_dir, d)
        for d in os.listdir(submission_dir)
        if os.path.isdir(os.path.join(submission_dir, d))
    ]
    return repo_paths


def get_github_token() -> str:
    """Resolve a GitHub token, checked in this order:

    1. GITHUB_TOKEN / GH_TOKEN environment variables
       (primary path for Docker / headless deployments)
    2. A token stored in the local config file
    3. The token from an existing 'gh auth login' session
       (nice interactive setup path for regular users on their own machine)
    """

    # 1) Try environment var
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token

    # 2) Try config file
    try:
        token = get_config("github_token")
        if token:
            return token
    except Exception:
        # get_config raising just means it's not set; fall through
        pass

    # 3) Try gh auth token
    gh_path = get_config("gh_path")
    try:
        result = subprocess.run(
            [gh_path, "auth", "token"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        token = result.stdout.strip()
        if token:
            return token
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    raise click.UsageError(
        "No GitHub token found. Set the GITHUB_TOKEN or GH_TOKEN environment "
        "variable, run 'gh auth login', or set 'github_token' in the config."
    )
