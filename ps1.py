#!/usr/bin/python3
"""
Yet another bash/zsh prompt script

Here we have yet another script for Git-aware customization of the command
prompt in Bash and zsh.  Unlike all the other scripts, I wrote this one, so
it's better.

Features:

- lets you know if you have mail in ``$MAIL``
- shows chroot and `virtualenv <https://virtualenv.pypa.io>`_ prompt prefixes
- automatically truncates the current directory path if it gets too long
- shows the status of the current Git repository
- thoroughly documented and easily customizable
- supports both Bash and zsh
- can optionally output just the Git status, in case you want to combine it
  with your own prompt string

Visit <https://github.com/jwodder/ps1.py> for more information.


Installation & Setup
====================

1. Save this script to your computer somewhere (I put my copy at
   ``~/share/ps1.py``)

2. If using Bash, add the following line to the end of your ``~/.bashrc``:

   .. code:: shell

        PROMPT_COMMAND="$PROMPT_COMMAND"'; PS1="$(/usr/bin/python3 ~/share/ps1.py "${PS1_GIT:-}")"'

   If using zsh, add the following to the end of your ``~/.zshrc``:

   .. code:: shell

        precmd_ps1_py() { PS1="$(/usr/bin/python3 ~/share/ps1.py --zsh "${PS1_GIT:-}")" }
        precmd_functions+=( precmd_ps1_py )

   If you want to use just the Git status portion of the script's output and
   combine it with your own prompt string, replace the ``PS1`` assignment with
   your desired prompt, with ``$(/usr/bin/python3 ~/share/ps1.py --git-only
   "${PS1_GIT:-}")`` inserted where you want the Git status string.

   Replace ``/usr/bin/python3`` with the path to your Python 3 interpreter, and
   replace ``~/share/ps1.py`` with the location you saved ``ps1.py`` at as
   appropriate.

3. Open a new shell

4. Enjoy!

5. If the Git integration causes you trouble (either because something breaks
   or just because it's taking too long to run), it can be temporarily disabled
   by running ``PS1_GIT=off`` on the command line.
"""

__version__      = '0.2.2'
__author__       = 'John T. Wodder II'
__author_email__ = 'ps1@varonathe.org'
__license__      = 'MIT'
__url__          = 'https://github.com/jwodder/ps1.py'

import argparse
from   enum       import Enum
import os
from   pathlib    import Path, PurePath
import re
import socket
from   subprocess import CalledProcessError, DEVNULL, check_output
from   types      import SimpleNamespace

#: Default maximum display length of the path to the current working directory
MAX_CWD_LEN = 30

class Color(Enum):
    """
    An enum of the supported foreground colors.  Each color's value equals its
    xterm number.
    """

    RED           = 1
    GREEN         = 2
    YELLOW        = 3
    BLUE          = 4
    MAGENTA       = 5
    CYAN          = 6
    LIGHT_RED     = 9
    LIGHT_GREEN   = 10
    LIGHT_YELLOW  = 11
    LIGHT_BLUE    = 12
    LIGHT_MAGENTA = 13
    LIGHT_CYAN    = 14

    def asfg(self):
        """
        Return the ANSI SGR parameter for setting the color as the foreground
        color
        """
        c = self.value
        return c + 30 if c < 8 else c + 82


class BashStyler:
    """ Class for escaping & styling strings for use in Bash's PS1 variable """

    #: The actual prompt symbol to add at the end of the output, just before a
    #: final space character
    prompt_suffix = r'\$'

    def __call__(self, s, fg=None, bold=False):
        r"""
        Return the string ``s`` escaped for use in a PS1 variable.  If ``fg``
        is non-`None`, the string will be wrapped in the proper escape
        sequences to display it as the given foreground color.  If ``bold`` is
        true, the string will be wrapped in the proper escape sequences to
        display it bold.  All escape sequences are wrapped in ``\[ ... \]`` so
        that they may be used in a PS1 variable.

        :param str s: the string to stylize
        :param Color fg: the foreground color to stylize the string with
        :param bool bold: whether to stylize the string as bold
        """
        s = self.escape(s)
        if fg is not None:
            s = r'\[\e[{}{}m\]{}\[\e[0m\]'.format(
                fg.asfg(),
                ';1' if bold else '',
                s,
            )
        elif bold:
            s = r'\[\e[1m\]{}\[\e[0m\]'.format(s)
        return s

    def escape(self, s):
        """
        Escape characters in the string ``s`` that have special meaning in a
        PS1 variable
        """
        return s.replace('\\', r'\\')


