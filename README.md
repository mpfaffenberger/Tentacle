# Tentacle

A professional Textual-based application for viewing differences between two text files and selectively accepting changes.

## Features

- Side-by-side comparison of two text files
- Line-by-line highlighting of additions, deletions, and changes
- Inline character-level diff highlighting for changed lines:
  - Red strikethrough text for removed content
  - Green text for added content
- Professional UI with intuitive button placement
- Accept/reject changes individually or in bulk
- Save accepted changes back to the original file

## Usage

```bash
python app.py <file1> <file2>
```

### Controls

- **Accept All**: Accept all changes from file2
- **Reject All**: Reject all changes (reset all acceptances)
- **Save Changes**: Save accepted changes to file1
- **Line-by-line buttons**:
  - Accept: Accept the change on that line
  - Reject: Reject the change on that line (if previously accepted)
  - Undo: Unaccept a previously accepted change

## Inline Diff Highlighting

This version features character-level inline diff highlighting for changed lines:

- Changed lines are displayed with a yellow background
- Removed text within changed lines appears in red with strikethrough formatting
- Added text within changed lines appears in green formatting
- Unchanged lines maintain their original appearance

## UI Improvements

This version features a professional design with:

- Enhanced button placement and styling
- Improved color scheme for better readability
- Clear visual indicators for accepted changes
- Streamlined control panel with intuitive actions

## Requirements

- Python 3.7+
- textual

## Installation

```bash
pip install textual
```

## Example

```bash
python app.py sample1.txt sample2.txt
```

The application will display both files side-by-side, with modifications highlighted and accept/reject buttons for each changed line.
