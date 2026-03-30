#!/usr/bin/env python3
"""serena CLI -- Code intelligence via Serena LSP-based MCP server.

Provides structural symbol navigation, cross-codebase refactoring,
and semantic code understanding for AI agents.

Usage:
    # Symbol navigation
    serena find "UserService" --depth 1 --body
    serena refs "handleLogin"
    serena overview src/main.py
    serena rename "old_name" "new_name"

    # Search
    serena search "TODO|FIXME" --include "*.py"

    # Project memory
    serena memory list
    serena memory read architecture
    serena memory write architecture "This project uses..."

    # Project management
    serena onboard
    serena config
    serena restart

    # Interactive REPL
    serena
"""

import sys
import json
import shlex
import os
import click
from typing import Optional

from cli_anything.serena.core.session import Session
from cli_anything.serena.utils import serena_backend as backend

# Global state
_session: Optional[Session] = None
_json_output = False
_repl_mode = False


def get_session() -> Session:
    global _session
    if _session is None:
        _session = Session()
    return _session


def output(data, message: str = ""):
    """Output data in JSON or human-readable format."""
    if _json_output:
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except (json.JSONDecodeError, TypeError):
                data = {"result": data}
        click.echo(json.dumps(data, indent=2, default=str))
    else:
        if message:
            click.echo(message)
        if isinstance(data, dict):
            _print_dict(data)
        elif isinstance(data, list):
            _print_list(data)
        elif data is not None:
            click.echo(str(data))


def _print_dict(d: dict, indent: int = 0):
    prefix = "  " * indent
    for k, v in d.items():
        if isinstance(v, dict):
            click.echo(f"{prefix}{k}:")
            _print_dict(v, indent + 1)
        elif isinstance(v, list):
            click.echo(f"{prefix}{k}:")
            _print_list(v, indent + 1)
        else:
            click.echo(f"{prefix}{k}: {v}")


def _print_list(items: list, indent: int = 0):
    prefix = "  " * indent
    for i, item in enumerate(items):
        if isinstance(item, dict):
            click.echo(f"{prefix}[{i}]")
            _print_dict(item, indent + 1)
        else:
            click.echo(f"{prefix}- {item}")


def handle_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RuntimeError as e:
            if _json_output:
                click.echo(json.dumps({"error": str(e), "type": "runtime_error"}))
            else:
                click.echo(f"Error: {e}", err=True)
            if not _repl_mode:
                sys.exit(1)
        except (ValueError, IndexError) as e:
            if _json_output:
                click.echo(json.dumps({"error": str(e), "type": type(e).__name__}))
            else:
                click.echo(f"Error: {e}", err=True)
            if not _repl_mode:
                sys.exit(1)
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


# -- Main CLI Group ----------------------------------------------------------

@click.group(invoke_without_command=True)
@click.option("--json", "use_json", is_flag=True, help="Output as JSON")
@click.option("--project", "project_path", default=None,
              help="Project root path (default: current directory)")
@click.pass_context
def cli(ctx, use_json, project_path):
    """serena CLI -- Code intelligence via Serena LSP-based MCP server.

    Run without a subcommand to enter interactive REPL mode.
    """
    global _json_output, _session
    _json_output = use_json

    _session = get_session()
    if project_path:
        _session.project_path = os.path.abspath(project_path)

    ctx.ensure_object(dict)
    ctx.obj["session"] = _session

    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)


# -- Symbol Commands ---------------------------------------------------------

@cli.command("find")
@click.argument("pattern")
@click.option("--depth", type=int, default=None, help="Child depth to include")
@click.option("--body", is_flag=True, help="Include symbol body/source")
@click.option("--info", is_flag=True, help="Include hover/type info")
@click.option("--kind", default=None, help="Filter by symbol kind (class, function, etc.)")
@click.option("--substring", is_flag=True, help="Match substring instead of exact")
@click.option("--max", "max_matches", type=int, default=None, help="Max results")
@handle_error
def cmd_find(pattern, depth, body, info, kind, substring, max_matches):
    """Find symbols by name pattern.

    Uses LSP to search for classes, functions, methods, variables by name.
    Use '/' for nested symbols: 'MyClass/my_method'
    """
    sess = get_session()
    result = backend.find_symbol(
        project_path=sess.project_path,
        name_path_pattern=pattern,
        depth=depth,
        include_body=body,
        include_info=info,
        kind=kind,
        substring=substring,
        max_matches=max_matches,
    )
    sess.last_result = result
    output(result)


@cli.command("refs")
@click.argument("pattern")
@click.option("--path", "relative_path", default=None, help="Restrict to file (relative path, required)")
@handle_error
def cmd_refs(pattern, relative_path):
    """Find all references to a symbol.

    Shows every location where the symbol is used across the codebase.
    Requires --path to specify the file containing the symbol.
    """
    sess = get_session()
    result = backend.find_referencing_symbols(
        project_path=sess.project_path,
        name_path_pattern=pattern,
        relative_path=relative_path,
    )
    sess.last_result = result
    output(result)


