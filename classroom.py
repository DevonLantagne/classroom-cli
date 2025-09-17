import subprocess  # for running shell commands
import os          # for working with directories and paths
import sys         # for exiting gracefully
import click       # for building the CLI with nice commands and arguments
from dotenv import load_dotenv

load_dotenv()  # this loads .env into os.environ

# Replace with your GitHub Classroom organization name
ORG = os.getenv("ORG", "")

def run_cmd(cmd, cwd=None, capture_output=False):
    """
    Run a shell command.
    - cmd: the command string, e.g. 'git pull'
    - cwd: the working directory where the command should run
    - capture_output: if True, capture stdout/stderr so we can log it
    Returns a subprocess.CompletedProcess object
    """
    result = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,      # treat output as text, not bytes
        shell=True,     # run through the shell (so pipes work)
        capture_output=capture_output
    )
    return result


@click.group()
def cli():
    """
    This is the root CLI group. All subcommands (clone, build, flash, push) hang off this.
    Example: 'python classroom.py clone assignment1'
    """
    pass


@cli.command()
@click.argument("assignment")
def clone(assignment):
    """
    Clone or update all repos for a given assignment.
    - assignment: prefix like 'assignment1'
    """
    
    # Make a folder for this assignment
    if not os.path.isdir(assignment):
        os.makedirs(assignment)
    
    # Use GitHub CLI to list all repos in the org as SSH URLs
    cmd = f'gh repo list {ORG} --limit 200 --json name,sshUrl --jq ".[].sshUrl"'
    result = run_cmd(cmd, capture_output=True)

    # Split into lines, filter only repos matching the assignment prefix
    repos = [r.strip() for r in result.stdout.splitlines() if r.startswith("git@")]
    repos = [r for r in repos if assignment in r]

    # Clone new repos or update existing ones
    for repo in repos:
        name = os.path.basename(repo).replace(".git", "")  # e.g. assignment1-alice
        if os.path.isdir(name):
            click.echo(f"Updating {name}...")
            run_cmd("git pull", cwd=name)
        else:
            click.echo(f"Cloning {name}...")
            run_cmd(f"git clone {repo}")


@cli.command()
@click.argument("assignment")
def build(assignment):
    """
    Build all student repos with PlatformIO.
    If build fails, create a build_feedback.txt file in that repo with the error log.
    """
    for dir in os.listdir("."):  # look at everything in the current folder
        if dir.startswith(assignment) and os.path.isdir(dir):  # only repos for this assignment
            click.echo(f"Building {dir}...")
            result = run_cmd("pio run", cwd=dir, capture_output=True)
            if result.returncode != 0:
                # Save build errors into a file for feedback
                log_file = os.path.join(dir, "build_feedback.txt")
                with open(log_file, "w") as f:
                    f.write(result.stdout)
                    f.write(result.stderr)
                click.echo(f"  Build FAILED. Logged to {log_file}")
            else:
                click.echo("  Build SUCCESS")


@cli.command()
@click.argument("assignment")
def flash(assignment):
    """
    Flash each student's repo one by one.
    After flashing, pause so you can test and give feedback.
    Also lets you open the repo in VS Code for review/editing.
    """
    # Gather all repos that match the assignment name
    students = [d for d in os.listdir(".") if d.startswith(assignment) and os.path.isdir(d)]

    for student in students:
        click.echo(f"--- Flashing {student} ---")
        result = run_cmd("pio run -t upload", cwd=student)
        if result.returncode != 0:
            click.echo(f"  Flash FAILED for {student}")
        else:
            click.echo("  Flash SUCCESS")

        # Ask if you want to open the entire repo in VS Code
        if click.confirm("Open repo in VS Code for review?"):
            os.system(f"code {student}")  # opens the whole folder

        # Wait for your input before moving to the next student
        click.prompt("Press Enter for next student", default="", show_default=False)


@cli.command()
@click.argument("student")
def push(student):
    """
    Push a single student's repo back to GitHub with instructor feedback.
    """
    if not os.path.isdir(student):
        click.echo(f"Repo {student} not found")
        sys.exit(1)

    run_cmd("git add .", cwd=student)
    run_cmd('git commit -m "Instructor feedback"', cwd=student)
    run_cmd("git push", cwd=student)
    click.echo(f"Pushed {student}")


@cli.command("push-all")
@click.argument("assignment")
def push_all(assignment):
    """
    Push all repos for an assignment back to GitHub.
    """
    for dir in os.listdir("."):
        if dir.startswith(assignment) and os.path.isdir(dir):
            click.echo(f"Pushing {dir}...")
            run_cmd("git add .", cwd=dir)
            run_cmd('git commit -m "Instructor feedback"', cwd=dir)
            run_cmd("git push", cwd=dir)


if __name__ == "__main__":
    cli()  # hand control to click
