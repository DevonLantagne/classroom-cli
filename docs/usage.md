# Classroom CLI Usage

## Terminology and Organization

`classroom-cli` is a CLI tool and will require you to be mindful of your terminals working directory.
Several commands ask for paths as input arguments - they can be relative or absolute.

|Term|Definition|
|-|-|
|`course-dir`|The directory that will hold all submission directories of the course. Each submission directory will contain all student repositories.|
|`submission-dir`|The directory inside `course_dir` where student repos will be stored. This will share the same name as the general assignment name (not including Term Code).|

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

In the `Permissions` section, add the `Administration` and `Contents` permissions and set them BOTH to `Read and write`.

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
classroom-cli configure
```

Running this will prompt you to set up authentication with GitHub, your class roster, and course details.

> [!WARNING]
> The GitHub Token (a password) will be stored in a plain-text config file and also be briefly exposed when being used. This isn't good practice but will suffice for a single-user safe machine.

Test that the CLI tool can see the roster after configuring by running:

```bash
classroom-cli roster
```


## Creating Assignments

This section shows you how to create an assignment using this CLI tool and thus creating repositories for each student.

### Create a Template Repository

TODO

### Batch-Create Student Repos

TODO

## Cloning Student Assignments

The `clone` command is used to clone all student submission to a `course-dir`/`assignment-name` directory.

```bash
classroom-cli clone --output-dir <course_dir> <assignment_name>
```

This will create a folder in `course_dir` with the name `assignment_name`. 
Inside the `assignment_name` folder will be the student repos.

`--output-dir` is optional and defaults to `.` (the current working directory). If your working directory is your `course-dir`, you do not need to provide `--output-dir`.

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
classroom-cli branch --submission-dir <assigment_dir>
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


### Detailed Assessment

If you want to compile the student's code for testing, run the `build` command.
This will build all student projects (serially).
Failed builds will be noted in the command output.
You will have to manually upload the binaries to your test board.

```bash
classroom-cli build --submission-dir <assigment_dir>
```

Replace `<assigment_dir>` with the directory that contains the student's repos.