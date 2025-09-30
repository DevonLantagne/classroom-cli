import os
import subprocess

import click
import pandas as pd
from github import Github

ORG_NAME = "your-classroom-org"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ROSTER_CSV = "classroom_roster.csv"


def load_roster(csv_path):
    df = pd.read_csv(csv_path)
    return dict(zip(df["github_username"], df["identifier"], strict=False))


def clone_or_pull_repo(repo_url, target_dir):
    if not os.path.exists(target_dir):
        click.echo(f"Cloning into {target_dir}...")
        subprocess.run(["git", "clone", repo_url, target_dir], check=True)
    else:
        git_dir = os.path.join(target_dir, ".git")
        if os.path.exists(git_dir):
            click.echo(f"Pulling latest changes in {target_dir}...")
            subprocess.run(["git", "-C", target_dir, "pull"], check=True)
        else:
            click.echo(f"Warning: {target_dir} exists but is not a git repo. Skipping.")


@click.group()
def cli():
    """GitHub Classroom assignment manager."""


@cli.command()
@click.argument("assignment_name")
@click.option(
    "--output-dir",
    default=".",
    help="Directory where assignment folder will be created.",
)
def sync(assignment_name, output_dir):
    """Clone or pull all repos for ASSIGNMENT_NAME."""
    roster = load_roster(ROSTER_CSV)
    g = Github(GITHUB_TOKEN)
    org = g.get_organization(ORG_NAME)

    repos = [
        repo for repo in org.get_repos() if repo.name.startswith(assignment_name + "-")
    ]
    if not repos:
        click.echo(f"No repos found for assignment '{assignment_name}'")
        return

    assignment_dir = os.path.join(output_dir, assignment_name)
    os.makedirs(assignment_dir, exist_ok=True)

    for repo in repos:
        github_username = repo.name[len(assignment_name) + 1 :]
        student_name = roster.get(github_username, github_username)
        repo_dir = os.path.join(assignment_dir, student_name)
        repo_url = repo.clone_url.replace("https://", f"https://{GITHUB_TOKEN}@")
        clone_or_pull_repo(repo_url, repo_dir)


@cli.command()
@click.argument("assignment_name")
@click.option(
    "--output-dir", default=".", help="Directory containing the assignment repos."
)
def build(assignment_name, output_dir):
    """Build all PlatformIO projects for ASSIGNMENT_NAME."""
    assignment_dir = os.path.join(output_dir, assignment_name)
    if not os.path.exists(assignment_dir):
        click.echo(f"Assignment folder {assignment_dir} not found.")
        return

    for student_dir in os.listdir(assignment_dir):
        student_path = os.path.join(assignment_dir, student_dir)
        platformio_ini = os.path.join(student_path, "platformio.ini")
        if os.path.exists(platformio_ini):
            click.echo(f"Building project for {student_dir}...")
            subprocess.run(["pio", "run"], cwd=student_path)
        else:
            click.echo(f"Skipping {student_dir}, no platformio.ini found.")


if __name__ == "__main__":
    cli()
