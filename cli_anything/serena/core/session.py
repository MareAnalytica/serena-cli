"""Session management for serena CLI.

Maintains operational state across CLI commands:
- Active project path
- Last operation result for reference
"""

import os
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Session:
    """Serena CLI session state.

    Tracks the active project path and last result.
    """

    project_path: str = ""
    last_result: Optional[dict] = None

    def __post_init__(self):
        if not self.project_path:
            self.project_path = os.environ.get("SERENA_PROJECT", os.getcwd())

    def status(self) -> dict:
        """Get session status as a dict."""
        return {
            "project_path": self.project_path,
            "serena_available": bool(os.popen("which uvx").read().strip()),
        }
