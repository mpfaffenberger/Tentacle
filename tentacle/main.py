import sys
import os

# Add the parent directory to sys.path so we can import tentacle modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tentacle.git_diff_viewer import GitDiffViewer

def main():
    if len(sys.argv) != 3:
        print("Usage: tentacle <file1> <file2>")
        sys.exit(1)

    file1_path = sys.argv[1]
    file2_path = sys.argv[2]

    app = GitDiffViewer(file1_path, file2_path)
    app.run()
