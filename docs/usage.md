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

```
classroom-cli clone --output-dir <course_dir> <assignment_id>
```

This will create a folder in `course_dir` with the name of the assignment slug (`assignment_dir`). Inside this folder will be the student repos with their names from the roster.

## Assessments

Open the `assignment_dir` in VS Code. You will then folders for each student's repo. Note that inside each student's repo is the `.git` folder. VS Code will track ALL of the repos in this one window. In the Source Control panel of VS Code you will see the change log for all student repos. You can now add or edit files in the student repos and make your own commits to their repos. Push each repo to 'submit' feedback to the students (for them to pull down).