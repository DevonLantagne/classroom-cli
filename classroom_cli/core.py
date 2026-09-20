import os
import shutil
import stat
import subprocess

import click
from github import Github

from .config import get_config
from .utils import get_github_token, getRepoPaths, load_roster


def get_github_client() -> Github:
    """Return an authenticated PyGithub client."""
    return Github(get_github_token())


def remove_readonly(func, path, excinfo):
    """
    func: the function that failed (os.remove, os.rmdir)
    path: the path that failed
    excinfo: exception info tuple (type, value, traceback)
    """
    # Make the file writable
    os.chmod(path, stat.S_IWRITE)
    func(path)  # retry


def get_assignment_repos(org, term_code: str, assignment_name: str):
    """Query an org for repos belonging to a given assignment.

    Repos are expected to follow the naming scheme:
        {term_code}-{assignment_name}-{student_email_prefix}
    e.g. AY2027S1-Lab1-jsmith

    Returns a list of (repo, student_email_prefix) tuples.
    """
    prefix = f"{term_code}-{assignment_name}-"
    matches = []
    for repo in org.get_repos():
        if repo.name.startswith(prefix):
            student_prefix = repo.name[len(prefix) :]
            matches.append((repo, student_prefix))
    return matches


def clone_assignment_repos(assignment_name, class_dir) -> str:
    """Clone all student repos for a given assignment from the GitHub org.

    Repos are discovered by querying the configured org and filtering by the
    assignment's naming prefix.

    Returns the directory where repos were cloned.
    """
    token = get_github_token()
    gh = get_github_client()

    org_name = get_config("github_org")
    term_code = get_config("term_code")
    org = gh.get_organization(org_name)

    roster = load_roster(get_config("roster_path"))  # {email_prefix: username}

    os.makedirs(class_dir, exist_ok=True)
    assignment_dir = os.path.join(class_dir, f"{assignment_name}")
    os.makedirs(assignment_dir, exist_ok=True)

    click.echo(
        f"Querying org '{org_name}' for '{assignment_name}' repos "
        f"(prefix '{term_code}-{assignment_name}-')..."
    )
    repo_matches = get_assignment_repos(org, term_code, assignment_name)

    if not repo_matches:
        raise RuntimeError(
            f"No repos found for assignment '{assignment_name}' in org "
            f"'{org_name}'. Check the term_code/assignment_name and that "
            "repos have been created."
        )

    click.echo(f"Found {len(repo_matches)} repo(s). Cloning into '{assignment_dir}'...")

    cloned, skipped, failed = [], [], []

    for repo, student_prefix in repo_matches:
        if student_prefix not in roster:
            click.echo(
                f"Warning: '{repo.name}' has no matching roster entry "
                f"for '{student_prefix}' (cloning anyway)."
            )

        target_path = os.path.join(assignment_dir, repo.name)

        if os.path.exists(target_path):
            click.echo(f"Skipping {repo.name}, already exists at {target_path}")
            skipped.append(repo.name)
            continue

        # NOTE: token is embedded in the clone URL, which briefly makes it
        # visible via inspection like `ps aux` while the subprocess runs.
        # Alternative is a GIT_ASKPASS helper.
        clone_url = repo.clone_url.replace("https://", f"https://{token}@")

        click.echo(f"Cloning {repo.name}...")
        try:
            subprocess.run(
                ["git", "clone", clone_url, target_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            cloned.append(repo.name)
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode(errors="ignore") if e.stderr else ""
            click.echo(f"Failed to clone {repo.name}: {stderr}")
            failed.append(repo.name)

    click.echo(
        f"\nSummary: {len(cloned)} cloned, {len(skipped)} skipped, "
        f"{len(failed)} failed"
    )
    click.echo(f"Repos available in: {assignment_dir}")
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
        click.echo("\t✅ Build Successful")
        return True
    except subprocess.CalledProcessError:
        click.echo("\t❌ Build Failed")
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
    """Change the branch of all git repositories in a submission directory.
    Creates the branch if it doesn't exist, otherwise checks it out.
    """

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
    """Commit and push all changes in a submission directory to the given branch."""

    # Confirms a token is resolvable before we start iterating repos
    get_github_token()

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
            click.echo("❌ Failed to push to origin.")


def launch_editor(editor_cmd: str, target_dir: str):
    parts = editor_cmd.split()

    exe = parts[0]
    if shutil.which(exe) is None:
        raise click.UsageError(f"Editor executable not found: {exe}")

    subprocess.Popen(parts + [target_dir])
