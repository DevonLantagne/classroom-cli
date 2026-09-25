# Classroom CLI Usage

Before configuring `classroom-cli`, familiarize yourself with some of its terminology and directory layout.


## Terminology and Organization

`classroom-cli` is a CLI tool and will require you to be mindful of your terminal's working directory.
Several commands use the current working directory as "input".

|Term|Definition|
|-|-|
|`course-dir`|**Course Directory.** The directory that will hold all *submission directories* of the course. Each submission directory will contain all student repositories. The name of `course-dir` can be anything. Do not place `course-dir` inside a cloud drive (OneDrive, iCloud, Box, etc.).|
|`submission-dir`|**Submission Directory.** A directory representing an assignment where all student repositories will be stored. This will share the same name as the general assignment name (not including Term Code).|

> [!TIP]
> Consider making your `course-dir` your terminal's working directory.

Assignment repositories will be named in the format: `{TermCode}-{AssignmentName}-{StudentEmailPrefix}`. Example: `AY2027S1-Lab1-Intro-studentEmail`.

The `course-dir` folder structure will look like:

```text
course-dir
├── submission-dir
│   ├── student-repo
│   ├── student-repo
│   └── ....
├── submission-dir
└── ...	
```

As an example:
- The course dir was `BME2310-AY2027S1` (a folder somewhere on your machine)
- The Term Code was `AY2027S1`
- The first lab assignment was named `Lab1-Intro`
- The second lab assignment was named `Lab2-InputOutput`
- There are two students with emails `studentA@school.edu` and `studentB@school.edu`

```text
BME2310-AY2027S1
├── Lab1-Intro
│   ├── AY2027S1-Lab1-Intro-studentA
│   └── AY2027S1-Lab1-Intro-studentB
└── Lab2-InputOutput
    ├── AY2027S1-Lab2-InputOutput-studentA
    └── AY2027S1-Lab2-InputOutput-studentA
```


## Preparation


### GitHub Organization Settings

TODO: Enable Fine-grained PATs


### GitHub Personal Access Token

TODO: token using 'gh' command or generate through personal github account settings:

Settings > Credentials > Fine-grained personal access tokens.

Generate new token.

Give it any name and description for your records.

Set the `Resource owner` to your classroom organization.

Set the expiration date. Consider setting it about a month after the end of the semester.

Set the `Repository access` to `All repositories`.

In the `Permissions` section:
- In the `Repositores` tab add the `Administration` and `Contents` permissions and set them BOTH to `Read and write`.
- In the `Organizations` tab, add the `Members` permission and set to `Read-only`.

Generate the token.

Save this token somewhere safe - it is essentially a password to your GitHub organization with limited control.
You will need this token during setup.


### Course Directory

You will need to make a directory on your local machine to contain all the different assignments, let this be called the `course_dir` directory. 
Inside this directory you will have folders for each assignment.
Inside each assignment folder will be all the student repositories.


### Student Roster

You must procure a roster of students as a `.csv` file with headers "email" and "github_username".
- `email` will be used to name student repos - text before the `@` will be included in the repo name.
- `github_username` is the student's GitHub username.

`classroom-cli` will create student repositories by appending their email prefix to the repository assignment name.

Place this roster file somewhere where it won't move.
You will need its local later (its file path).


### Configuration

The CLI tool has an interactive configuration wizard by running:

```bash
clsrm configure
```

Running this will prompt you to set up authentication with GitHub, your class roster, and course details.

> [!WARNING]
> The GitHub Token (a password) will be stored in a plain-text config file and also be briefly exposed when being used. This isn't good practice but will suffice for a single-user safe machine.

Test that the CLI tool can see the roster after configuring by running:

```bash
clsrm roster
```


## Typical Workflow

For this example:
- We want to make an assignment for a lab activity named "Lab1-Intro".
- Our organization is called "BME-2310"
- We made a folder on our local machine called "msoe_bme_2310" (you must know the full path).

Create a template repo in your organization.
Ensure the repo name ends in `-template` and is also configured as a template repository in its settings page.
We would make a template repo named `Lab1-Intro-template`.

