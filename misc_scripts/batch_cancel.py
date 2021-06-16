#!/usr/bin/python3
"""
Script for batch cancelling Github Actions CI jobs.
"""

# isort: STDLIB
import itertools
import os
import sys
from getpass import getpass

# isort: THIRDPARTY
from github import Github


def main():
    """
    Main function
    """
    if len(sys.argv) < 4:
        print("USAGE: %s <GITHUB_ORG_OR_USER> <GITHUB_REPO> <PR_USER>" % sys.argv[0])
        print(
            "GITHUB_ORG_OR_USER: Github user or organization in which the repo is located"
        )
        print("GITHUB_REPO: Name of the Github repo")
        print("PR_USER: Name of the user who opened the PR")
        raise RuntimeError("Three positional arguments are required")
    user = sys.argv[1]
    repo = sys.argv[2]
    actions_user = sys.argv[3]

    api_key = os.environ.get("GITHUB_API_KEY")
    if api_key is None:
        api_key = getpass("Github API key: ")

    github = Github(api_key)
    repo = github.get_repo("%s/%s" % (user, repo))
    runs = itertools.chain(
        repo.get_workflow_runs(actor=actions_user, status="queued"),
        repo.get_workflow_runs(actor=actions_user, status="in_progress"),
    )
    for run in runs:
        run.cancel()


if __name__ == "__main__":
    try:
        main()
    except Exception as err:  # pylint: disable=broad-except
        print(err)
        sys.exit(1)
