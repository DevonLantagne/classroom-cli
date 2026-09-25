# GitHub Classroom CLI for PlatformIO

Python program to assist in grading PlatformIO projects submitted via GitHub.

Version: `0.2.0`

> [!CAUTION]
> ClassroomCLI is under heavy development; use at your own risk.

## Requirements

For all Git/GitHub features:
- Git CLI `git`
- GitHub CLI `gh` (optional - nice for easy authentication)

For easy assessment:
- VS Code (or any editor that can open a folder)

For embedded mass-building features (course-specific):
- PlatformIO Extension for VS Code

One of the following:
- Python 3.12 or later
- The `uv` Python package manager tool

See *Installation* below for the differences in installation methods.


# Installation

This cli program is built using Python.
This installation guide will help you install the `classroom-cli` tool onto your system.

There are several ways to install a Python CLI tool.
Both methods create a virtual environment on your system and installs dependencies there to prevent contaminating your system Python 
This guide suggests two methods:

- [`uv`](https://docs.astral.sh/uv/) - a tool that manages Python interpreters, packages, and environments. Does not require Python pre-installed on host system (it installs the tool's preferred version of Python inside the virtual environment itself). If you do not have Python on your system, use `uv`.

- `pipx` - Python package (installed with Python) to manage virtual environments and install Python CLI tools. If you already have Python, use this method.

Both of these tools set up a virtual environment specific for the `classroom-cli` tool and adds the entrypoint `clsrm` to your system PATH.
Virtual environment prevent the tool from compromising your system Python dependencies.

> [!CAUTION]
> It is not recommended to use `conda` to install general-purpose CLI tools such as `classroom-cli` since you would have to manually activate the environment to use the tool.


> [!TIP]
> Developers should consider installing `classroom-cli` in editable mode.
> See **Developer Installation** for `uv` or `pipx`.
>
> This requires you to clone the repository source code.
> Editable mode means that any changes you make to source code will be reflected automatically in the CLI tool commands - no need to reinstall the tool after every change.


## Installing with `uv`

Install the `uv` tool on your system if you do not yet have it:

### For Windows:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### For macOS and Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install `classroom-cli` using `uv`:

1. Run the following in your terminal after installing `uv`. You may need to restart your terminal for `uv` to be on your system PATH.

    ```bash
    uv tool install git+https://github.com/DevonLantagne/classroom-cli
    ```

2. You can test `classroom-cli` by running its command `clsrm` with the `--help` flag:

    ```bash
    clsrm --help
    ```


### Updating with `uv`

To update `classroom-cli`:

```bash
uv tool upgrade classroom-cli
```


### Uninstalling with `uv`

```bash
uv tool uninstall classroom-cli
```

### Developer Installation with `uv`

```bash
cd <your code projects folder>
git clone https://github.com/DevonLantagne/classroom-cli.git
cd classroom-cli
uv tool install -e .
```

Editing the command name or dependencies requires a re-install:

```bash
cd classroom-cli
uv tool install -e . --reinstall
```

## Installing with `pipx`

> [!NOTE]
> If using macOS or Linux, replace all instances of `python` with `python3`.

1. Install Python 3.12+ on your system if you don't have it already.

    https://www.python.org/downloads/

    During installation, make sure to enable "**Add Python to PATH**".

2. Test your Python installation.

    Open a terminal and run the command: `python --version`. It should say something like `Python 3.12.xx`.

3. Install `pipx` to manage Python packages.

    Open a terminal (or use the same one from earlier) and run:

    ```bash
    python -m pip install --user pipx
    python -m pipx ensurepath
    ```

4. Close the terminal and open a new one for path changes to take effect.

    Test pipx with by running `pipx --version`.

5. Install `classroom-cli` with `pipx`:

    ```bash
    pipx install git+https://github.com/DevonLantagne/classroom-cli
    ```

6. You can test `classroom-cli` by running its command `clsrm` with the `--help` flag:

    ```bash
    clsrm --help
    ```


### Updating with `pipx`

To update `classroom-cli`:

```bash
pipx upgrade --spec git+https://github.com/DevonLantagne/classroom-cli classroom-cli
```


### Uninstalling with `pipx`

You can uninstall the CLI tool by running:

```bash
pipx uninstall classroom-cli
```

### Developer Installation with `pipx`

```bash
cd <your code projects folder>
git clone https://github.com/DevonLantagne/classroom-cli.git
cd classroom-cli
pipx install -e .
```

Editing the command name or dependencies requires a re-install:

```bash
cd classroom-cli
pipx install -e . --force
```


# Setup and Usage

After installing `classroom-cli`, configure the tool by running the configuration command below.

Read the [usage guide](docs/usage.md) for instructions for configuration and obtaining required information.

```bash
clsrm configure
```
