from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Static, Header, Footer, Button, Tree, Label, Input, TabbedContent, TabPane
from textual.containers import Horizontal, Vertical, Container, VerticalScroll
from textual.widgets.tree import TreeNode
from tentacle.git_status_sidebar import GitStatusSidebar, Hunk
from datetime import datetime
from textual.widget import Widget


class GitDiffViewer(App):
    """A Textual app for viewing git diffs with hunk-based staging in a three-panel UI."""
    
    TITLE = "Tentacle"
    CSS_PATH = "../style.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("Ctrl+d", "toggle_dark", "Toggle Dark Mode"),
        ("c", "commit", "Commit Staged Changes"),
    ]
    
    def __init__(self, repo_path: str = None):
        super().__init__()
        self.git_sidebar = GitStatusSidebar(repo_path)
        self.current_file = None
        self.hunks = []
        self.file_tree = None
    def compose(self) -> ComposeResult:
        """Create the UI layout with three-panel view: file tree, diff view, and commit history."""
        yield Header()
        
        yield Horizontal(
            # Left panel - File tree
            Vertical(
                Static("File Tree", id="sidebar-header"),
                Tree("Files", id="file-tree"),
                id="sidebar"
            ),
            # Center panel - Tabbed diff view and commit history
            Vertical(
                GitDiffHistoryTabs(),
                id="diff-panel"
            ),
            # Right panel - Commit functionality only
            Vertical(
                Vertical(
                    Label("Commit Message:"),
                    Input(placeholder="Enter commit message...", id="commit-message", classes="commit-input"),
                    Button("Commit", id="commit-button", classes="commit-button"),
                    id="commit-section",
                    classes="commit-section"
                ),
                id="history-panel"
            ),
            id="main-content"
        )
        yield Footer()
        
    def on_mount(self) -> None:
        """Initialize the UI when app mounts."""
        self.populate_file_tree()
        self.populate_commit_history()
        
        # If no files are selected, show a message in the diff panel
        try:
            diff_content = self.query_one("#diff-content", VerticalScroll)
            if not diff_content.children:
                diff_content.mount(Static("Select a file from the tree to view its diff", classes="info"))
        except Exception:
            pass
        
        # Ensure the history tab has content to test scrolling
        try:
            history_content = self.query_one("#history-content", VerticalScroll)
            if not history_content.children:
                history_content.mount(Static("No commit history available", classes="info"))
        except Exception:
            pass

        
    def action_quit(self) -> None:
        """Quit the application with a message."""
        self.exit("Thanks for using GitDiffViewer!")
        
    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.dark = not self.dark
        
    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle tree node selection to display file diffs."""
        node_data = event.node.data
        
        if node_data and isinstance(node_data, dict) and "path" in node_data:
            file_path = node_data["path"]
            self.current_file = file_path
            self.display_file_diff(file_path)
            
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events for hunk operations and commit."""
        button_id = event.button.id
        
        if button_id.startswith("stage-hunk-"):
            # Extract hunk index and file path
            parts = button_id.split("-", 3)
            if len(parts) == 4:
                hunk_index = int(parts[2])
                file_path = parts[3]
                self.stage_hunk(file_path, hunk_index)
                
        elif button_id.startswith("unstage-hunk-"):
            # Extract hunk index and file path
            parts = button_id.split("-", 3)
            if len(parts) == 4:
                hunk_index = int(parts[2])
                file_path = parts[3]
                self.unstage_hunk(file_path, hunk_index)
                
        elif button_id.startswith("discard-hunk-"):
            # Extract hunk index and file path
            parts = button_id.split("-", 3)
            if len(parts) == 4:
                hunk_index = int(parts[2])
                file_path = parts[3]
                self.discard_hunk(file_path, hunk_index)
                
        elif button_id == "commit-button":
            self.action_commit()
        
    def populate_file_tree(self) -> None:
        """Populate the file tree sidebar with all files and their git status."""
        if not self.git_sidebar.repo:
            return
            
        try:
            # Get the tree widget
            tree = self.query_one("#file-tree", Tree)
            
            # Clear existing tree
            tree.clear()
            
            # Get all files in the repository with their statuses
            file_tree = self.git_sidebar.get_file_tree()
            
            # Sort file_tree so directories are processed first
            file_tree.sort(key=lambda x: (x[1] != "directory", x[0]))
            
            # Keep track of created directory nodes to avoid duplicates
            directory_nodes = {"": tree.root}  # Empty string maps to root node
            
            # Add all files and directories
            for file_path, file_type, git_status in file_tree:
                parts = file_path.split('/')
                
                # Build intermediate directory nodes as needed
                # Create a path for each level to use as a key in our directory_nodes map
                for i in range(len(parts)):
                    # For directories, we need to process all parts
                    # For files, we need to process all parts except the last one (handled separately)
                    if file_type == "directory" or i < len(parts) - 1:
                        parent_path = "/".join(parts[:i])
                        current_path = "/".join(parts[:i+1])
                        
                        # Create node if it doesn't exist
                        if current_path not in directory_nodes:
                            parent_node = directory_nodes[parent_path]
                            new_node = parent_node.add(parts[i], expand=True)
                            new_node.label.stylize("bold blue")  # Color directories blue
                            directory_nodes[current_path] = new_node
                
                # For files, add as leaf node under the appropriate directory
                if file_type == "file":
                    # Get the parent directory node
                    parent_dir_path = "/".join(parts[:-1])
                    parent_node = directory_nodes[parent_dir_path] if parent_dir_path else tree.root
                    
                    leaf_node = parent_node.add_leaf(parts[-1], data={"path": file_path, "status": git_status})
                    # Apply specific text colors based on git status
                    if git_status == "staged":
                        leaf_node.label.stylize("bold green")
                    elif git_status == "modified":
                        leaf_node.label.stylize("bold red")
                    elif git_status == "untracked":
                        leaf_node.label.stylize("bold purple")
                    else:  # unchanged
                        leaf_node.label.stylize("default")
                
        except Exception as e:
            # Show error in diff panel
            try:
                diff_content = self.query_one("#diff-content", VerticalScroll)
                diff_content.remove_children()
                diff_content.mount(Static(f"Error populating file tree: {e}", classes="error"))
            except Exception:
                # If we can't even show the error, that's okay - just continue without it
                pass
        except Exception as e:
            # Show error in diff panel
            try:
                diff_content = self.query_one("#diff-content", VerticalScroll)
                diff_content.remove_children()
                diff_content.mount(Static(f"Error populating file tree: {e}", classes="error"))
            except Exception:
                # If we can't even show the error, that's okay - just continue without it
                pass
            
    def stage_hunk(self, file_path: str, hunk_index: int) -> None:
        """Stage a specific hunk of a file."""
        try:
            # For this implementation, we'll stage the entire file
            # A more advanced implementation would stage only the specific hunk
            success = self.git_sidebar.stage_file(file_path)
            
            if success:
                self.notify(f"Staged changes in {file_path}", severity="information")
                # Refresh the file tree to update styling
                self.populate_file_tree()
                # Refresh the diff view
                self.display_file_diff(file_path)
            else:
                self.notify(f"Failed to stage {file_path}", severity="error")
                
        except Exception as e:
            self.notify(f"Error staging hunk: {e}", severity="error")
            
    def unstage_hunk(self, file_path: str, hunk_index: int) -> None:
        """Unstage a specific hunk of a file."""
        try:
            # For this implementation, we'll unstage the entire file
            # A more advanced implementation would unstage only the specific hunk
            success = self.git_sidebar.unstage_file(file_path)
            
            if success:
                self.notify(f"Unstaged changes in {file_path}", severity="information")
                # Refresh the file tree to update styling
                self.populate_file_tree()
                # Refresh the diff view
                self.display_file_diff(file_path)
            else:
                self.notify(f"Failed to unstage {file_path}", severity="error")
                
        except Exception as e:
            self.notify(f"Error unstaging hunk: {e}", severity="error")
            
    def discard_hunk(self, file_path: str, hunk_index: int) -> None:
        """Discard changes in a specific hunk of a file."""
        try:
            # For this implementation, we'll discard all changes in the file
            # A more advanced implementation would discard only the specific hunk
            success = self.git_sidebar.discard_file_changes(file_path)
            
            if success:
                self.notify(f"Discarded changes in {file_path}", severity="information")
                # Refresh the file tree to update styling
                self.populate_file_tree()
                # Refresh the diff view
                self.display_file_diff(file_path)
            else:
                self.notify(f"Failed to discard changes in {file_path}", severity="error")
                
        except Exception as e:
            self.notify(f"Error discarding hunk: {e}", severity="error")
            
    def populate_commit_history(self) -> None:
        """Populate the commit history tab."""
        try:
            history_content = self.query_one("#history-content", VerticalScroll)
            history_content.remove_children()
            
            commits = self.git_sidebar.get_commit_history()
            
            for commit in commits:
                commit_container = Container(
                    Static(f"[bold]{commit.sha}[/bold]", classes="info"),
                    Static(commit.message, classes="info"),
                    Static(f"{commit.author} - {commit.date.strftime('%Y-%m-%d %H:%M')}", classes="info"),
                    classes="info-container"
                )
                history_content.mount(commit_container)
                
        except Exception:
            pass
            

            
    def display_file_diff(self, file_path: str) -> None:
        """Display the diff for a selected file in the diff panel with appropriate buttons."""
        # Skip if this is the same file we're already displaying
        if hasattr(self, '_current_displayed_file') and self._current_displayed_file == file_path:
            return
            
        try:
            diff_content = self.query_one("#diff-content", VerticalScroll)
            # Ensure we're starting with a clean slate
            diff_content.remove_children()
            
            # Track which file we're currently displaying
            self._current_displayed_file = file_path
            
            # Get file status to determine which buttons to show
            file_status = self.git_sidebar.get_file_status(file_path)
            hunks = self.git_sidebar.get_diff_hunks(file_path)
            
            if not hunks:
                diff_content.mount(Static("No changes to display", classes="info"))
                return
                
            # Display each hunk
            for i, hunk in enumerate(hunks):
                # Create all the widgets for this hunk first
                hunk_widgets = [Static(hunk.header, classes="hunk-header")]
                
                # Determine if we should apply diff highlighting
                # Apply highlighting for staged, modified, and untracked files
                apply_diff_highlighting = file_status in ["staged", "modified", "untracked"]
                
                # Add lines to the hunk widgets list
                for line in hunk.lines:
                    if apply_diff_highlighting and line:
                        # Determine line type based on the first character only
                        if line[:1] == '+':  # Added line
                            classes = "added"
                        elif line[:1] == '-':  # Removed line
                            classes = "removed"
                        else:
                            classes = "unchanged"
                    else:
                        # Disable highlighting altogether if we're not in a diff
                        classes = "unchanged"
                    
                    # Escape any markup characters in the line content
                    escaped_line = line.replace('[', r'\[').replace(']', r'\]') if line else ''
                    line_widget = Static(escaped_line, classes=classes)
                    hunk_widgets.append(line_widget)
                
                # Add appropriate action buttons for the hunk based on file status
                # Sanitize file path for use in ID (replace invalid characters)
                sanitized_file_path = file_path.replace('/', '_').replace(' ', '_').replace('.', '_')
                if file_status == "staged":
                    buttons = Horizontal(
                        Button("Unstage", id=f"unstage-hunk-{i}-{sanitized_file_path}", classes="unstage-button"),
                        Button("Discard", id=f"discard-hunk-{i}-{sanitized_file_path}", classes="discard-button"),
                        classes="hunk-buttons"
                    )
                else:  # modified or untracked
                    buttons = Horizontal(
                        Button("Stage", id=f"stage-hunk-{i}-{sanitized_file_path}", classes="stage-button"),
                        Button("Discard", id=f"discard-hunk-{i}-{sanitized_file_path}", classes="discard-button"),
                        classes="hunk-buttons"
                    )
                hunk_widgets.append(buttons)
                
                # Create the complete container with all widgets
                # Include file_path in hunk_container ID to prevent collisions
                hunk_container = Container(*hunk_widgets, id=f"hunk-{i}-{sanitized_file_path}", classes="hunk-container")
                
                # Mount the complete hunk container
                diff_content.mount(hunk_container)
                
        except Exception as e:
            self.notify(f"Error displaying diff: {e}", severity="error")
            
    def action_commit(self) -> None:
        """Commit staged changes with a commit message from the UI."""
        try:
            # Get the commit message input widget
            commit_input = self.query_one("#commit-message", Input)
            message = commit_input.value.strip()
            
            # Check if there's a commit message
            if not message:
                self.notify("Please enter a commit message", severity="warning")
                return
                
            # Check if there are staged changes
            staged_files = self.git_sidebar.get_staged_files()
            if not staged_files:
                self.notify("No staged changes to commit", severity="warning")
                return
                
            # Attempt to commit staged changes
            success = self.git_sidebar.commit_staged_changes(message)
            
            if success:
                self.notify(f"Successfully committed changes with message: {message}", severity="information")
                # Clear the commit message input
                commit_input.value = ""
                # Refresh the UI
                self.populate_file_tree()
                self.populate_commit_history()
            else:
                self.notify("Failed to commit changes", severity="error")
                
        except Exception as e:
            self.notify(f"Error committing changes: {e}", severity="error")


class GitDiffHistoryTabs(Widget):
    """A widget that contains tabbed diff view and commit history."""
    
    def compose(self) -> ComposeResult:
        """Create the tabbed content with diff view and commit history tabs."""
        with TabbedContent():
            with TabPane("Diff View"):
                yield VerticalScroll(id="diff-content")
            with TabPane("Commit History"):
                yield VerticalScroll(id="history-content")
