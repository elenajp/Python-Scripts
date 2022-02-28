
import argparse
from unittest.mock import MagicMock, patch

import github_checker
import pytest
import requests
from github_checker import (check_repositories, count_dependabot_prs,
                            get_bypassers)
from prometheus_client.registry import CollectorRegistry


@pytest.mark.parametrize(
    "fake_pulls, expected_count",
    [
        # No pull requests
        ([], 0),
        # One PR not created by Dependabot
        (
            [
                {
                    "number": 1,
                    "state": "open",
                    "title": "This is a very cool PR",
                    "user": {"login": "toto"},
                },
            ],
            0,
        ),
        # 3 PRs and 2 created by dependabot
        (
            [
                {
                    "number": 448,
                    "state": "open",
                    "title": "maven(deps): bump swagger-request-validator-core from 2.15.1 to 2.25.0 in /copernic",
                    "user": {"login": "dependabot[bot]"},
                },
                {
                    "number": 439,
                    "state": "open",
                    "title": "Reword dependabot commit message prefix",
                    "user": {"login": "A-Ibm"},
                },
                {
                    "number": 198,
                    "state": "open",
                    "title": "Bump spring-boot-starter-parent from 2.1.5.RELEASE to 2.2.5.RELEASE",
                    "user": {"login": "dependabot-preview[bot]"},
                },
            ],
            1,
        ),
    ],
)
def test_count_dependabot_prs(fake_pulls, expected_count):
    mock_session = MagicMock(spec=requests.Session)
    mock_session.get().__enter__().json.return_value = fake_pulls

    assert count_dependabot_prs(mock_session, "fake_repo") == expected_count


@pytest.mark.parametrize(
    "fake_audit_logs, expected_bypassers",
    [
        # If no git logs, no bypass
        ([], {}),
        (
            [
                {
                    "repo": "edgelab/stacks",
                    "action": "protected_branch.policy_override",
                    "branch": "refs/heads/master",
                    "actor": "cyrilgdn",
                    "org": "edgelab",
                },
                {
                    "repo": "edgelab/pigeon",
                    "action": "protected_branch.policy_override",
                    "branch": "refs/heads/master",
                    "actor": "vthiery",
                    "org": "edgelab",
                },
                {
                    "repo": "edgelab/eve",
                    "action": "protected_branch.policy_override",
                    "branch": "refs/heads/master",
                    "actor": "cyrilgdn",
                    "org": "edgelab",
                },
                {
                    "repo": "edgelab/stacks",
                    "action": "protected_branch.policy_override",
                    "branch": "refs/heads/master",
                    "actor": "cyrilgdn",
                    "org": "edgelab",
                },
            ],
            {
                "cyrilgdn": {"edgelab/eve": 1, "edgelab/stacks": 2},
                "vthiery": {"edgelab/pigeon": 1},
            },
        ),
    ],
)
def test_get_bypasses(fake_audit_logs, expected_bypassers):
    mock_session = MagicMock(spec=requests.Session)
    mock_registry = MagicMock(spec=CollectorRegistry)

    mock_session.get().__enter__().json.return_value = fake_audit_logs
    assert get_bypassers(mock_session, mock_registry) == expected_bypassers


@pytest.mark.parametrize(
    "fake_repos, fake_repos_filter, expected_output",
    [
        ([], None, []),
        (
            [
                {
                    "name": "fusion",
                    "visibility": "public",
                    "default_branch": "master",
                    "archived": True,
                },
                {
                    "name": "ops-docs",
                    "visibility": "private",
                    "default_branch": "master",
                    "archived": False,
                },
                {
                    "name": "potato",
                    "visibility": "private",
                    "default_branch": "master",
                    "archived": False,
                },
            ],
            ["fusion", "ops-test", "ops-docs"],
            [
                {
                    "name": "ops-docs",
                }
            ],
        ),
        (
            [
                {
                    "name": "fusion",
                    "visibility": "public",
                    "default_branch": "master",
                    "archived": True,
                },
                {
                    "name": "ops-docs",
                    "visibility": "private",
                    "default_branch": "master",
                    "archived": False,
                },
                {
                    "name": "potato",
                    "visibility": "private",
                    "default_branch": "master",
                    "archived": False,
                },
            ],
            None,
            [
                {
                    "name": "ops-docs",
                },
                {
                    "name": "potato",
                },
            ],
        ),
    ],
)
def test_check_repositories(fake_repos, fake_repos_filter, expected_output):
    mock_session = MagicMock(spec=requests.Session)
    mock_session.get().json.return_value = fake_repos

    args = argparse.Namespace(repos=fake_repos_filter)

    with patch.object(
        github_checker, "get_repo_info", side_effect=lambda _, c: {"name": c["name"]}
    ):
        assert check_repositories(mock_session, args) ==
