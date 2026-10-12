import os
import shutil
import stat
import subprocess
import sys

import click
from github import GithubException, UnknownObjectException

from .config import get_config
from .utils import get_github_client, get_github_token, getRepoPaths, load_roster

# --------------------------------------------------------------------------------------
# Create Assignment Repos
# --------------------------------------------------------------------------------------

TEMPLATE_SUFFIX = "-template"


def _describe(exc):
    """Short human-readable text for a GithubException."""
    data = exc.data if isinstance(exc.data, dict) else {}
    return f"{exc.status}: {data.get('message') or exc}"


def create_assignment_repos(template_name, dry_run=False, progress=None):
    """Create one private repo per rostered student from a template repo.

    Repo name: "<term_code>-<template name minus '-template'>-<email prefix>"

    Returns a list of dicts, one per student, with keys:
        student, username, repo, status, access, detail, invite_url
    status: "created" | "exists" | "would_create" | "error"
    access: "granted" | "invited" | None

    Raises ValueError for problems affecting the whole run (bad template).
    If `progress` (function handle) is given, it is called with each result
    as it completes.
    """
    if not template_name.endswith(TEMPLATE_SUFFIX):
        raise ValueError(
            f"Template repo name must end with '{TEMPLATE_SUFFIX}': {template_name}"
        )

    # Connect to GitHub and get roster
    gh = get_github_client()
    org = gh.get_organization(get_config("github_org"))
    roster = load_roster(get_config("roster_path"))

    # Check the template repo is configured correctly
    try:
        template = org.get_repo(template_name)
    except UnknownObjectException:
        raise ValueError(
            f"Template repo '{org.login}/{template_name}'"
            "not found (or token lacks access)."
        ) from None
    if not template.is_template:
        raise ValueError(
            f"'{template_name}' is not marked as a template repository "
            "(GitHub repo Settings -> check 'Template repository')."
        )

    # Assemble repo naming parts and create repo for each student
    term_code = get_config("term_code")
    base_name = template_name[: -len(TEMPLATE_SUFFIX)]
    results = []
    for prefix, username in roster.items():
        repo_name = f"{term_code}-{base_name}-{prefix}"
        result = _process_student(
            gh, org, template, repo_name, prefix, username, dry_run
        )
        results.append(result)
        if progress:
            progress(result)
    return results


def _process_student(gh, org, template, repo_name, prefix, username, dry_run):
    """Create (or repair access to) one student's repo.
    Creates a private repo from a template in the organization.
    Then grants that student write access to that repo.
    If the repo already exists, it will not be recreated, but access will be granted.

    GitHub errors never propagate; they are reported in the returned dict (from result).
    """

    def result(status, access=None, detail="", invite_url=None):
        return {
            "student": prefix,
            "username": username,
            "repo": repo_name,
            "status": status,
            "access": access,
            "detail": detail,
            "invite_url": invite_url,
        }

    created = False
    try:
        try:
            user = gh.get_user(username)
        except UnknownObjectException:
            return result(
                "error", detail=f"GitHub user '{username}' not found (check spelling)"
            )

        note = "" if org.has_in_members(user) else "not an org member yet"

        try:
            repo = org.get_repo(repo_name)
        except UnknownObjectException:
            repo = None

        if dry_run:
            return result("would_create" if repo is None else "exists", detail=note)

        if repo is None:
            repo = org.create_repo_from_template(repo_name, template, private=True)
            created = True
        elif repo.has_in_collaborators(user):
            return result("exists", access="granted", detail="already has access")

        # Returns an Invitation if GitHub sent an invite, None if access was immediate
        invitation = repo.add_to_collaborators(user, permission="push")

    except GithubException as e:
        prefix_msg = (
            "repo created, but granting access failed (re-run to retry): "
            if created
            else ""
        )
        return result("error", detail=prefix_msg + _describe(e))

    status = "created" if created else "exists"
    if invitation is None:
        return result(status, access="granted")
    return result(
        status,
        access="invited",
        detail=note or "repo invitation sent",
        invite_url=invitation.html_url,
    )


