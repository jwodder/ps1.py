from __future__ import annotations
from enum import Enum
from pathlib import Path
import re
import subprocess
from types import SimpleNamespace
from .util import cat


class GitState(Enum):
    """
    Represents the various "in progress" states that a Git repository can be
    in.  The value of each enumeration is a short string for displaying in a
    command prompt.
    """

    REBASE_MERGING = "REBAS"
    REBASE_APPLYING = "REBAS"
    MERGING = "MERGE"
    CHERRY_PICKING = "CHYPK"
    REVERTING = "REVRT"
    BISECTING = "BSECT"


def git_status(timeout: float = 3) -> SimpleNamespace | None:
    """
    If the current directory is in a Git repository, ``git_status()`` returns
    an object with the following attributes:

    :var head: a description of the repository's ``HEAD``: either the name of
        the current branch (if any), or the name of the currently checked-out
        tag (if any), or the short form of the current commit hash
    :vartype head: str

    :var detached: `True` iff the repository is in detached ``HEAD`` state
    :vartype detached: bool

    :var ahead: the number of commits by which ``HEAD`` is ahead of
        ``@{upstream}``, or `None` if there is no upstream
    :vartype ahead: int or None

    :var behind: the number of commits by which ``HEAD`` is behind
        ``@{upstream}``, or `None` if there is no upstream
    :vartype behind: int or None

    :var bare: `True` iff the repository is a bare repository
    :vartype bare: bool

    The following attributes are only present when ``bare`` is `False`:

    :var stashed: `True` iff there are any stashed changes
    :vartype stashed: bool

    :var staged: `True` iff there are changes staged to be committed
    :vartype staged: bool

    :var unstaged: `True` iff there are unstaged changes in the working tree
    :vartype unstaged: bool

    :var untracked: `True` iff there are untracked files in the working tree
    :vartype untracked: bool

    :var conflict: `True` iff there are any paths in the working tree with
        merge conflicts
    :vartype conflict: bool

    :var state: the current state of the working tree, or `None` if there are
        no rebases/bisections/etc. currently in progress
    :vartype state: GitState or None

    :var rebase_head: the name of the original branch when rebasing?
    :vartype rebase_head: str or None

    :var progress: when rebasing, the current progress as a ``(current, total)``
        pair
    :vartype progress: tuple(int, int) or None

    If the current directory is *not* in a Git repository, or if the runtime of
    the ``git status`` command exceeds ``timeout``, ``git_status()`` returns
    `None`.

    This function is based on a combination of Git's `git-prompt.sh`__ and
    magicmonty's bash-git-prompt__.

    __ https://github.com/git/git/blob/master/contrib/completion/git-prompt.sh
    __ https://github.com/magicmonty/bash-git-prompt/blob/master/gitstatus.py
    """

    git_dir_str = git("rev-parse", "--git-dir")
    if git_dir_str is None:
        return None
    git_dir = Path(git_dir_str)

    gs = SimpleNamespace()
    gs.head = cat(git_dir / "HEAD")
    if gs.head is None:
        gs.detached = False
    elif gs.head.startswith("ref: "):
        gs.head = re.sub(r"^(ref: )?(refs/heads/)?", "", gs.head)
        gs.detached = False
    else:
        gs.head = git("describe", "--tags", "--exact-match", "HEAD") or git(
            "rev-parse", "--short", "HEAD"
        )
        gs.detached = True

    gs.ahead = gs.behind = None
    gs.bare = (
        git("rev-parse", "--is-bare-repository") == "true"
        or git("rev-parse", "--is-inside-work-tree") == "false"
    )
    # Note: The latter condition above actually means that we're inside a .git
    # directory, but that's similar enough to a bare repo that no one will
    # care.
    if gs.bare:
        delta = git("rev-list", "--count", "--left-right", "@{upstream}...HEAD")
        if delta is not None:
            gs.behind, gs.ahead = map(int, delta.split())
        return gs

    gs.stashed = git("rev-parse", "--verify", "--quiet", "refs/stash") is not None
    gs.staged = False
    gs.unstaged = False
    gs.untracked = False
    gs.conflict = False

    try:
        r = subprocess.run(
            ["git", "status", "--porcelain", "--branch"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None

    for line in r.stdout.strip().splitlines():
        if line.startswith("##"):
            m = re.fullmatch(
                r"""
                \#\#\s*(?:(?:Initial commit|No commits yet) on )?
                (?P<branch>(?:[^\s.]|\.(?!\.))+)
                (?:\.\.\.\S+
                    (?:
                        \s*\[
                            (?:ahead\s*(?P<ahead>\d+))?
                            (?:(?(ahead)[,\s]+)behind\s*(?P<behind>\d+))?
                        \]
                    )?
                )?\s*
            """,
                line,
                flags=re.X,
            )
            if m:
                if m.group("ahead") is not None:
                    gs.ahead = int(m.group("ahead"))
                if m.group("behind") is not None:
                    gs.behind = int(m.group("behind"))
        elif line.startswith("??"):
            gs.untracked = True
        elif not line.startswith("!!"):
            if "U" in line[:2]:
                gs.conflict = True
            else:
                if line[0] != " ":
                    gs.staged = True
                if line[1] in "DM":
                    gs.unstaged = True

    gs.rebase_head = None
    gs.progress = None
    if (git_dir / "rebase-merge").is_dir():
        gs.state = GitState.REBASE_MERGING
        gs.rebase_head = cat(git_dir / "rebase-merge" / "head-name")
        rebase_msgnum = cat(git_dir / "rebase-merge" / "msgnum")
        assert rebase_msgnum is not None
        rebase_end = cat(git_dir / "rebase-merge" / "end")
        assert rebase_end is not None
        gs.progress = (int(rebase_msgnum), int(rebase_end))
    elif (git_dir / "rebase-apply").is_dir():
        gs.state = GitState.REBASE_APPLYING
        if (git_dir / "rebase-apply" / "rebasing").is_file():
            gs.rebase_head = cat(git_dir / "rebase-apply" / "head-name")
        rebase_next = cat(git_dir / "rebase-apply" / "next")
        assert rebase_next is not None
        rebase_last = cat(git_dir / "rebase-apply" / "last")
        assert rebase_last is not None
        gs.progress = (int(rebase_next), int(rebase_last))
    elif (git_dir / "MERGE_HEAD").is_file():
        gs.state = GitState.MERGING
    elif (git_dir / "CHERRY_PICK_HEAD").is_file():
        gs.state = GitState.CHERRY_PICKING
    elif (git_dir / "REVERT_HEAD").is_file():
        gs.state = GitState.REVERTING
    elif (git_dir / "BISECT_LOG").is_file():
        gs.state = GitState.BISECTING
    else:
        gs.state = None

    return gs


def git(*args: str) -> str | None:
    """
    Run a Git command (suppressing stderr) and return its stdout with leading &
    trailing whitespace stripped.  If the command fails, return `None`.
    """
    try:
        return subprocess.run(
            ["git", *args],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return None
