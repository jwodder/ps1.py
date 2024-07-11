from __future__ import annotations
from ast import literal_eval
from dataclasses import dataclass
import os
from pathlib import Path, PurePath
import re
import socket
from .git import GitStatus, git_status
from .styles import Painter
from .styles import StyleClass as SC

#: Default maximum display length of the path to the current working directory
MAX_CWD_LEN = 30


@dataclass
class PromptInfo:
    #: `True` iff the :envvar:`MAIL` file is nonempty
    mail: bool

    #: The chroot we're working in (if any)
    debian_chroot: str | None

    #: If a Conda environment is active, this is its prompt prefix (including
    #: the parentheses and trailing space)
    conda_prompt_modifier: str | None

    #: If we're inside a Python virtualenv, this is its custom prompt prefix,
    #: if set, (without parentheses) or else the basename of the virtualenv
    #: directory
    venv_prompt: str | None

    hostname: str

    #: The path to the current working directory.  If the directory is at or
    #: under :envvar:`HOME`, the path will start with ``~/``.  The path will
    #: also be truncated to be no more than `MAX_CWD_LEN` characters long.
    cwdstr: str

    git: GitStatus | None

    @classmethod
    def get(cls, git: bool = True, git_timeout: float = 3) -> PromptInfo:
        try:
            mail = os.stat(os.environ["MAIL"]).st_size > 0
        except (KeyError, FileNotFoundError):
            mail = False

        try:
            debian_chroot = (
                Path("/etc/debian_chroot").read_text(encoding="utf-8").strip()
            )
        except FileNotFoundError:
            debian_chroot = None

        conda_prompt_modifier = os.environ.get("CONDA_PROMPT_MODIFIER")

        venv_prompt: str | None
        if (venv_str := os.environ.get("VIRTUAL_ENV")) is not None:
            venv = Path(venv_str)
            venv_prompt = venv.name
            try:
                with (venv / "pyvenv.cfg").open(encoding="utf-8") as fp:
                    for line in fp:
                        line = line.strip()
                        if m := re.match(r"^prompt\s*=\s*", line):
                            venv_prompt = line[m.end() :]
                            if re.fullmatch(r'([\x27"]).*\1', venv_prompt):
                                # repr-ized prompt produced by venv
                                try:
                                    venv_prompt = literal_eval(venv_prompt)
                                except Exception:
                                    pass
                            break
            except FileNotFoundError:
                pass
        else:
            venv_prompt = None

        hostname = socket.gethostname()

        if git:
            gs = git_status(timeout=git_timeout)
        else:
            gs = None

        return cls(
            mail=mail,
            debian_chroot=debian_chroot,
            conda_prompt_modifier=conda_prompt_modifier,
            venv_prompt=venv_prompt,
            hostname=hostname,
            cwdstr=cwdstr(),
            git=gs,
        )

    def display(self, paint: Painter, hostname: bool = True) -> str:
        """
        Construct & return a complete prompt string for the current environment
        """

        # The beginning of the prompt string:
        ps1 = ""

        # If the $MAIL file is nonempty, show the string "[MAIL]":
        if self.mail:
            ps1 += paint("[MAIL] ", SC.MAIL)

        # Show the chroot we're working in (if any):
        if self.debian_chroot is not None:
            ps1 += paint(f"[{self.debian_chroot}] ", SC.CHROOT)

        # If a Conda environment is active, show its prompt prefix:
        if self.conda_prompt_modifier is not None:
            # Green like a snake!
            ps1 += paint(self.conda_prompt_modifier, SC.CONDA)

        # If we're inside a Python virtualenv, show the basename of the
        # virtualenv directory (or the custom prompt prefix, if set).
        if self.venv_prompt is not None:
            ps1 += paint(f"({self.venv_prompt}) ", SC.VENV)

        if hostname:
            # Show the current hostname:
            ps1 += paint(self.hostname, SC.HOST)
            # Separator:
            ps1 += ":"

        # Show the path to the current working directory:
        ps1 += paint(self.cwdstr, SC.CWD)

        # Show Git status information, if any:
        if self.git is not None:
            ps1 += self.git.display(paint)

        # The actual prompt symbol at the end of the prompt:
        ps1 += paint.styler.prompt_suffix + " "

        return ps1


def cwdstr() -> str:
    """
    Show the path to the current working directory.  If the directory is at or
    under :envvar:`HOME`, the path will start with ``~/``.  The path will also
    be truncated to be no more than `MAX_CWD_LEN` characters long.
    """
    # Prefer $PWD to os.getcwd() as the former does not resolve symlinks
    cwd = Path(os.environ.get("PWD") or os.getcwd())
    try:
        cwd = "~" / cwd.relative_to(Path.home())
    except ValueError:
        pass
    return shortpath(cwd)


def shortpath(p: PurePath, max_len: int = MAX_CWD_LEN) -> str:
    """
    If the filepath ``p`` is too long (longer than ``max_len``), cut off
    leading components to make it fit; if that's not enough, also truncate the
    final component.  Deleted bits are replaced with ellipses.
    """
    assert len(p.parts) > 0
    if len(str(p)) > max_len:
        p = PurePath("…", *p.parts[1 + (p.parts[0] == "/") :])
        while len(str(p)) > max_len:
            if len(p.parts) > 2:
                p = PurePath("…", *p.parts[2:])
            else:
                p = PurePath("…", p.parts[1][: max_len - 3] + "…")
                assert len(str(p)) <= max_len
    return str(p)
