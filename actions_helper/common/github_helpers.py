import logging
import os
import uuid
from http import HTTPStatus
from typing import Sequence
from github import Github, GithubException, Repository

from .utils import _run_process

GIT_REF_PREFIX = "refs/heads/"
BASE_BRANCH_REF = f"{GIT_REF_PREFIX}master"
FEATURE_BRANCH_NAME = "feature/automatic-dependency-bump"
FEATURE_BRANCH_REF = f"{GIT_REF_PREFIX}{FEATURE_BRANCH_NAME}"

COMMIT_MESSAGE = "chore(poetry): bump dependencies"

GIT_AUTHOR_NAME = "Sir Mergealot"
GIT_AUTHOR_EMAIL = "mergealot@moneymeets.com"


def get_github_repository() -> Repository:
    return Github(login_or_token=os.environ["GITHUB_TOKEN"]).get_repo(
        os.environ["GITHUB_REPOSITORY"],
    )


def check_branch_exists(repo: Repository, branch: str) -> bool:
    try:
        repo.get_branch(branch=branch)
        return True
    except GithubException as e:
        if e.status != HTTPStatus.NOT_FOUND:
            raise
        return False

def modified_files() -> bool:
    return bool(_run_process("git diff --quiet", check=False, capture_output=True).returncode)

def checkout_remote_feature_branch_or_create_new_local_branch(branch_exists: bool):
    logging.info(
        "Feature branch exists, checking out" if branch_exists else "Feature branch does not exist, creating it",
    )
    _run_process(f"git checkout {'' if branch_exists else '-b'} {FEATURE_BRANCH_NAME}")

def commit_and_push_changes(branch_exists: bool):
    logging.info(
        "Adding fixup commit to existing branch" if branch_exists else "Adding commit to newly created branch",
    )
    commit_message = f"fixup! {COMMIT_MESSAGE}" if branch_exists else COMMIT_MESSAGE
    _run_process(f"git commit -a -m '{commit_message}'")
    _run_process(f"git push {'' if branch_exists else '-u origin HEAD'}")


def ensure_pull_request_created(repo: Repository, reviewers: Sequence[str]):
    logging.info("Checking for pull requests")
    pr = repo.get_pulls(state="open", head=f"{repo.organization.login}:{FEATURE_BRANCH_REF}")

    if pr.totalCount == 0:
        pull_request = repo.create_pull(
            title="Auto bump dependencies",
            body="This PR was created automatically. Check the updated dependency changes.",
            base=BASE_BRANCH_REF,
            head=FEATURE_BRANCH_REF,
        )

        pull_request.create_review_request(reviewers=reviewers)
        logging.info(f"PR <{pull_request.number}> created, reviewers <{reviewers}>")
    else:
        pull_request, *_ = tuple(pr)
        logging.info(f"Pull request already exists, {pull_request.number}")


def check_and_push_changes():
    if modified_files():
        logging.info("Found modified files, committing changes")
        repository = get_github_repository()
        commit_and_push_changes(branch_exists=check_branch_exists(repository, FEATURE_BRANCH_REF))
        ensure_pull_request_created(repo=repository, reviewers=["IamAbbey"])
    else:
        logging.info("Nothing changed, skipping this step")