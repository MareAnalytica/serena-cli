---
name: "serena"
description: "Code intelligence CLI via Serena LSP-based MCP server. Use for structural symbol navigation, cross-codebase refactoring, and semantic code understanding. Replaces grep-based code exploration with LSP-powered structural queries."
---

# Serena CLI -- Code Intelligence for Agents

Serena wraps real language servers (gopls, pyright, typescript-language-server, rust-analyzer, etc.) to give you structural understanding of code. It knows what symbols are, where they're defined, and how they connect -- not just text matching.

## Installation

```bash
pip install git+https://github.com/MareAnalytica/serena-cli.git
```

Prerequisites: `uvx` (install uv from https://docs.astral.sh/uv/). Serena auto-installs language servers for your project's languages.

## CRITICAL: Tool Usage Rules

### ALWAYS use Serena for these (read/query):

| Command | Purpose | When to use |
|---------|---------|-------------|
| `serena find <pattern>` | Find symbols by name | Instead of grepping for class/function definitions |
| `serena refs <pattern>` | Find all references to a symbol | Before modifying a function -- know every caller |
| `serena overview <file>` | Get file's symbol structure | Instead of reading entire files to understand structure |
| `serena rename <old> <new>` | Cross-codebase symbol rename | The ONE editing operation to use via Serena |
| `serena search <pattern>` | Regex search across files | When you need pattern matching with file filtering |
| `serena restart` | Restart language server | After bulk file operations or stale query results |

### NEVER use Serena for these (use Claude Code tools instead):

| Serena command | Use this instead | Why |
|----------------|-------------------|-----|
| `serena edit replace-body` | Claude Code `Edit` tool | Claude Code edits are tracked, reversible, and don't risk LSP desync |
| `serena edit insert-after` | Claude Code `Edit` tool | Same reason |
| `serena edit insert-before` | Claude Code `Edit` tool | Same reason |
| `serena edit replace` | Claude Code `Edit` tool | Same reason |
| `serena ls` | Claude Code `Glob` tool | Glob is faster and doesn't spawn an MCP server |
| `serena find-file` | Claude Code `Glob` tool | Same reason |

### Serena stays in sync WITHOUT its editing tools

Language servers watch the filesystem. When Claude Code's Edit tool modifies a file on disk, the language server detects the change via file watchers and mtime checks. You do NOT need to use Serena's editing tools to keep the code graph fresh.

### When to restart the language server

| Situation | Restart needed? |
|-----------|----------------|
| After Claude Code edits a single file | NO -- LS detects file change automatically |
| After `git checkout` or `git rebase` | YES -- many files changed at once |
| After bulk refactoring (10+ files) | YES -- to ensure full consistency |
| If `serena find` returns stale/wrong results | YES -- the LS may have missed an update |
| Between individual queries | NO -- never restart unnecessarily |

```bash
serena restart --project /path/to/project
```

## Command Reference

### Symbol Navigation

```bash
# Find a symbol (class, function, method, variable)
serena find "UserService"
serena find "UserService" --depth 1          # include child symbols (methods)
serena find "UserService/getUser" --body      # include full source code
serena find "handle" --substring --max 10    # substring match, limit results
serena find "MyClass" --kind class           # filter by kind

# Find all references to a symbol
serena refs "handleLogin"
serena refs "handleLogin" --body             # include referencing code

# Get file symbol overview
serena overview src/services/user.py
serena overview src/main.go --depth 1        # include method-level detail

# Cross-codebase rename (the ONE editing operation to use via Serena)
serena rename "oldFunctionName" "newFunctionName"
```

### Search

```bash
# Regex search across project
serena search "TODO|FIXME"
serena search "func.*Handler" --include "*.go"
serena search "import.*redis" --context 3
```

### Project Memory

```bash
# Serena maintains project-specific memories in .serena/memories/
serena memory list
serena memory read architecture
serena memory write "auth/flow" "Login uses JWT with httpOnly cookies..."
serena memory delete old-note
```

### Project Management

```bash
# First time with a project -- run onboarding
serena onboard --project /path/to/project

# Check configuration
serena config

# Check if onboarding was done
serena status

# Restart language server (after git operations or stale results)
serena restart
```

## Global Options

- `--json` -- Output as JSON (for programmatic parsing)
- `--project <path>` -- Project root (default: current directory)

## Agent Workflow: Best Practices

### Before modifying code:

1. `serena find "SymbolName" --body` -- Read the current implementation
2. `serena refs "SymbolName"` -- Know every caller before you change it
3. Make your edit with Claude Code's `Edit` tool
4. If you changed many files, `serena restart` to refresh the LS

### For exploring unfamiliar code:

1. `serena overview src/main.go --depth 1` -- Get the file's structure
2. `serena find "EntryPoint" --depth 2` -- Drill into specific symbols
3. `serena refs "SomeFunction"` -- Trace the call graph

### For renaming/refactoring:

1. `serena refs "oldName"` -- Check blast radius first
2. `serena rename "oldName" "newName"` -- Let LSP handle all references
3. Run tests to verify

## Performance Notes

- Each CLI command spawns a fresh Serena MCP server + language server (3-8s startup)
- This is acceptable for agent workflows (few queries per task)
- Language server startup caches improve on subsequent calls
- For heavy interactive use, use the REPL: `serena` (no subcommand)

## Supported Languages

Serena auto-detects and auto-installs language servers for:
Go (gopls), Python (pyright), TypeScript/JavaScript (typescript-language-server),
Rust (rust-analyzer), Java (JDT), C/C++ (clangd), C# (Roslyn), Ruby (ruby-lsp),
PHP (intelephense), Scala (metals), Kotlin, Dart, Bash, Lua, Zig, Elixir,
Haskell, Swift, Perl, R, YAML, TOML, Markdown, and 40+ more.

You just need the base runtime installed (e.g., Go for gopls, Node.js for TS).
