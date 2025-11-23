import os
import shutil
import stat
import subprocess

import click

from .config import get_config
from .utils import getRepoPaths, load_roster


def gh_classroom_clone(assignment_id, class_dir) -> str:
    """Clone a GitHub Classroom assignment.
    Returns path of directory where assignments were cloned.
    """

    get_config("github_token")

    def remove_readonly(func, path, excinfo):
        """
        func: the function that failed (os.remove, os.rmdir)
        path: the path that failed
        excinfo: exception info tuple (type, value, traceback)
        """
        # Make the file writable
        os.chmod(path, stat.S_IWRITE)
        func(path)  # retry

    roster = load_roster(get_config("roster_csv"))
    os.makedirs(class_dir, exist_ok=True)

    click.echo(f"Cloning assignment ID '{assignment_id}' into '{class_dir}'...")

    # Run gh classroom clone command with -a ID and the directory
    subprocess.run(
        [
            get_config("gh_path"),
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

    # Find the "submissions" folder gh just made (the most recent one)
    subdirs = [
        os.path.join(class_dir, d)
        for d in os.listdir(class_dir)
        if os.path.isdir(os.path.join(class_dir, d))
    ]
    if not subdirs:
        raise RuntimeError(
            f"No assignment folder found in {class_dir}. The clone might have failed."
        )

    assignment_dir = max(subdirs, key=os.path.getmtime)
    click.echo(f"Using assignment (submission) directory: {assignment_dir}")

    # Rename folders using roster
    for folder in os.listdir(assignment_dir):
        folder_path = os.path.join(assignment_dir, folder)
        if not os.path.isdir(folder_path):
            continue

        # Detect already-renamed folders (they start with a roster name)
        # A simple heuristic: if the folder starts with any known "student_name_",
        # skip it
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
                    click.echo(f"Deleting duplicate {folder} (renamed already exists)")
                    shutil.rmtree(folder_path, onexc=remove_readonly)
                else:
                    # This is a first-time rename
                    click.echo(f"Renaming {folder} -> {new_folder_name}")
                    os.rename(folder_path, new_path)

                break  # stop after handling this folder

    click.echo(f"Assignments cloned to 'submission-dir': {assignment_dir}")
    click.echo(
        "cd into or use this directory for the\n"
        "--submission-dir option for other commands"
    )

    return assignment_dir


def build_project(repo_path) -> bool:
    """Build a PlatformIO project located at repo_path."""
    pio_path = get_config("pio_path")

    click.echo(f"Building PIO project in: {os.path.basename(repo_path)}")
    try:
        subprocess.run(
            [pio_path, "run", "--disable-auto-clean", "--silent"],
            cwd=repo_path,
            check=True,
        )
        click.echo("\tBuild Successfull")
        return True
    except subprocess.CalledProcessError:
        click.echo("\tBuild Failed")
        return False


def build_all(submission_dir):
    """Build all PlatformIO projects in an submission directory."""
    repo_paths = getRepoPaths(submission_dir)
    results = []

    for p in repo_paths:
        results.append(build_project(p))

    click.echo(
        f"\nSummary: {results.count(True)} passed, {results.count(False)} failed"
    )


def changeBranch(submission_dir, branch_name):
    """Change the branch of all git repositories in a submission directory."""

    click.echo(
        f"Changing branch to '{branch_name}' for all repositories in '{submission_dir}'"
    )

    repo_paths = getRepoPaths(submission_dir)

    for repo_path in repo_paths:
        # Check if 'assessment' branch exists in this repo
        result = subprocess.run(
            ["git", "branch", "--list", branch_name],
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        branch_exists = result.stdout.strip() != ""

        if branch_exists:
            click.echo(
                f"'{branch_name}' branch exists in {os.path.basename(repo_path)}.\n"
                "\tChecking it out. Consider merging from main if necessary."
            )
            subprocess.run(
                ["git", "checkout", branch_name],
                cwd=repo_path,
                check=True,
            )
        else:
            click.echo(
                f"Creating and checking out '{branch_name}' branch in "
                f"{os.path.basename(repo_path)}"
            )
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=repo_path,
                check=True,
            )


def push_branches(submission_dir, message, branch_name):

    get_config("github_token")

    repo_paths = getRepoPaths(submission_dir)

    click.echo(
        f"Committing and pushing '{branch_name}' branch to "
        "origin for all student repos..."
    )

    for repo_path in repo_paths:
        repo_name = os.path.basename(repo_path)
        click.echo(f"\n--- {repo_name} ---")

        # Ensure assessment branch exists and is checked out
        result = subprocess.run(
            ["git", "branch", "--list", branch_name],
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        branch_exists = result.stdout.strip() != ""

        if branch_exists:
            subprocess.run(
                ["git", "checkout", branch_name],
                cwd=repo_path,
                check=True,
            )
        else:
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=repo_path,
                check=True,
            )

        # Stage all changes
        subprocess.run(
            ["git", "add", "-A"],
            cwd=repo_path,
            check=True,
        )

        # Create commit if there are staged changes
        commit_proc = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if (
            "nothing to commit" in commit_proc.stdout.lower()
            or "nothing to commit" in commit_proc.stderr.lower()
        ):
            click.echo("No changes to commit.")
        else:
            click.echo("Committed changes.")

        # Push branch to origin
        try:
            subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                cwd=repo_path,
                check=True,
            )
            click.echo("Pushed to origin.")
        except subprocess.CalledProcessError:
            click.echo("Failed to push to origin.")


def launch_editor(editor_cmd: str, target_dir: str):
    parts = editor_cmd.split()

    exe = parts[0]
    if shutil.which(exe) is None:
        raise click.UsageError(f"Editor executable not found: {exe}")

    subprocess.Popen(parts + [target_dir])
