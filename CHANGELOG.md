v0.7.2 (2024-07-11)
-------------------
- Fix crash when `$MAIL` is set but file is empty

v0.7.1 (2024-05-23)
-------------------
- Fixed support for custom venv prompt prefixes

v0.7.0 (2024-05-13)
-------------------
- The branch name/`HEAD` description is now truncated if it gets too long.
- Add `--theme` option for selecting between dark and light themes
- Add `--no-hostname` option
- Drop support for Python 3.8

v0.6.0 (2024-05-12)
-------------------
- Always open text files in UTF-8
- If Git is not installed, the Git integration will now be automatically
  disabled instead of raising an error
- Require Python 3.8+
- Now available as a package on PyPI

v0.5.0 (2022-07-03)
-------------------
- Add a `--git-timeout` option for disabling the Git integration if `git
  status` takes too long to run

v0.4.0 (2022-02-14)
-------------------
- Support custom virtualenv prompt prefixes

v0.3.0 (2021-10-13)
-------------------
- Support showing Conda environment prompt prefixes

v0.2.2 (2021-07-11)
-------------------
- When inside a `.git` directory, treat it like a bare repository, thereby
  fixing a crash

v0.2.1 (2021-06-03)
-------------------
- Remove some Python 3.6 syntax that snuck in

v0.2.0 (2020-07-24)
-------------------
- [#1] Added an `--ansi` option for outputting raw escape sequences without
  Bash's `\[ ... \]` wrappers
- [#2] When outputting for Bash, backslashes in strings are now escaped
- Added version, author, etc. variables to the top of the file
- Added a `--version` option
- Added support for zsh
- Added a `-G`, `--git-only` option for only outputting the Git status string

v0.1.0 (2018-09-09)
-------------------
Initial release/announcement
