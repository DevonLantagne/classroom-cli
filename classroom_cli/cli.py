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
    Clones all student repos for an assignment. A submission directory
    will be created in the output_dir. Student repos will be cloned into
    the submission directory. Student repos are prepended with their
    student names provided by the classroom roster csv file.

    Do not run this command twice as it will cause bad duplicates.
    """
    roster = load_roster(ROSTER_CSV)
    os.makedirs(output_dir, exist_ok=True)

    click.echo(f"Cloning assignment ID '{assignment_id}' into '{output_dir}'...")

    # Run gh classroom clone command with -a ID and the directory
    subprocess.run(
        [
            gh_path,
            "classroom",
            "clone",
            "student-repos",
            "-a",
            str(assignment_id),
            "--directory",
            output_dir,
        ],
        shell=True,
        check=True,
    )

    # Find the "-submissions" folder gh just made (the most recent one)
    subdirs = [
        os.path.join(output_dir, d)
        for d in os.listdir(output_dir)
        if os.path.isdir(os.path.join(output_dir, d))
    ]
    if not subdirs:
        raise RuntimeError(f"No assignment folder found in {output_dir}")

    assignment_dir = max(subdirs, key=os.path.getmtime)
    click.echo(f"Using assignment directory: {assignment_dir}")

    # Rename folders using roster
    for folder in os.listdir(assignment_dir):
        folder_path = os.path.join(assignment_dir, folder)
        if not os.path.isdir(folder_path):
            continue

        new_folder_name = folder  # start with original
        for github_username, student_name in roster.items():
            if github_username in folder:
                safe_name = student_name.replace(" ", "_")
                # prepend username and student name
                new_folder_name = f"{safe_name}-{folder}"
                break  # stop after first match

        new_path = os.path.join(assignment_dir, new_folder_name)
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
def clone(assignment_id, output_dir):
    """Clone all student repos for assignment_id."""
    gh_classroom_clone(assignment_id, output_dir)


@cli.command()
def roster():
    """Print the roster dictionary."""
    roster = load_roster(ROSTER_CSV)
    for username, identifier in roster.items():
        click.echo(f"{identifier}: {username}")


if __name__ == "__main__":
    cli()
