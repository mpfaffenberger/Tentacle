from textual.widgets import Static
from textual.app import ComposeResult
from textual.containers import Container
from textual.widget import Widget
from .custom_figlet_widget import FigletWidget


class AnimatedLogo(Widget):
    """An animated pyfiglet logo with gradient colors."""
    
    DEFAULT_CSS = """    
    AnimatedLogo {
        height: 8;
        width: 1fr;
        content-align: center middle;
        background: #001f3f;
        align: center middle;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.logo_text = "TENTACLE"
        
    def compose(self) -> ComposeResult:
        """Create the animated logo widget."""
        self.figlet_widget = FigletWidget(
            self.logo_text,
            font="smmono9",
            justify="center",
            colors=["white", "cyan", "lightblue", "darkblue", "navy"],
            animate=True,
            horizontal=True,
            fps=20,
        )
        yield self.figlet_widget
        
    def on_resize(self) -> None:
        """Handle resize events to maintain proper sizing."""
        self.figlet_widget.refresh_size()