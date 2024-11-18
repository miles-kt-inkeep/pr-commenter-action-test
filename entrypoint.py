import json
import os
import requests
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


def get_changed_files_dump(sha):
    changed_files = []
    commit = repo.get_commit(sha)
    # Loop through the changed files in the commit
    for file in commit.files:
        if file.filename.startswith("docs/"):  # Filter by docs/** folder
            changed_files.append(file.filename)
    return json.dumps({"changed_files": changed_files})


def main():
    graphql_endpoint = "https://api.management.inkeep.com/graphql"
    # Your GraphQL mutation
    graphql_mutation = """
    mutation CreateSourceSyncJob($sourceId: ID!, $type: SourceSyncJobType! $statusMessage: String!) {
    createSourceSyncJob(input: {sourceId: $sourceId, type: $type}) {
        success
    }
    }
    """
    graphql_query = """
    query source($sourceId: ID!) {
        source(sourceId: $sourceId) {
            displayName
        }
    }
    """
    gh = Github(os.getenv("GITHUB_TOKEN"))
    event = read_json(os.getenv("GITHUB_EVENT_PATH"))
    repo = gh.get_repo(event["repository"]["full_name"])
    sha = event.get("after")  # The commit SHA from the push event
    files_changed_str = get_changed_files_dump(sha)
    source_id = get_actions_input("sourceId")
    api_key = get_actions_input("apiKey")
    # Prepare the JSON payload
    json_payload = {
        "query": graphql_mutation,
        "variables": {
            "sourceId": source_id,
            "type": "INCREMENTAL",
            "statusMessage": files_changed_str,
        },
    }
    query_payload = {
        "query": graphql_query,
        "variables": {"sourceId": source_id},
    }
    # Headers including the Authorization token
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "Imitated-Organization-Alias": "inkeepdev",
    }
    # Make the GraphQL request
    mutation_response = requests.post(
        graphql_endpoint, headers=headers, json=json_payload
    )
    mutation_result = mutation_response.json()
    print(mutation_result)
    query_response = requests.post(
        graphql_endpoint, headers=headers, json=query_payload
    )
    print(query_response.json())
    display_name = query_response.json()["data"]["source"]["displayName"]
    if (
        "data" in mutation_result.keys()
        and "createSourceSyncJob" in mutation_result["data"].keys()
        and mutation_result["data"]["createSourceSyncJob"]["success"] is True
    ):
        pr = find_pr_by_sha(repo, sha)
        if pr is None:
            print(f"No PR found for commit {sha}.")
            return
        new_comment = f""":mag_right::speech_balloon: [Inkeep](https://inkeep.com) AI search and chat service is syncing content for source '{display_name}'"""
        # Check for duplicated comment
        old_comments = [c.body for c in pr.get_issue_comments()]
        if new_comment in old_comments:
            print("This pull request already has a duplicated comment.")
            return
        # Add the comment
        pr.create_issue_comment(new_comment)


if __name__ == "__main__":
    main()
