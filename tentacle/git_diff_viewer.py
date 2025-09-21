import os
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Static, Header, Footer, Button, Tree, Label, Input, TabbedContent, TabPane, Select
from textual.containers import Horizontal, Vertical, Container, VerticalScroll
from textual.widgets.tree import TreeNode
from tentacle.git_status_sidebar import GitStatusSidebar, Hunk
from tentacle.animated_logo import AnimatedLogo
from textual.widget import Widget
from textual.widgets import Static
from textual.screen import ModalScreen
from textual.widgets import OptionList
from textual.widgets.option_list import Option
import time

class CommitLine(Static):
    """A widget for displaying a commit line with SHA and message."""
    
    DEFAULT_CSS = """
    CommitLine {
        width: 100%;
        height: 1;
        overflow: hidden hidden;
    }
    """


class GitDiffHistoryTabs(Widget):
    """A widget that contains tabbed diff view and commit history."""
    
    def compose(self) -> ComposeResult:
        """Create the tabbed content with diff view and commit history tabs."""
        with TabbedContent():
            with TabPane("Diff View"):
                yield VerticalScroll(id="diff-content")
            with TabPane("Commit History"):
                yield VerticalScroll(id="history-content")



class BranchSwitchModal(ModalScreen):
    """Modal screen for switching branches."""
    
    DEFAULT_CSS = """
    BranchSwitchModal {
        align: center middle;
    }
    
    #Container {
        border: solid white;
        background: #00122f;
        width: 50%;
        height: 50%;
        margin: 1;
        padding: 1;
    }
    
    OptionList {
        height: 1fr;
        border: tall white;
    }
    """
    
    def __init__(self, git_sidebar: GitStatusSidebar):
        super().__init__()
        self.git_sidebar = git_sidebar
        
    def compose(self) -> ComposeResult:
        """Create the modal content."""
        with Container():
            yield Static("Switch Branch", classes="panel-header")
            yield OptionList()
            with Horizontal():
                yield Button("Cancel", id="cancel-branch-switch", classes="cancel-button")
                yield Button("Refresh", id="refresh-branches", classes="refresh-button")
                
    def on_mount(self) -> None:
        """Populate the branch list when the modal is mounted."""
        self.populate_branch_list()
        
    def populate_branch_list(self) -> None:
        """Populate the option list with all available branches."""
        try:
            option_list = self.query_one(OptionList)
            option_list.clear_options()
            
            # Get all branches
            branches = self.git_sidebar.get_all_branches()
            current_branch = self.git_sidebar.get_current_branch()
            
            # Add branches to the option list
            for branch in branches:
                if branch == current_branch:
                    option_list.add_option(Option(branch, id=branch, disabled=True))
                else:
                    option_list.add_option(Option(branch, id=branch))
                    
        except Exception as e:
            self.app.notify(f"Error populating branches: {e}", severity="error")
            
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in the modal."""
        if event.button.id == "cancel-branch-switch":
            self.app.pop_screen()
        elif event.button.id == "refresh-branches":
            self.populate_branch_list()
            self.app.notify("Branch list refreshed", severity="information")
            
    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle branch selection."""
        branch_name = event.option.id
        
        if branch_name:
            # Check if repo is dirty before switching
            if self.git_sidebar.is_dirty():
                self.app.notify("Cannot switch branches with uncommitted changes. Please commit or discard changes first.", severity="error")
            else:
                # Attempt to switch branch
                success = self.git_sidebar.switch_branch(branch_name)
                if success:
                    self.app.notify(f"Switched to branch: {branch_name}", severity="information")
                    # Refresh the UI
                    self.app.populate_file_tree()
                    self.app.populate_commit_history()
                    # Close the modal
                    self.app.pop_screen()
                else:
                    self.app.notify(f"Failed to switch to branch: {branch_name}", severity="error")
