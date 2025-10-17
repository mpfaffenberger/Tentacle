# Tentacle 🐙

A powerful Textual-based TUI (Terminal User Interface) for viewing and managing git diffs with **AI-powered commit message generation** using GAC (Git Auto Commit).

## ⌨️ Keybindings

### 📁 File Navigation
- `↑/↓` - Navigate through files and hunks
- `Enter` - Select file to view diff
- `Tab` - Navigate through UI elements (use `Shift+Tab` to go backwards)

### 🔄 Git Operations
- `s` - Stage selected file
- `u` - Unstage selected file
- `a` - **Stage ALL unstaged changes**
- `x` - **Unstage ALL staged changes**
- `c` - Commit staged changes

### 🌿 Branch Management
- `b` - Show branch switcher
- `r` - Refresh branches

### 📡 Remote Operations
- `p` - Push current branch
- `o` - Pull latest changes

### 🤖 AI Integration (GAC)
- `Ctrl+G` - **Configure GAC** (Git Commit Assistant)
- `g` - **Generate commit message with AI**

### ⚙️ Application
- `h` - **Show help modal** with all keybindings
- `r` - Refresh git status and file tree
- `q` - Quit application

## ✨ Features

### Core Git Features
- **Three-panel UI**: File tree, diff viewer, and git status
- **Hunk-based staging**: Stage, unstage, or discard individual hunks
- **Branch management**: View, switch between branches
- **Commit history**: Browse commit history with details
- **Real-time git status**: Color-coded file status indicators

### 🤖 AI-Powered Commits with GAC
- **AI-generated commit messages**: Press `g` to generate a suggested commit message (no auto-commit)
- **Multiple AI providers**: OpenAI, Anthropic, Cerebras, Groq, Ollama support
- **Smart configuration**: Easy setup through built-in modal (Ctrl+G)
- **Context-aware**: Generates messages based on your actual code changes

## 🎨 Git Status Colors

- **🟢 Green**: Staged files (ready to commit)
- **🟡 Yellow**: Modified files (unstaged changes)
- **🔵 Blue**: Directories
- **🟣 Purple**: Untracked files
- **🔴 Red**: Deleted files

## 🚀 Usage

```bash
# Run Tentacle with UV (recommended)
uv run tentacle [repo_path]

# Or run directly with Python module syntax
uv run python -m tentacle.main [repo_path]
```

## ⌨️ Controls

### Basic Navigation
- `q` - Quit the application
- `Ctrl+d` - Toggle dark mode
- `r` - Refresh branches
- `b` - Switch branch

### Git Operations
- `c` - Commit staged changes (manual message)
- `g` - **GAC Generate Message** (AI-suggested commit message, no auto-commit)
- `Ctrl+G` - **Configure GAC** settings

### File Operations
- Click files to view diffs
- Use hunk buttons to stage/unstage/discard changes
- Stage entire files or individual hunks

## 🤖 Setting Up GAC (AI Commits)

1. **Open Tentacle** in your git repository
2. **Press `Ctrl+G`** to open GAC configuration
3. **Choose your provider**:
   - **Cerebras**: Qwen3-Coder-480B (recommended for code, 1M free tokens/day)
   - **OpenAI**: GPT-4o, GPT-4o-mini, GPT-3.5-turbo
   - **Anthropic**: Claude-3.5-Sonnet, Claude-3.5-Haiku
   - **Groq**: Llama-3.3-70B, Mixtral-8x7B (fast & free)
   - **Ollama**: Local models (llama3.2, qwen2.5, etc.)
4. **Select a model** from the dropdown
5. **Paste your API key** directly into the config modal
6. **Click Save**

### Cerebras: Recommended for GAC

Cerebras' Qwen3-Coder-480B model is well-suited for commit message generation:

- Free tier with 1 million tokens per day (no credit card required)
- Optimized specifically for code-related tasks
- Fast response times
- Get your API key: https://cloud.cerebras.ai/

## 🔧 Installation

This project uses **UV** for Python environment management and **Walmart's internal PyPI**.

```bash
# Clone the repository
git clone <tentacle-repo>
cd tentacle

# Install with UV
uv sync

# Run the application
uv run tentacle
```

## 📦 Dependencies

- **textual>=6.1.0** - Modern TUI framework
- **GitPython>=3.1.42** - Git repository operations

- **gac>=0.18.0** - AI-powered commit message generation

## 🎯 Workflow Example

1. **Open Tentacle**: `uv run tentacle`
2. **Make some changes** to your code
3. **Review diffs** in the center panel
4. **Stage hunks** by clicking "Stage" buttons
5. **Press `g`** for AI-generated commit message
6. **Boom!** 🎉 Professional commit message is generated and filled in—review/edit, then press Commit

## 🔮 What Makes This Special

Tentacle combines the power of a visual git interface with AI-powered commit messages, making it perfect for:

- **Code reviews**: Visual diff inspection with hunk-level control
- **Professional commits**: AI generates conventional commit messages
- **Fast workflow**: Stage, review, and commit without leaving the terminal
- **Team consistency**: Standardized commit message formats

---

**Built with ❤️*

*"Because managing git shouldn't require a kraken!"* 🐙
