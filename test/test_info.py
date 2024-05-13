from __future__ import annotations
import pytest
from jwodder_ps1.git import GitStatus, WorkTreeStatus
from jwodder_ps1.info import PromptInfo
from jwodder_ps1.styles import DARK_THEME, LIGHT_THEME, ANSIStyler, Painter


@pytest.mark.parametrize(
    "info,rendered",
    [
        pytest.param(
            PromptInfo(
                mail=False,
                debian_chroot=None,
                conda_prompt_modifier=None,
                venv_prompt=None,
                hostname="firefly",
                cwdstr="~/work",
                git=None,
            ),
            "\x1B[91mfirefly\x1B[m:\x1B[96m~/work\x1B[m$ ",
            id="simple",
        ),
        pytest.param(
            PromptInfo(
                mail=True,
                debian_chroot="/chroot/jail",
                conda_prompt_modifier="(base) ",
                venv_prompt="venv",
                hostname="firefly",
                cwdstr="~/work",
                git=None,
            ),
            (
                "\x1B[36;1m[MAIL] \x1B[m"
                "\x1B[34;1m[/chroot/jail] \x1B[m"
                "\x1B[92m(base) \x1B[m"
                "(venv) "
                "\x1B[91mfirefly\x1B[m:"
                "\x1B[96m~/work\x1B[m$ "
            ),
            id="full",
        ),
        pytest.param(
            PromptInfo(
                mail=False,
                debian_chroot=None,
                conda_prompt_modifier=None,
                venv_prompt=None,
                hostname="firefly",
                cwdstr="~/work",
                git=GitStatus(
                    head="main",
                    detached=False,
                    ahead=None,
                    behind=None,
                    wkt=WorkTreeStatus(
                        stashed=False,
                        staged=False,
                        unstaged=False,
                        untracked=False,
                        conflict=False,
                        state=None,
                    ),
                ),
            ),
            "\x1B[91mfirefly\x1B[m:\x1B[96m~/work\x1B[m@\x1B[92mmain\x1B[m$ ",
            id="simple-git",
        ),
    ],
)
def test_display_prompt_info_ansi(info: PromptInfo, rendered: str) -> None:
    paint = Painter(ANSIStyler(), DARK_THEME)
    assert info.display(paint) == rendered


def test_display_full_git_prompt_info_ansi_light() -> None:
    info = PromptInfo(
        mail=True,
        debian_chroot="/chroot/jail",
        conda_prompt_modifier="(base) ",
        venv_prompt="venv",
        hostname="firefly",
        cwdstr="~/work",
        git=GitStatus(
            head="main",
            detached=False,
            ahead=None,
            behind=None,
            wkt=WorkTreeStatus(
                stashed=False,
                staged=False,
                unstaged=False,
                untracked=False,
                conflict=False,
                state=None,
            ),
        ),
    )
    paint = Painter(ANSIStyler(), LIGHT_THEME)
    assert info.display(paint) == (
        "\x1B[36;1m[MAIL] \x1B[m"
        "\x1B[34;1m[/chroot/jail] \x1B[m"
        "\x1B[32m(base) \x1B[m"
        "(venv) "
        "\x1B[91mfirefly\x1B[m:"
        "\x1B[34m~/work\x1B[m"
        "@\x1B[32mmain\x1B[m$ "
    )


def test_display_prompt_info_ansi_no_hostname() -> None:
    info = PromptInfo(
        mail=False,
        debian_chroot=None,
        conda_prompt_modifier=None,
        venv_prompt=None,
        hostname="firefly",
        cwdstr="~/work",
        git=None,
    )
    paint = Painter(ANSIStyler(), DARK_THEME)
    assert info.display(paint, hostname=False) == "\x1B[96m~/work\x1B[m$ "