class GitDiffViewer(App):
    """A Textual app for viewing git diffs with hunk-based staging in a three-panel UI."""
    
    TITLE = "Tentacle"
    CSS_PATH = "../style.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("Ctrl+d", "toggle_dark", "Toggle Dark Mode"),
        ("c", "commit", "Commit Staged Changes"),
        ("r", "refresh_branches", "Refresh Branches"),
        ("b", "show_branch_switcher", "Switch Branch"),
    ]
    
    def __init__(self, repo_path: str = None):
        super().__init__()
        self.git_sidebar = GitStatusSidebar(repo_path)
        self.current_file = None
        self.hunks = []
        self.file_tree = None
        self.current_is_staged = None
        self._current_displayed_file = None
        self._current_displayed_is_staged = None

    def compose(self) -> ComposeResult:
        """Create the UI layout with three-panel view: file tree, diff view, and commit history."""
        yield Header()
        
        yield Horizontal(
            # Left panel - File tree
            Vertical(
                AnimatedLogo(),
                Static("File Tree", id="sidebar-header", classes="panel-header"),
                Tree(os.path.basename(os.getcwd()), id="file-tree"),
                id="sidebar"
            ),
            # Center panel - Tabbed diff view and commit history
            Vertical(
                GitDiffHistoryTabs(),
                id="diff-panel"
            ),
            # Right panel - Git status functionality
            Vertical(
                # Top pane - Unstaged changes
                Vertical(
                    Static("Unstaged Changes", classes="panel-header"),
                    Tree("Unstaged", id="unstaged-tree"),
                    id="unstaged-panel"
                ),
                # Middle pane - Staged changes
                Vertical(
                    Static("Staged Changes", classes="panel-header"),
                    Tree("Staged", id="staged-tree"),
                    id="staged-panel"
                ),
                # Bottom pane - Commit functionality
                Vertical(
                    Input(placeholder="Enter commit message...", id="commit-message", classes="commit-input"),
                    Button("Commit", id="commit-button", classes="commit-button"),
                    id="commit-section",
                    classes="commit-section"
                ),
                id="status-panel"
            ),
            id="main-content"
        )
        yield Footer()
        
    def on_mount(self) -> None:
        """Initialize the UI when app mounts."""
        self.populate_file_tree()
        self.populate_unstaged_changes()
        self.populate_staged_changes()
        self.populate_commit_history()
        
        # If no files are selected, show a message in the diff panel
        try:
            diff_content = self.query_one("#diff-content", VerticalScroll)
            if not diff_content.children:
                diff_content.mount(Static("Select a file from the tree to view its diff", classes="info"))
        except Exception:
            pass
        try:
            history_content = self.query_one("#history-content", VerticalScroll)
            if not history_content.children:
                history_content.mount(Static("No commit history available", classes="info"))
        except Exception:
            pass
            
    def populate_branch_dropdown(self) -> None:
        """Populate the branch dropdown with all available branches."""
        try:
            # Get the select widget
            branch_select = self.query_one("#branch-select", Select)
            
            # Get all branches
            branches = self.git_sidebar.get_all_branches()
            current_branch = self.git_sidebar.get_current_branch()
            
            # Create options for the select widget
            options = [(branch, branch) for branch in branches]
            
            # Set the options and default value
            branch_select.set_options(options)
            branch_select.value = current_branch
            
        except Exception as e:
            # If we can't populate branches, that's okay - continue without it
            pass
            
    def action_show_branch_switcher(self) -> None:
        """Show the branch switcher modal."""
        modal = BranchSwitchModal(self.git_sidebar)
        self.push_screen(modal)
        
    def action_refresh_branches(self) -> None:
        """Refresh the branch dropdown menu."""
        self.populate_branch_dropdown()
        self.notify("Branch list refreshed", severity="information")
        
    def action_quit(self) -> None:
        """Quit the application with a message."""
        self.exit("Thanks for using GitDiffViewer!")
        
    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.dark = not self.dark
        
    def on_unstaged_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle unstaged tree node selection to display file diffs."""
        node_data = event.node.data
        
        if node_data and isinstance(node_data, dict) and "path" in node_data:
            file_path = node_data["path"]
            self.current_file = file_path
            self.display_file_diff(file_path, is_staged=False)
            
    def on_staged_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle staged tree node selection to display file diffs."""
        node_data = event.node.data
        
        if node_data and isinstance(node_data, dict) and "path" in node_data:
            file_path = node_data["path"]
            self.current_file = file_path
            self.display_file_diff(file_path, is_staged=True)
            
    def on_unstaged_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Handle unstaged tree node highlighting to display file diffs."""
        node_data = event.node.data
        
        if node_data and isinstance(node_data, dict) and "path" in node_data:
            file_path = node_data["path"]
            self.current_file = file_path
            self.display_file_diff(file_path, is_staged=False)

    def on_staged_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Handle staged tree node highlighting to display file diffs."""
        node_data = event.node.data
        
        if node_data and isinstance(node_data, dict) and "path" in node_data:
            file_path = node_data["path"]
            self.current_file = file_path
            self.display_file_diff(file_path, is_staged=True)
            
    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle tree node selection to display file diffs."""
        node_data = event.node.data
        
        if node_data and isinstance(node_data, dict) and "path" in node_data:
            file_path = node_data["path"]
            status = node_data.get("status", "unchanged")
            is_staged = (status == "staged")
            self.current_file = file_path
            self.display_file_diff(file_path, is_staged)
            
    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Handle tree node highlighting to display file diffs."""
        node_data = event.node.data
        
        if node_data and isinstance(node_data, dict) and "path" in node_data:
            file_path = node_data["path"]
            status = node_data.get("status", "unchanged")
            is_staged = (status == "staged")
            self.current_file = file_path
            self.display_file_diff(file_path, is_staged)
            
    def _reverse_sanitize_path(self, sanitized_path: str) -> str:
        """Reverse the sanitization of a file path.
        
        Args:
            sanitized_path: The sanitized path with encoded characters
            
        Returns:
            The original file path
        """
        return sanitized_path.replace('__SLASH__', '/').replace('__SPACE__', ' ').replace('__DOT__', '.')
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events for hunk operations and commit."""
        button_id = event.button.id
        
        if button_id.startswith("stage-hunk-"):
            # Extract hunk index and file path (ignoring the timestamp at the end)
            parts = button_id.split("-")
            if len(parts) >= 4:
                hunk_index = int(parts[2])
                # Join parts 3 through second-to-last (excluding timestamp)
                sanitized_file_path = "-".join(parts[3:-1])
                file_path = self._reverse_sanitize_path(sanitized_file_path)
                self.stage_hunk(file_path, hunk_index)
                
        elif button_id.startswith("unstage-hunk-"):
            # Extract hunk index and file path (ignoring the timestamp at the end)
            parts = button_id.split("-")
            if len(parts) >= 4:
                hunk_index = int(parts[2])
                # Join parts 3 through second-to-last (excluding timestamp)
                sanitized_file_path = "-".join(parts[3:-1])
                file_path = self._reverse_sanitize_path(sanitized_file_path)
                self.unstage_hunk(file_path, hunk_index)
                
        elif button_id.startswith("discard-hunk-"):
            # Extract hunk index and file path (ignoring the timestamp at the end)
            parts = button_id.split("-")
            if len(parts) >= 4:
                hunk_index = int(parts[2])
                # Join parts 3 through second-to-last (excluding timestamp)
                sanitized_file_path = "-".join(parts[3:-1])
                file_path = self._reverse_sanitize_path(sanitized_file_path)
                self.discard_hunk(file_path, hunk_index)
                
        elif button_id == "commit-button":
            self.action_commit()
            
    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle branch selection changes."""
        if event.select.id == "branch-select":
            branch_name = event.value
            if branch_name:
                # Check if repo is dirty before switching
                if self.git_sidebar.is_dirty():
                    self.notify("Cannot switch branches with uncommitted changes. Please commit or discard changes first.", severity="error")
                    # Reset to current branch
                    current_branch = self.git_sidebar.get_current_branch()
                    event.select.value = current_branch
                else:
                    # Attempt to switch branch
                    success = self.git_sidebar.switch_branch(branch_name)
                    if success:
                        self.notify(f"Switched to branch: {branch_name}", severity="information")
                        # Refresh the UI
                        self.populate_branch_dropdown()
                        self.populate_file_tree()
                        self.populate_commit_history()
                    else:
                        self.notify(f"Failed to switch to branch: {branch_name}", severity="error")
                        # Reset to current branch
                        current_branch = self.git_sidebar.get_current_branch()
                        event.select.value = current_branch
            
    def action_refresh_branches(self) -> None:
        """Refresh the branch dropdown menu."""
        self.populate_branch_dropdown()
        self.notify("Branch list refreshed", severity="information")
        
    def populate_file_tree(self) -> None:
        """Populate the file tree sidebar with all files and their git status."""
        if not self.git_sidebar.repo:
            return
            
        try:
            # Get the tree widget
            tree = self.query_one("#file-tree", Tree)
            
            # Clear existing tree
            tree.clear()
            
            # Automatically expand the root node
            tree.root.expand()
            
            # Get all files in the repository with their statuses
            file_tree = self.git_sidebar.get_file_tree()
            
            # Sort file_tree so directories are processed first
            file_tree.sort(key=lambda x: (x[1] != "directory", x[0]))
            
            # Keep track of created directory nodes to avoid duplicates
            directory_nodes = {"": tree.root}  # Empty string maps to root node
            
            # Add all files and directories
            for file_path, file_type, git_status in file_tree:
                parts = file_path.split('/')
                
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

    def populate_unstaged_changes(self) -> None:
        """Populate the unstaged changes tree in the right sidebar."""
        if not self.git_sidebar.repo:
            return
            
        try:
            # Get the unstaged tree widget
            tree = self.query_one("#unstaged-tree", Tree)
            
            # Clear existing tree
            tree.clear()
            
            # Automatically expand the root node
            tree.root.expand()
            
            # Get unstaged files (modified and untracked)
            unstaged_files = self.git_sidebar.get_files_with_unstaged_changes()
            
            # Sort unstaged_files so directories are processed first
            unstaged_files.sort()
            
            # Keep track of created directory nodes to avoid duplicates
            directory_nodes = {"": tree.root}  # Empty string maps to root node
            
            # Add unstaged files to tree with directory structure
            for file_path in unstaged_files:
                parts = file_path.split('/')
                file_name = parts[-1]
                
                # Determine file status
                if file_path in self.git_sidebar.get_untracked_files():
                    status = "untracked"
                else:
                    status = "modified"
                
                # Build intermediate directory nodes as needed
                for i in range(len(parts) - 1):
                    parent_path = "/".join(parts[:i])
                    current_path = "/".join(parts[:i+1])
                    
                    # Create node if it doesn't exist
                    if current_path not in directory_nodes:
                        parent_node = directory_nodes[parent_path]
                        new_node = parent_node.add(parts[i], expand=True)
                        new_node.label.stylize("bold blue")  # Color directories blue
                        directory_nodes[current_path] = new_node
                
                # Add file as leaf node under the appropriate directory
                parent_dir_path = "/".join(parts[:-1])
                parent_node = directory_nodes[parent_dir_path] if parent_dir_path else tree.root
                
                leaf_node = parent_node.add_leaf(file_name, data={"path": file_path, "status": status})
                
                # Apply styling based on status
                if status == "modified":
                    leaf_node.label.stylize("bold red")
                else:  # untracked
                    leaf_node.label.stylize("bold purple")
                
        except Exception as e:
            # Show error in diff panel
            try:
                diff_content = self.query_one("#diff-content", VerticalScroll)
                diff_content.remove_children()
                diff_content.mount(Static(f"Error populating unstaged changes: {e}", classes="error"))
            except Exception:
                pass

    def populate_staged_changes(self) -> None:
        """Populate the staged changes tree in the right sidebar."""
        if not self.git_sidebar.repo:
            return
            
        try:
            # Get the staged tree widget
            tree = self.query_one("#staged-tree", Tree)
            
            # Clear existing tree
            tree.clear()
            
            # Automatically expand the root node
            tree.root.expand()
            
            # Get staged files
            staged_files = self.git_sidebar.get_staged_files()
            
            # Sort staged_files so directories are processed first
            staged_files.sort()
            
            # Keep track of created directory nodes to avoid duplicates
            directory_nodes = {"": tree.root}  # Empty string maps to root node
            
            # Add staged files with directory structure
            for file_path in staged_files:
                parts = file_path.split('/')
                file_name = parts[-1]
                
                # Build intermediate directory nodes as needed
                for i in range(len(parts) - 1):
                    parent_path = "/".join(parts[:i])
                    current_path = "/".join(parts[:i+1])
                    
                    # Create node if it doesn't exist
                    if current_path not in directory_nodes:
                        parent_node = directory_nodes[parent_path]
                        new_node = parent_node.add(parts[i], expand=True)
                        new_node.label.stylize("bold blue")  # Color directories blue
                        directory_nodes[current_path] = new_node
                
                # Add file as leaf node under the appropriate directory
                parent_dir_path = "/".join(parts[:-1])
                parent_node = directory_nodes[parent_dir_path] if parent_dir_path else tree.root
                
                leaf_node = parent_node.add_leaf(file_name, data={"path": file_path, "status": "staged"})
                leaf_node.label.stylize("bold green")
                
        except Exception as e:
            # Show error in diff panel
            try:
                diff_content = self.query_one("#diff-content", VerticalScroll)
                diff_content.remove_children()
                diff_content.mount(Static(f"Error populating staged changes: {e}", classes="error"))
            except Exception:
                pass
            
    def stage_hunk(self, file_path: str, hunk_index: int) -> None:
        """Stage a specific hunk of a file."""
        try:
            # For this implementation, we'll stage the entire file
            # A more advanced implementation would stage only the specific hunk
            success = self.git_sidebar.stage_hunk(file_path, hunk_index)
            
            if success:
                self.notify(f"Staged hunk in {file_path}", severity="information")
                self.populate_file_tree()
                self.populate_unstaged_changes()
                self.populate_staged_changes()
                if self.current_file:
                    # Check if the file still has unstaged changes to determine which view to show
                    file_status = self.git_sidebar.get_file_status(self.current_file)
                    if file_status == "modified":  # File has both staged and unstaged changes
                        # Keep showing unstaged view
                        self.display_file_diff(self.current_file, False, force_refresh=True)
                    else:
                        # File is fully staged, show staged view
                        self.current_is_staged = True
                        self.display_file_diff(self.current_file, True, force_refresh=True)
            else:
                self.notify(f"Failed to stage {file_path}", severity="error")
                
        except Exception as e:
            self.notify(f"Error staging hunk: {e}", severity="error")
            
    def unstage_hunk(self, file_path: str, hunk_index: int) -> None:
        """Unstage a specific hunk of a file."""
        try:
            # For this implementation, we'll unstage the entire file
            # A more advanced implementation would unstage only the specific hunk
            success = self.git_sidebar.unstage_hunk(file_path, hunk_index)
            
            if success:
                self.notify(f"Unstaged hunk in {file_path}", severity="information")
                self.populate_file_tree()
                self.populate_unstaged_changes()
                self.populate_staged_changes()
                if self.current_file:
                    # After unstaging, we should show the unstaged view of the file
                    self.current_is_staged = False
                    self.display_file_diff(self.current_file, False, force_refresh=True)
            else:
                self.notify(f"Failed to unstage {file_path}", severity="error")
                
        except Exception as e:
            self.notify(f"Error unstaging hunk: {e}", severity="error")
            
    def discard_hunk(self, file_path: str, hunk_index: int) -> None:
        """Discard changes in a specific hunk of a file."""
        try:
            # For this implementation, we'll discard all changes in the file
            # A more advanced implementation would discard only the specific hunk
            success = self.git_sidebar.discard_hunk(file_path, hunk_index)
            
            if success:
                self.notify(f"Discarded hunk in {file_path}", severity="information")
                self.populate_file_tree()
                self.populate_unstaged_changes()
                self.populate_staged_changes()
                if self.current_file:
                    self.display_file_diff(self.current_file, self.current_is_staged, force_refresh=True)
            else:
                self.notify(f"Failed to discard changes in {file_path}", severity="error")
                
        except Exception as e:
            self.notify(f"Error discarding hunk: {e}", severity="error")
            
    def populate_commit_history(self) -> None:
        """Populate the commit history tab."""
        try:
            history_content = self.query_one("#history-content", VerticalScroll)
            history_content.remove_children()
            
            branch_name = self.git_sidebar.get_current_branch()
            commits = self.git_sidebar.get_commit_history()
            
            for commit in commits:
                # Display branch, commit ID, author, and message with colors that match our theme
                commit_text = f"[#87CEEB]{branch_name}[/#87CEEB] [#E0FFFF]{commit.sha}[/#E0FFFF] [#00BFFF]{commit.author}[/#00BFFF]: {commit.message}"
                commit_line = CommitLine(commit_text, classes="info")
                history_content.mount(commit_line)
                
        except Exception:
            pass
            

            
    def display_file_diff(self, file_path: str, is_staged: bool = False, force_refresh: bool = False) -> None:
        """Display the diff for a selected file in the diff panel with appropriate buttons."""
        # Skip if this is the same file we're already displaying (unless force_refresh is True)
        if not force_refresh and hasattr(self, '_current_displayed_file') and self._current_displayed_file == file_path and self._current_displayed_is_staged == is_staged:
            return
        self.current_is_staged = is_staged
            
        try:
            diff_content = self.query_one("#diff-content", VerticalScroll)
            # Ensure we're starting with a clean slate
            diff_content.remove_children()
            
            # Track which file we're currently displaying
            self._current_displayed_file = file_path
            self._current_displayed_is_staged = is_staged
            
            # Get file status to determine which buttons to show
            hunks = self.git_sidebar.get_diff_hunks(file_path, staged=is_staged)
            
            if not hunks:
                diff_content.mount(Static("No changes to display", classes="info"))
                return
                
            # Generate a unique timestamp for this refresh to avoid ID collisions
            refresh_id = str(int(time.time() * 1000000))  # microsecond timestamp
            
            # Display each hunk
            for i, hunk in enumerate(hunks):
                # Create all the widgets for this hunk first
                hunk_widgets = [Static(hunk.header, classes="hunk-header")]
                
                # Determine if we should apply diff highlighting
                # Apply highlighting for staged, modified, and untracked files
                apply_diff_highlighting = True
                
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
                # Sanitize file path for use in ID (replace invalid characters with reversible encodings)
                sanitized_file_path = file_path.replace('/', '__SLASH__').replace(' ', '__SPACE__').replace('.', '__DOT__')
                if is_staged:
                    buttons = Horizontal(
                        Button("Unstage", id=f"unstage-hunk-{i}-{sanitized_file_path}-{refresh_id}", classes="unstage-button"),
                        classes="hunk-buttons"
                    )
                else:
                    buttons = Horizontal(
                        Button("Stage", id=f"stage-hunk-{i}-{sanitized_file_path}-{refresh_id}", classes="stage-button"),
                        Button("Discard", id=f"discard-hunk-{i}-{sanitized_file_path}-{refresh_id}", classes="discard-button"),
                        classes="hunk-buttons"
                    )
                hunk_widgets.append(buttons)
                
                # Create the complete container with all widgets
                # Include file_path and staging status in hunk_container ID to prevent collisions
                hunk_container = Container(*hunk_widgets, id=f"{'staged' if is_staged else 'unstaged'}-hunk-{i}-{sanitized_file_path}-{refresh_id}", classes="hunk-container")
                
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
                self.populate_unstaged_changes()
                self.populate_staged_changes()
                self.populate_commit_history()
            else:
                self.notify("Failed to commit changes", severity="error")
                
        except Exception as e:
            self.notify(f"Error committing changes: {e}", severity="error")
