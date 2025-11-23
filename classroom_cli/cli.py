import os

import click
from dotenv import load_dotenv

from .core import build_all, changeBranch, gh_classroom_clone, push_branches
from .utils import load_roster

# Load .env file into environment variables
load_dotenv()

roster_csv = os.getenv("ROSTER_PATH")
token = os.getenv("GITHUB_TOKEN")
gh_path = os.getenv("GH_PATH")
pio_path = os.getenv("PIO_PATH")

if not token:
    raise RuntimeError("GITHUB_TOKEN not found in .env or environment")


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
    gh_classroom_clone(assignment_id, class_dir)


@cli.command()
@click.argument("assignment_id")
@click.option(
    "--class-dir",
    default=".",
    help="Directory where the assignment folder will be created.",
)
@click.option(
    "--branch-name",
    default="assessment",
    help="Name of the branch to be created in the student's repo.",
)
def cloneBuildBranch(assignment_id, class_dir, branch_name):
    """Clone, build, and create an 'Assessment' branch for all students."""
    # Clone assignments just like the 'clone' command
    submissionDir = gh_classroom_clone(assignment_id, class_dir)
    # Build the assignment just like the 'build' command
    build_all(submissionDir)
    # Create 'Assessment' branch just like the 'branch' command
    changeBranch(submissionDir, branch_name)


@cli.command()
def roster():
    """Print the roster dictionary."""
    roster = load_roster(roster_csv)
    for username, identifier in roster.items():
        click.echo(f"{identifier}: {username}")


@cli.command()
@click.option(
    "--submission-dir", default=".", help="Directory containing student repos."
)
def build(submission_dir):
    """Build all PlatformIO projects in an submission directory."""
    build_all(submission_dir)


@cli.command()
@click.option(
    "--submission-dir", default=".", help="Directory containing student repos."
)
@click.option(
    "--branch-name",
    default="assessment",
    help="Name of the branch to be created in the student's repo.",
)
def branch(submission_dir, branch_name):
    """Creates an 'assessment' branch in all student repos in a submission directory."""
    changeBranch(submission_dir, branch_name)


@cli.command()
@click.option(
    "--submission-dir", default=".", help="Directory containing student repos."
)
@click.option(
    "--message",
    default="assessment",
    help="Commit message to use for assessment branch commits.",
)
@click.option(
    "--branch-name",
    default="assessment",
    help="Name of the branch to be pushed to the origin (GitHub).",
)
def push(submission_dir, message, branch_name):
    """
    Stage all changes, commit, and push the 'assessment' branch
    for every student repo in a submission directory.
    """
    push_branches(submission_dir, message, branch_name)


if __name__ == "__main__":
    cli()