@cli.command("overview")
@click.argument("file_path")
@click.option("--depth", type=int, default=None, help="Child depth (e.g. 1 for class methods)")
@handle_error
def cmd_overview(file_path, depth):
    """Get symbol structure overview of a file.

    Shows top-level symbols (classes, functions, variables) grouped by kind.
    """
    sess = get_session()
    result = backend.get_symbols_overview(
        project_path=sess.project_path,
        relative_path=file_path,
        depth=depth,
    )
    sess.last_result = result
    output(result)


@cli.command("rename")
@click.argument("old_name")
@click.argument("new_name")
@handle_error
def cmd_rename(old_name, new_name):
    """Rename a symbol across the entire codebase.

    Uses LSP refactoring to update all references. This is the one editing
    operation that should use Serena instead of Claude Code's Edit tool.
    """
    sess = get_session()
    result = backend.rename_symbol(
        project_path=sess.project_path,
        name_path_pattern=old_name,
        new_name=new_name,
    )
    sess.last_result = result
    output(result, f"Renamed '{old_name}' -> '{new_name}'")


# -- Search Commands ---------------------------------------------------------

@cli.command("search")
@click.argument("pattern")
@click.option("--path", default=None, help="Restrict to path")
@click.option("--context", "context_lines", type=int, default=None, help="Context lines")
@click.option("--include", "include_glob", default=None, help="Include glob (e.g. '*.py')")
@click.option("--exclude", "exclude_glob", default=None, help="Exclude glob")
@handle_error
def cmd_search(pattern, path, context_lines, include_glob, exclude_glob):
    """Regex search across project files."""
    sess = get_session()
    result = backend.search_for_pattern(
        project_path=sess.project_path,
        pattern=pattern,
        path=path,
        context_lines=context_lines,
        include_glob=include_glob,
        exclude_glob=exclude_glob,
    )
    sess.last_result = result
    output(result)


@cli.command("ls")
@click.argument("path", default="", required=False)
@click.option("--recursive", "-r", is_flag=True, help="List recursively")
@handle_error
def cmd_ls(path, recursive):
    """List files and directories in the project."""
    sess = get_session()
    result = backend.list_dir(
        project_path=sess.project_path,
        path=path or None,
        recursive=recursive,
    )
    sess.last_result = result
    output(result)


@cli.command("find-file")
@click.argument("pattern")
@click.argument("path", default="", required=False)
@handle_error
def cmd_find_file(pattern, path):
    """Find files matching a glob pattern."""
    sess = get_session()
    result = backend.find_file(
        project_path=sess.project_path,
        pattern=pattern,
        path=path or None,
    )
    sess.last_result = result
    output(result)


# -- Memory Commands ---------------------------------------------------------

@cli.group()
def memory():
    """Project memory commands (stored in .serena/memories/)."""
    pass


@memory.command("write")
@click.argument("name")
@click.argument("content")
@handle_error
def memory_write(name, content):
    """Write a named memory file."""
    sess = get_session()
    result = backend.write_memory(
        project_path=sess.project_path,
        name=name,
        content=content,
    )
    sess.last_result = result
    output(result, f"Memory '{name}' written")


@memory.command("read")
@click.argument("name")
@handle_error
def memory_read(name):
    """Read a memory file by name."""
    sess = get_session()
    result = backend.read_memory(
        project_path=sess.project_path,
        name=name,
    )
    sess.last_result = result
    output(result)


@memory.command("list")
@handle_error
def memory_list():
    """List available project memories."""
    sess = get_session()
    result = backend.list_memories(
        project_path=sess.project_path,
    )
    sess.last_result = result
    output(result)


@memory.command("delete")
@click.argument("name")
@click.option("--yes", is_flag=True, help="Skip confirmation")
@handle_error
def memory_delete(name, yes):
    """Delete a memory file."""
    if not yes:
        if not click.confirm(f"Delete memory '{name}'?"):
            click.echo("Aborted.")
            return
    sess = get_session()
    result = backend.delete_memory(
        project_path=sess.project_path,
        name=name,
    )
    sess.last_result = result
    output(result, f"Memory '{name}' deleted")


# -- Project/Config Commands -------------------------------------------------

@cli.command("onboard")
@handle_error
def cmd_onboard():
    """Run project onboarding -- explore structure and create memories."""
    sess = get_session()
    result = backend.onboarding(project_path=sess.project_path)
    sess.last_result = result
    output(result)


@cli.command("config")
@handle_error
def cmd_config():
    """Show current Serena configuration and active project."""
    sess = get_session()
    result = backend.get_current_config(project_path=sess.project_path)
    sess.last_result = result
    output(result)


@cli.command("restart")
@handle_error
def cmd_restart():
    """Restart the language server to refresh code intelligence.

    Use after bulk file operations (git checkout, large refactors)
    or if symbol queries return stale results.
    """
    sess = get_session()
    result = backend.restart_language_server(project_path=sess.project_path)
    sess.last_result = result
    output(result, "Language server restarted")


