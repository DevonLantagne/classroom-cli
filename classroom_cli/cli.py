import os
import shutil
import stat
import subprocess
from concurrent.futures import ThreadPoolExecutor

import click
import pandas as pd
from dotenv import load_dotenv

# Load .env file into environment variables
load_dotenv()

roster_csv = os.getenv("ROSTER_PATH")
token = os.getenv("GITHUB_TOKEN")
gh_path = os.getenv("GH_PATH")
pio_path = os.getenv("PIO_PATH")

if not token:
    raise RuntimeError("GITHUB_TOKEN not found in .env or environment")


def load_roster(csv_path):
    """Load CSV mapping GitHub usernames to student identifiers."""
    df = pd.read_csv(csv_path)
    return dict(zip(df["github_username"], df["identifier"], strict=False))


def gh_classroom_clone(assignment_id, class_dir):
    """
    Clones all student repos for an assignment. A submission directory
    will be created in the class_dir. Student repos will be cloned into
    the submission directory. Student repos are prepended with their
    student names provided by the classroom roster csv file.

    Do not run this command twice for the same assignment unless some
    students did not have a repo prior to your first clone. This will
    cause gh to clone new repos and waste your time. This command will
    detect if gh clones new repos and remove them (you will still have
    the repos from your first assignment clone).
    """

    def remove_readonly(func, path, excinfo):
        """
        func: the function that failed (os.remove, os.rmdir)
        path: the path that failed
        excinfo: exception info tuple (type, value, traceback)
        """
        # Make the file writable
        os.chmod(path, stat.S_IWRITE)
        func(path)  # retry

    roster = load_roster(roster_csv)
    os.makedirs(class_dir, exist_ok=True)

    click.echo(f"Cloning assignment ID '{assignment_id}' into '{class_dir}'...")

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
            class_dir,
        ],
        shell=True,
        check=True,
    )

    # Find the "-submissions" folder gh just made (the most recent one)
    subdirs = [
        os.path.join(class_dir, d)
        for d in os.listdir(class_dir)
        if os.path.isdir(os.path.join(class_dir, d))
    ]
    if not subdirs:
        raise RuntimeError(
            f"No assignment folder found in {class_dir}. The clone might have failed"
        )

    assignment_dir = max(subdirs, key=os.path.getmtime)
    click.echo(f"Using assignment directory: {assignment_dir}")

    # Rename folders using roster
    for folder in os.listdir(assignment_dir):
        folder_path = os.path.join(assignment_dir, folder)
        if not os.path.isdir(folder_path):
            continue

        # Detect already-renamed folders (they start with a roster name)
        # A simple heuristic: if the folder starts with any known student_name_, skip it
        already_named = any(
            folder.startswith(student_name.replace(" ", "_"))
            for student_name in roster.values()
        )
        if already_named:
            # This folder was renamed in an earlier run, leave it alone
            continue

        # Otherwise, see if the folder matches a known GitHub username
        for github_username, student_name in roster.items():
            if github_username in folder:
                safe_name = student_name.replace(" ", "_")
                new_folder_name = f"{safe_name}-{folder}"
                new_path = os.path.join(assignment_dir, new_folder_name)

                if os.path.exists(new_path):
                    # The properly renamed folder already exists.
                    # 'folder' is a duplicate!
                    click.echo(f"Deleting duplicate {folder} (already renamed exists)")
                    shutil.rmtree(folder_path, onexc=remove_readonly)
                else:
                    # This is a first-time rename
                    click.echo(f"Renaming {folder} -> {new_folder_name}")
                    os.rename(folder_path, new_path)

                break  # stop after handling this folder


@click.group()
def cli():
    """GitHub Classroom assignment manager."""


@cli.command()
@click.argument("assignment_id")
@click.option(
    "--class-dir",
    default=".",
    help="Directory where the assignment folder will be created.",
)
def clone(assignment_id, class_dir):
    """Clone all student repos for assignment_id."""
    gh_classroom_clone(assignment_id, class_dir)


@cli.command()
def roster():
    """Print the roster dictionary."""
    roster = load_roster(roster_csv)
    for username, identifier in roster.items():
        click.echo(f"{identifier}: {username}")


def build_project(repo_path):
    """Build a PlatformIO project located at repo_path."""
    try:
        subprocess.run(
            [pio_path, "run", "--disable-auto-clean", "--silent"],
            cwd=repo_path,
            check=True,
        )
        click.echo(f"Successfully built {os.path.basename(repo_path)}")
        return True
    except subprocess.CalledProcessError:
        click.echo(f"Failed to build {os.path.basename(repo_path)}")
        return False


@cli.command()
@click.option(
    "--submission-dir", default=".", help="Directory containing student repos."
)
def build(submission_dir):
    """Build all PlatformIO projects in an submission directory."""
    repo_paths = [
        os.path.join(submission_dir, d)
        for d in os.listdir(submission_dir)
        if os.path.isdir(os.path.join(submission_dir, d))
    ]
    results = []

    for p in repo_paths:
        results.append(build_project(p))

    click.echo(
        f"\nSummary: {results.count(True)} passed, {results.count(False)} failed"
    )


if __name__ == "__main__":
    cli()

# This is a comment from GitHub.com