def remove_readonly(func, path, excinfo):
    """
    func: the function that failed (os.remove, os.rmdir)
    path: the path that failed
    excinfo: exception info tuple (type, value, traceback)
    """
    # Make the file writable
    os.chmod(path, stat.S_IWRITE)
    func(path)  # retry


# --------------------------------------------------------------------------------------
# Reading / Cloning Student Repos
# --------------------------------------------------------------------------------------


def get_template_repos(org):
    """Return all repos in the org that look like assignment templates
    (i.e. whose name ends in '-template')."""
    return [repo for repo in org.get_repos() if repo.name.endswith("-template")]


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

    click.echo(f"Found {len(repo_matches)} repo(s).")
    click.echo(f"Cloning into '{assignment_dir}'...")

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


def _git(path, *args):
    """Run a git command in `path` and return stripped stdout."""
    result = subprocess.run(
        ["git", "-C", path, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",  # avoids Windows cp1252 decode errors on student content
        errors="replace",
        check=True,
    )
    return result.stdout.strip()


def _rev_or_none(path, ref):
    """Return the SHA for `ref`, or None if it doesn't exist."""
    try:
        return _git(path, "rev-parse", "--verify", "--quiet", ref)
    except subprocess.CalledProcessError:
        return None


def _find_repo_dirs(submission_dir, students):
    """Return repo folder names to update, optionally filtered by student prefix."""
    all_dirs = sorted(
        d
        for d in os.listdir(submission_dir)
        if os.path.isdir(os.path.join(submission_dir, d, ".git"))
    )

    if not students:
        return all_dirs

    selected = []
    for student in students:
        suffix = f"-{student}".lower()
        matches = [d for d in all_dirs if d.lower().endswith(suffix)]
        if not matches:
            raise click.UsageError(
                f"No repo found for student '{student}' in {submission_dir}"
            )
        if len(matches) > 1:
            raise click.UsageError(
                f"Student '{student}' matches multiple repos: {', '.join(matches)}"
            )
        selected.append(matches[0])
    return selected


def _update_main(path):
    """Bring local 'main' up to date without disturbing the checked-out branch.

    Returns (before, after) SHAs of local main (before is None if main didn't
    exist locally). Raises CalledProcessError on git failure.
    """
    before = _rev_or_none(path, "refs/heads/main")
    current = _git(path, "rev-parse", "--abbrev-ref", "HEAD")

    if current == "main":
        _git(path, "pull", "--ff-only", "origin", "main")
    else:
        # Fast-forwards local main from the remote without touching the
        # working tree or the current branch.
        _git(path, "fetch", "origin", "main:main")

    after = _rev_or_none(path, "refs/heads/main")
    return before, after


def pull_assignment_repos(submission_dir, students=(), verbosity=0) -> bool:
    """Update local 'main' in student repos under submission_dir.

    verbosity: 0 = changed-repo report, 1 = + stat (files / line counts),
               2 = + full diff.

    Returns True if no repo failed.
    """
    repo_dirs = _find_repo_dirs(submission_dir, students)
    if not repo_dirs:
        raise RuntimeError(f"No git repos found in '{submission_dir}'.")

    click.echo(
        f"Updating 'main' in {len(repo_dirs)} repo(s) under '{submission_dir}'..."
    )

    updated, current, no_main, failed = [], [], [], []

    for name in repo_dirs:
        path = os.path.join(submission_dir, name)
        try:
            before, after = _update_main(path)
        except subprocess.CalledProcessError as e:
            stderr = (e.stderr or "").strip()
            if "couldn't find remote ref" in stderr:
                click.echo(f"Warning: {name} has no 'main' branch on the remote.")
                no_main.append(name)
            else:
                click.echo(f"Failed {name}: {stderr or e}")
                failed.append(name)
            continue

        if before == after:
            current.append(name)
            continue

        updated.append(name)

        if before is None:
            click.echo(f"{name}: local 'main' created")
            continue

        count = _git(path, "rev-list", "--count", f"{before}..{after}")
        click.echo(f"{name}: {count} new commit(s) on main")

        if verbosity == 1:
            stat = _git(path, "diff", "--stat", before, after)
            click.echo(_indent(stat))
        elif verbosity >= 2:
            diff = _git(path, "diff", "--color=always", before, after)
            click.echo(f"\n{'=' * 70}\n{name}\n{'=' * 70}")
            click.echo(diff)
            click.echo()

    click.echo(
        f"\nSummary: {len(updated)} updated, {len(current)} up to date, "
        f"{len(no_main)} without main, {len(failed)} failed"
    )
    if updated:
        click.echo("Updated: " + ", ".join(updated))
    if no_main:
        click.echo("No main: " + ", ".join(no_main))
    if failed:
        click.echo("Failed: " + ", ".join(failed))

    return not failed


def _indent(text, prefix="    "):
    return "\n".join(prefix + line for line in text.splitlines())


# --------------------------------------------------------------------------------------
# PlatformIO-Specific Building
# --------------------------------------------------------------------------------------


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


# --------------------------------------------------------------------------------------
# Assessment Branching
# --------------------------------------------------------------------------------------


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


# --------------------------------------------------------------------------------------
# Pushing Assessment Branches
# --------------------------------------------------------------------------------------


def _run_git(repo_path, *args):
    return subprocess.run(
        ["git", *args],
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _summarize_changes(repo_path):
    """Return display lines describing what `git add -A && git commit` would include.
    Does not modify the repo or its index.
    """
    lines = []

    # Tracked files (staged and unstaged) compared to the last commit
    diff = _run_git(repo_path, "diff", "HEAD", "--numstat")
    for row in diff.stdout.splitlines():
        added, removed, path = row.split("\t", 2)
        if added == "-":  # git reports binary files as "-\t-"
            lines.append(f"{path} (binary)")
        else:
            lines.append(f"{path} +{added}/-{removed}")

    # New files that `git add -A` would pick up (respects .gitignore)
    untracked = _run_git(repo_path, "ls-files", "--others", "--exclude-standard")
    for path in untracked.stdout.splitlines():
        lines.append(f"{path} (new, untracked)")

    return lines


def push_branches(submission_dir, message, branch_name, dry_run=False):
    """Commit and push all changes in a submission directory to the given branch.
    If there are no changes to commit, the branch is still pushed to origin but no
    commit is created.

    With dry_run=True, nothing is checked out, committed, or pushed; a per-file
    summary of pending changes is printed instead.
    """

    # Confirms a token is resolvable before we start iterating repos
    get_github_token()

    repo_paths = getRepoPaths(submission_dir)

    if dry_run:
        click.echo(f"DRY RUN: pending changes for '{branch_name}' in each student repo")
    else:
        click.echo(
            f"Committing and pushing '{branch_name}' branch to "
            "origin for all student repos..."
        )

    for repo_path in repo_paths:
        repo_name = os.path.basename(repo_path)

        if dry_run:
            click.echo(f"\n{repo_name}:")
            changes = _summarize_changes(repo_path)
            if changes:
                for line in changes:
                    click.echo(f"  {line}")
            else:
                click.echo("  No changes to commit")
            continue

        # else not dry_run

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


# --------------------------------------------------------------------------------------
# Launching Code Editor
# --------------------------------------------------------------------------------------


def launch_editor(editor_cmd: str, target_dir: str):
    parts = editor_cmd.split()

    exe = parts[0]
    if shutil.which(exe) is None:
        raise click.UsageError(f"Editor executable not found: {exe}")

    subprocess.Popen(parts + [target_dir])
