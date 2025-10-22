# Classroom CLI Usage

## Preparation

### Course Directory

You will likely want to make a directory on your local machine to contain all the different assignments, let this be called the `course_dir` directory. Inside this directory you will have folders for each GitHub Classroom assignment. Inside each assignment folder will be all the student repositories.

### Student Roster

Download the student roster from GitHub Classroom. This will help `classroom-cli` prepend the student names to their repos when the repos are cloned.

Place this roster file in the classroom-cli's root directory.

## Cloning Student Assignments

First you will need the assignment ID. There are several options to get this ID:

- **Web**: Visit your assignment on GitHub Classroom's website, clicking the `Download` dropdown in the top right, selecting the `Student Repositories` tab, and getting the number after the `-a` flag in the command.

- **gh CLI**: From a terminal run: `gh classroom assignments`. If you have more than one GitHub classroom you will be prompted to select the classroom. The command will then display all the assignments and their IDs.

Now we can clone the student's submissions:

```bash
classroom-cli clone --output-dir <course_dir> <assignment_id>
```

This will create a folder in `course_dir` with the name of the assignment slug (`assignment_dir`). Inside this folder will be the student repos with their names from the roster.

## Preparing Repos for Assessment

Before making changes to student repos, it is advised to create an assessment branch in their Git history. This prevents issues for students that forget to push their last commit if an evaluator makes a commit on their older version of code. Students will need to be instructed on how to view a different branch.

The `classroom-cli` tool has a command to create these assessment branches for all repos for an assignment. After the branches are created, the assessment branch will be checked out. This keeps the `main` branch in the student's control and makes any edits made by the evaluator only applied to the assessment branch.

```bash
classroom-cli branch --submission-dir <assigment_dir>
```

Replace `<assignment_dir>` with the path to the assignment folder (submission folder) that contains all the student repos.

## Assessments

Note that inside each student's repo is the `.git` folder. VS Code will track ALL of the repos in this one window. In the Source Control panel of VS Code you will see the change log for all student repos. You can now add or edit files in the student repos and make your own commits to their repos. Push each repo to 'submit' feedback to the students (for them to pull down).

### Quick Assessment

If you only want to read source code and not compile, you can open the `assignment_dir` in VS Code. All subfolders (student submissions) will be viewed as subfolders in the VS Code workspace. Git only tracks files in its respective repo.

### Detailed Assessment

If you want to compile the student's code for testing, run the `build` command. This will build all student projects (serially). Failed builds will be noted in the command output. You will have to manually upload the binaries to your test board.

```bash
classroom-cli build --submission-dir <assigment_dir>
```

Replace `<assigment_dir>` with the directory that contains the student's repos.