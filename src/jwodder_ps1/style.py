from __future__ import annotations
from enum import Enum
from typing import ClassVar, Protocol


class Color(Enum):
    """
    An enum of the supported foreground colors.  Each color's value equals its
    xterm number.
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


class Styler(Protocol):
    prompt_suffix: ClassVar[str]

    def __call__(self, s: str, fg: Color | None = None, bold: bool = False) -> str: ...


class BashStyler:
    """Class for escaping & styling strings for use in Bash's PS1 variable"""

    #: The actual prompt symbol to add at the end of the output, just before a
    #: final space character
    prompt_suffix: ClassVar[str] = r"\$"

    def __call__(self, s: str, fg: Color | None = None, bold: bool = False) -> str:
        r"""
        Return the string ``s`` escaped for use in a PS1 variable.  If ``fg``
        is non-`None`, the string will be wrapped in the proper escape
        sequences to display it as the given foreground color.  If ``bold`` is
        true, the string will be wrapped in the proper escape sequences to
        display it bold.  All escape sequences are wrapped in ``\[ ... \]`` so
        that they may be used in a PS1 variable.

        :param str s: the string to stylize
        :param Color fg: the foreground color to stylize the string with
        :param bool bold: whether to stylize the string as bold
        """
        s = self.escape(s)
        if fg is not None:
            s = rf"\[\e[{fg.asfg()}{'1' if bold else ''}m\]{s}\[\e[m\]"
        elif bold:
            s = rf"\[\e[1m\]{s}\[\e[m\]"
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

    def __call__(self, s: str, fg: Color | None = None, bold: bool = False) -> str:
        r"""
        Stylize the string ``s`` with ANSI escape sequences.  If ``fg`` is
        non-`None`, the string will be stylized with the given foreground
        color.  If ``bold`` is true, the string will be stylized bold.

        :param str s: the string to stylize
        :param Color fg: the foreground color to stylize the string with
        :param bool bold: whether to stylize the string as bold
        """
        if fg is not None:
            s = f"\x1B[{fg.asfg()}{';1' if bold else ''}m{s}\x1B[m"
        elif bold:
            s = f"\x1B[1m{s}\x1B[m"
        return s


class ZshStyler:
    """Class for escaping & styling strings for use in zsh's PS1 variable"""

    #: The actual prompt symbol to add at the end of the output, just before a
    #: final space character
    prompt_suffix: ClassVar[str] = "%#"

    def __call__(self, s: str, fg: Color | None = None, bold: bool = False) -> str:
        """
        Return the string ``s`` escaped for use in a zsh PS1 variable.  If
        ``fg`` is non-`None`, the string will be wrapped in the proper escape
        sequences to display it as the given foreground color.  If ``bold`` is
        true, the string will be wrapped in the proper escape sequences to
        display it bold.

        :param str s: the string to stylize
        :param Color fg: the foreground color to stylize the string with
        :param bool bold: whether to stylize the string as bold
        """
        s = self.escape(s)
        if bold:
            s = f"%B{s}%b"
        if fg is not None:
            s = f"%F{{{fg.value}}}{s}%f"
        return s

    def escape(self, s: str) -> str:
        return s.replace("%", "%%")
