"""
Yet another bash/zsh custom prompt script

``jwodder-ps1`` is yet another program for Git-aware customization of the
command prompt in Bash and zsh.  Unlike all the others, I wrote this one, so
it's better.

Features:

- Lets you know if you have mail in ``$MAIL``
- Shows chroot, `virtualenv <https://virtualenv.pypa.io>`_, and `Conda
  <https://conda.io>`_ environment prompt prefixes
- Automatically truncates the current directory path if it gets too long
- Shows the status of the current Git repository
- Supports both Bash and zsh
- Can optionally output just the Git status, in case you want to combine it
  with your own prompt string

Visit <https://github.com/jwodder/ps1.py> for more information.
"""

__version__ = "0.7.2"
__author__ = "John Thorvald Wodder II"
__author_email__ = "ps1@varonathe.org"
__license__ = "MIT"
__url__ = "https://github.com/jwodder/ps1.py"
