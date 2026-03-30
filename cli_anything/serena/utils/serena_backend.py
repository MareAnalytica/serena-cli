"""Serena MCP client wrapper -- communicates with Serena via stdio.

Serena is an LSP-based MCP server providing structural code intelligence:
symbol navigation, cross-codebase refactoring, and semantic understanding.

Server command:
    uvx serena start-mcp-server --project /path/to/project

No required environment variables -- Serena auto-manages language servers.
"""

import asyncio
import json
import os
import shutil
from typing import Any, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


DEFAULT_SERVER_CMD = "uvx"


def _build_server_args(project_path: str) -> list[str]:
    """Build server args for the Serena MCP server."""
    return [
        "serena",
        "start-mcp-server",
        "--project",
        project_path,
    ]


def _build_env() -> dict[str, str]:
    """Build environment variables for the MCP server subprocess."""
    env = dict(os.environ)
    for key in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE"):
        if key not in env:
            cert_path = "/etc/ssl/certs/ca-certificates.crt"
            if os.path.exists(cert_path):
                env[key] = cert_path
    return env


def is_available() -> tuple[bool, str]:
    """Check if Serena MCP server prerequisites are available."""
    if not shutil.which("uvx"):
        return (
            False,
            "uvx not found. Install uv from https://docs.astral.sh/uv/\n"
            "Then run: uv tool install uvx"
        )
    return True, "Serena MCP server prerequisites available"


