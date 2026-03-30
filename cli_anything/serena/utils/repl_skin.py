"""cli-anything REPL Skin -- Unified terminal interface for all CLI harnesses.

Usage:
    from cli_anything.serena.utils.repl_skin import ReplSkin

    skin = ReplSkin("serena", version="1.0.0")
    skin.print_banner()
"""

import os
import sys

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_ITALIC = "\033[3m"
_UNDERLINE = "\033[4m"

_CYAN = "\033[38;5;80m"
_CYAN_BG = "\033[48;5;80m"
_WHITE = "\033[97m"
_GRAY = "\033[38;5;245m"
_DARK_GRAY = "\033[38;5;240m"
_LIGHT_GRAY = "\033[38;5;250m"

_ACCENT_COLORS = {
    "serena":      "\033[38;5;114m",   # green (code/structure)
    "mem0":        "\033[38;5;183m",   # soft purple (memory)
}
_DEFAULT_ACCENT = "\033[38;5;75m"

_GREEN = "\033[38;5;78m"
_YELLOW = "\033[38;5;220m"
_RED = "\033[38;5;196m"
_BLUE = "\033[38;5;75m"
_MAGENTA = "\033[38;5;176m"

_ICON = f"{_CYAN}{_BOLD}*{_RESET}"
_ICON_SMALL = f"{_CYAN}>{_RESET}"

_H_LINE = "-"
_V_LINE = "|"
_TL = "+"
_TR = "+"
_BL = "+"
_BR = "+"


def _strip_ansi(text: str) -> str:
    import re
    return re.sub(r"\033\[[^m]*m", "", text)


def _visible_len(text: str) -> int:
    return len(_strip_ansi(text))


