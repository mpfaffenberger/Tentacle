# Tentacle: GitKraken-like TUI Development Plan

This document outlines a step-by-step plan to transform the current file diff viewer into a full-featured Git client similar to GitKraken, with a focus on making small, independently developable components.

## Core Customer Problem

Currently, the application only compares two arbitrary files. Users want a Git client that allows them to:
- View repository status and file changes
- Stage/unstage individual hunks of changes (not just lines)
- Discard unwanted changes at the hunk level
- Commit staged changes
- Navigate files through a Git-aware tree view

## Component Decomposition

### Component 1: Git Repository Integration
**Owner:** Git operations specialist
**Dependencies:** None (foundation component)
**Success Criteria:** 
- Application can detect and work with Git repositories
- Can retrieve repository information (branch, status, etc.)
- Error handling for non-Git directories

**Implementation Strategy:**
1. Modify main.py to detect Git repository automatically
2. Create a Git repository manager class
3. Add better error handling for Git operations

**Testing Approach:**
- Unit tests for Git repository detection
- Test in both Git and non-Git directories
- Verify repository information retrieval

**Monitoring Requirements:**
- Log Git operation failures
- Track repository status changes

```
# Estimated effort: 2-3 days
# Complexity: Medium
# Risk: Low (mostly refactoring existing code)
```

### Component 2: Hunk-based Diff Processing
**Owner:** Diff algorithm specialist
**Dependencies:** Component 1
**Success Criteria:**
- Files are processed in hunks rather than lines
- Clear visual separation between hunks
- Accurate detection of related changes

**Implementation Strategy:**
1. Replace line-based diff with hunk-based diff in git_diff_viewer.py
2. Create hunk grouping algorithm
3. Modify data structures to track hunks instead of lines

**Testing Approach:**
- Unit tests for hunk detection algorithm
- Integration tests with various diff scenarios
- Verify hunk boundaries are correctly identified

**Acceptance Tests:**
- Verify consecutive line changes are grouped into hunks
- Verify that unrelated changes are in separate hunks
- Test with files that have insertions, deletions, and modifications

**Monitoring Requirements:**
- Log when hunk processing fails
- Track performance of diff calculations

```
# Estimated effort: 3-4 days
# Complexity: High (algorithm changes)
# Risk: Medium (core functionality change)
```

### Component 3: Hunk Staging Controls
**Owner:** UI/UX specialist
**Dependencies:** Component 2
**Success Criteria:**
- Each hunk has "Stage Hunk" and "Discard Hunk" buttons
- Staged hunks display "Unstage Hunk" button
- Visual indication of staged vs unstaged hunks

**Implementation Strategy:**
1. Replace line-level accept/reject with hunk-level stage/discard
2. Add "Unstage Hunk" button for staged hunks
3. Implement hunk-level operations in the GitDiffViewer class
4. Update CSS styling for staged/unstaged hunks

**Testing Approach:**
- UI tests to verify button states and transitions
- Integration tests with staging operations
- Visual inspection of hunk presentation

**Acceptance Tests:**
- Stage button changes to Unstage when clicked
- Discard button removes hunk from view
- Staged hunks are visually differentiated

**Monitoring Requirements:**
- Track staging operations
- Log staging failures

```
# Estimated effort: 2-3 days
# Complexity: Medium
# Risk: Low (UI changes)
```

### Component 4: Git Status File Tree Enhancement
**Owner:** UI/UX specialist
**Dependencies:** Component 1
**Success Criteria:**
- File tree organized by git status (modified, staged, untracked)
- Clear visual indicators for file status
- Interactive file selection to view changes

**Implementation Strategy:**
1. Enhance git_status_sidebar.py to organize files by status
2. Add tree view filtering and grouping
3. Implement file selection handlers

**Testing Approach:**
- Unit tests for tree organization logic
- Integration tests with different file status combinations
- Verify visual styling matches Git status

**Acceptance Tests:**
- Files appear in correct status groups
- Visual styling matches status (red for modified, green for staged, etc.)
- Clicking files shows their changes in the diff panel

