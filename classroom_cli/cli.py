from collections import Counter

import click

from .config import config_wizard, get_config
from .core import (
    TEMPLATE_SUFFIX,
    build_all,
    changeBranch,
    clone_assignment_repos,
    create_assignment_repos,
    get_template_repos,
    launch_editor,
    push_branches,
)
from .utils import get_github_client


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

    Saves a config.json files in the following locations:
        Windows: %APPDATA%\\classroom-cli
        Linux: ~/.config/classroom-cli

    User can edit the config.json manually if needed.
    """
    config_wizard()


@cli.command()
def show_templates():
    """
    List all template repos in the org.

    Queries the org for repos whose name ends in '-template' and prints
    them. Useful for sanity-checking what's available before running
    'createAssignment'.

    Pass one of the items as the TEMPLATE_NAME argument to 'createAssignment'.
    """
    gh = get_github_client()
    org = gh.get_organization(get_config("github_org"))

    templates = get_template_repos(org)

    if not templates:
        click.echo("No template repos found.")
        return

    for repo in templates:
        click.echo(repo.name)


def _print_result(r):
    colors = {
        "created": "green",
        "exists": "yellow",
        "would_create": "cyan",
        "error": "red",
    }
    click.secho(
        f"[{r['status']}] {r['repo']}  ({r['username']})", fg=colors[r["status"]]
    )
    if r["detail"]:
        click.echo(f"    {r['detail']}")
    if r["invite_url"]:
        click.echo(f"    invitation link: {r['invite_url']}")


@cli.command()
@click.argument("template_name")
@click.option(
    "--dry-run", is_flag=True, help="Show what would happen without creating anything."
)
@click.option("--yes", "-y", is_flag=True, help="Skip the confirmation prompt.")
def create_assignment(template_name, dry_run, yes):
    """Create an assignment repo for each student.

    TEMPLATE_NAME is a template repo in your GitHub organization that must end with
    '-template'. Assignment repos will be created with the following naming convention:

    <term_code>-<template name minus '-template'>-<email prefix>

    For example, if the template is 'Lab1-Intro-template' and term code is 'AY2026S1',
    the repo for student would be:

    'AY2026S1-Lab1-Intro-<student email prefix>'

    This command is idempotent. If a repo already exists, it will not be recreated,
    but access will be granted again.
    """

    click.echo(f"Org:            {get_config('github_org')}")
    click.echo(f"Template repo:  {template_name}")
    click.echo(f"Lab name:       {template_name.removesuffix(TEMPLATE_SUFFIX)}")
    click.echo(f"Term prefix:    {get_config('term_code')}")
    click.echo(f"CSV file:       {get_config('roster_path')}")
    if dry_run:
        click.echo(
            "Mode:           DRY RUN (no repos will be created, no access granted)"
        )
    click.echo()
    if not yes:
        click.confirm("Proceed?", abort=True)

    try:
        results = create_assignment_repos(
            template_name, dry_run=dry_run, progress=_print_result
        )
    except ValueError as e:
        raise click.ClickException(str(e)) from e

    counts = Counter(r["status"] for r in results)
    click.echo("\nSummary: " + ", ".join(f"{n} {s}" for s, n in sorted(counts.items())))
    if counts["error"]:
        raise click.exceptions.Exit(1)


@cli.command()
@click.argument("assignment_name")
@click.option(
    "--class-dir",
    default=".",
    help="Directory where the assignment folder will be created. Default is current working directory.",
    type=click.Path(file_okay=False, dir_okay=True, writable=True, resolve_path=True),
)
def clone(assignment_name, class_dir):
    """
    Clones all student repos for an assignment.

    ASSIGNMENT_NAME is the name of the template repo used to create the assignment but
    without the '-template' suffix.

    --class-dir is the directory where the assignment folder (which will contain all
    student repos) will be created. Defaults to the current working directory.

    This command is idempotent. If the repos have already been cloned,
    the command will skip cloning.
    """
    clone_assignment_repos(assignment_name, class_dir)


@cli.command()
@click.argument("assignment_name")
@click.option(
    "--class-dir",
    default=".",
    help="Directory where the assignment folder will be created. Default is current working directory.",
    type=click.Path(file_okay=False, dir_okay=True, writable=True, resolve_path=True),
)
@click.option(
    "--branch-name",
    default="assessment",
    help="Name of the branch to be created in the student's repo. Default is 'assessment'.",
    type=click.STRING,
)
def clone_build_branch(assignment_name, class_dir, branch_name):
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
    click.echo("email prefix : github username")
    for email_prefix, github_username in roster.items():
        click.echo(f"{email_prefix}: {github_username}")


@cli.command()
@click.option(
    "--submission-dir",
    default=".",
    help="Directory containing student repos. Default is current working directory.",
    type=click.Path(exists=True, file_okay=False),
)
def open_all(submission_dir):
    """
    Opens the default editor with the submission directory as the working folder.
    """
    editor = get_config("editor")
    launch_editor(editor, submission_dir)
    click.echo(f"Opened {submission_dir} in {editor}.")


@cli.command()
@click.option(
    "--submission-dir",
    default=".",
    help="Directory containing student repos. Default is current working directory.",
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
    help="Directory containing student repos. Default is current working directory.",
    type=click.Path(exists=True, file_okay=False),
)
@click.option(
    "--branch-name",
    default="assessment",
    help="Name of the branch to be created in the student's repo. Default is 'assessment'.",
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
    help="Directory containing student repos. Default is current working directory.",
    type=click.Path(exists=True, file_okay=False),
)
@click.option(
    "--message",
    default="assessment",
    help="Commit message to use for assessment branch commits. Default is 'assessment'.",
    type=click.STRING,
)
@click.option(
    "--branch-name",
    default="assessment",
    help="Name of the branch to be pushed to the origin (GitHub). Default is 'assessment'.",
    type=click.STRING,
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would happen without commiting and pushing anything.",
)
def push(submission_dir, message, branch_name, dry_run):
    """
    Stage all changes, commit, and push to origin.

    This command will iterate through each student repo and
    stage all your assessment changes, commit them with the provided
    commit message, and push to origin with the provided branch name.

    With dry_run=True, nothing is checked out, committed, or pushed; a per-file
    summary of pending changes is printed instead.
    """
    push_branches(submission_dir, message, branch_name, dry_run)


if __name__ == "__main__":
    cli()