class ANSIStyler:
    """ Class for styling strings for display immediately in the terminal """

    #: The actual prompt symbol to add at the end of the output, just before a
    #: final space character
    prompt_suffix = '$'

    def __call__(self, s, fg=None, bold=False):
        r"""
        Stylize the string ``s`` with ANSI escape sequences.  If ``fg`` is
        non-`None`, the string will be stylized with the given foreground
        color.  If ``bold`` is true, the string will be stylized bold.

        :param str s: the string to stylize
        :param Color fg: the foreground color to stylize the string with
        :param bool bold: whether to stylize the string as bold
        """
        if fg is not None:
            s = '\033[{}{}m{}\033[0m'.format(fg.asfg(), ';1' if bold else '', s)
        elif bold:
            s = '\033[1m{}\033[0m'.format(s)
        return s


class ZshStyler:
    """ Class for escaping & styling strings for use in zsh's PS1 variable """

    #: The actual prompt symbol to add at the end of the output, just before a
    #: final space character
    prompt_suffix = '%#'

    def __call__(self, s, fg=None, bold=False):
        """
        Return the string ``s`` escaped for use in a zsh PS1 variable.  If
        ``fg`` is non-`None`, the string will be wrapped in the proper escape
        sequences to display it as the given foreground color.  If ``bold`` is
        true, the string will be wrapped in the proper escape sequences to
        display it bold.

        :param str s: the string to stylize
        :param Color fg: the foreground color to stylize the string with
        :param bool bold: whether to stylize the string as bold
        """
        s = self.escape(s)
        if bold:
            s = '%B{}%b'.format(s)
        if fg is not None:
            s = '%F{{{}}}{}%f'.format(fg.value, s)
        return s

    def escape(self, s):
        return s.replace('%', '%%')


def main():
    parser = argparse.ArgumentParser(
        description='Yet another bash/zsh prompt script.  '
                    'Visit <{}> for more information.'.format(__url__)
    )
    parser.add_argument(
        '--ansi',
        action = 'store_const',
        dest   = 'stylecls',
        const  = ANSIStyler,
        help   = 'Format prompt for direct display',
    )
    parser.add_argument(
        '--bash',
        action = 'store_const',
        dest   = 'stylecls',
        const  = BashStyler,
        help   = "Format prompt for Bash's PS1 (default)",
    )
    parser.add_argument(
        '-G', '--git-only',
        action = 'store_true',
        help   = 'Only output the Git portion of the prompt',
    )
    parser.add_argument(
        '--zsh',
        action = 'store_const',
        dest   = 'stylecls',
        const  = ZshStyler,
        help   = "Format prompt for zsh's PS1",
    )
    parser.add_argument(
        '-V', '--version',
        action  = 'version',
        version = '%(prog)s {}'.format(__version__),
    )
    parser.add_argument(
        'git_flag',
        nargs = '?',
        help  = 'Set to "off" to disable Git integration'
    )
    args = parser.parse_args()
    show_git = args.git_flag != "off"
    # Stylizing & escaping callable:
    style = (args.stylecls or BashStyler)()
    if args.git_only:
        s = show_git_status(style) if show_git else ''
    else:
        s = show_prompt_string(style, show_git=show_git)
    print(s)