Confirm the template is valid:

```bash
clsrm show-templates
```

Now create the repos for each student:

```bash
clsrm create-assignment Lab1-Intro-template
```

You can also use the `--dry-run` option to see a 'what would happen' view of the command:

```bash
clsrm create-assignment --dry-run Lab1-Intro-template
```

After students submit their work by committing and pushing to github, clone them to your machine.

Change working directory into your `msoe_bme_2310` folder.

```bash
clsrm clone Lab1-Intro
```

This creates a folder in `msoe_bme_2310` titled `Lab1-Intro`. CD into it:

```bash
cd Lab1-Intro
```

We CD into the assignment directory because now we don't need to use the `--submission-dir` flag for the assignment-level commands.

Optional: you can build all repositories to check if they actually build. This uses PlatformIO.

```bash
clsrm build
```

To begin the assessment process, create an `assessment` branch (the default name) in all of the repositories:

```bash
clsrm branch
```

The repositories cloned to your machine now have the `assessment` branch checked-out.
Any edits you make in their repos will not be applied to their `main` branch.
You can also add new files to their repo.

To view all repositories in VS Code (or whatever editor you configured):

```bash
clsrm open-all
```

> [!IMPORTANT]
> `open-all` is only really good for viewing and editing source code.
> Because the working directory is one above the actual repo, some build commands may not work.

After making edits and providing feedback (perhaps by adding a `feedback.md` file to their repo), you can mass-commit and push all repos:

```bash
clsrm push
```

This also has a `--dry-run` flag to see what edits have been made and what will be committed:

```bash
clsrm push --dry-run
```

## Creating Assignments

This section shows you how to create an assignment using this CLI tool and thus creating repositories for each student.

### Create a Template Repository

TODO

### Batch-Create Student Repos

```bash
clsrm create-assignment <template repo name>
```

## Cloning Student Assignments

The `clone` command is used to clone all student submission to a `course-dir`/`assignment-name` directory.

```bash
clsrm clone --output-dir <course_dir> <assignment_name>
```

This will create a folder in `course_dir` with the name `assignment_name`. 
Inside the `assignment_name` folder will be the student repos.

`--output-dir` is optional and defaults to `.` (the current working directory).
If your working directory is your `course-dir`, you do not need to provide `--output-dir`.

> [!IMPORTANT]
> `assignment_name` must match that of the created repositories from the naming convention:
>
> `TermCode-AssignmentName-studentPrefix`


## Preparing Repos for Assessment

Before making changes to student repos, it is advised to create an assessment branch in their Git history.
This prevents issues for students that forget to push their last commit if an evaluator makes a commit on their older version of code.
Students will need to be instructed on how to view a different branch.

The `classroom-cli` tool has a command to create these assessment branches for all repos for an assignment.
After the branches are created, the assessment branch will be checked out. 
This keeps the `main` branch in the student's control and makes any edits made by the evaluator only applied to the assessment branch.

```bash
clsrm branch --submission-dir <assignment_dir>
```

Replace `<assignment_dir>` with the path to the assignment folder (submission folder) that contains all the student repos.


## Assessments

Note that inside each student's repo is the `.git` folder.
VS Code will track ALL of the repos in this one window.
In the Source Control panel of VS Code you will see the change log for all student repos.
You can now add or edit files in the student repos and make your own commits to their repos.
Push each repo to 'submit' feedback to the students (for them to pull down).


### Quick Assessment

If you only want to read source code and not compile, you can open the `assignment_dir` in VS Code.
All subfolders (student submissions) will be viewed as subfolders in the VS Code workspace.
Git only tracks files in its respective repo.

You can use the command:

```bash
clsrm open-all --submission-dir <assignment_dir>
```


### Detailed Assessment

If you want to compile the student's code for testing, run the `build` command.
This will build all student projects (serially).
Failed builds will be noted in the command output.
You will have to manually upload the binaries to your test board.

```bash
clsrm build --submission-dir <assignment_dir>
```

Replace `<assignment_dir>` with the directory that contains the student's repos.