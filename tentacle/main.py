import sys

from tentacle.git_diff_viewer import GitDiffViewer

def main():
    if len(sys.argv) != 3:
        print("Usage: python git_diff_viewer.py <file1> <file2>")
        sys.exit(1)

    file1_path = sys.argv[1]
    file2_path = sys.argv[2]

    app = GitDiffViewer(file1_path, file2_path)
    app.run()
