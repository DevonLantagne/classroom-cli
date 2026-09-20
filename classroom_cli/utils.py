import os
import subprocess

import click
import pandas as pd
from github import Github

from .config import get_config


def load_roster(csv_path):
    """Load CSV mapping student email-prefixes to GitHub usernames.

    Rows missing an email or a github_username are skipped with a warning
    (e.g. a student who hasn't submitted their username yet). Identical
    duplicate rows are collapsed silently. Raises ValueError if the same
    email appears with two different usernames, since we can't tell which
    is right.
    """
    # skip_blank_lines=False keeps the row numbers below matching the file
    df = pd.read_csv(csv_path, dtype=str, skip_blank_lines=False).dropna(how="all")

    df["email"] = df["email"].str.strip().str.split("@").str[0].str.strip()
    df["github_username"] = df["github_username"].str.strip()
    for col in ("email", "github_username"):
        df[col] = df[col].replace("", pd.NA)

    incomplete = df["email"].isna() | df["github_username"].isna()
    for idx, row in df[incomplete].iterrows():
        missing = [c for c in ("email", "github_username") if pd.isna(row[c])]
        who = row["email"] if pd.notna(row["email"]) else "<no email>"
        click.secho(
            f"WARNING: skipping roster row {idx + 2} ({who}): missing {' and '.join(missing)}",
            fg="yellow",
            err=True,
        )
    df = df[~incomplete].drop_duplicates(subset=["email", "github_username"])

    conflicts = df[df["email"].duplicated(keep=False)]
    if not conflicts.empty:
        names = ", ".join(sorted(conflicts["email"].unique()))
        raise ValueError(
            f"Conflicting roster entries (same email, different username): {names}"
        )

    return dict(zip(df["email"], df["github_username"], strict=False))


def getRepoPaths(submission_dir):
    """Returns a list of directories (repos) for an assignment."""
    repo_paths = [
        os.path.join(submission_dir, d)
        for d in os.listdir(submission_dir)
        if os.path.isdir(os.path.join(submission_dir, d))
    ]
    return repo_paths


def get_github_client() -> Github:
    """Return an authenticated PyGithub client."""
    return Github(get_github_token())


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
