import os
import subprocess

import click
import pandas as pd
from dotenv import load_dotenv

ROSTER_CSV = "classroom_roster.csv"

# Load .env file into environment variables
load_dotenv()

token = os.getenv("GITHUB_TOKEN")
gh_path = os.getenv("GH_PATH")

if not token:
    raise RuntimeError("GITHUB_TOKEN not found in .env or environment")


def load_roster(csv_path):
    """Load CSV mapping GitHub usernames to student identifiers."""
    df = pd.read_csv(csv_path)
    return dict(zip(df["github_username"], df["identifier"], strict=False))


def gh_classroom_clone(assignment_id, output_dir):
    """
    Use GitHub CLI Classroom extension to clone all student repos.
    Renames them using roster for LMS-friendly names.
    """
    roster = load_roster(ROSTER_CSV)
    assignment_dir = os.path.join(output_dir)
    os.makedirs(assignment_dir, exist_ok=True)

    click.echo(f"Cloning assignment ID '{assignment_id}' into '{assignment_dir}'...")

    # Run gh classroom clone command with -a ID
    subprocess.run(
        [
            gh_path,
            "classroom",
            "clone",
            "student-repos",
            "-a",
            str(assignment_id),
            "--directory",
            assignment_dir,
        ],
        shell=True,
        check=True,
    )

    # Rename folders using roster
    for folder in os.listdir(assignment_dir):
        folder_path = os.path.join(assignment_dir, folder)
        if os.path.isdir(folder_path):
            # Extract GitHub username (folder name is usually assignment-username)
            if "-" in folder:
                github_username = folder.split("-", 1)[1]
                student_name = roster.get(github_username, github_username)
                new_path = os.path.join(assignment_dir, student_name.replace(" ", "_"))
                if folder_path != new_path:
                    click.echo(f"Renaming {folder_path} -> {new_path}")
                    os.rename(folder_path, new_path)


@click.group()
def cli():
    """GitHub Classroom assignment manager."""


@cli.command()
@click.argument("assignment_id")
@click.option(
    "--output-dir",
    default=".",
    help="Directory where assignment folder will be created.",
)
def sync(assignment_id, output_dir):
    """Clone or update all repos for assignment_id using gh classroom."""
    gh_classroom_clone(assignment_id, output_dir)


if __name__ == "__main__":
    cli()
