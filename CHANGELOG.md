v0.3.0 (in development)
-----------------------
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
