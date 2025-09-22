"""Custom FigletWidget that can use any font available to pyfiglet."""

from __future__ import annotations
from typing import List, Literal, cast

# Import the pyfiglet library from textual_pyfiglet
try:
    from textual_pyfiglet.pyfiglet import Figlet, FigletError, FigletFont
except ImportError:
    # Fallback direct import
    from pyfiglet import Figlet, FigletError, FigletFont

# Textual and Rich imports
from textual.css.scalar import Scalar
from textual.widget import Widget
from textual.reactive import reactive

# Import Coloromatic for gradient functionality
try:
    from textual_coloromatic import Coloromatic
except ImportError:
    # Fallback if textual_coloromatic is not available
    class Coloromatic(Widget):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)


# Get all available fonts dynamically from pyfiglet
ALL_AVAILABLE_FONTS = sorted(FigletFont.getFonts())

# Create a Literal type that can accommodate all fonts
# We'll use a string type instead of Literal for maximum flexibility

# CONSTANTS:
JUSTIFY_OPTIONS = Literal["left", "center", "right"]
COLOR_MODE = Literal["color", "gradient", "none"]
ANIMATION_TYPE = Literal["gradient", "smooth_strobe", "fast_strobe"]


class CustomFiglet(Figlet):
    """Extended Figlet class with additional properties."""
    
    @property
    def direction(self) -> str:
        if self._direction == "auto":
            direction = self.Font.printDirection
            if direction == 0:
                return "left-to-right"
            elif direction == 1:
                return "right-to-left"
            else:
                return "left-to-right"
        else:
            return self._direction

    @direction.setter
    def direction(self, value: str) -> None:
        self._direction = value

    @property
    def justify(self) -> str:
        if self._justify == "auto":
            if self.direction == "left-to-right":
                return "left"
            else:
                assert self.direction == "right-to-left"
                return "right"
        else:
            return self._justify

    @justify.setter
    def justify(self, value: str) -> None:
        self._justify = value


