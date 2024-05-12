from __future__ import annotations
import argparse
from ast import literal_eval
import os
from pathlib import Path, PurePath
import re
import socket
from . import __url__, __version__
from .git import git_status
from .style import ANSIStyler, BashStyler, Color, Styler, ZshStyler
from .util import cat

#: Default maximum display length of the path to the current working directory
MAX_CWD_LEN = 30


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Yet another bash/zsh prompt script."
            f"  Visit <{__url__}> for more information."
        )
    )
    parser.add_argument(
        "--ansi",
        action="store_const",
        dest="stylecls",
        const=ANSIStyler,
        help="Format prompt for direct display",
    )
    parser.add_argument(
        "--bash",
        action="store_const",
        dest="stylecls",
        const=BashStyler,
        help="Format prompt for Bash's PS1 (default)",
    )
    parser.add_argument(
        "-G",
        "--git-only",
        action="store_true",
        help="Only output the Git portion of the prompt",
    )
    parser.add_argument(
        "--git-timeout",
        type=float,
        metavar="SECONDS",
        default=3,
        help=(
            "Disable Git integration if `git status` runtime exceeds timeout"
            "  [default: 3]"
        ),
    )
    parser.add_argument(
        "--zsh",
        action="store_const",
        dest="stylecls",
        const=ZshStyler,
        help="Format prompt for zsh's PS1",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "git_flag", nargs="?", help='Set to "off" to disable Git integration'
    )
    args = parser.parse_args()
    show_git = args.git_flag != "off"
    # Stylizing & escaping callable:
    style = (args.stylecls or BashStyler)()
    if args.git_only:
        if show_git:
            s = show_git_status(style, git_timeout=args.git_timeout)
        else:
            s = ""
    else:
        s = show_prompt_string(style, show_git=show_git, git_timeout=args.git_timeout)
    print(s)


def show_prompt_string(
    style: Styler, show_git: bool = True, git_timeout: float = 3
) -> str:
    """
    Construct & return a complete prompt string for the current environment
    """

    # The beginning of the prompt string:
    PS1 = ""

    # If the $MAIL file is nonempty, show the string "[MAIL]":
    try:
        if Path(os.environ["MAIL"]).stat().st_size > 0:
            PS1 += style("[MAIL] ", fg=Color.CYAN, bold=True)
    except (KeyError, FileNotFoundError):
        pass

    # Show the chroot we're working in (if any):
    debian_chroot = cat(Path("/etc/debian_chroot"))
    if debian_chroot:
        PS1 += style(f"[{debian_chroot}] ", fg=Color.BLUE, bold=True)

    # If a Conda environment is active, show its prompt prefix (which already
    # includes the parentheses and trailing space).
    if "CONDA_PROMPT_MODIFIER" in os.environ:
        # Green like a snake!
        PS1 += style(os.environ["CONDA_PROMPT_MODIFIER"], fg=Color.LIGHT_GREEN)

    # If we're inside a Python virtualenv, show the basename of the virtualenv
    # directory (or the custom prompt prefix, if set).
    if "VIRTUAL_ENV" in os.environ:
        venv = Path(os.environ["VIRTUAL_ENV"])
        prompt = venv.name
        try:
            with (venv / "pyvenv.cfg").open(encoding="utf-8") as fp:
                for line in fp:
                    line = line.strip()
                    if m := re.match(r"^prompt\s*=\s*", line):
                        prompt = line[m.end() :]
                        if re.fullmatch(r'([\x27"]).*\1', prompt):
                            # repr-ized prompt produced by venv
                            try:
                                prompt = literal_eval(prompt)
                            except Exception:
                                pass
                        break
        except FileNotFoundError:
            pass
        PS1 += style(f"({prompt}) ")

    # Show the username of the current user.  I know who I am, so I don't need
    # to see this, but the code is left in here as an example in case you want
    # to enable it.
    # PS1 += style(os.getlogin(), fg=Color.LIGHT_GREEN)

    # Separator:
    # PS1 += style('@')

    # Show the current hostname:
    PS1 += style(socket.gethostname(), fg=Color.LIGHT_RED)

    # Separator:
    PS1 += style(":")

    # Show the path to the current working directory:
    PS1 += style(cwdstr(), fg=Color.LIGHT_CYAN)

    # If we're in a Git repository, show its status.  This can be disabled
    # (e.g., in case of breakage or slowness) by passing "off" as the script's
    # first argument.
    if show_git:
        PS1 += show_git_status(style, git_timeout=git_timeout)

    # The actual prompt symbol at the end of the prompt:
    PS1 += style.prompt_suffix + " "

    # If your terminal emulator supports it, it's also possible to set the
    # title of the terminal window by emitting "\[\e]0;$TITLE\a\]" somewhere in
    # the prompt.  Here's an example that sets the title to `username@host`:
    # PS1 += fr"\[\e]0;{os.getlogin()}@{socket.gethostname()}\a\]"

    return PS1


