from __future__ import annotations
from pathlib import PurePosixPath
import pytest
from jwodder_ps1.info import shortpath


@pytest.mark.parametrize(
    "path,short",
    [
        ("/", "/"),
        ("~", "~"),
        ("/var/lib/data", "/var/lib/data"),
        ("~/.local/lib/data", "~/.local/lib/data"),
        ("/var/atlassian/applicationdata", "/var/atlassian/applicationdata"),
        ("/var/atlassian/application-data", "…/atlassian/application-data"),
        ("/var/atlassian/application-data/jira", "…/application-data/jira"),
        ("~/var/atlassian/applicationdata", "…/atlassian/applicationdata"),
        (
            "~/Photos/Vacation_2000_summer_part_1_funny",
            "…/Vacation_2000_summer_part_1…",
        ),
    ],
)
def test_shortpath(path: str, short: str) -> None:
    assert shortpath(PurePosixPath(path)) == short
