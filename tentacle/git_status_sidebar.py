from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
import tempfile
import os
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
            
    def get_untracked_files(self) -> List[str]:
        """Get list of untracked files in the repository.
        
        Returns:
            List of file paths that are untracked
        """
        if not self.repo:
            return []
            
        return self.repo.untracked_files
        
    def get_files_with_unstaged_changes(self) -> List[str]:
        """Get list of files with unstaged changes (modified and untracked).
        
        Returns:
            List of file paths that have unstaged changes
        """
        if not self.repo:
            return []
            
        statuses = self.get_file_statuses()
        unstaged_files = []
        
        for file_path, status in statuses.items():
            if status in ["modified", "untracked"]:
                unstaged_files.append(file_path)
                
        return unstaged_files
        
    def get_staged_files(self) -> List[str]:
        """Get list of staged files in the repository.
        
        Returns:
            List of file paths that are staged
        """
        if not self.repo:
            return []
            
        # Get staged changes
        staged_files = self.repo.index.diff("HEAD")
        return [diff.b_path for diff in staged_files]
            
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
            
    def get_files_with_unstaged_changes(self) -> List[str]:
        """Get a list of files that have unstaged changes.
        
        Returns:
            List of file paths that have unstaged changes (modified or untracked)
        """
        if not self.repo:
            return []
            
        try:
            # Get modified files
            unstaged_files = self.repo.index.diff(None)
            modified_files = [diff.b_path for diff in unstaged_files]
            
            # Add untracked files
            untracked_files = self.repo.untracked_files
            
            # Combine both lists
            all_unstaged = modified_files + untracked_files
            
            # Remove duplicates while preserving order
            seen = set()
            result = []
            for file_path in all_unstaged:
                if file_path not in seen:
                    seen.add(file_path)
                    result.append(file_path)
            
            return result
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
        
    def get_diff_hunks(self, file_path: str, staged: bool = False) -> List[Hunk]:
        """Get diff hunks for a specific file.
        
        Args:
            file_path: Path to the file relative to repository root
            staged: Whether to get staged diff
            
        Returns:
            List of Hunk objects representing the diff hunks
        """
        if not self.repo:
            return []
            
        try:
            diff_cmd = ['--', file_path]
            if staged:
                diff_cmd.insert(0, '--cached')
            diff = self.repo.git.diff(*diff_cmd)
            if not diff:
                status = self.get_file_status(file_path)
                if staged:
                    return []
                if status == "untracked":
                    with (self.repo_path / file_path).open('r') as f:
                        content = f.read()
                    lines = ['+' + l for l in content.splitlines()]
                    return [Hunk("@@ -0,0 +1," + str(len(lines)) + " @@", lines)]
                elif status == "unchanged":
                    with (self.repo_path / file_path).open('r') as f:
                        content = f.read()
                    lines = content.splitlines()
                    return [Hunk("", lines)]
                else:
                    return []
            hunks = self._parse_diff_into_hunks(diff)
            if file_path.endswith('.md'):
                hunks = self._filter_whitespace_hunks(hunks)
            return hunks
        except Exception:
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
            
            for commit in commits:
                commit_info = CommitInfo(
                    sha=commit.hexsha[:8],  # Short SHA
                    message=commit.message.strip(),
                    author=commit.author.name,
                    date=commit.committed_datetime
                )
                commit_info_list.append(commit_info)
                
            return commit_info_list
        except Exception:
            return []
            
    def get_current_branch(self) -> str:
        """Get the current branch name.
        
        Returns:
            Current branch name or 'unknown' if not in a repo
        """
        if not self.repo:
            return "unknown"
            
        try:
            return self.repo.active_branch.name
        except Exception:
            return "unknown"
            
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
            
    def get_all_branches(self) -> List[str]:
        """Get all branch names in the repository.
        
        Returns:
            List of branch names
        """
        if not self.repo:
            return []
            
        try:
            # Try a simpler approach using git branch command
            branches_output = self.repo.git.branch()
            branches = [branch.strip() for branch in branches_output.split('\n')]
            # Remove the '*' marker from current branch and filter out empty lines
            branches = [branch.replace('*', '').strip() for branch in branches if branch.strip()]
            return branches
        except Exception:
            # Fallback to the previous method
            try:
                branches = [ref.name for ref in self.repo.refs if ref.name.startswith('refs/heads/')]
                # Remove the 'refs/heads/' prefix
                branches = [branch.replace('refs/heads/', '') for branch in branches]
                return branches
            except Exception:
                return []
            
    def is_dirty(self) -> bool:
        """Check if the repository has modified or staged changes.
        
        Returns:
            True if repository is dirty, False otherwise
        """
        if not self.repo:
            return False
            
        try:
            # Check for staged changes
            if self.get_staged_files():
                return True
            
            # Check for unstaged changes
            if self.get_unstaged_files():
                return True
                
            return False
        except Exception:
            return False
            
    def switch_branch(self, branch_name: str) -> bool:
        """Switch to a different branch.
        
        Args:
            branch_name: Name of the branch to switch to
            
        Returns:
            True if successful, False otherwise
        """
        if not self.repo or self.is_dirty():
            return False
            
        try:
            self.repo.git.checkout(branch_name)
            return True
        except Exception:
            return False

    def _reverse_hunk_header(self, header: str) -> str:
        match = re.match(r'@@ -(\\d+),(\\d+) \\+(\\d+),(\\d+) @@', header)
        if match:
            old_start, old_len, new_start, new_len = map(int, match.groups())
            return f"@@ -{new_start},{new_len} +{old_start},{old_len} @@"
        return header

    def _create_patch_from_hunk(self, hunk: Hunk, reverse: bool = False) -> str:
        if reverse:
            header = self._reverse_hunk_header(hunk.header)
            reversed_lines = []
            for line in hunk.lines:
                if line.startswith('+'):
                    reversed_lines.append('-' + line[1:])
                elif line.startswith('-'):
                    reversed_lines.append('+' + line[1:])
                else:
                    reversed_lines.append(line)
            lines = [header] + reversed_lines
        else:
            lines = [hunk.header] + hunk.lines
        return '\n'.join(lines) + '\n'

    def _apply_patch(self, patch: str, cached: bool = False, reverse: bool = False, index: bool = False) -> bool:
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.write(patch)
            tmp_path = tmp.name
        args = []
        if reverse:
            args.append('-R')
        if cached:
            args.append('--cached')
        if index:
            args.append('--index')
        args.append(tmp_path)
        try:
            self.repo.git.apply(*args)
            return True
        except git.GitCommandError as e:
            print(f"Error applying patch: {e}")
            return False
        finally:
            os.unlink(tmp_path)

    def stage_hunk(self, file_path: str, hunk_index: int) -> bool:
        hunks = self.get_diff_hunks(file_path, staged=False)
        if hunk_index >= len(hunks):
            return False
        hunk = hunks[hunk_index]
        patch = self._create_patch_from_hunk(hunk)
        return self._apply_patch(patch, cached=True)

    def unstage_hunk(self, file_path: str, hunk_index: int) -> bool:
        hunks = self.get_diff_hunks(file_path, staged=True)
        if hunk_index >= len(hunks):
            return False
        hunk = hunks[hunk_index]
        patch = self._create_patch_from_hunk(hunk, reverse=True)
        return self._apply_patch(patch, index=True)

    def discard_hunk(self, file_path: str, hunk_index: int) -> bool:
        hunks = self.get_diff_hunks(file_path, staged=False)
        if hunk_index >= len(hunks):
            return False
        hunk = hunks[hunk_index]
        patch = self._create_patch_from_hunk(hunk, reverse=True)
        return self._apply_patch(patch)