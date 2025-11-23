import os

import pandas as pd


def load_roster(csv_path):
    """Load CSV mapping GitHub usernames to student identifiers."""
    df = pd.read_csv(csv_path)
    return dict(zip(df["github_username"], df["identifier"], strict=False))


def getRepoPaths(submission_dir):
    """Returns a list of directories (repos) for an assignment."""
    repo_paths = [
        os.path.join(submission_dir, d)
        for d in os.listdir(submission_dir)
        if os.path.isdir(os.path.join(submission_dir, d))
    ]
    return repo_paths
