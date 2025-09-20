from pathlib import Path
from typing import Dict, List, Optional, Tuple
import git


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
            
    def get_file_statuses(self) -> Dict[str, str]:
        """Get git status for all files in the repository.
        
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
        
    def get_file_tree(self, directory: Path = None) -> List[Tuple[str, str, str]]:
        """Get file tree with git status information.
        
        Args:
            directory: Directory to scan. If None, uses repo root.
            
        Returns:
            List of tuples (file_path, file_type, git_status) where:
            - file_path is the relative path to the file
            - file_type is "file" or "directory"
            - git_status is one of "modified", "staged", "untracked", or "unchanged"
        """
        if not self.repo:
            return []
            
        if directory is None:
            directory = self.repo_path
            
        file_tree = []
        
        try:
            # Get all files in directory recursively
            for item in directory.rglob("*"):
                # Skip hidden files and directories
                if any(part.startswith(".") for part in item.parts):
                    continue
                    
                # Skip __pycache__ directories
                if "__pycache__" in item.parts:
                    continue
                    
                relative_path = str(item.relative_to(self.repo_path))
                
                if item.is_dir():
                    # Add directory entry
                    file_tree.append((relative_path, "directory", "directory"))
                else:
                    # Check git status for files
                    file_status = self._get_file_status(relative_path)
                    file_tree.append((relative_path, "file", file_status))
                    
        except Exception:
            # Directory might not exist or be accessible
            pass
            
        # Sort by path
        file_tree.sort(key=lambda x: x[0])
        return file_tree
        
    def _get_file_status(self, file_path: str) -> str:
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
