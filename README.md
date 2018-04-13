Here we have yet another script for Git-aware customization of the bash command
prompt.  Unlike all the other scripts, I wrote this one, so it's better.

<!-- example screenshots -->
<!-- explanation of symbols -->
<!-- list of features (mail, shortening pwd name, well documented?, etc.) -->


Requirements
============

* Python 3, version 3.5 or higher
* Git
* bash


Installation
============

1. Save `ps1.py` to your computer somewhere (I put my copy at `~/share/ps1.py`)

2. Add the following line to the end of your `~/.bashrc`:

        PROMPT_COMMAND="$PROMPT_COMMAND"'; PS1="$(python3 ~/share/ps1.py "${PS1_GIT:-}")"'

    Replace `~/share/ps1.py` with the location you saved `ps1.py` at as
    appropriate.

3. Open a new shell

4. Enjoy!

5. In case something breaks with the Git integration and prevents you from
   enjoying, the Git integration can be temporarily disabled by running
   `PS1_GIT=off` in bash.
