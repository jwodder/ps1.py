"""
Yet another bash/zsh prompt script

Here we have yet another script for Git-aware customization of the command
prompt in Bash and zsh.  Unlike all the other scripts, I wrote this one, so
it's better.

Features:

- lets you know if you have mail in ``$MAIL``
- shows chroot, `virtualenv <https://virtualenv.pypa.io>`_, and `Conda
  <https://conda.io>`_ environment prompt prefixes
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

__version__ = "0.6.0.dev1"
__author__ = "John Thorvald Wodder II"
__author_email__ = "ps1@varonathe.org"
__license__ = "MIT"
__url__ = "https://github.com/jwodder/ps1.py"