def show_prompt_string(style, show_git=True):
    """
    Construct & return a complete prompt string for the current environment
    """

    # The beginning of the prompt string:
    PS1 = ''

    # If the $MAIL file is nonempty, show the string "[MAIL]":
    try:
        if Path(os.environ['MAIL']).stat().st_size > 0:
            PS1 += style('[MAIL] ', fg=Color.CYAN, bold=True)
    except (KeyError, FileNotFoundError):
        pass

    # Show the chroot we're working in (if any):
    debian_chroot = cat(Path('/etc/debian_chroot'))
    if debian_chroot:
        PS1 += style('[{}] '.format(debian_chroot), fg=Color.BLUE, bold=True)

    # If we're inside a Python virtualenv, show the basename of the virtualenv
    # directory.  (Note: As of virtualenv v20.0.27, we can't support custom
    # virtualenv prompt prefixes, as virtualenv does not export the relevant
    # information to the environment.)
    if 'VIRTUAL_ENV' in os.environ:
        PS1 += style('({0.name}) '.format(Path(os.environ['VIRTUAL_ENV'])))

    # Show the username of the current user.  I know who I am, so I don't need
    # to see this, but the code is left in here as an example in case you want
    # to enable it.
    #PS1 += style(os.getlogin(), fg=Color.LIGHT_GREEN)

    # Separator:
    #PS1 += style('@')

    # Show the current hostname:
    PS1 += style(socket.gethostname(), fg=Color.LIGHT_RED)

    # Separator:
    PS1 += style(':')

    # Show the path to the current working directory:
    PS1 += style(cwdstr(), fg=Color.LIGHT_CYAN)

    # If we're in a Git repository, show its status.  This can be disabled
    # (e.g., in case of breakage or slowness) by passing "off" as the script's
    # first argument.
    if show_git:
        PS1 += show_git_status(style)

    # The actual prompt symbol at the end of the prompt:
    PS1 += style.prompt_suffix + ' '

    # If your terminal emulator supports it, it's also possible to set the
    # title of the terminal window by emitting "\[\e]0;$TITLE\a\]" somewhere in
    # the prompt.  Here's an example that sets the title to `username@host`:
    #PS1 += r'\[\e]0;{}@{}\a\]'.format(os.getlogin(), socket.gethostname())

    return PS1


def show_git_status(style):
    """
    Returns the portion of the prompt string (including the leading separator)
    dedicated to showing the status of the current Git repository.  If we are
    not in a Git repository, returns the empty string.
    """
    gs = git_status()
    if gs is None:
        return ''
    # Start building the status string with the separator:
    p = style('@')
    if not gs.bare and gs.stashed:
        # We have stashed changes:
        p += style('+', fg=Color.LIGHT_YELLOW, bold=True)
    # Show HEAD; color changes depending on whether it's detached:
    head_color = Color.LIGHT_BLUE if gs.detached else Color.LIGHT_GREEN
    p += style(gs.head, fg=head_color)
    if gs.ahead:
        # Show commits ahead of upstream:
        p += style('+{}'.format(gs.ahead), fg=Color.GREEN)
        if gs.behind:
            # Ahead/behind separator:
            p += style(',')
    if gs.behind:
        # Show commits behind upstream:
        p += style('-{}'.format(gs.behind), fg=Color.RED)
    if not gs.bare:
        # Show staged/unstaged status:
        if gs.staged and gs.unstaged:
            p += style('*', fg=Color.LIGHT_YELLOW, bold=True)
        elif gs.staged:
            p += style('*', fg=Color.GREEN)
        elif gs.unstaged:
            p += style('*', fg=Color.RED)
        #else: Show nothing
        if gs.untracked:
            # There are untracked files:
            p += style('+', fg=Color.RED, bold=True)
        if gs.state is not None:
            # The repository is in the middle of something special:
            p += style('[' + gs.state.value + ']', fg=Color.MAGENTA)
        if gs.conflict:
            # There are conflicted files:
            p += style('!', fg=Color.RED, bold=True)
    return p

def cwdstr():
    """
    Show the path to the current working directory.  If the directory is at or
    under :envvar:`HOME`, the path will start with ``~/``.  The path will also
    be truncated to be no more than `MAX_CWD_LEN` characters long.
    """
    # Prefer $PWD to os.getcwd() as the former does not resolve symlinks
    cwd = Path(os.environ.get('PWD') or os.getcwd())
    try:
        cwd = '~' / cwd.relative_to(Path.home())
    except ValueError:
        pass
    return shortpath(cwd)

def shortpath(p: PurePath, max_len=MAX_CWD_LEN):
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
        p = PurePath('…', *p.parts[1+(p.parts[0] == '/'):])
        while len(str(p)) > max_len:
            if len(p.parts) > 2:
                p = PurePath('…', *p.parts[2:])
            else:
                p = PurePath('…', p.parts[1][:max_len-3] + '…')
                assert len(str(p)) <= max_len
    return str(p)


class GitState(Enum):
    """
    Represents the various "in progress" states that a Git repository can be
    in.  The value of each enumeration is a short string for displaying in a
    command prompt.
    """
    REBASE_MERGING  = 'REBAS'
    REBASE_APPLYING = 'REBAS'
    MERGING         = 'MERGE'
    CHERRY_PICKING  = 'CHYPK'
    REVERTING       = 'REVRT'
    BISECTING       = 'BSECT'


