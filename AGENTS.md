# Tentacle Project Structure

## Main Application
- `tentacle/git_diff_viewer.py` - The Textual TUI application (DO NOT RUN THIS!)

## Supporting Components
- `tentacle/git_status_sidebar.py` - Git repository interaction and status management

## Assets
- `style.tcss` - CSS styling for the Textual application

## Build & Configuration
- `pyproject.toml` - Project configuration and dependencies
- `uv.lock` - Dependency lock file

This project uses Textual for its terminal UI. The application should only be run through the proper entry points and not directly executed.