async def _call_tool(
    tool_name: str,
    arguments: dict,
    project_path: str,
) -> Any:
    """Call a Serena MCP tool.

    Args:
        tool_name: Name of the MCP tool
        arguments: Arguments to pass to the tool
        project_path: Path to the project root

    Returns:
        Tool result as returned by MCP server

    Raises:
        RuntimeError: If MCP server is not available or tool call fails
    """
    server_params = StdioServerParameters(
        command=DEFAULT_SERVER_CMD,
        args=_build_server_args(project_path),
        env=_build_env(),
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                return result
    except Exception as e:
        raise RuntimeError(
            f"Serena MCP call failed: {e}\n"
            f"Ensure uvx is installed and the project path is valid.\n"
            f"Server command: uvx serena start-mcp-server --project {project_path}"
        ) from e


def _extract_text(result) -> Any:
    """Extract text or structured data from an MCP tool result."""
    if result is None:
        return None

    if hasattr(result, "content"):
        contents = result.content
        if not contents:
            return None
        texts = []
        for item in contents:
            if hasattr(item, "text"):
                texts.append(item.text)
        if len(texts) == 1:
            try:
                return json.loads(texts[0])
            except (json.JSONDecodeError, TypeError):
                return texts[0]
        return texts if texts else str(result)

    return result


def _tool(tool_name: str, project_path: str, **kwargs) -> Any:
    """Generic tool call with auto-cleanup of None values."""
    args = {k: v for k, v in kwargs.items() if v is not None}
    result = asyncio.run(_call_tool(tool_name, args, project_path))
    return _extract_text(result)


# -- Symbol Tools ------------------------------------------------------------


def find_symbol(
    project_path: str,
    name_path_pattern: str,
    depth: Optional[int] = None,
    include_body: bool = False,
    include_info: bool = False,
    kind: Optional[str] = None,
    substring: bool = False,
    max_matches: Optional[int] = None,
) -> Any:
    """Find symbols by name pattern via LSP."""
    return _tool(
        "find_symbol",
        project_path,
        name_path_pattern=name_path_pattern,
        depth=depth,
        include_body=include_body if include_body else None,
        include_info=include_info if include_info else None,
        kind=kind,
        substring=substring if substring else None,
        max_matches=max_matches,
    )


def find_referencing_symbols(
    project_path: str,
    name_path_pattern: str,
    include_body: bool = False,
    include_info: bool = False,
    max_matches: Optional[int] = None,
) -> Any:
    """Find all symbols that reference a given symbol."""
    return _tool(
        "find_referencing_symbols",
        project_path,
        name_path_pattern=name_path_pattern,
        include_body=include_body if include_body else None,
        include_info=include_info if include_info else None,
        max_matches=max_matches,
    )


def get_symbols_overview(
    project_path: str,
    relative_path: str,
    depth: Optional[int] = None,
) -> Any:
    """Get top-level symbols in a file grouped by kind."""
    return _tool(
        "get_symbols_overview",
        project_path,
        relative_path=relative_path,
        depth=depth,
    )


def rename_symbol(
    project_path: str,
    name_path_pattern: str,
    new_name: str,
) -> Any:
    """Rename a symbol across the entire codebase via LSP refactoring."""
    return _tool(
        "rename_symbol",
        project_path,
        name_path_pattern=name_path_pattern,
        new_name=new_name,
    )


# -- File/Search Tools -------------------------------------------------------


def search_for_pattern(
    project_path: str,
    pattern: str,
    path: Optional[str] = None,
    context_lines: Optional[int] = None,
    include_glob: Optional[str] = None,
    exclude_glob: Optional[str] = None,
) -> Any:
    """Regex search across project files."""
    return _tool(
        "search_for_pattern",
        project_path,
        substring_pattern=pattern,
        path=path,
        context_lines=context_lines,
        include_glob=include_glob,
        exclude_glob=exclude_glob,
    )


def list_dir(
    project_path: str,
    path: Optional[str] = None,
    recursive: bool = False,
) -> Any:
    """List files and directories."""
    return _tool(
        "list_dir",
        project_path,
        path=path,
        recursive=recursive if recursive else None,
    )


def find_file(
    project_path: str,
    pattern: str,
    path: Optional[str] = None,
) -> Any:
    """Find files matching a glob pattern."""
    return _tool(
        "find_file",
        project_path,
        pattern=pattern,
        path=path,
    )


# -- Memory Tools ------------------------------------------------------------


def write_memory(
    project_path: str,
    name: str,
    content: str,
) -> Any:
    """Write a named memory file."""
    return _tool(
        "write_memory",
        project_path,
        name=name,
        content=content,
    )


def read_memory(
    project_path: str,
    name: str,
) -> Any:
    """Read a memory file by name."""
    return _tool(
        "read_memory",
        project_path,
        name=name,
    )


def list_memories(
    project_path: str,
    topic: Optional[str] = None,
) -> Any:
    """List available memories."""
    return _tool(
        "list_memories",
        project_path,
        topic=topic,
    )


def delete_memory(
    project_path: str,
    name: str,
) -> Any:
    """Delete a memory."""
    return _tool(
        "delete_memory",
        project_path,
        name=name,
    )


# -- Config/Workflow Tools ---------------------------------------------------


def activate_project(
    project_path: str,
    project_name_or_path: Optional[str] = None,
) -> Any:
    """Activate a project by name or path."""
    return _tool(
        "activate_project",
        project_path,
        project_name_or_path=project_name_or_path or project_path,
    )


def get_current_config(project_path: str) -> Any:
    """Get active project configuration."""
    return _tool("get_current_config", project_path)


def onboarding(project_path: str) -> Any:
    """Run project onboarding to explore structure and create memories."""
    return _tool("onboarding", project_path)


def check_onboarding_performed(project_path: str) -> Any:
    """Check if project onboarding has been performed."""
    return _tool("check_onboarding_performed", project_path)


def restart_language_server(project_path: str) -> Any:
    """Restart the language server to refresh code intelligence."""
    return _tool("restart_language_server", project_path)


# -- Editing Tools (exposed but discouraged -- use Claude Code Edit instead) --


def replace_symbol_body(
    project_path: str,
    name_path: str,
    relative_path: str,
    body: str,
) -> Any:
    """Replace the body of a named symbol. Prefer Claude Code Edit tool."""
    return _tool(
        "replace_symbol_body",
        project_path,
        name_path=name_path,
        relative_path=relative_path,
        body=body,
    )


def insert_after_symbol(
    project_path: str,
    name_path: str,
    relative_path: str,
    body: str,
) -> Any:
    """Insert code after a symbol. Prefer Claude Code Edit tool."""
    return _tool(
        "insert_after_symbol",
        project_path,
        name_path=name_path,
        relative_path=relative_path,
        body=body,
    )


def insert_before_symbol(
    project_path: str,
    name_path: str,
    relative_path: str,
    body: str,
) -> Any:
    """Insert code before a symbol. Prefer Claude Code Edit tool."""
    return _tool(
        "insert_before_symbol",
        project_path,
        name_path=name_path,
        relative_path=relative_path,
        body=body,
    )


def replace_content(
    project_path: str,
    relative_path: str,
    old: str,
    new: str,
    use_regex: bool = False,
) -> Any:
    """Replace content in a file. Prefer Claude Code Edit tool."""
    return _tool(
        "replace_content",
        project_path,
        relative_path=relative_path,
        old=old,
        new=new,
        use_regex=use_regex if use_regex else None,
    )
