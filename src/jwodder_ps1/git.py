from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import re
import subprocess
from .styles import Painter
from .styles import StyleClass as SC

#: Default maximum display length of the repository HEAD
MAX_HEAD_LEN = 15


@dataclass
class GitStatus:
    #: A description of the repository's ``HEAD``: either the name of the
    #: current branch (if any), or the name of the currently checked-out tag
    #: (if any), or the short form of the current commit hash
    head: str

    #: `True` iff the repository is in a detached ``HEAD`` state
    detached: bool

    #: The number of commits by which ``HEAD`` is ahead of ``@{upstream}``, or
    #: `None` if there is no upstream
    ahead: int | None

    #: The number of commits by which ``HEAD`` is behind ``@{upstream}``, or
    #: `None` if there is no upstream
    behind: int | None

    #: Status of the repository's worktree; this is non-`None` iff the
    #: repository is not a bare repository
    wkt: WorkTreeStatus | None

    def display(self, paint: Painter) -> str:
        # Start building the status string with the separator:
        p = "@"
        if self.wkt is not None and self.wkt.stashed:
            # We have stashed changes:
            p += paint("+", SC.GIT_STASHED)
        # Show HEAD; color changes depending on whether it's detached:
        p += paint(
            shorthead(self.head), SC.GIT_DETACHED if self.detached else SC.GIT_HEAD
        )
        if self.ahead:
            # Show commits ahead of upstream:
            p += paint(f"+{self.ahead}", SC.GIT_AHEAD)
            if self.behind:
                # Ahead/behind separator:
                p += ","
        if self.behind:
            # Show commits behind upstream:
            p += paint(f"-{self.behind}", SC.GIT_BEHIND)
        if (wkt := self.wkt) is not None:
            # Show staged/unstaged status:
            if wkt.staged and wkt.unstaged:
                p += paint("*", SC.GIT_STAGED_UNSTAGED)
            elif wkt.staged:
                p += paint("*", SC.GIT_STAGED)
            elif wkt.unstaged:
                p += paint("*", SC.GIT_UNSTAGED)
            # else: Show nothing
            if wkt.untracked:
                # There are untracked files:
                p += paint("+", SC.GIT_UNTRACKED)
            if wkt.state is not None:
                # The repository is in the middle of something special:
                p += paint("[" + wkt.state.value + "]", SC.GIT_STATE)
            if wkt.conflict:
                # There are conflicted files:
                p += paint("!", SC.GIT_CONFLICT)
        return p


@dataclass
class WorkTreeStatus:
    #: `True` iff there are any stashed changes
    stashed: bool

    #: `True` iff there are changes staged to be committed
    staged: bool

    #: `True` iff there are unstaged changes in the working tree
    unstaged: bool

    #: `True` iff there are untracked files in the working tree
    untracked: bool

    #: `True` iff there are any paths in the working tree with merge conflicts
    conflict: bool

    #: The current state of the working tree, or `None` if there are no
    #: rebases/bisections/etc. currently in progress
    state: GitState | None

    #: The name of the original branch when rebasing?
    # rebase_head: str | None

    #: When rebasing, the current progress as a ``(current, total)`` pair
    # progress: tuple[int, int] | None


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


def git_status(timeout: float = 3) -> GitStatus | None:
    """
    If the current directory is in a Git repository, ``git_status()`` returns
    a `GitStatus` instance describing the repository's current state.

    If the current directory is not in a Git repository, or if Git is not
    installed, or or if the runtime of the ``git status`` command exceeds
    ``timeout``, ``git_status()`` returns `None`.

    This function is based on a combination of Git's `git-prompt.sh`__ and
    magicmonty's bash-git-prompt__.

    __ https://github.com/git/git/blob/master/contrib/completion/git-prompt.sh
    __ https://github.com/magicmonty/bash-git-prompt/blob/master/gitstatus.py
    """

    try:
        git_dir_str = git("rev-parse", "--git-dir")
    except FileNotFoundError:
        # Git is not installed
        return None
    if git_dir_str is None:
        return None
    git_dir = Path(git_dir_str)

    head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
    if head.startswith("ref: "):
        head = re.sub(r"^(ref: )?(refs/heads/)?", "", head)
        detached = False
    else:
        head2 = git("describe", "--tags", "--exact-match", "HEAD") or git(
            "rev-parse", "--short", "HEAD"
        )
        assert head2 is not None
        head = head2
        detached = True

    ahead: int | None = None
    behind: int | None = None
    bare = (
        git("rev-parse", "--is-bare-repository") == "true"
        or git("rev-parse", "--is-inside-work-tree") == "false"
    )
    # Note: The latter condition above actually means that we're inside a .git
    # directory, but that's similar enough to a bare repo that no one will
    # care.
    if bare:
        delta = git("rev-list", "--count", "--left-right", "@{upstream}...HEAD")
        if delta is not None:
            behind, ahead = map(int, delta.split())
        return GitStatus(
            head=head,
            detached=detached,
            ahead=ahead,
            behind=behind,
            wkt=None,
        )

    stashed = git("rev-parse", "--verify", "--quiet", "refs/stash") is not None
    staged = False
    unstaged = False
    untracked = False
    conflict = False

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
                    ahead = int(m.group("ahead"))
                if m.group("behind") is not None:
                    behind = int(m.group("behind"))
        elif line.startswith("??"):
            untracked = True
        elif not line.startswith("!!"):
            if "U" in line[:2]:
                conflict = True
            else:
                if line[0] != " ":
                    staged = True
                if line[1] in "DM":
                    unstaged = True

    # rebase_head: str | None = None
    # progress: tuple[int, int] | None = None
    if (git_dir / "rebase-merge").is_dir():
        state = GitState.REBASE_MERGING
        # rbdir = git_dir / "rebase-merge"
        # rebase_head = (rbdir / "head-name").read_text(encoding="utf-8").strip()
        # rebase_msgnum = (rbdir / "msgnum").read_text(encoding="utf-8").strip()
        # rebase_end = (rbdir / "end").read_text(encoding="utf-8").strip()
        # progress = (int(rebase_msgnum), int(rebase_end))
    elif (git_dir / "rebase-apply").is_dir():
        state = GitState.REBASE_APPLYING
        # rbdir = git_dir / "rebase-apply"
        # if (rbdir / "rebasing").is_file():
        #     rebase_head = (rbdir / "head-name").read_text(encoding="utf-8").strip()
        # rebase_next = (rbdir / "next").read_text(encoding="utf-8").strip()
        # rebase_last = (rbdir / "last").read_text(encoding="utf-8").strip()
        # progress = (int(rebase_next), int(rebase_last))
    elif (git_dir / "MERGE_HEAD").is_file():
        state = GitState.MERGING
    elif (git_dir / "CHERRY_PICK_HEAD").is_file():
        state = GitState.CHERRY_PICKING
    elif (git_dir / "REVERT_HEAD").is_file():
        state = GitState.REVERTING
    elif (git_dir / "BISECT_LOG").is_file():
        state = GitState.BISECTING
    else:
        state = None

    return GitStatus(
        head=head,
        detached=detached,
        ahead=ahead,
        behind=behind,
        wkt=WorkTreeStatus(
            stashed=stashed,
            staged=staged,
            unstaged=unstaged,
            untracked=untracked,
            conflict=conflict,
            state=state,
            # rebase_head=rebase_head,
            # progress=progress,
        ),
    )


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


def shorthead(head: str, max_len: int = MAX_HEAD_LEN) -> str:
    if len(head) > max_len:
        return head[: max_len - 1] + "…"
    else:
        return head
