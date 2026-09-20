import click

from .config import config_wizard, get_config
from .core import (
    build_all,
    changeBranch,
    clone_assignment_repos,
    launch_editor,
    push_branches,
)


@click.group()
def cli():
    """
    Assignment manager for GitHub as an alternative to GitHub Classroom.

    This CLI tool can clone all student repos to a selected folder.
    You can perform a batched build (PlatformIO) of all student repositories.
    You can easily create 'assessment' branches from student main branches.
    You can also commit and push all 'assessment' branches at once.

    To begin, run: classroom-cli configure
    """


@cli.command()
def configure():
    """
    Interactive setup for classroom-cli.

    Configures GitHub token, roster paths, and tool paths.
    Creates ~/.classroom_cli/config.json.

    User can edit the config.json manually if needed.
    """
    config_wizard()


@cli.command()
@click.argument("assignment_name")
@click.option(
    "--class-dir",
    default=".",
    help="Directory where the assignment folder will be created.",
    type=click.Path(file_okay=False, dir_okay=True, writable=True, resolve_path=True),
)
def clone(assignment_name, class_dir):
    """
    Clones all student repos for an assignment.

    A submission directory will be created in the class_dir. Student
    repos will be cloned into the submission directory.

    This command is idempotent. If the repos have already been cloned,
    the command will skip cloning.
    """
    clone_assignment_repos(assignment_name, class_dir)


@cli.command()
@click.argument("assignment_name")
@click.option(
    "--class-dir",
    default=".",
    help="Directory where the assignment folder will be created.",
    type=click.Path(file_okay=False, dir_okay=True, writable=True, resolve_path=True),
)
@click.option(
    "--branch-name",
    default="assessment",
    help="Name of the branch to be created in the student's repo.",
    type=click.STRING,
)
def cloneBuildBranch(assignment_name, class_dir, branch_name):
    """
    Runs 'clone', 'build', and 'branch' commands.

    This command will run the 'clone', 'build', and 'branch' commands
    sequentially. This is useful if you want to clone an assignment,
    build it, and then create a branch for assessment.
    """
    # Clone assignments just like the 'clone' command
    submissionDir = clone_assignment_repos(assignment_name, class_dir)
    # Build the assignment just like the 'build' command
    build_all(submissionDir)
    # Create 'Assessment' branch just like the 'branch' command
    changeBranch(submissionDir, branch_name)


@cli.command()
def roster():
    """
    Print the roster dictionary.

    Prints the roster that you provided in the config.
    """
    from .utils import load_roster

    roster = load_roster(get_config("roster_path"))
    for email_prefix, github_username in roster.items():
        click.echo(f"{email_prefix}: {github_username}")


@cli.command()
@click.option(
    "--submission-dir",
    default=".",
    help="Directory containing student repos.",
    type=click.Path(exists=True, file_okay=False),
)
def openAll(submission_dir):
    """
    Opens the default editor.
    """
    editor = get_config("editor")
    launch_editor(editor, submission_dir)
    click.echo(f"Opened {submission_dir} in {editor}.")


@cli.command()
@click.option(
    "--submission-dir",
    default=".",
    help="Directory containing student repos.",
    type=click.Path(exists=True, file_okay=False),
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
    "--submission-dir",
    default=".",
    help="Directory containing student repos.",
    type=click.Path(exists=True, file_okay=False),
)
@click.option(
    "--branch-name",
    default="assessment",
    help="Name of the branch to be created in the student's repo.",
    type=click.STRING,
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
    "--submission-dir",
    default=".",
    help="Directory containing student repos.",
    type=click.Path(exists=True, file_okay=False),
)
@click.option(
    "--message",
    default="assessment",
    help="Commit message to use for assessment branch commits.",
    type=click.STRING,
)
@click.option(
    "--branch-name",
    default="assessment",
    help="Name of the branch to be pushed to the origin (GitHub).",
    type=click.STRING,
)
def push(submission_dir, message, branch_name):
    """
    Stage all changes, commit, and push to origin.

    This command will iterate through each student repo and
    stage all your assessment changes, commit them with the provided
    commit message, and push to origin with the provided branch name.
    """
    push_branches(submission_dir, message, branch_name)


if __name__ == "__main__":
    cli()
