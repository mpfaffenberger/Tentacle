"""GAC (Git Auto Commit) integration for Tentacle."""

import os
from pathlib import Path
from textual.screen import ModalScreen
from textual.widgets import Static, Button, Input, Select, Label
from textual.containers import Horizontal, Vertical, Container
from textual.app import ComposeResult
from textual import on
import gac
from typing import Optional, Dict, Any


class GACConfigModal(ModalScreen):
    """Modal screen for configuring GAC settings."""
    
    DEFAULT_CSS = """
    GACConfigModal {
        align: center middle;
    }
    
    #gac-container {
        border: solid #6c7086;
        background: #00122f;
        width: 60%;
        height: 70%;
        margin: 1;
        padding: 1;
    }
    
    .gac-input {
        margin: 1 0;
        width: 100%;
    }
    
    .gac-select {
        margin: 1 0;
        width: 100%;
    }
    
    .gac-buttons {
        align: center bottom;
        height: auto;
        margin: 2 0 0 0;
    }
    
    .gac-label {
        margin: 1 0 0 0;
        color: #bb9af7;
        text-style: bold;
    }
    """
    
    # Common AI providers and their models
    PROVIDERS = {
        "openai": [
            "gpt-4o",
            "gpt-4o-mini", 
            "gpt-4-turbo",
            "gpt-3.5-turbo"
        ],
        "anthropic": [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ],
        "cerebras": [
            "qwen-3-coder-480b",
            "llama3.1-70b",
            "llama3.1-8b"
        ],
        "groq": [
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768"
        ],
        "ollama": [
            "llama3.2",
            "llama3.1",
            "qwen2.5",
            "codestral",
            "deepseek-coder"
        ]
    }
    
    def __init__(self):
        super().__init__()
        self.current_config = self._load_current_config()
        
    def _load_current_config(self) -> Dict[str, str]:
        """Load current GAC configuration from environment or config file."""
        config = {}
        
        # Try to load from GAC config
        gac_env_file = Path.home() / ".gac.env"
        if gac_env_file.exists():
            try:
                with open(gac_env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip().strip('"\'')
            except Exception:
                pass
                
        # Also check environment variables
        for provider in self.PROVIDERS.keys():
            api_key_var = f"{provider.upper()}_API_KEY"
            if api_key_var in os.environ:
                config[api_key_var] = os.environ[api_key_var]
                
        return config
        
    def compose(self) -> ComposeResult:
        """Create the modal content."""
        with Container(id="gac-container"):
            yield Static("🤖 Configure GAC (Git Auto Commit)", classes="panel-header")
            
            yield Label("Provider:", classes="gac-label")
            provider_options = [(provider.title(), provider) for provider in self.PROVIDERS.keys()]
            current_provider = self._detect_current_provider()
            yield Select(provider_options, value=current_provider, id="provider-select", classes="gac-select")
            
            yield Label("Model:", classes="gac-label")
            initial_models = self.PROVIDERS.get(current_provider, [])
            model_options = [(model, model) for model in initial_models]
            yield Select(model_options, id="model-select", classes="gac-select")
            
            yield Label("API Key:", classes="gac-label")
            current_key = self._get_current_api_key(current_provider)
            yield Input(
                value=current_key, 
                password=True, 
                placeholder="Enter your API key...",
                id="api-key-input",
                classes="gac-input"
            )
            
            with Horizontal(classes="gac-buttons"):
                yield Button("Cancel", id="gac-cancel", classes="cancel-button")
                yield Button("Test", id="gac-test", classes="test-button")
                yield Button("Save", id="gac-save", classes="save-button")
                
    def _detect_current_provider(self) -> str:
        """Detect the current provider from config."""
        # Check for API keys in config to detect provider
        for provider in self.PROVIDERS.keys():
            api_key_var = f"{provider.upper()}_API_KEY"
            if api_key_var in self.current_config:
                return provider
        return "openai"  # Default to OpenAI
        
    def _get_current_api_key(self, provider: str) -> str:
        """Get the current API key for the provider."""
        api_key_var = f"{provider.upper()}_API_KEY"
        return self.current_config.get(api_key_var, "")
        
    @on(Select.Changed, "#provider-select")
    def on_provider_changed(self, event: Select.Changed) -> None:
        """Update model options when provider changes."""
        provider = str(event.value)
        model_select = self.query_one("#model-select", Select)
        api_key_input = self.query_one("#api-key-input", Input)
        
        # Update model options
        models = self.PROVIDERS.get(provider, [])
        model_options = [(model, model) for model in models]
        model_select.set_options(model_options)
        
        # Update API key placeholder
        current_key = self._get_current_api_key(provider)
        api_key_input.value = current_key
        
    @on(Button.Pressed, "#gac-cancel")
    def on_cancel(self, event: Button.Pressed) -> None:
        """Cancel configuration."""
        self.app.pop_screen()
        
    @on(Button.Pressed, "#gac-test")
    def on_test(self, event: Button.Pressed) -> None:
        """Test the GAC configuration."""
        config = self._get_form_config()
        if not config:
            return
            
        # TODO: Implement a test commit message generation
        # For now, just validate the configuration
        self.app.notify("🧪 Testing GAC configuration... (Feature coming soon!)", severity="information")
        
    @on(Button.Pressed, "#gac-save")
    def on_save(self, event: Button.Pressed) -> None:
        """Save the GAC configuration."""
        config = self._get_form_config()
        if not config:
            return
            
        try:
            self._save_config(config)
            self.app.notify("✅ GAC configuration saved successfully!", severity="information")
            self.app.pop_screen()
        except Exception as e:
            self.app.notify(f"❌ Failed to save GAC config: {e}", severity="error")
            
    def _get_form_config(self) -> Optional[Dict[str, str]]:
        """Get configuration from form fields."""
        provider_select = self.query_one("#provider-select", Select)
        model_select = self.query_one("#model-select", Select)
        api_key_input = self.query_one("#api-key-input", Input)
        
        provider = str(provider_select.value)
        model = str(model_select.value)
        api_key = api_key_input.value.strip()
        
        if not provider:
            self.app.notify("❌ Please select a provider", severity="error")
            return None
            
        if not model:
            self.app.notify("❌ Please select a model", severity="error")
            return None
            
        if not api_key:
            self.app.notify("❌ Please enter an API key", severity="error")
            return None
            
        return {
            "provider": provider,
            "model": model,
            "api_key": api_key
        }
        
    def _save_config(self, config: Dict[str, str]) -> None:
        """Save configuration to GAC config file."""
        gac_env_file = Path.home() / ".gac.env"
        provider = config["provider"]
        gac_model = f"{provider}:{config['model']}"
        out_config = dict()
        out_config["GAC_MODEL"] = gac_model
        out_config[f"{provider.upper()}_API_KEY"] = config["api_key"]

        # Write back to file
        with open(gac_env_file, 'w') as f:
            f.write("# GAC Configuration\n")
            for key, value in out_config.items():
                f.write(f"{key}='{value}'\n")


class GACIntegration:
    """Integration class for GAC functionality."""
    
    def __init__(self, git_sidebar):
        self.git_sidebar = git_sidebar
        self.config = self._load_config()
        
    def _load_config(self) -> Optional[Dict[str, str]]:
        """Load GAC configuration."""
        gac_env_file = Path.home() / ".gac.env"
        if not gac_env_file.exists():
            return None

        config = {}
        try:
            with open(gac_env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip().strip('"\'')
            self.config = config
            return config
        except Exception:
            return None
            
    def is_configured(self) -> bool:
        """Check if GAC is properly configured."""
        self.config = self._load_config()
        if not self.config:
            return False
        return True
        
    def generate_commit_message(self, staged_only: bool = True, one_liner: bool = False, 
                              hint: str = "", scope: Optional[str] = None) -> Optional[str]:
        """Generate a commit message using GAC."""
        if not self.is_configured():
            raise ValueError("GAC is not configured. Please configure it first.")
            
        try:
            # Get git status and diff
            status = self.git_sidebar.get_git_status()
            if staged_only:
                diff = self.git_sidebar.get_staged_diff()
            else:
                diff = self.git_sidebar.get_full_diff()
                
            if not diff.strip():
                raise ValueError("No changes to commit")
                
            # Build the prompt
            system_prompt, user_prompt = gac.build_prompt(
                status=status,
                processed_diff=diff,
                one_liner=one_liner,
                hint=hint,
                scope=scope
            )
            
            # Generate commit message
            model = self.config["GAC_MODEL"]
            commit_message = gac.generate_commit_message(
                model=model,
                prompt=(system_prompt, user_prompt),
                quiet=True
            )
            
            return commit_message
            
        except Exception as e:
            raise ValueError(f"Failed to generate commit message: {e}")
