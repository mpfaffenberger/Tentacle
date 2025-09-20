# Tentacle

A Textual app for viewing diffs between two text files in a split-screen UI.

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
# Compare two files and view git status sidebar
tentacle <file1> <file2>
```

## Controls

- `q` - Quit the application
- `Ctrl+d` - Toggle dark mode
- Buttons for accepting/rejecting changes

## Installation

```bash
uv pip install -e .
```

## Dependencies

- textual>=6.1.0
- GitPython>=3.1.42
