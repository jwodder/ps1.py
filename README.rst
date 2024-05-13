|repostatus| |ci-status| |coverage| |pyversions| |license|

.. |repostatus| image:: https://www.repostatus.org/badges/latest/active.svg
    :target: https://www.repostatus.org/#active
    :alt: Project Status: Active — The project has reached a stable, usable
          state and is being actively developed.

.. |ci-status| image:: https://github.com/jwodder/ps1.py/actions/workflows/test.yml/badge.svg
    :target: https://github.com/jwodder/ps1.py/actions/workflows/test.yml
    :alt: CI Status

.. |coverage| image:: https://codecov.io/gh/jwodder/ps1.py/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/jwodder/ps1.py

.. |pyversions| image:: https://img.shields.io/pypi/pyversions/jwodder-ps1.svg
    :target: https://pypi.org/project/jwodder-ps1/

.. |license| image:: https://img.shields.io/github/license/jwodder/ps1.py.svg
    :target: https://opensource.org/licenses/MIT
    :alt: MIT License

`GitHub <https://github.com/jwodder/ps1.py>`_
| `PyPI <https://pypi.org/project/jwodder-ps1/>`_
| `Issues <https://github.com/jwodder/ps1.py/issues>`_

``jwodder-ps1`` is yet another program for Git-aware customization of the
command prompt in Bash and zsh.  Unlike all the others, I wrote this one, so
it's better.

.. image:: https://github.com/jwodder/ps1.py/raw/master/screenshot.png

Features:

- Lets you know if you have mail in ``$MAIL``
- Shows chroot, `virtualenv <https://virtualenv.pypa.io>`_, and `Conda
  <https://conda.io>`_ environment prompt prefixes
- Automatically truncates the current directory path if it gets too long
- Shows the status of the current Git repository (see below)
- Supports both Bash and zsh
- Can optionally output just the Git status, in case you want to combine it
  with your own prompt string


Installation & Setup
====================

``jwodder-ps1`` requires Python 3.9 or higher.  You'll also need a Bash or zsh
shell to set the program up in, and you'll need ``git`` v1.7.10+ installed in
order to get status information about Git repositories.

Install the ``jwodder-ps1`` command by using `pip <https://pip.pypa.io>`_ or
similar (using `pipx <https://pipx.pypa.io>`_ is recommended) to install the
package of the same name from PyPI.

If you use Bash, configure it to use ``jwodder-ps1`` for the prompt by adding
the following line to the end of your ``~/.bashrc``:

.. code:: shell

    PROMPT_COMMAND="$PROMPT_COMMAND"'; PS1="$(jwodder-ps1 "${PS1_GIT:-}")"'

If you use zsh instead, add the following to the end of your ``~/.zshrc``:

.. code:: shell

    precmd_jwodder_ps1() { PS1="$(jwodder-ps1 --zsh "${PS1_GIT:-}")" }
    precmd_functions+=( precmd_jwodder_ps1 )

If you want to use just the Git status portion of the script's output and
combine it with your own prompt string, replace the ``PS1`` assignment with
your desired prompt, with ``$(jwodder-ps1 --git-only "${PS1_GIT:-}")`` inserted
where you want the Git status string.

Depending on how ``jwodder-ps1`` was installed and what the value of your
``PATH`` is, you may have to use the full path to the ``jwodder-ps1``
executable instead.

Once ``jwodder-ps1`` is configured, open a new shell and enjoy!

If the Git integration causes you trouble (either because something breaks or
just because it's taking too long to run), it can be temporarily disabled by
running ``PS1_GIT=off`` on the command line.


Usage
=====

::

    jwodder-ps1 [<options>] [<git flag>]

The ``jwodder-ps1`` command outputs a single line containing a stylized prompt
string for the current directory.  By default, the stylization is in a format
usable in Bash's ``PS1`` variable, though the ``--ansi`` and ``--zsh`` option
can be supplied to change the format.

``jwodder-ps1`` takes a single optional argument.  If this argument is "off",
then the Git integration is disabled.  If it is any other value or not
specified, the Git integration is enabled.

Options
-------

--ansi          Format output for direct display

--bash          Format output for use in Bash's ``PS1`` (default)

-G, --git-only  Only output the Git status string (including leading
                separator); output an empty line if not in a Git repository or
                if "off" is given on the command line

--git-timeout SECONDS
                If running ``git status`` takes longer than the given number of
                seconds (default: 3), disable the Git integration

--no-hostname   Do not include the local hostname in the prompt string

-T THEME, --theme THEME
                Select the theme to use for coloring prompt elements.  The
                available themes are ``dark`` (the default, for use with light
                text on dark backgrounds) and ``light`` (for use with dark text
                on light backgrounds).

--zsh           Format output for use in zsh's ``PS1``

-V, --version   Display version information and exit

-h, --help      Display usage information and exit


Git Status Symbols
==================

When inside a Git repository, a number of symbols showing the current ``HEAD``
and its status are added near the end of the prompt.  Except for the ``@``
separator and the ``HEAD`` itself, individual symbols are omitted when not
relevant.  From left to right, the symbols are:

- ``@`` — separator
- ``+`` (bold light yellow) — Indicates there are stashed changes
- The name of the ``HEAD`` (light green): the name of the current branch (if
  any), or the name of the currently checked-out tag (if any), or the short
  form of the current commit hash.  This is light blue when the repository is
  in a detached ``HEAD`` state.

  This string is truncated if it gets too long.

- ``+n`` (green) — how many commits ``HEAD`` is ahead of upstream
- ``-n`` (red) — how many commits ``HEAD`` is behind upstream
- ``*`` — Indicates whether there are any staged or unstaged changes in the
  working tree:

  - Green: There are staged changes
  - Red: There are unstaged changes
  - Bold light yellow: There are both staged and unstaged changes

- ``+`` (bold red) — Indicates there are untracked files in the working tree
- ``[STATE]`` (magenta) — Shows what activity Git is currently in the middle
  of, if any:

  - ``[BSECT]`` — bisecting
  - ``[CHYPK]`` — cherry-picking
  - ``[MERGE]`` — merging
  - ``[REBAS]`` — rebasing
  - ``[REVRT]`` — reverting

- ``!`` (bold red) — Indicates there are paths with merge conflicts
