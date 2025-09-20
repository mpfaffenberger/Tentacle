import sys
from difflib import SequenceMatcher
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Static, Header, Footer, Button, Tree
from textual.containers import Horizontal, Vertical, Container
from textual.widgets.tree import TreeNode
from tentacle.git_status_sidebar import GitStatusSidebar


class GitDiffViewer(App):
    """A Textual app for viewing diffs between two text files in a split-screen UI."""
    
    CSS_PATH = "../style.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("Ctrl+d", "toggle_dark", "Toggle Dark Mode"),
    ]
    
    def __init__(self, file1_path: str, file2_path: str):
        super().__init__()
        self.file1_path = file1_path
        self.file2_path = file2_path
        self.file1_lines = []
        self.file2_lines = []
        self.line_diffs_file1 = []
        self.line_diffs_file2 = []
        self.accepted_changes = []  # Track which changes have been accepted
        self.git_sidebar = GitStatusSidebar()
        self.file_tree = None
        
    def on_mount(self) -> None:
        """Load files and calculate diff when app mounts."""
        self.load_files_and_calculate_diff()
        self.populate_file_tree()
        
        # Populate the file content areas with styled lines
        file1_content = self.query_one("#file1-content", Vertical)
        file2_content = self.query_one("#file2-content", Vertical)
        
        for i, (diff_type, line) in enumerate(self.line_diffs_file1):
            display_line = line if line else " "
            file1_content.mount(Static(display_line, classes=diff_type, id=f"file1-line-{i}", markup=True))
            
        for i, (diff_type, line) in enumerate(self.line_diffs_file2):
            display_line = line if line else " "
            
            # For modified lines, create a container with the line and accept/reject buttons
            if diff_type in ["added", "changed"]:
                line_container = Container(
                    Static(display_line, classes=diff_type, id=f"file2-line-{i}", markup=True),
                    Horizontal(
                        Button("Accept", id=f"accept-{i}", classes="accept-button"),
                        Button("Reject", id=f"reject-{i}", classes="reject-button"),
                        id=f"buttons-{i}",
                        classes="line-buttons"
                    ),
                    id=f"line-container-{i}",
                    classes="line-container"
                )
                file2_content.mount(line_container)
            else:
                line_container = Container(
                    Static(display_line, classes=diff_type, id=f"file2-line-{i}", markup=True),
                    id=f"line-container-{i}",
                    classes="line-container"
                )
                file2_content.mount(line_container)
        
    def load_files_and_calculate_diff(self) -> None:
        """Load the two files and calculate their diff."""
        try:
            with open(self.file1_path, 'r') as f1:
                self.file1_lines = f1.readlines()
            with open(self.file2_path, 'r') as f2:
                self.file2_lines = f2.readlines()
                
            # Calculate diff using SequenceMatcher
            self.calculate_line_diffs()
            
        except Exception as e:
            # Create error displays for both panels
            self.line_diffs_file1 = [("error", f"Error loading files: {e}")]
            self.line_diffs_file2 = [("error", f"Error loading files: {e}")]
            
    def refresh_diff_view(self) -> None:
        """Refresh the diff view after saving changes."""
        # Clear existing content
        file1_content = self.query_one("#file1-content", Vertical)
        file2_content = self.query_one("#file2-content", Vertical)
        
        # Remove all existing widgets
        file1_content.remove_children()
        file2_content.remove_children()
        
        # Repopulate with new diff content
        for i, (diff_type, line) in enumerate(self.line_diffs_file1):
            display_line = line if line else " "
            file1_content.mount(Static(display_line, classes=diff_type, id=f"file1-line-{i}", markup=True))
            
        for i, (diff_type, line) in enumerate(self.line_diffs_file2):
            display_line = line if line else " "
            
            # For modified lines, create a container with the line and accept/reject buttons
            if diff_type in ["added", "changed"]:
                line_container = Container(
                    Static(display_line, classes=diff_type, id=f"file2-line-{i}", markup=True),
                    Horizontal(
                        Button("Accept", id=f"accept-{i}", classes="accept-button"),
                        Button("Reject", id=f"reject-{i}", classes="reject-button"),
                        id=f"buttons-{i}",
                        classes="line-buttons"
                    ),
                    id=f"line-container-{i}",
                    classes="line-container"
                )
                file2_content.mount(line_container)
            else:
                line_container = Container(
                    Static(display_line, classes=diff_type, id=f"file2-line-{i}", markup=True),
                    id=f"line-container-{i}",
                    classes="line-container"
                )
                file2_content.mount(line_container)
            
    def calculate_line_diffs(self) -> None:
        """Calculate differences between the two files line by line."""
        matcher = SequenceMatcher(None, self.file1_lines, self.file2_lines)
        
        # Initialize with all lines as unchanged
        self.line_diffs_file1 = [("unchanged", line.rstrip()) for line in self.file1_lines]
        self.line_diffs_file2 = [("unchanged", line.rstrip()) for line in self.file2_lines]
        
        # Apply diff tags based on matcher results
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'delete':
                # Mark lines in file1 as removed
                for i in range(i1, i2):
                    self.line_diffs_file1[i] = ("removed", self.line_diffs_file1[i][1])
            elif tag == 'insert':
                # Mark lines in file2 as added
                for j in range(j1, j2):
                    self.line_diffs_file2[j] = ("added", self.line_diffs_file2[j][1])
            elif tag == 'replace':
                # For replacement, treat as changed lines when same number of lines
                # or separate delete/insert when different number of lines
                
                # Number of lines changed in each file
                file1_changes = i2 - i1
                file2_changes = j2 - j1
                
                if file1_changes == file2_changes:
                    # Same number of lines - treat as changed lines and compute inline diffs
                    for i, j in zip(range(i1, i2), range(j1, j2)):
                        if i < len(self.line_diffs_file1) and j < len(self.line_diffs_file2):
                            # Compute inline diff for these lines
                            inline_diff1, inline_diff2 = self.compute_inline_diff(
                                self.line_diffs_file1[i][1], 
                                self.line_diffs_file2[j][1]
                            )
                            self.line_diffs_file1[i] = ("changed", inline_diff1)
                            self.line_diffs_file2[j] = ("changed", inline_diff2)
                else:
                    # Different number of lines - mark as removed in file1 and added in file2
                    for i in range(i1, i2):
                        if i < len(self.line_diffs_file1):
                            self.line_diffs_file1[i] = ("removed", self.line_diffs_file1[i][1])
                    for j in range(j1, j2):
                        if j < len(self.line_diffs_file2):
                            self.line_diffs_file2[j] = ("added", self.line_diffs_file2[j][1])
                    
    def compute_inline_diff(self, line1: str, line2: str) -> tuple:
        """Compute character-level differences between two lines and return marked up strings
        in GitKraken style with inline highlighting."""
        # For unchanged lines, return as is
        if line1 == line2:
            return line1, line2
            
        # Create a SequenceMatcher for character-level differences
        char_matcher = SequenceMatcher(None, line1, line2)
        
        # For GitKraken-style inline diff, we show both old and new text in the modified file panel
        # The original file panel shows the original text
        # The modified file panel shows the new text with inline changes
        
        # Build marked up string for the modified file (file2)
        marked_line2 = ""
        
        # Process changes to build the inline diff for file2
        for tag, i1, i2, j1, j2 in char_matcher.get_opcodes():
            if tag == 'equal':
                # Common text - add without markup
                marked_line2 += line2[j1:j2]
            elif tag == 'delete':
                # Text removed from line1 - mark in red with strike-through
                marked_line2 += f"[red strike]{line1[i1:i2]}[/red strike]"
            elif tag == 'insert':
                # Text added to line2 - mark in green
                marked_line2 += f"[green]{line2[j1:j2]}[/green]"
            elif tag == 'replace':
                # Text replaced - mark old in red with strike-through and new in green
                marked_line2 += f"[red strike]{line1[i1:i2]}[/red strike]" + f"[green]{line2[j1:j2]}[/green]"
                
        return line1, marked_line2
        
    def compose_file_content(self, file_type: str) -> ComposeResult:
        """Compose file content with diff highlighting."""
        if file_type == "file1":
            for diff_type, line in self.line_diffs_file1:
                # Handle empty lines by adding a space
                display_line = line if line else " "
                yield Static(display_line, classes=diff_type)
        else:  # file2
            for diff_type, line in self.line_diffs_file2:
                # Handle empty lines by adding a space
                display_line = line if line else " "
                yield Static(display_line, classes=diff_type)
        
    def compose(self) -> ComposeResult:
        """Create the UI layout with split-screen view and professional control panel."""
        yield Header()
        
        # Professional control panel with better button arrangement
        yield Container(
            Button("Accept All", id="accept-all"),
            Button("Reject All", id="reject-all"),
            Button("Save Changes", id="save-changes"),
            id="control-panel"
        )
        
        yield Horizontal(
            Vertical(
                Static("File Tree", id="sidebar-header"),
                Tree("Files", id="file-tree"),
            ),
            Vertical(
                Static(f"Original File: {self.file1_path}", id="file1-header"),
                Vertical(id="file1-content"),
            ),
            Vertical(
                Static(f"Modified File: {self.file2_path}", id="file2-header"),
                Vertical(id="file2-content"),
            ),
            id="main-content"
        )
        yield Footer()
        
    def action_quit(self) -> None:
        """Quit the application with a message."""
        self.exit("Thanks for using GitDiffViewer!")
        
    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.dark = not self.dark
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        
        if button_id == "accept-all":
            self.accept_all_changes()
        elif button_id == "reject-all":
            self.reject_all_changes()
        elif button_id == "save-changes":
            self.save_changes()
        elif button_id.startswith("accept-"):
            line_index = int(button_id.split("-")[-1])
            self.accept_single_change(line_index)
        elif button_id.startswith("reject-"):
            line_index = int(button_id.split("-")[-1])
            self.reject_single_change(line_index)
            
    def accept_all_changes(self) -> None:
        """Accept all changes in the diff view."""
        # Mark all changes as accepted
        for i, (diff_type, line) in enumerate(self.line_diffs_file2):
            if diff_type in ["added", "changed"] and i not in self.accepted_changes:
                self.accepted_changes.append(i)
                
        # Update UI to reflect accepted changes
        for i in self.accepted_changes:
            try:
                accept_button = self.query_one(f"#accept-{i}", Button)
                accept_button.label = "Undo"
                accept_button.add_class("accepted-button")
                accept_button.remove_class("accept-button")
            except:
                # Button might not exist for some lines
                pass
            
        # Show notification
        self.notify("All changes accepted", severity="information")
            
    def reject_all_changes(self) -> None:
        """Reject all changes in the diff view."""
        # Clear all accepted changes
        self.accepted_changes.clear()
        
        # Update UI to reflect rejected changes
        try:
            buttons = self.query("Button")
            for button in buttons:
                if button.id and button.id.startswith("accept-"):
                    button.label = "Accept"
                    button.add_class("accept-button")
                    button.remove_class("accepted-button")
        except:
            # No buttons found
            pass
            
        # Show notification
        self.notify("All changes rejected", severity="information")
                
    def accept_single_change(self, line_index: int) -> None:
        """Accept a single change by line index."""
        if line_index not in self.accepted_changes:
            self.accepted_changes.append(line_index)
            
            # Update button to show it's accepted
            accept_button = self.query_one(f"#accept-{line_index}", Button)
            accept_button.label = "Undo"
            accept_button.add_class("accepted-button")
            accept_button.remove_class("accept-button")
        else:
            # If already accepted, unaccept it
            self.accepted_changes.remove(line_index)
            
            # Update button to show it's no longer accepted
            accept_button = self.query_one(f"#accept-{line_index}", Button)
            accept_button.label = "Accept"
            accept_button.add_class("accept-button")
            accept_button.remove_class("accepted-button")
            
    def reject_single_change(self, line_index: int) -> None:
        """Reject a single change by line index."""
        if line_index in self.accepted_changes:
            self.accepted_changes.remove(line_index)
            
            # Update accept button to show it's no longer accepted
            accept_button = self.query_one(f"#accept-{line_index}", Button)
            accept_button.label = "Accept"
            accept_button.add_class("accept-button")
            accept_button.remove_class("accepted-button")
            
            # No need to update reject button styling as it doesn't change state
            
    def save_changes(self) -> None:
        """Save accepted changes to file1 and refresh the diff view."""
        try:
            # Create a new version of file1 with accepted changes
            new_file1_lines = []
            
            matcher = SequenceMatcher(None, self.file1_lines, self.file2_lines)
            opcodes = list(matcher.get_opcodes())
            
            # Process each opcode to build the new file1
            for tag, i1, i2, j1, j2 in opcodes:
                if tag == 'equal':
                    # Add unchanged lines from file1
                    new_file1_lines.extend(self.file1_lines[i1:i2])
                elif tag == 'delete':
                    # Skip deleted lines (they're removed in file2)
                    pass
                elif tag == 'insert':
                    # Add inserted lines if they were accepted
                    for j in range(j1, j2):
                        if j in self.accepted_changes:
                            new_file1_lines.append(self.file2_lines[j])
                elif tag == 'replace':
                    # Check if any replacement lines were accepted
                    replacement_indices = list(range(j1, j2))
                    accepted_in_replacement = [j for j in replacement_indices if j in self.accepted_changes]
                    
                    if accepted_in_replacement:
                        # Add only the accepted lines from file2
                        for j in replacement_indices:
                            if j in self.accepted_changes:
                                new_file1_lines.append(self.file2_lines[j])
                    else:
                        # If no lines were accepted, keep original lines from file1
                        new_file1_lines.extend(self.file1_lines[i1:i2])
                    
            # Save to file1
            with open(self.file1_path, 'w') as f1:
                f1.writelines(new_file1_lines)
                
            # Clear accepted changes since we've saved them
            self.accepted_changes.clear()
            
            # Refresh the diff view so buttons reset
            self.load_files_and_calculate_diff()
            self.refresh_diff_view()
            
            # Reset accept button styles (reject buttons don't change state)
            try:
                buttons = self.query("Button")
                for button in buttons:
                    if button.id and button.id.startswith("accept-"):
                        button.label = "Accept"
                        button.add_class("accept-button")
                        button.remove_class("accepted-button")
            except:
                # No buttons found
                pass
            
            # Show success message
            self.notify("Changes saved successfully to file 1!", severity="information")
            
        except Exception as e:
            self.notify(f"Error saving changes: {e}", severity="error")
            
    def populate_file_tree(self) -> None:
        """Populate the file tree sidebar with files and their git status."""
        if not self.git_sidebar.repo:
            # If not in a git repo, just show a simple file tree
            self.populate_simple_file_tree()
            return
            
        try:
            # Get the tree widget
            tree = self.query_one("#file-tree", Tree)
            
            # Clear existing tree
            tree.clear()
            
            # Get file tree with git status
            file_tree = self.git_sidebar.get_file_tree()
            
            # Build tree structure
            root_nodes = {}
            
            for file_path, file_type, git_status in file_tree:
                # Split path into components
                parts = file_path.split('/')
                
                # Create nodes for each directory level if they don't exist
                current_nodes = root_nodes
                current_tree_node = tree.root
                
                # Navigate/create intermediate nodes
                for i, part in enumerate(parts[:-1] if file_type == "file" else parts):
                    path_key = '/'.join(parts[:i+1])
                    if path_key not in current_nodes:
                        # Create directory node
                        current_tree_node = current_tree_node.add(part, expand=True)
                        current_nodes[path_key] = current_tree_node
                    else:
                        current_tree_node = current_nodes[path_key]
                
                # Add the file or last directory node
                if file_type == "file":
                    # Add file node with git status as data
                    label = parts[-1] if parts else file_path
                    leaf_node = current_tree_node.add_leaf(label, data=git_status)
                    # Add CSS class based on git status
                    leaf_node.set_class(True, git_status)
                else:
                    # For directories
                    if file_path not in root_nodes:
                        label = parts[-1] if parts else file_path
                        dir_node = current_tree_node.add(label, expand=True)
                        dir_node.set_class(True, "directory")
                        root_nodes[file_path] = dir_node
            
        except Exception as e:
            # If we can't populate the tree, that's okay - just continue without it
            self.populate_simple_file_tree()
            
    def populate_simple_file_tree(self) -> None:
        """Populate a simple file tree without git status when not in a git repo."""
        try:
            tree = self.query_one("#file-tree", Tree)
            tree.clear()
            
            # Add the two files being compared
            tree.root.add_leaf(Path(self.file1_path).name, data="file1")
            tree.root.add_leaf(Path(self.file2_path).name, data="file2")
            
        except Exception:
            pass
