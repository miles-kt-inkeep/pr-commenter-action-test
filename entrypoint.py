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


def main():

    graphql_endpoint = "https://api.management.inkeep.com/graphql"

    # Your GraphQL mutation
    graphql_mutation = """
    mutation CreateSourceSyncJob($sourceId: ID!, $type: SourceSyncJobType!) {
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

    source_id = get_actions_input("source-id")
    print(source_id)
    print("Direct ENV:", os.getenv("INPUT_SOURCE_ID"))
    print("Direct ENV 2:", os.getenv("INPUT_SOURCE-ID"))
    api_key = get_actions_input("api-key")

    # Prepare the JSON payload
    json_payload = {
        "query": graphql_mutation,
        "variables": {"sourceId": source_id, "type": "INCREMENTAL"},
    }

    query_payload = {
        "query": graphql_query,
        "variables": {"sourceId": source_id},
    }

    # Headers including the Authorization token
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

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
        gh = Github(os.getenv("GITHUB_TOKEN"))
        event = read_json(os.getenv("GITHUB_EVENT_PATH"))
        repo = gh.get_repo(event["repository"]["full_name"])
        sha = event.get("after")  # The commit SHA from the push event

        pr = find_pr_by_sha(repo, sha)
        if pr is None:
            print(f"No PR found for commit {sha}")
            return

        new_comment = f"""![Inkeep Logo](https://storage.googleapis.com/public_inkeep_assetts/inkeep_logo_16h.png) [Inkeep](https://inkeep.com) AI search and chat service is syncing content for source '{display_name}'"""

        # Check for duplicated comment
        old_comments = [c.body for c in pr.get_issue_comments()]
        if new_comment in old_comments:
            print("This pull request already has a duplicated comment.")
            return

        # Add the comment
        pr.create_issue_comment(new_comment)


if __name__ == "__main__":
    main()
