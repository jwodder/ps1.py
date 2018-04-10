#!/usr/bin/python3
# TODO:
# - Automatically shorten the prompt if it gets too long
# - Escape backslashes in $USER, $HOSTNAME, $PWD, branch names, etc.
# - Add a command-line option for removing `\[ ... \]` escapes?
# - When rebasing in Git, show rebase head and/or progress?
# - Show relative location when bisecting commits?
# - Set the terminal title? ("\[\e]0;$TITLE\a\]")
from   enum       import Enum
import os
from   pathlib    import Path, PurePath
import re
import socket
from   subprocess import CalledProcessError, DEVNULL, check_output
import sys
from   types      import SimpleNamespace

MAX_CWD_LEN = 30

def colorer(c):
    return lambda txt, bold=False: \
        r'\[\033[{}{}m\]{}\[\033[0m\]'.format(c, ';1' if bold else '', txt)

red     = colorer(31)
green   = colorer(32)
yellow  = colorer(33)
blue    = colorer(34)
magenta = colorer(35)
cyan    = colorer(36)

light_red     = colorer(91)
light_green   = colorer(92)
light_yellow  = colorer(93)
light_blue    = colorer(94)
light_magenta = colorer(95)
light_cyan    = colorer(96)

def main():
    PS1 = ''

    try:
        if Path(os.environ['MAIL']).stat().st_size > 0:
            PS1 += cyan('[MAIL] ', bold=True)
    except (KeyError, FileNotFoundError):
        pass

    debian_chroot = Path('/etc/debian_chroot')
    if debian_chroot.is_file():
        PS1 += blue('[{}] '.format(cat(debian_chroot), bold=True))

    if 'VIRTUAL_ENV' in os.environ:
        # As of v15.1.0, virtualenv does not export the relevant information
        # for custom prompt prefixes.
        PS1 += '({0.name}) '.format(Path(os.environ['VIRTUAL_ENV']))

    #PS1 += light_green(os.getlogin()) + '@'
    PS1 += light_red(socket.gethostname()) + ':' + light_cyan(cwdstr())

    gs = git_status() if sys.argv[1:2] != ["off"] else None
    if gs is not None:
        PS1 += '@'
        if not gs.bare and gs.stashed:
            PS1 += light_yellow('+', bold=True)
        PS1 += (light_blue if gs.detached else light_green)(gs.head)
        if gs.ahead:
            PS1 += green('+{}'.format(gs.ahead))
            if gs.behind:
                PS1 += ','
        if gs.behind:
            PS1 += red('-{}'.format(gs.behind))
        if not gs.bare:
            if gs.staged and gs.unstaged:
                PS1 += light_yellow('*', bold=True)
            elif gs.staged:
                PS1 += green('*')
            elif gs.unstaged:
                PS1 += red('*')
            if gs.untracked:
                PS1 += red('+', bold=True)
            if gs.state is not None:
                PS1 += magenta('[' + gs.state.value + ']')
            if gs.conflict:
                PS1 += red('!', bold=True)

    PS1 += '$ '
    #print(PS1.replace(r'\[', '').replace(r'\]', ''))
    print(PS1)

def cwdstr():
    # Prefer $PWD to os.getcwd() as the former does not resolve symlinks
    cwd = Path(os.environ.get('PWD') or os.getcwd())
    try:
        cwd = '~' / cwd.relative_to(Path.home())
    except ValueError:
        pass
    return shortpath(cwd)

def shortpath(p: PurePath, max_len=MAX_CWD_LEN):
    """
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
    REBASE_MERGING  = 'REBAS'
    REBASE_APPLYING = 'REBAS'
    MERGING         = 'MERGE'
    CHERRY_PICKING  = 'CHPCK'
    REVERTING       = 'REVRT'
    BISECTING       = 'BSECT'


def git_status():
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
    gs.bare = git('rev-parse', '--is-bare-repository') == 'true'
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
    # Based on <https://git.io/v5HSP>:
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
                gs.ahead  = m.group('ahead')
                gs.behind = m.group('behind')
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
    try:
        return check_output(
            ('git',) + args,
            universal_newlines=True,
            stderr=DEVNULL,
        ).strip()
    except CalledProcessError:
        return None

def cat(path):
    try:
        return path.read_text().strip()
    except FileNotFoundError:
        return None

if __name__ == '__main__':
    main()
