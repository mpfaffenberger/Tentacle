# Tentacle Git Status Sidebar Test Plan

## Overview
This document outlines a comprehensive test plan for the Git Status Sidebar functionality, including the file tree display which we've recently fixed.

## Test Cases

### File Tree Display
1. **Basic functionality** - Verify that the file tree correctly displays all files and directories in a repository
   - Setup: Create a test repository with various files and directories
   - Action: Initialize the GitStatusSidebar and call get_file_tree()
   - Expected: All files and directories should be returned in the list, excluding .git directory

2. **Nested directories** - Verify that deeply nested directory structures are properly displayed
   - Setup: Create a test repository with nested directories (at least 3 levels deep)
   - Action: Call get_file_tree() method
   - Expected: All nested files and directories should be included in the returned list

3. **Large repositories** - Verify that the file tree still works with repositories containing hundreds of files
   - Setup: Create or use a large repository
   - Action: Call get_file_tree() method
   - Expected: Method should return complete file tree without hanging or crashing

4. **Empty repositories** - Verify behavior with an empty repository
   - Setup: Create a git repository with no files except .git directory
   - Action: Call get_file_tree() method
   - Expected: Should return an empty list (possibly just the root directory)

5. **Fallback mechanism** - Verify that the git ls-files fallback works when pathlib.Path.walk() fails
   - Setup: Create conditions where pathlib.Path.walk() might fail (mock.patch could be used)
   - Action: Call get_file_tree() method
   - Expected: Should gracefully fallback to using git ls-files and still return correct file tree

### Git Status Detection
1. **Untracked files** - Verify that untracked files are properly marked
   - Setup: Create a test repository with some untracked files
   - Action: Call get_file_tree() method
   - Expected: Untracked files should have status "untracked"

2. **Modified files** - Verify that modified files are properly marked
   - Setup: Create a test repository with some modified files
   - Action: Call get_file_tree() method
   - Expected: Modified files should have status "modified"

3. **Deleted files** - Verify that deleted files are properly marked
   - Setup: Create a test repository with some deleted files
   - Action: Call get_file_tree() method
   - Expected: Deleted files should have status "deleted"

4. **Staged files** - Verify that staged files are properly marked
   - Setup: Create a test repository with some staged files
   - Action: Call get_file_tree() method
   - Expected: Staged files should have status "staged"

### Error Handling
1. **Non-existent repository path** - Verify graceful handling of invalid paths
   - Setup: Point to a non-existent directory
   - Action: Initialize GitStatusSidebar with invalid path
   - Expected: Should handle error gracefully without crashing

2. **Non-git repository** - Verify behavior when path is not a git repository
   - Setup: Use a directory that is not a git repository
   - Action: Initialize GitStatusSidebar and call get_file_tree()
   - Expected: Should handle error gracefully, possibly returning empty list

3. **Permission denied** - Verify behavior when lacking permissions to read repository
   - Setup: Create a repository with restricted permissions
   - Action: Call get_file_tree() method
   - Expected: Should handle error gracefully and not crash the application

## Test Implementation

Tests should be written using pytest and should mock git operations where appropriate to avoid creating actual repositories.

Each test should cover:
- The specific functionality
- Edge cases
- Error conditions
