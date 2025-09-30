# GitHub Classroom CLI for PlatformIO

Python program to assist in grading PlatformIO projects submitted via GitHub Classroom.

# Installation

This cli program is built using Python. Installation will be different depending on your use-case:

## Easiest: pipx



# Development

Clone this repo and configure a virtual environment using `conda`. Use the Anaconda Prompt for environment setup and testing. In Anaconda Prompt:

```bash
cd <path to this repo>
conda create -n classroom-cli-dev python=3.11
conda activate classroom-cli-dev
pip install -e .
```

If using VS Code you will want to change your default terminal to CMD as this shell will automatically activate the virtual environment whenever a new terminal in VS Code is opened (for this workspace).

> [!NOTE]
> There is probably a way to make a VS Code profile and set CMD as the default terminal for this profile. This is a TODO. 

You are now ready to test the CLI commands inside this environment.

If the `environment.yml` changes, run the following in the environment:

```
conda env update --file environment.yml --prune
```