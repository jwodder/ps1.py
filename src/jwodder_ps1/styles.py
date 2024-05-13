from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Protocol


class Color(Enum):
    """
    An enumeration of the supported foreground colors.  Each color's value
    equals its xterm number.
    """

    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4
    MAGENTA = 5
    CYAN = 6
    LIGHT_RED = 9
    LIGHT_GREEN = 10
    LIGHT_YELLOW = 11
    LIGHT_BLUE = 12
    LIGHT_MAGENTA = 13
    LIGHT_CYAN = 14

    def asfg(self) -> int:
        """
        Return the ANSI SGR parameter for setting the color as the foreground
        color
        """
        c = self.value
        return c + 30 if c < 8 else c + 82


@dataclass
class Style:
    color: Color | None = None
    bold: bool = False

    def as_params(self) -> list[str]:
        params = []
        if self.color is not None:
            params.append(str(self.color.asfg()))
        if self.bold:
            params.append("1")
        return params


class Styler(Protocol):
    prompt_suffix: ClassVar[str]

    def __call__(self, s: str, style: Style) -> str: ...


class BashStyler:
    """Class for escaping & styling strings for use in Bash's PS1 variable"""

    #: The actual prompt symbol to add at the end of the output, just before a
    #: final space character
    prompt_suffix: ClassVar[str] = r"\$"

    def __call__(self, s: str, style: Style) -> str:
        r"""
        Return the string ``s`` escaped for use in a PS1 variable.  If
        ``style.color`` is non-`None`, the string will be wrapped in the proper
        escape sequences to display it as the given foreground color.  If
        ``style.bold`` is true, the string will be wrapped in the proper escape
        sequences to display it bold.  All escape sequences are wrapped in ``\[
        ... \]`` so that they may be used in a PS1 variable.

        :param str s: the string to stylize
        :param Style style: the color & weight to stylize the string with
        """
        s = self.escape(s)
        if params := style.as_params():
            s = rf"\[\e[{';'.join(params)}m\]{s}\[\e[m\]"
        return s

    def escape(self, s: str) -> str:
        """
        Escape characters in the string ``s`` that have special meaning in a
        PS1 variable
        """
        return s.replace("\\", r"\\")


class ANSIStyler:
    """Class for styling strings for display immediately in the terminal"""

    #: The actual prompt symbol to add at the end of the output, just before a
    #: final space character
    prompt_suffix: ClassVar[str] = "$"

    def __call__(self, s: str, style: Style) -> str:
        r"""
        Stylize the string ``s`` with ANSI escape sequences.  If
        ``style.color`` is non-`None`, the string will be stylized with the
        given foreground color.  If ``style.bold`` is true, the string will be
        stylized bold.

        :param str s: the string to stylize
        :param Style style: the color & weight to stylize the string with
        """
        if params := style.as_params():
            s = f"\x1B[{';'.join(params)}m{s}\x1B[m"
        return s


class ZshStyler:
    """Class for escaping & styling strings for use in zsh's PS1 variable"""

    #: The actual prompt symbol to add at the end of the output, just before a
    #: final space character
    prompt_suffix: ClassVar[str] = "%#"

    def __call__(self, s: str, style: Style) -> str:
        """
        Return the string ``s`` escaped for use in a zsh PS1 variable.  If
        ``style.color`` is non-`None`, the string will be wrapped in the proper
        escape sequences to display it as the given foreground color.  If
        ``style.bold`` is true, the string will be wrapped in the proper escape
        sequences to display it bold.

        :param str s: the string to stylize
        :param Style style: the color & weight to stylize the string with
        """
        s = self.escape(s)
        if style.bold:
            s = f"%B{s}%b"
        if style.color is not None:
            s = f"%F{{{style.color.value}}}{s}%f"
        return s

    def escape(self, s: str) -> str:
        return s.replace("%", "%%")


StyleClass = Enum(
    "StyleClass",
    [
        "MAIL",
        "CHROOT",
        "CONDA",
        "VENV",
        "HOST",
        "CWD",
        "GIT_STASHED",
        "GIT_HEAD",
        "GIT_DETACHED",
        "GIT_AHEAD",
        "GIT_BEHIND",
        "GIT_STAGED_UNSTAGED",
        "GIT_STAGED",
        "GIT_UNSTAGED",
        "GIT_UNTRACKED",
        "GIT_STATE",
        "GIT_CONFLICT",
    ],
)

Theme = dict[StyleClass, Style]

DARK_THEME = {
    StyleClass.MAIL: Style(Color.CYAN, bold=True),
    StyleClass.CHROOT: Style(Color.BLUE, bold=True),
    StyleClass.CONDA: Style(Color.LIGHT_GREEN),
    StyleClass.VENV: Style(),
    StyleClass.HOST: Style(Color.LIGHT_RED),
    StyleClass.CWD: Style(Color.LIGHT_CYAN),
    StyleClass.GIT_STASHED: Style(Color.LIGHT_YELLOW, bold=True),
    StyleClass.GIT_HEAD: Style(Color.LIGHT_GREEN),
    StyleClass.GIT_DETACHED: Style(Color.LIGHT_BLUE),
    StyleClass.GIT_AHEAD: Style(Color.GREEN),
    StyleClass.GIT_BEHIND: Style(Color.RED),
    StyleClass.GIT_STAGED_UNSTAGED: Style(Color.LIGHT_YELLOW, bold=True),
    StyleClass.GIT_STAGED: Style(Color.GREEN),
    StyleClass.GIT_UNSTAGED: Style(Color.RED),
    StyleClass.GIT_UNTRACKED: Style(Color.RED, bold=True),
    StyleClass.GIT_STATE: Style(Color.MAGENTA),
    StyleClass.GIT_CONFLICT: Style(Color.RED, bold=True),
}

LIGHT_THEME = DARK_THEME | {
    StyleClass.CONDA: Style(Color.GREEN),
    StyleClass.CWD: Style(Color.BLUE),
    StyleClass.GIT_HEAD: Style(Color.GREEN),
    StyleClass.GIT_DETACHED: Style(Color.BLUE),
}

THEMES = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
}


@dataclass
class Painter:
    styler: Styler
    theme: Theme

    def __call__(self, s: str, klass: StyleClass) -> str:
        return self.styler(s, self.theme[klass])