def git_status():
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

    If the current directory is *not* in a Git repository, ``git_status()``
    returns `None`.

    This function is based on a combination of Git's ``git-prompt.sh``
    <https://git.io/qD0ykw> and magicmonty's bash-git-prompt
    <https://git.io/v5HSP>.
    """

    git_dir = git('rev-parse', '--git-dir')
    if git_dir is None:
        return None
    git_dir = Path(git_dir)

    gs = SimpleNamespace()
    gs.head = cat(git_dir / 'HEAD')
    if gs.head is None:
        gs.detached = False
    elif gs.head.startswith('ref: '):
        gs.head = re.sub(r'^(ref: )?(refs/heads/)?', '', gs.head)
        gs.detached = False
    else:
        gs.head = git('describe', '--tags', '--exact-match', 'HEAD') or \
                    git('rev-parse', '--short', 'HEAD')
        gs.detached = True

    gs.ahead = gs.behind = None
    gs.bare = git('rev-parse', '--is-bare-repository') == 'true' or \
                git('rev-parse', '--is-inside-work-tree') == 'false'
    # Note: The latter condition above actually means that we're inside a .git
    # directory, but that's similar enough to a bare repo that no one will
    # care.
    if gs.bare:
        delta = git('rev-list', '--count', '--left-right', '@{upstream}...HEAD')
        if delta is not None:
            gs.behind, gs.ahead = map(int, delta.split())
        return gs

    gs.stashed   = git('rev-parse','--verify','--quiet','refs/stash')is not None
    gs.staged    = False
    gs.unstaged  = False
    gs.untracked = False
    gs.conflict  = False
    for line in git('status', '--porcelain', '--branch').splitlines():
        if line.startswith('##'):
            m = re.fullmatch(r'''
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
            ''', line, flags=re.X)
            if m:
                if m.group('ahead') is not None:
                    gs.ahead  = int(m.group('ahead'))
                if m.group('behind') is not None:
                    gs.behind = int(m.group('behind'))
        elif line.startswith('??'):
            gs.untracked = True
        elif not line.startswith('!!'):
            if 'U' in line[:2]:
                gs.conflict = True
            else:
                if line[0] != ' ':
                    gs.staged = True
                if line[1] in 'DM':
                    gs.unstaged = True

    gs.rebase_head = None
    gs.progress    = None
    if (git_dir/'rebase-merge').is_dir():
        gs.state = GitState.REBASE_MERGING
        gs.rebase_head = cat(git_dir/'rebase-merge'/'head-name')
        gs.progress = (
            int(cat(git_dir/'rebase-merge'/'msgnum')),
            int(cat(git_dir/'rebase-merge'/'end')),
        )
    elif (git_dir/'rebase-apply').is_dir():
        gs.state = GitState.REBASE_APPLYING
        if (git_dir/'rebase-apply'/'rebasing').is_file():
            gs.rebase_head = cat(git_dir/'rebase-apply'/'head-name')
        gs.progress = (
            int(cat(git_dir/'rebase-apply'/'next')),
            int(cat(git_dir/'rebase-apply'/'last')),
        )
    elif (git_dir/'MERGE_HEAD').is_file():
        gs.state = GitState.MERGING
    elif (git_dir/'CHERRY_PICK_HEAD').is_file():
        gs.state = GitState.CHERRY_PICKING
    elif (git_dir/'REVERT_HEAD').is_file():
        gs.state = GitState.REVERTING
    elif (git_dir/'BISECT_LOG').is_file():
        gs.state = GitState.BISECTING
    else:
        gs.state = None

    return gs


def git(*args):
    """
    Run a Git command (suppressing stderr) and return its stdout with leading &
    trailing whitespace stripped.  If the command fails, return `None`.
    """
    try:
        return check_output(
            ('git',) + args,
            universal_newlines=True,
            stderr=DEVNULL,
        ).strip()
    except CalledProcessError:
        return None

def cat(path: Path):
    """
    Return the contents of the given file with leading & trailing whitespace
    stripped.  If the file does not exist, return `None`.
    """
    try:
        return path.read_text().strip()
    except FileNotFoundError:
        return None

if __name__ == '__main__':
    main()
