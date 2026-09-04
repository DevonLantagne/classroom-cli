# GitHub Classroom CLI for PlatformIO

Python program to assist in grading PlatformIO projects submitted via GitHub Classroom.

You will need the following on your system:
- Python 3.12+
- Git CLI
- GitHub CLI
- VS Code
- PlatformIO Extension for VS Code

# Installation

This cli program is built using Python. This installation guide will help you install Python and then install the `classroom-cli` tool into a virtual environment.

## Install Python and Pipx

> [!NOTE]
> If using MacOS or Linux, replace all instances of `python` with `python3`.

1. Install Python 3.12+ on your system.

    https://www.python.org/downloads/

    During installation, make sure to check "**Add Python to PATH**".

2. Test your Python installation.

    Open a terminal and run the command: `python --version`. It should say something like `Python 3.12.xx`.

3. Install pipx to manage Python packages globally.

    Open a terminal (or use the same one from earlier) and run:

    ```
    python -m pip install --user pipx
    python -m pipx ensurepath
    ```

4. Close the terminal and open a new one for path changes to take effect. Test pipx with by running `pipx --version`.

    `pipx` is the Python tool that will install `classroom-cli` so that the tool's dependencies don't interfere with your system Python.

## Install `classroom-cli`

1. Open a terminal and run:

    ```
    pipx install git+https://github.com/DevonLantagne/classroom-cli
    ```

    This will install `classroom-cli` and its dependencies. You should now be able to run `classroom-cli` from any terminal in any directory.

2. You can test `classroom-cli` by running:

    ```
    classroom-cli --help
    ```

You can now run `classroom-cli` commands in any terminal and directory.

## Updating `classoom-cli`

You can easily update the CLI tool by running:

```
pipx upgrade --spec git+https://github.com/DevonLantagne/classroom-cli classroom-cli
```

## Uninistalling `classroom-cli`

You can uninstall the CLI tool by running:

```
pipx uninstall classroom-cli
```

# Setup

After installing `classroom-cli`, configure the tool by running the configuration command:

```
classroom-cli configure
```

This setup wizard will ask you to set up:

- `ROSTER_PATH`: path to the GitHub Classroom roster file `classroom_roster.csv` to link student names with GitHub users.
- `GH_PATH`: The path to your gh.exe
- `GITHUB_TOKEN`: The token from your GH CLI. Run `gh auth token` in your terminal to show the token.
- `PIO_PATH`: Path to the PlatformIO `pio` command. This is often found in your home folder in the `.platformio` folder.
- `EDITOR`: The editor you want to open for each project (default is VS Code)

# Development

You can clone this repo and install this CLI tool in "editable" mode.
This means that any changes you make to source code will be reflected automatically in the CLI tool commands - no need to reinstall the tool after every change.

## Virtual Environment

Create a virtual environment.

```bash
python -m venv .venv
```

VS Code will likely detect the new venv and ask if you want to activate this for this workspace. Do so.
VS Code will now activate the venv whenever you open this project.

Activate the virtual environment if not already. Then install the cli tool. 
Because the venv is active, the tool's dependencies will be saved to the `.venv` directory instead of the system.

```bash
source .venv/bin/activate
pip install -e .
```

`pip install -e .` will install the CLI tool in editable mode.

## Conda

Clone this repo and configure a virtual environment using `conda`.
Use the Anaconda Prompt for environment setup and testing. In Anaconda Prompt:

```bash
cd <path to this repo>
conda create -n classroom-cli python=3.11
conda activate classroom-cli
pip install -e .
```

If using VS Code you will want to change your default terminal to CMD as this shell will automatically activate the virtual environment whenever a new terminal in VS Code is opened (for this workspace).

> [!NOTE]
> There is probably a way to make a VS Code profile and set CMD as the default terminal for this profile. This is a TODO. 

You are now ready to test the CLI commands inside this environment.

If the `environment.yml` changes, run the following in the environment:

```bash
conda env update --file environment.yml --prune
```
