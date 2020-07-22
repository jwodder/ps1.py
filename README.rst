Here we have yet another script for Git-aware customization of the command
prompt in Bash and zsh.  Unlike all the other scripts, I wrote this one, so
it's better.

.. image:: screenshot.png

Features:

- lets you know if you have mail in ``$MAIL``
- shows chroot and `virtualenv <https://virtualenv.pypa.io>`_ prompt prefixes
- automatically truncates the current directory path if it gets too long
- shows the status of the current Git repository (see below)
- thoroughly documented and easily customizable
- supports both Bash and zsh


Requirements
============

- Python 3, version 3.5 or higher
- Git, version 1.7.10 or higher
- bash or zsh


Installation & Setup
====================

1. Save `ps1.py <ps1.py>`_ to your computer somewhere (I put my copy at
   ``~/share/ps1.py``)

2. If using Bash, add the following line to the end of your ``~/.bashrc``:

   .. code:: shell

        PROMPT_COMMAND="$PROMPT_COMMAND"'; PS1="$(/usr/bin/python3 ~/share/ps1.py "${PS1_GIT:-}")"'

   If using zsh, add the following to the end of your ``~/.zshrc``:

   .. code:: shell

        precmd_ps1_py() { PS1="$(/usr/bin/python3 ~/share/ps1.py --zsh "${PS1_GIT:-}")" }
        precmd_functions+=( precmd_ps1_py )

   Replace ``/usr/bin/python3`` with the path to your Python 3 interpreter, and
   replace ``~/share/ps1.py`` with the location you saved ``ps1.py`` at as
   appropriate.

3. Open a new shell

4. Enjoy!

5. If the Git integration causes you trouble (either because something breaks
   or just because it's taking too long to run), it can be temporarily disabled
   by running ``PS1_GIT=off`` on the command line.


Usage
=====

::

    python3 ps1.py [<options>] [<git flag>]

``ps1.py`` outputs a single line containing a stylized prompt string for the
current directory.  By default, the stylization is in a format usable in Bash's
``PS1`` variable, though the ``--ansi`` and ``--zsh`` option can be supplied to
change the format.

``ps1.py`` takes a single optional argument.  If this argument is "off", then
the Git integration is disabled.  If it is any other value or not specified,
the Git integration is enabled.

Options
-------

--ansi         Format output for direct display
--bash         Format output for use in Bash's ``PS1`` (default)
--zsh          Format output for use in zsh's ``PS1``
-V, --version  Display version information and exit
-h, --help     Display usage information and exit


Git Status Symbols
==================

When inside a Git repository, a number of symbols showing the current ``HEAD``
and its status are added to the end of the prompt.  Except for the ``@``
separator and the ``HEAD`` itself, individual symbols are omitted when not
relevant.  From left to right, the symbols are:

- ``@`` — separator
- ``+`` (bold light yellow) — Indicates there are stashed changes
- the name of the ``HEAD`` (light green) — the name of the current branch (if
  any), or the name of the currently checked-out tag (if any), or the short
  form of the current commit hash; turns light blue when the repository is in
  detached ``HEAD`` state
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
