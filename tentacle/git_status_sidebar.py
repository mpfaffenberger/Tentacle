from pathlib import Path
from typing import Dict, List, Optional, Tuple
import git
from dataclasses import dataclass
from datetime import datetime

# Import for backward compatibility with existing code
from typing import List as ListType


@dataclass
class Hunk:
    """Represents a diff hunk with header and line information."""
    header: str
    lines: List[str]
    
    def __post_init__(self):
        # Remove the newline at the end of header if present
        if self.header.endswith('\n'):
            self.header = self.header[:-1]

@dataclass
class CommitInfo:
    """Represents commit information for history display."""
    sha: str
    message: str
    author: str
    date: datetime
    parents: List[str]  # List of parent commit SHAs
    branches: List[str]  # List of branches this commit belongs to
    
    def __post_init__(self):
        # Remove the newline at the end of message if present
        if self.message.endswith('\n'):
            self.message = self.message[:-1]


class GitStatusSidebar:
    """Manages git repository status and file tree display."""
    
    def __init__(self, repo_path: Optional[str] = None):
        """Initialize the git status sidebar.
        
        Args:
            repo_path: Path to the git repository. If None, uses current directory.
        """
        try:
            self.repo = git.Repo(repo_path or ".", search_parent_directories=True)
            self.repo_path = Path(self.repo.working_dir)
        except git.InvalidGitRepositoryError:
            self.repo = None
            self.repo_path = Path("")
        except Exception:
            self.repo = None
            self.repo_path = Path("")
            
    def get_file_statuses(self) -> Dict[str, str]:
        """Get git status for tracked files in the repository.
        
        Returns:
            Dictionary mapping file paths to their git status (modified, staged, etc.)
        """
        if not self.repo:
            return {}
            
        statuses = {}
        
        # Get staged changes
        staged_files = self.repo.index.diff("HEAD")
        for diff in staged_files:
            statuses[diff.b_path] = "staged"
            
        # Get unstaged changes
        unstaged_files = self.repo.index.diff(None)
        for diff in unstaged_files:
            statuses[diff.b_path] = "modified"
            
        # Get untracked files
        untracked_files = self.repo.untracked_files
        for file_path in untracked_files:
            statuses[file_path] = "untracked"
            
        return statuses
        
    def get_staged_files(self) -> List[str]:
        """Get a list of staged files.
        
        Returns:
            List of file paths that are staged
        """
        if not self.repo:
            return []
            
        try:
            staged_files = self.repo.index.diff("HEAD")
            return [diff.b_path for diff in staged_files]
        except Exception:
            return []
            
    def get_unstaged_files(self) -> List[str]:
        """Get a list of unstaged (modified) files.
        
        Returns:
            List of file paths that are modified but not staged
        """
        if not self.repo:
            return []
            
        try:
            unstaged_files = self.repo.index.diff(None)
            return [diff.b_path for diff in unstaged_files]
        except Exception:
            return []
            
    def get_untracked_files(self) -> List[str]:
        """Get a list of untracked files.
        
        Returns:
            List of file paths that are untracked
        """
        if not self.repo:
            return []
            
        try:
            return self.repo.untracked_files
        except Exception:
            return []
        
    def get_file_tree(self) -> List[Tuple[str, str, str]]:
        """Get a flattened list of all files with their git status.
        
        Returns:
            List of tuples (file_path, file_type, git_status) where file_type is "file" or "directory"
            and git_status is "staged", "modified", "untracked", or "unchanged"
        """
        if not self.repo:
            return []
            
        try:
            file_list = []
            
            # Check if repo_path exists and is valid
            if not self.repo_path.exists() or not self.repo:
                return []
            
            # Get all files and directories in the repository
            try:
                # Handle root directory items
                for item in self.repo_path.iterdir():
                    if not item.exists() or '.git' in item.parts:
                        continue
                        
                    if item.is_dir():
                        file_list.append((item.name, "directory", "unchanged"))
                    elif item.is_file():
                        file_list.append((item.name, "file", "unchanged"))
                
                # Walk subdirectories
                for root, dirs, files in self.repo_path.walk():
                    # Skip git directory
                    if '.git' in root.parts:
                        continue
                    
                    # Skip root directory since we already handled it
                    if root == self.repo_path:
                        continue
                        
                    # Add directories
                    for dir_name in dirs:
                        dir_path = (root / dir_name).relative_to(self.repo_path)
                        file_list.append((str(dir_path), "directory", "unchanged"))
                        
                    # Add files
                    for file_name in files:
                        file_path = (root / file_name).relative_to(self.repo_path)
                        file_list.append((str(file_path), "file", "unchanged"))
            except Exception:
                pass
            
            # Always use git ls-files as the primary approach since it's more reliable
            # Only use pathlib for directories as a true fallback
            try:
                file_list = []
                
                # Get all tracked files
                tracked_files = self.repo.git.ls_files().splitlines()
                for file_path in tracked_files:
                    # Only add files that exist and aren't in .git directory
                    full_path = self.repo_path / file_path
                    if full_path.exists() and '.git' not in full_path.parts:
                        file_list.append((file_path, "file", "unchanged"))
                
                # Add untracked files
                untracked_files = self.repo.untracked_files
                for file_path in untracked_files:
                    full_path = self.repo_path / file_path
                    if full_path.exists() and '.git' not in full_path.parts:
                        file_list.append((file_path, "file", "untracked"))
                
                # Add all directories in the repository (but not .git directories)
                try:
                    # Use git to get all directories in the repository
                    ls_tree_dirs = self.repo.git.ls_tree("--full-tree", "-d", "--name-only", "HEAD")
                    tracked_directories = ls_tree_dirs.splitlines() if ls_tree_dirs else []
                    
                    directories = set()
                    # Add tracked directories
                    for dir_path in tracked_directories:
                        if dir_path and '.git' not in dir_path.split('/'):
                            directories.add(dir_path)
                    
                    # Also check for empty directories that might not be in ls-tree but are in the repo
                    # Only walk the repository root, not into subdirectories like .venv
                    for item in self.repo_path.iterdir():
                        if item.is_dir() and '.git' not in item.parts and item.name != '.venv' and item.name != '.pytest_cache' and item.name != 'dist':
                            directories.add(item.name)
                    
                    # Add directories to file_list
                    for dir_path in directories:
                        file_list.append((dir_path, "directory", "unchanged"))
                except Exception:
                    # If git operations fail, just proceed with files only
                    pass
                    
            except Exception:
                # If git ls-files fails, use pathlib walk as fallback
                try:
                    file_list = []
                    
                    # Handle root directory items
                    for item in self.repo_path.iterdir():
                        if not item.exists() or '.git' in item.parts:
                            continue
                        
                        if item.is_dir():
                            file_list.append((item.name, "directory", "unchanged"))
                        elif item.is_file():
                            file_list.append((item.name, "file", "unchanged"))
                    
                    # Walk subdirectories
                    for root, dirs, files in self.repo_path.walk():
                        # Skip git directory
                        if '.git' in root.parts:
                            continue
                        
                        # Skip root directory since we already handled it
                        if root == self.repo_path:
                            continue
                            
                        # Add directories
                        for dir_name in dirs:
                            dir_path = (root / dir_name).relative_to(self.repo_path)
                            file_list.append((str(dir_path), "directory", "unchanged"))
                            
                        # Add files
                        for file_name in files:
                            file_path = (root / file_name).relative_to(self.repo_path)
                            file_list.append((str(file_path), "file", "unchanged"))
                except Exception:
                    return []
            
            # Get file statuses
            statuses = self.get_file_statuses()
            
            # Update file list with actual statuses
            for i, (file_path, file_type, git_status) in enumerate(file_list):
                if file_type == "file":
                    actual_status = statuses.get(file_path, "unchanged")
                    file_list[i] = (file_path, file_type, actual_status)
                
            return file_list
        except Exception:
            return []
        
    def get_diff_hunks(self, file_path: str) -> List[Hunk]:
        """Get diff hunks for a specific file.
        
        Args:
            file_path: Path to the file relative to repository root
            
        Returns:
            List of Hunk objects representing the diff hunks
        """
        if not self.repo:
            return []
            
        try:
            # Check if file is staged
            file_status = self.get_file_status(file_path)
            
            if file_status == "staged":
                # Get diff between HEAD and index
                diff = self.repo.git.diff("HEAD", "--", file_path)
            elif file_status == "modified":
                # Get diff between index and working tree
                diff = self.repo.git.diff("--", file_path)
            elif file_status == "untracked":
                # For untracked files, just show the content
                with open(self.repo_path / file_path, 'r') as f:
                    content = f.read()
                lines = content.splitlines()
                return [Hunk(header="@@ -0,0 +1,@@", lines=lines)]
            else:
                # For unchanged files, show current content without diffs
                with open(self.repo_path / file_path, 'r') as f:
                    content = f.read()
                lines = content.splitlines()
                return [Hunk(header="", lines=lines)]
                
            # Parse the diff into hunks
            hunks = self._parse_diff_into_hunks(diff)
            
            # For markdown files, filter out whitespace-only changes
            if file_path.endswith('.md'):
                hunks = self._filter_whitespace_hunks(hunks)
                
            return hunks
            
        except Exception as e:
            # If we can't get the diff, return an empty list
            return []
        
    def _is_whitespace_only_change(self, old_line: str, new_line: str) -> bool:
        """Check if a change is only whitespace differences.
        
        Args:
            old_line: The original line
            new_line: The new line
            
        Returns:
            True if the change is only whitespace, False otherwise
        """
        # Strip the lines to compare content
        old_stripped = old_line.strip()
        new_stripped = new_line.strip()
        
        # If stripped lines are identical, it's a whitespace-only change
        if old_stripped == new_stripped:
            return True
            
        # For markdown bullet points, check if it's just leading space differences
        # But only if the bullet type is the same
        bullet_types = ['- ', '* ', '+ ']
        for bullet in bullet_types:
            if old_stripped.startswith(bullet) and new_stripped.startswith(bullet):
                # Get the content part (without the bullet)
                old_content = old_stripped[len(bullet):]
                new_content = new_stripped[len(bullet):]
                return old_content == new_content
        
        # Not a whitespace-only change
        return False
    
    def _filter_whitespace_hunks(self, hunks: List[Hunk]) -> List[Hunk]:
        """Filter out hunks that contain only whitespace changes.
        
        Args:
            hunks: List of hunks to filter
            
        Returns:
            List of hunks with meaningful changes
        """
        filtered_hunks = []
        
        for hunk in hunks:
            # We'll implement a simple filter that removes lines where the only change is whitespace
            filtered_lines = []
            i = 0
            while i < len(hunk.lines):
                line = hunk.lines[i]
                
                # Handle diff lines
                if line and line[:1] == '-':  # Only check first character to avoid confusion with content starting with '-'
                    # Check if there's a corresponding addition line
                    if i + 1 < len(hunk.lines) and hunk.lines[i + 1] and hunk.lines[i + 1][:1] == '+':  # Only check first character
                        next_line = hunk.lines[i + 1]
                        
                        # Check if they're only whitespace different
                        if self._is_whitespace_only_change(line[1:], next_line[1:]):  # Skip the +/- prefix
                            # Skip both lines (filter out this whitespace change)
                            i += 2
                            continue
                        else:
                            filtered_lines.append(line)
                            filtered_lines.append(next_line)
                            i += 2
                            continue
                    else:
                        filtered_lines.append(line)
                        i += 1
                elif line and line[:1] == '+':  # Only check first character to avoid confusion with content starting with '+'
                    # Check if there's a corresponding removal line
                    if i > 0 and hunk.lines[i - 1] and hunk.lines[i - 1][:1] == '-':  # Only check first character
                        # This line was already processed with the previous line, skip it
                        i += 1
                        continue
                    else:
                        # This is an addition without a corresponding removal
                        filtered_lines.append(line)
                        i += 1
                else:
                    # Context line (unchanged)
                    filtered_lines.append(line)
                    i += 1
                    
            # Only add hunk if it has meaningful content
            filtered_hunks.append(Hunk(header=hunk.header, lines=filtered_lines))
            
        return filtered_hunks
    
    def _parse_diff_into_hunks(self, diff: str) -> List[Hunk]:
        """Parse a unified diff string into hunks.
        
        Args:
            diff: Unified diff string
            
        Returns:
            List of Hunk objects
        """
        hunks = []
        lines = diff.splitlines()
        
        current_hunk_lines = []
        current_hunk_header = ""
        
        for line in lines:
            if line.startswith("@@"):
                # If we have a previous hunk, save it
                if current_hunk_header and current_hunk_lines:
                    hunks.append(Hunk(header=current_hunk_header, lines=current_hunk_lines))
                    current_hunk_lines = []
                
                # Start new hunk
                current_hunk_header = line
            elif current_hunk_header:
                # Add line to current hunk
                current_hunk_lines.append(line)
                
        # Don't forget the last hunk
        if current_hunk_header and current_hunk_lines:
            hunks.append(Hunk(header=current_hunk_header, lines=current_hunk_lines))
            
        # If no hunks were found, return empty hunk
        if not hunks and lines:
            hunks.append(Hunk(header="", lines=lines))
            
        return hunks
        
    def get_file_status(self, file_path: str) -> str:
        """Get the git status of a specific file.
        
        Args:
            file_path: Relative path to the file
            
        Returns:
            Git status: "modified", "staged", "untracked", or "unchanged"
        """
        # Check staged changes first (index vs HEAD)
        try:
            diff_index = self.repo.index.diff("HEAD")
            for diff in diff_index:
                if diff.b_path == file_path:
                    return "staged"
        except Exception:
            pass
            
        # Check unstaged changes (working tree vs index)
        try:
            diff_working = self.repo.index.diff(None)
            for diff in diff_working:
                if diff.b_path == file_path:
                    return "modified"
        except Exception:
            pass
            
        # Check untracked files
        try:
            if file_path in self.repo.untracked_files:
                return "untracked"
        except Exception:
            pass
            
        return "unchanged"
        
    def stage_file(self, file_path: str) -> bool:
        """Stage a file.
        
        Args:
            file_path: Path to the file relative to repository root
            
        Returns:
            True if successful, False otherwise
        """
        if not self.repo:
            return False
            
        try:
            self.repo.index.add([file_path])
            return True
        except Exception:
            return False
            
    def unstage_file(self, file_path: str) -> bool:
        """Unstage a file.
        
        Args:
            file_path: Path to the file relative to repository root
            
        Returns:
            True if successful, False otherwise
        """
        if not self.repo:
            return False
            
        try:
            self.repo.index.remove([file_path], working_tree=False)
            return True
        except Exception:
            return False
            
    def discard_file_changes(self, file_path: str) -> bool:
        """Discard changes to a file.
        
        Args:
            file_path: Path to the file relative to repository root
            
        Returns:
            True if successful, False otherwise
        """
        if not self.repo:
            return False
            
        try:
            self.repo.git.checkout("--", file_path)
            return True
        except Exception:
            return False
            
    def get_commit_history(self) -> List[CommitInfo]:
        """Get commit history.
        
        Returns:
            List of CommitInfo objects
        """
        if not self.repo:
            return []
            
        try:
            commits = list(self.repo.iter_commits('HEAD'))
            commit_info_list = []
            
            # Get branch information
            branch_heads = {}
            try:
                for branch in self.repo.heads:
                    branch_heads[branch.commit.hexsha] = branch.name
            except:
                pass  # If we can't get branches, continue without them
            
            for commit in commits:
                # Get parent commit SHAs
                parents = [parent.hexsha[:8] for parent in commit.parents]
                
                # Get branches this commit belongs to
                branches = []
                if commit.hexsha in branch_heads:
                    branches.append(branch_heads[commit.hexsha])
                
                commit_info = CommitInfo(
                    sha=commit.hexsha[:8],  # Short SHA
                    message=commit.message.strip(),
                    author=commit.author.name,
                    date=commit.committed_datetime,
                    parents=parents,
                    branches=branches
                )
                commit_info_list.append(commit_info)
                
            return commit_info_list
        except Exception:
            return []
            
    def commit_staged_changes(self, message: str) -> bool:
        """Commit staged changes.
        
        Args:
            message: Commit message
            
        Returns:
            True if successful, False otherwise
        """
        if not self.repo:
            return False
            
        try:
            self.repo.index.commit(message)
            return True
        except Exception:
            return False
