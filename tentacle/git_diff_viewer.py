from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Static, Header, Footer, Button, Tree, Label, Input
from textual.containers import Horizontal, Vertical, Container
from textual.widgets.tree import TreeNode
from tentacle.git_status_sidebar import GitStatusSidebar, Hunk
from datetime import datetime


class GitDiffViewer(App):
    """A Textual app for viewing git diffs with hunk-based staging in a three-panel UI."""
    
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
            # Center panel - Diff view
            Vertical(
                Static("Diff View", id="diff-header"),
                Vertical(id="diff-content"),
                id="diff-panel"
            ),
            # Right panel - Commit history and commit functionality
            Vertical(
                Static("Commit History", id="history-header"),
                Vertical(id="history-content"),
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
            diff_content = self.query_one("#diff-content", Vertical)
            if not diff_content.children:
                diff_content.mount(Static("Select a file from the tree to view its diff", classes="info"))
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
            
            # Add all files and directories
            for file_path, file_type, git_status in file_tree:
                parts = file_path.split('/')
                current_tree_node = tree.root
                
                # Navigate/create intermediate nodes
                # For both files and directories, we need to process all parts except the last one
                for part in parts[:-1]:
                    # Look for existing node
                    found = False
                    for child in current_tree_node.children:
                        if child.label == part:
                            current_tree_node = child
                            found = True
                            break
                    
                    # Create new node if not found
                    if not found:
                        current_tree_node = current_tree_node.add(part, expand=True)
                        current_tree_node.set_class(True, "directory")
                        
                # Add leaf node for file, or regular node for directory
                if file_type == "file":
                    leaf_node = current_tree_node.add_leaf(parts[-1], data={"path": file_path, "status": git_status})
                    leaf_node.set_class(True, git_status)
                else:  # directory
                    # For directories, we add all parts (including the last one)
                    dir_tree_node = current_tree_node.add(parts[-1], expand=False)
                    dir_tree_node.set_class(True, "directory")
        except Exception as e:
            # Show error in diff panel
            try:
                diff_content = self.query_one("#diff-content", Vertical)
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
        """Populate the commit history panel."""
        try:
            history_content = self.query_one("#history-content", Vertical)
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
        try:
            diff_content = self.query_one("#diff-content", Vertical)
            diff_content.remove_children()
            
            # Get file status to determine which buttons to show
            file_status = self.git_sidebar.get_file_status(file_path)
            hunks = self.git_sidebar.get_diff_hunks(file_path)
            
            if not hunks:
                diff_content.mount(Static("No changes to display", classes="info"))
                return
                
            # Display each hunk
            for i, hunk in enumerate(hunks):
                hunk_container = Container(
                    Static(hunk.header, classes="hunk-header"),
                    id=f"hunk-{i}",
                    classes="hunk-container"
                )
                
                # Add lines to the hunk container
                for line in hunk.lines:
                    # Determine line type based on the first character
                    if line.startswith('+'):
                        line_widget = Static(line, classes="added")
                    elif line.startswith('-'):
                        line_widget = Static(line, classes="removed")
                    else:
                        line_widget = Static(line, classes="unchanged")
                    hunk_container.mount(line_widget)
                
                # Add appropriate action buttons for the hunk based on file status
                if file_status == "staged":
                    buttons = Horizontal(
                        Button("Unstage", id=f"unstage-hunk-{i}-{file_path}", classes="unstage-button"),
                        Button("Discard", id=f"discard-hunk-{i}-{file_path}", classes="discard-button"),
                        classes="hunk-buttons"
                    )
                else:  # modified or untracked
                    buttons = Horizontal(
                        Button("Stage", id=f"stage-hunk-{i}-{file_path}", classes="stage-button"),
                        Button("Discard", id=f"discard-hunk-{i}-{file_path}", classes="discard-button"),
                        classes="hunk-buttons"
                    )
                hunk_container.mount(buttons)
                
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