@cli.command("status")
@handle_error
def cmd_status():
    """Check if project onboarding has been performed."""
    sess = get_session()
    result = backend.check_onboarding_performed(project_path=sess.project_path)
    sess.last_result = result
    output(result)


# -- Editing Commands (exposed but discouraged) ------------------------------

@cli.group("edit")
def edit_group():
    """Editing commands (prefer Claude Code Edit/Write tools instead)."""
    pass


@edit_group.command("replace-body")
@click.argument("symbol_path")
@click.option("--file", "file_path", required=True, help="Relative file path")
@click.argument("body")
@handle_error
def edit_replace_body(symbol_path, file_path, body):
    """Replace a symbol's body. Prefer Claude Code Edit tool."""
    sess = get_session()
    result = backend.replace_symbol_body(
        project_path=sess.project_path,
        name_path=symbol_path,
        relative_path=file_path,
        body=body,
    )
    sess.last_result = result
    output(result, f"Replaced body of '{symbol_path}'")


@edit_group.command("insert-after")
@click.argument("symbol_path")
@click.option("--file", "file_path", required=True, help="Relative file path")
@click.argument("body")
@handle_error
def edit_insert_after(symbol_path, file_path, body):
    """Insert code after a symbol. Prefer Claude Code Edit tool."""
    sess = get_session()
    result = backend.insert_after_symbol(
        project_path=sess.project_path,
        name_path=symbol_path,
        relative_path=file_path,
        body=body,
    )
    sess.last_result = result
    output(result, f"Inserted after '{symbol_path}'")


@edit_group.command("insert-before")
@click.argument("symbol_path")
@click.option("--file", "file_path", required=True, help="Relative file path")
@click.argument("body")
@handle_error
def edit_insert_before(symbol_path, file_path, body):
    """Insert code before a symbol. Prefer Claude Code Edit tool."""
    sess = get_session()
    result = backend.insert_before_symbol(
        project_path=sess.project_path,
        name_path=symbol_path,
        relative_path=file_path,
        body=body,
    )
    sess.last_result = result
    output(result, f"Inserted before '{symbol_path}'")


@edit_group.command("replace")
@click.option("--file", "file_path", required=True, help="Relative file path")
@click.argument("old")
@click.argument("new")
@click.option("--regex", is_flag=True, help="Use regex matching")
@handle_error
def edit_replace(file_path, old, new, regex):
    """Replace content in a file. Prefer Claude Code Edit tool."""
    sess = get_session()
    result = backend.replace_content(
        project_path=sess.project_path,
        relative_path=file_path,
        old=old,
        new=new,
        use_regex=regex,
    )
    sess.last_result = result
    output(result, "Content replaced")


# -- Session Commands --------------------------------------------------------

@cli.group("session")
def session_group():
    """Session management commands."""
    pass


@session_group.command("status")
@handle_error
def session_status():
    """Show current session status and configuration."""
    sess = get_session()
    status = sess.status()
    output(status)


# -- REPL --------------------------------------------------------------------

@cli.command()
@handle_error
def repl():
    """Start interactive REPL session."""
    from cli_anything.serena.utils.repl_skin import ReplSkin

    global _repl_mode
    _repl_mode = True

    skin = ReplSkin("serena", version="1.0.0")
    skin.print_banner()

    pt_session = skin.create_prompt_session()

    _repl_commands = {
        "find":         "<pattern> [--depth N] [--body] -- Find symbols",
        "refs":         "<pattern> [--body] -- Find references",
        "overview":     "<file> [--depth N] -- File symbol overview",
        "rename":       "<old> <new> -- Cross-codebase rename",
        "search":       "<pattern> [--include GLOB] -- Regex search",
        "ls":           "[path] [-r] -- List files",
        "find-file":    "<pattern> -- Find files by glob",
        "memory":       "write|read|list|delete -- Project memories",
        "onboard":      "Run project onboarding",
        "config":       "Show Serena configuration",
        "restart":      "Restart language server",
        "status":       "Check onboarding status",
        "edit":         "replace-body|insert-after|insert-before|replace",
        "session":      "status",
        "help":         "Show this help",
        "quit":         "Exit REPL",
    }

    while True:
        try:
            sess = get_session()
            context = os.path.basename(sess.project_path)

            line = skin.get_input(pt_session, context=context)
            if not line:
                continue
            if line.lower() in ("quit", "exit", "q"):
                skin.print_goodbye()
                break
            if line.lower() == "help":
                skin.help(_repl_commands)
                continue

            try:
                args = shlex.split(line)
            except ValueError:
                args = line.split()
            try:
                cli.main(args, standalone_mode=False)
            except SystemExit:
                pass
            except click.exceptions.UsageError as e:
                skin.warning(f"Usage error: {e}")
            except Exception as e:
                skin.error(f"{e}")

        except (EOFError, KeyboardInterrupt):
            skin.print_goodbye()
            break

    _repl_mode = False


# -- Entry Point -------------------------------------------------------------

def main():
    cli()


if __name__ == "__main__":
    main()
