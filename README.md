# Tentacle

A Textual app for viewing git repository file tree and git diffs in a split-screen UI.

## Features

- Split-screen diff viewer
- Git status sidebar with color-coded file statuses
- Accept/reject individual changes or all changes
- Save accepted changes back to the original file

## Git Status Colors

- **Green**: Staged files (added to index)
- **Yellow**: Modified files (changed but not staged)
- **Blue**: Directories
- **Purple**: Untracked files

## Usage

```bash
# Run the tentacle app with an optional repository path
uv run tentacle [repo_path]

# Or run directly with Python module syntax
uv run python -m tentacle.main [repo_path]
```

## Controls

- `q` - Quit the application
- `Ctrl+d` - Toggle dark mode
- Buttons for accepting/rejecting changes

## Installation

This project uses UV for Python environment management.

```bash
uv pip install -e .
```

## Dependencies

- textual>=6.1.0
- GitPython>=3.1.42
