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
    """
    GitHub Classroom assignment manager.

    This CLI tool can clone all student repos to a selected folder.
    You can perform a batched build of all student repositories.
    You can easily create 'assessment' branches from their main.
    You can also commit and push all 'assessment' branches at once.
    """


@cli.command()
@click.argument("assignment_id")
@click.option(
    "--class-dir",
    default=".",
    help="Directory where the assignment folder will be created.",
)
def clone(assignment_id, class_dir):
    """
    Clones all student repos for an assignment.

    A submission directory will be created in the class_dir. Student
    repos will be cloned into the submission directory. Student repos
    are prepended with their student names provided by the classroom
    roster csv file.

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
    """
    Runs 'clone', 'build', and 'branch' commands.

    This command will run the 'clone', 'build', and 'branch' commands
    sequentially. This is useful if you want to clone an assignment,
    build it, and then create a branch for assessment.
    """
    # Clone assignments just like the 'clone' command
    submissionDir = gh_classroom_clone(assignment_id, class_dir)
    # Build the assignment just like the 'build' command
    build_all(submissionDir)
    # Create 'Assessment' branch just like the 'branch' command
    changeBranch(submissionDir, branch_name)


@cli.command()
def roster():
    """
    Print the roster dictionary.

    Prints the roster that you provided with your roster_csv .env variable.
    """
    roster = load_roster(roster_csv)
    for username, identifier in roster.items():
        click.echo(f"{identifier}: {username}")


@cli.command()
@click.option(
    "--submission-dir", default=".", help="Directory containing student repos."
)
def build(submission_dir):
    """
    Build all projects in an submission directory.

    This command calls your PlatformIO build command for each student project.
    This command is useful if you want to quickly check which project earned
    an automatic 'zero' grade.
    """
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
    """
    Creates an 'assessment' branch in all student repos.

    Assessing on the main branch is not recommended as students like to forget
    to push their most recent changes. Creating an assessment branch allows
    students to push thier most recent changes without your assessment causing
    merge conflicts.

    """
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
    Stage all changes, commit, and push to origin.

    This command will iterate through each studentn repo and
    stage all your assessment changes, commit them with the provided
    commit message and push to origin with the provided branch name.
    """
    push_branches(submission_dir, message, branch_name)


if __name__ == "__main__":
    cli()
