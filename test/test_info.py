from __future__ import annotations
from jwodder_ps1.git import GitStatus, WorkTreeStatus
from jwodder_ps1.info import PromptInfo
from jwodder_ps1.style import ANSIStyler


def test_display_simple_prompt_info_ansi() -> None:
    info = PromptInfo(
        mail=False,
        debian_chroot=None,
        conda_prompt_modifier=None,
        venv_prompt=None,
        hostname="firefly",
        cwdstr="~/work",
        git=None,
    )
    assert info.display(ANSIStyler()) == "\x1B[91mfirefly\x1B[m:\x1B[96m~/work\x1B[m$ "


def test_display_full_prompt_info_ansi() -> None:
    info = PromptInfo(
        mail=True,
        debian_chroot="/chroot/jail",
        conda_prompt_modifier="(base) ",
        venv_prompt="venv",
        hostname="firefly",
        cwdstr="~/work",
        git=None,
    )
    assert info.display(ANSIStyler()) == (
        "\x1B[36;1m[MAIL] \x1B[m"
        "\x1B[34;1m[/chroot/jail] \x1B[m"
        "\x1B[92m(base) \x1B[m"
        "(venv) "
        "\x1B[91mfirefly\x1B[m:"
        "\x1B[96m~/work\x1B[m$ "
    )


def test_display_simple_prompt_info_with_git_ansi() -> None:
    info = PromptInfo(
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
    )
    assert (
        info.display(ANSIStyler())
        == "\x1B[91mfirefly\x1B[m:\x1B[96m~/work\x1B[m@\x1B[92mmain\x1B[m$ "
    )