class ReplSkin:
    def __init__(self, software: str, version: str = "1.0.0",
                 history_file: str | None = None):
        self.software = software.lower().replace("-", "_")
        self.display_name = software.replace("_", " ").title()
        self.version = version
        self.accent = _ACCENT_COLORS.get(self.software, _DEFAULT_ACCENT)

        if history_file is None:
            from pathlib import Path
            hist_dir = Path.home() / f".cli-anything-{self.software}"
            hist_dir.mkdir(parents=True, exist_ok=True)
            self.history_file = str(hist_dir / "history")
        else:
            self.history_file = history_file

        self._color = self._detect_color_support()

    def _detect_color_support(self) -> bool:
        if os.environ.get("NO_COLOR"):
            return False
        if os.environ.get("CLI_ANYTHING_NO_COLOR"):
            return False
        if not hasattr(sys.stdout, "isatty"):
            return False
        return sys.stdout.isatty()

    def _c(self, code: str, text: str) -> str:
        if not self._color:
            return text
        return f"{code}{text}{_RESET}"

    def print_banner(self):
        inner = 54

        def _box_line(content: str) -> str:
            pad = inner - _visible_len(content)
            vl = self._c(_DARK_GRAY, _V_LINE)
            return f"{vl}{content}{' ' * max(0, pad)}{vl}"

        top = self._c(_DARK_GRAY, f"{_TL}{_H_LINE * inner}{_TR}")
        bot = self._c(_DARK_GRAY, f"{_BL}{_H_LINE * inner}{_BR}")

        icon = self._c(_CYAN + _BOLD, "*")
        name = self._c(self.accent + _BOLD, self.display_name)
        title = f" {icon}  {name} {self._c(_DARK_GRAY, 'CLI')}"

        ver = f" {self._c(_DARK_GRAY, f'   v{self.version}')}"
        tip = f" {self._c(_DARK_GRAY, '   Type help for commands, quit to exit')}"
        empty = ""

        print(top)
        print(_box_line(title))
        print(_box_line(ver))
        print(_box_line(empty))
        print(_box_line(tip))
        print(bot)
        print()

    def prompt(self, project_name: str = "", modified: bool = False,
               context: str = "") -> str:
        parts = []
        if self._color:
            parts.append(f"{_CYAN}*{_RESET} ")
        else:
            parts.append("> ")

        parts.append(self._c(self.accent + _BOLD, self.software))

        if project_name or context:
            ctx = context or project_name
            mod = "*" if modified else ""
            parts.append(f" {self._c(_DARK_GRAY, '[')}")
            parts.append(self._c(_LIGHT_GRAY, f"{ctx}{mod}"))
            parts.append(self._c(_DARK_GRAY, ']'))

        parts.append(self._c(_GRAY, " > "))
        return "".join(parts)

    def prompt_tokens(self, project_name: str = "", modified: bool = False,
                      context: str = ""):
        tokens = []
        tokens.append(("class:icon", "* "))
        tokens.append(("class:software", self.software))

        if project_name or context:
            ctx = context or project_name
            mod = "*" if modified else ""
            tokens.append(("class:bracket", " ["))
            tokens.append(("class:context", f"{ctx}{mod}"))
            tokens.append(("class:bracket", "]"))

        tokens.append(("class:arrow", " > "))
        return tokens

    def get_prompt_style(self):
        try:
            from prompt_toolkit.styles import Style
        except ImportError:
            return None

        return Style.from_dict({
            "icon": "#5fdfdf bold",
            "software": "#87d787 bold",
            "bracket": "#585858",
            "context": "#bcbcbc",
            "arrow": "#808080",
            "completion-menu.completion": "bg:#303030 #bcbcbc",
            "completion-menu.completion.current": "bg:#87d787 #000000",
            "auto-suggest": "#585858",
            "bottom-toolbar": "bg:#1c1c1c #808080",
            "bottom-toolbar.text": "#808080",
        })

    def success(self, message: str):
        icon = self._c(_GREEN + _BOLD, "[ok]")
        print(f"  {icon} {self._c(_GREEN, message)}")

    def error(self, message: str):
        icon = self._c(_RED + _BOLD, "[err]")
        print(f"  {icon} {self._c(_RED, message)}", file=sys.stderr)

    def warning(self, message: str):
        icon = self._c(_YELLOW + _BOLD, "[warn]")
        print(f"  {icon} {self._c(_YELLOW, message)}")

    def info(self, message: str):
        icon = self._c(_BLUE, "[i]")
        print(f"  {icon} {self._c(_LIGHT_GRAY, message)}")

    def hint(self, message: str):
        print(f"  {self._c(_DARK_GRAY, message)}")

    def section(self, title: str):
        print()
        print(f"  {self._c(self.accent + _BOLD, title)}")
        print(f"  {self._c(_DARK_GRAY, _H_LINE * len(title))}")

    def status(self, label: str, value: str):
        lbl = self._c(_GRAY, f"  {label}:")
        val = self._c(_WHITE, f" {value}")
        print(f"{lbl}{val}")

    def help(self, commands: dict[str, str]):
        self.section("Commands")
        max_cmd = max(len(c) for c in commands) if commands else 0
        for cmd, desc in commands.items():
            cmd_styled = self._c(self.accent, f"  {cmd:<{max_cmd}}")
            desc_styled = self._c(_GRAY, f"  {desc}")
            print(f"{cmd_styled}{desc_styled}")
        print()

    def print_goodbye(self):
        print(f"\n  {_ICON_SMALL} {self._c(_GRAY, 'Goodbye!')}\n")

    def create_prompt_session(self):
        try:
            from prompt_toolkit import PromptSession
            from prompt_toolkit.history import FileHistory
            from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

            style = self.get_prompt_style()
            session = PromptSession(
                history=FileHistory(self.history_file),
                auto_suggest=AutoSuggestFromHistory(),
                style=style,
                enable_history_search=True,
            )
            return session
        except ImportError:
            return None

    def get_input(self, pt_session, project_name: str = "",
                  modified: bool = False, context: str = "") -> str:
        if pt_session is not None:
            from prompt_toolkit.formatted_text import FormattedText
            tokens = self.prompt_tokens(project_name, modified, context)
            return pt_session.prompt(FormattedText(tokens)).strip()
        else:
            raw_prompt = self.prompt(project_name, modified, context)
            return input(raw_prompt).strip()