**Monitoring Requirements:**
- Track file tree refresh operations
- Log tree population failures

```
# Estimated effort: 2-3 days
# Complexity: Medium
# Risk: Low
```

### Component 5: Commit Functionality
**Owner:** Git operations specialist
**Dependencies:** Component 1, Component 3
**Success Criteria:**
- Users can commit staged changes
- Commit message input interface
- Commit history display

**Implementation Strategy:**
1. Add commit panel to the UI
2. Create commit message input dialog
3. Implement Git commit operations
4. Display commit history sidebar

**Testing Approach:**
- Unit tests for commit operations
- Integration tests with staged changes
- Verify commit history is displayed correctly

**Acceptance Tests:**
- Staged changes are committed with message
- Commit appears in history after operation
- Unstaged changes remain in working directory

**Monitoring Requirements:**
- Log commit operations and results
- Track commit failures

```
# Estimated effort: 3-4 days
# Complexity: Medium
# Risk: Medium (modifying Git repository)
```

### Component 6: Branch Management
**Owner:** Git operations specialist
**Dependencies:** Component 1
**Success Criteria:**
- Users can view and switch branches
- Users can create new branches
- Current branch is displayed in UI

**Implementation Strategy:**
1. Add branch sidebar panel
2. Implement branch switching functionality
3. Add branch creation interface
4. Display current branch in header/status bar

**Testing Approach:**
- Unit tests for branch operations
- Integration tests for branch switching
- Verify current branch display is accurate

**Acceptance Tests:**
- Branch list displays correctly
- Switching branches updates working directory
- Creating new branches works properly

**Monitoring Requirements:**
- Log branch operations
- Track branch switching failures

```
# Estimated effort: 2-3 days
# Complexity: Medium
# Risk: Medium (modifying Git repository state)
```

### Component 7: Status Bar Enhancement
**Owner:** UI/UX specialist
**Dependencies:** Component 1
**Success Criteria:**
- Status bar shows repository information
- Shows current operation status
- Displays helpful hints for users

**Implementation Strategy:**
1. Replace simple Footer with enhanced status bar
2. Add repository information display
3. Implement operation status indicators
4. Add user guidance hints

**Testing Approach:**
- UI tests for status bar content
- Integration tests with Git operations
- Verify real-time status updates

**Acceptance Tests:**
- Repository path displayed correctly
- Current branch shown
- Operation status updates in real-time

**Monitoring Requirements:**
- Track status bar update frequency
- Log status display errors

```
# Estimated effort: 1-2 days
# Complexity: Low
# Risk: Low (UI only)
```

### Component 8: Configuration and Preferences
**Owner:** System architect
**Dependencies:** Component 1
**Success Criteria:**
- Users can configure application settings
- Settings persist between sessions
- Default behaviors can be customized

**Implementation Strategy:**
1. Create configuration manager
2. Add settings panel/UI
3. Implement persistent storage for settings
4. Add keyboard shortcuts configuration

**Testing Approach:**
- Unit tests for configuration manager
- Integration tests for settings persistence
- Verify configuration affects application behavior

**Acceptance Tests:**
- Settings can be changed and saved
- Settings persist after application restart
- Configuration changes affect UI behavior

**Monitoring Requirements:**
- Log configuration changes
- Track configuration load failures

```
# Estimated effort: 2-3 days
# Complexity: Medium
# Risk: Low
```

## Implementation Order

1. Components 1 and 4 (Git repository integration and file tree enhancement) - Can be done in parallel
2. Component 2 (Hunk-based diff processing)
3. Component 3 (Hunk staging controls)
4. Component 5 (Commit functionality)
5. Component 6 (Branch management)
6. Components 7 and 8 (Status bar enhancement and configuration) - Can be done in parallel

## Success Metrics

- Reduced cognitive load for Git operations
- Faster staging operations than command line
- Clear visual feedback for all actions
- Maintained performance with large repositories
- Positive user feedback on usability

## Failure Modes

- Git repository detection fails
- Diff processing becomes too slow
- Staging operations corrupt repository state
- UI becomes unresponsive with large diffs
- Configuration system fails to persist settings