def show_git_status(style: Styler, git_timeout: float = 3) -> str:
    """
    Returns the portion of the prompt string (including the leading separator)
    dedicated to showing the status of the current Git repository.  If we are
    not in a Git repository, or if ``git status`` times out, returns the empty
    string.
    """
    gs = git_status(timeout=git_timeout)
    if gs is None:
        return ""
    # Start building the status string with the separator:
    p = style("@")
    if not gs.bare and gs.stashed:
        # We have stashed changes:
        p += style("+", fg=Color.LIGHT_YELLOW, bold=True)
    # Show HEAD; color changes depending on whether it's detached:
    head_color = Color.LIGHT_BLUE if gs.detached else Color.LIGHT_GREEN
    p += style(gs.head, fg=head_color)
    if gs.ahead:
        # Show commits ahead of upstream:
        p += style(f"+{gs.ahead}", fg=Color.GREEN)
        if gs.behind:
            # Ahead/behind separator:
            p += style(",")
    if gs.behind:
        # Show commits behind upstream:
        p += style(f"-{gs.behind}", fg=Color.RED)
    if not gs.bare:
        # Show staged/unstaged status:
        if gs.staged and gs.unstaged:
            p += style("*", fg=Color.LIGHT_YELLOW, bold=True)
        elif gs.staged:
            p += style("*", fg=Color.GREEN)
        elif gs.unstaged:
            p += style("*", fg=Color.RED)
        # else: Show nothing
        if gs.untracked:
            # There are untracked files:
            p += style("+", fg=Color.RED, bold=True)
        if gs.state is not None:
            # The repository is in the middle of something special:
            p += style("[" + gs.state.value + "]", fg=Color.MAGENTA)
        if gs.conflict:
            # There are conflicted files:
            p += style("!", fg=Color.RED, bold=True)
    return p


def cwdstr() -> str:
    """
    Show the path to the current working directory.  If the directory is at or
    under :envvar:`HOME`, the path will start with ``~/``.  The path will also
    be truncated to be no more than `MAX_CWD_LEN` characters long.
    """
    # Prefer $PWD to os.getcwd() as the former does not resolve symlinks
    cwd = Path(os.environ.get("PWD") or os.getcwd())
    try:
        cwd = "~" / cwd.relative_to(Path.home())
    except ValueError:
        pass
    return shortpath(cwd)


def shortpath(p: PurePath, max_len: int = MAX_CWD_LEN) -> str:
    """
    If the filepath ``p`` is too long (longer than ``max_len``), cut off
    leading components to make it fit; if that's not enough, also truncate the
    final component.  Deleted bits are replaced with ellipses.

    >>> shortpath(PurePath('/'))
    '/'
    >>> shortpath(PurePath('~'))
    '~'
    >>> shortpath(PurePath('/var/lib/data'))
    '/var/lib/data'
    >>> shortpath(PurePath('~/.local/lib/data'))
    '~/.local/lib/data'
    >>> shortpath(PurePath('/var/atlassian/applicationdata'))
    '/var/atlassian/applicationdata'
    >>> shortpath(PurePath('/var/atlassian/application-data'))
    '…/atlassian/application-data'
    >>> shortpath(PurePath('/var/atlassian/application-data/jira'))
    '…/application-data/jira'
    >>> shortpath(PurePath('~/var/atlassian/applicationdata'))
    '…/atlassian/applicationdata'
    >>> shortpath(PurePath('~/Photos/Vacation_2000_summer_part_1_funny'))
    '…/Vacation_2000_summer_part_1…'
    """
    assert len(p.parts) > 0
    if len(str(p)) > max_len:
        p = PurePath("…", *p.parts[1 + (p.parts[0] == "/") :])
        while len(str(p)) > max_len:
            if len(p.parts) > 2:
                p = PurePath("…", *p.parts[2:])
            else:
                p = PurePath("…", p.parts[1][: max_len - 3] + "…")
                assert len(str(p)) <= max_len
    return str(p)


if __name__ == "__main__":
    main()
