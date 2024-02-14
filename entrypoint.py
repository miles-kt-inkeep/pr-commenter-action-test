import json
import os

from github import Github


def read_json(filepath):
    with open(filepath, "r") as f:
        return json.load(f)


def get_actions_input(input_name):
    return os.getenv("INPUT_{}".format(input_name).upper())


def load_template(filename):
    template_path = os.path.join(".github/workflows", filename)
    with open(template_path, "r") as f:
        return f.read()


def find_pr_by_sha(repo, sha):
    """Find a PR by commit SHA.

    Parameters:
    - repo: The repository object from PyGithub.
    - sha: The commit SHA to search for in PRs.

    Returns:
    - The pull request object if found, otherwise None.
    """
    prs = repo.get_pulls(state="all")
    for pr in prs:
        if pr.merge_commit_sha == sha:
            return pr
    return None


def main():
    gh = Github(os.getenv("GITHUB_TOKEN"))
    event = read_json(os.getenv("GITHUB_EVENT_PATH"))
    repo = gh.get_repo(event["repository"]["full_name"])
    sha = event.get("after")  # The commit SHA from the push event

    pr = find_pr_by_sha(repo, sha)
    if pr is None:
        print(f"No PR found for commit {sha}")
        return

    new_comment = "Inkeep sync has been started."

    # Check for duplicated comment
    old_comments = [c.body for c in pr.get_issue_comments()]
    if new_comment in old_comments:
        print("This pull request already has a duplicated comment.")
        return

    # Add the comment
    pr.create_issue_comment(new_comment)


if __name__ == "__main__":
    main()