class FigletWidget(Coloromatic):
    """A FigletWidget that can use any font available to pyfiglet."""
    
    DEFAULT_CSS = "FigletWidget {width: auto; height: auto; background: #001f3f;}"

    # Get all available fonts dynamically from pyfiglet
    fonts_list: list[str] = ALL_AVAILABLE_FONTS
    
    ############################
    # ~ Public API Reactives ~ #
    ############################
    text_input: reactive[str] = reactive[str]("", always_update=True)
    font: reactive[str] = reactive[str]("standard", always_update=True)  # Allow any font
    justify: reactive[JUSTIFY_OPTIONS] = reactive[JUSTIFY_OPTIONS]("center", always_update=True)

    def __init__(
        self,
        text: str = "",
        *,
        font: str = "standard",
        justify: JUSTIFY_OPTIONS = "center",
        colors: list[str] = [],
        animate: bool = False,
        animation_type: ANIMATION_TYPE = "gradient",
        gradient_quality: int | str = "auto",
        horizontal: bool = False,
        reverse: bool = False,
        fps: float | str = "auto",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """
        Create a FigletWidget.

        Args:
            text: Text to render in the Figlet widget.
            font: Font to use for the ASCII art. Can be any font available in pyfiglet.
            justify: Justification for the text.
            colors: List of colors to use for the gradient.
            animate: Whether to animate the gradient.
            animation_type: Type of animation.
            gradient_quality: Quality of the gradient.
            horizontal: Whether the gradient should be horizontal.
            reverse: Whether the animation should run in reverse.
            fps: Frames per second for the animation.
            name: Name of widget.
            id: ID of Widget.
            classes: Space separated list of class names.
        """
        try:
            string = str(text)
        except Exception as e:
            raise e

        super().__init__(
            name=name,
            id=id,
            classes=classes,
            colors=colors,
            animate=animate,
            animation_type=animation_type,
            gradient_quality=gradient_quality,
            horizontal=horizontal,
            reverse=reverse,
            fps=fps,
        )

        self.figlet = CustomFiglet()
        self._previous_height: int = 0

        # Use our custom validation that allows any pyfiglet font
        self.font = self.validate_font(font)
        self.justify = justify
        self.text_input = string

        # Mark as initialized
        self._initialized = True

    def update(self, text: str) -> None:
        """Update the PyFiglet area with new text."""
        self.text_input = text

    def set_text(self, text: str) -> None:
        """Alias for the update() method."""
        self.text_input = text

    def set_justify(self, justify: str) -> None:
        """Set the justification of the PyFiglet widget."""
        self.justify = cast(JUSTIFY_OPTIONS, justify)

    def set_font(self, font: str) -> None:
        """Set the font of the PyFiglet widget.
        This method allows passing in any string font name available in pyfiglet.

        Args:
            font: The font to set. Must be one of the available fonts in pyfiglet."""
        self.font = font

    def get_figlet_as_string(self) -> str:
        """Return the PyFiglet render as a string."""
        return getattr(self, 'figlet_render', '')

    @classmethod
    def figlet_quick(
        cls, text: str, font: str = "standard", width: int = 80, justify: JUSTIFY_OPTIONS = "left"
    ) -> str:
        """Quick access to figlet rendering with any available font."""
        return str(Figlet(font=font, width=width).renderText(text))

    #################
    # ~ Validators ~#
    #################

    def validate_text_input(self, text: str) -> str:
        """Validate text input."""
        assert isinstance(text, str), "Figlet input must be a string."
        return text

    def validate_font(self, font: str) -> str:
        """Validate font against all available pyfiglet fonts.
        Allows any font that pyfiglet supports, not just those in the hardcoded list."""
        # Check if font is available in pyfiglet
        if font in self.fonts_list:
            return font
        else:
            available_fonts_sample = ', '.join(self.fonts_list[:10])
            raise ValueError(f"Invalid font: {font} \nMust be one of the available fonts in pyfiglet.\nSample available fonts: {available_fonts_sample}")

    def validate_justify(self, value: str) -> str:
        """Validate justification options."""
        if value in ("left", "center", "right", "auto"):
            return value
        else:
            raise ValueError(
                f"Invalid justification: {value} \nMust be 'left', 'center', 'right', or 'auto'."
            )

    ###############
    # ~ Watchers ~#
    ###############

    def watch_text_input(self, text: str) -> None:
        """Watch for text input changes and re-render."""
        if text == "":
            self._animation_lines = [""]
            if hasattr(self, 'mutate_reactive'):
                self.mutate_reactive(FigletWidget._animation_lines)
        else:
            self._animation_lines = self.render_figlet(text)
            if hasattr(self, 'mutate_reactive'):
                self.mutate_reactive(FigletWidget._animation_lines)

        # TODO: Implement Updated message if needed
        # self.post_message(self.Updated(self))

    def watch_font(self, font: str) -> None:
        """Watch for font changes and update figlet rendering."""
        try:
            self.figlet.setFont(font=font)
        except Exception as e:
            self.log.error(f"Error setting font: {e}")
            raise e

        if hasattr(self, '_initialized') and self._initialized and hasattr(self, 'watch_text_input'):
            self.watch_text_input(self.text_input)  # trigger reactive

    def watch_justify(self, justify: str) -> None:
        """Watch for justify changes and update figlet rendering."""
        try:
            self.figlet.justify = justify
        except Exception as e:
            self.log.error(f"Error setting justify: {e}")
            raise e

        if hasattr(self, '_initialized') and self._initialized and hasattr(self, 'watch_text_input'):
            self.watch_text_input(self.text_input)  # trigger reactive

    ######################
    # ~ RENDERING LOGIC ~#
    ######################

    def on_resize(self) -> None:
        """Handle resize events."""
        self.refresh_size()

    def refresh_size(self) -> None:
        """Refresh the size of the figlet widget."""
        # Skip if not initialized yet
        if not hasattr(self, '_initialized') or not self._initialized:
            return

        if (
            self.size.width == 0 or self.size.height == 0
        ) and hasattr(self.app, '_dom_ready') and not self.app._dom_ready:
            return

        if self.parent is None:
            return

        # TODO: Update this part based on actual requirements
        assert isinstance(self.parent, Widget)  # This is for type hinting.
        if hasattr(self.styles, 'width') and hasattr(self.styles.width, 'is_auto'):
            assert isinstance(self.styles.width, Scalar)  # These should always pass if it reaches here.

            if self.styles.width.is_auto:
                self.size_mode = "auto"
                self.figlet.width = self.parent.size.width
            else:
                self.size_mode = "not_auto"
                self.figlet.width = self.size.width

        self.text_input = self.text_input  # trigger the reactive to update the figlet.

        # This will make it recalculate the gradient only when the height changes:
        if hasattr(self, 'size') and hasattr(self, '_previous_height') and self.size.height != self._previous_height:
            self._previous_height = self.size.height
            # TODO: Recalculate gradient if needed

    def render_figlet(self, text_input: str) -> List[str]:
        """Render the figlet text."""
        try:
            self.figlet_render = str(self.figlet.renderText(text_input))
        except FigletError as e:
            self.log.error(f"Pyfiglet returned an error when attempting to render: {e}")
            raise e
        except Exception as e:
            self.log.error(f"Unexpected error occurred when rendering figlet: {e}")
            raise e
        else:
            render_lines: List[str] = self.figlet_render.splitlines()

            # Clean up blank lines at the start and end
            while True:
                lines_cleaned: List[str] = []
                for i, line in enumerate(render_lines):
                    if i == 0 and all(c == " " for c in line):  # if first line and blank
                        pass
                    elif i == len(render_lines) - 1 and all(c == " " for c in line):  # if last line and blank
                        pass
                    else:
                        lines_cleaned.append(line)

                if lines_cleaned == render_lines:
                    break
                else:
                    render_lines = lines_cleaned

            if lines_cleaned == []:
                return [""]

            # Check if we need to trim lines for auto width mode
            if (
                hasattr(self.styles, 'width') and 
                hasattr(self.styles.width, 'is_auto') and 
                self.styles.width.is_auto
            ):  # if the width is auto, we need to trim the lines
                startpoints: List[int] = []
                for line in lines_cleaned:
                    for c in line:
                        if c != " ":  # find first character that is not space
                            if line:  # Check if line is not empty
                                startpoints.append(line.index(c))  # get the index
                            break
                figstart = min(startpoints) if startpoints else 0
                shortened_fig = [line[figstart:].rstrip() if line else "" for line in lines_cleaned]
                return shortened_fig
            else:
                return lines_cleaned
