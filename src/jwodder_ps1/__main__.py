from __future__ import annotations
import argparse
from . import __url__, __version__
from .git import git_status
from .info import PromptInfo
from .style import ANSIStyler, BashStyler, ZshStyler


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
        if show_git and (gs := git_status(timeout=args.git_timeout)):
            s = gs.display(style)
        else:
            s = ""
    else:
        s = PromptInfo.get(git=show_git, git_timeout=args.git_timeout).display(style)
    print(s)


if __name__ == "__main__":
    main()
