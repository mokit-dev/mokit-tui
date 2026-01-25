from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Select, Static

from mokit_tui.gen import GJFGenerator


class InputPreview(Static):
    """Widget to display the gjf file content"""

    content = reactive("")  # type: ignore[assignment]

    def watch_content(self, content: str) -> None:
        """Update display when content changes"""
        self.update(f"[b]MOKIT Input Preview:[/b]\n\n{content}")


class NextStepPreview(Static):
    """Widget to display next step input content"""

    content = reactive("[dim]No next step prepared[/dim]")  # type: ignore[assignment]

    def watch_content(self, content: str) -> None:
        """Update display when content changes"""
        self.update(content)


class TemplateInfo(Static):
    """Display template information"""

    info = reactive("No template loaded")  # type: ignore[assignment]

    def watch_info(self, info: str) -> None:
        """Update display when info changes"""
        self.update(f"[b]Template Info:[/b] {info}")


class OutputPreview(Container):
    """Widget to display output file preview information"""

    output_content = reactive("")  # type: ignore[assignment]
    fch_content = reactive("")  # type: ignore[assignment]
    output_file = reactive("")  # type: ignore[assignment]
    has_output = reactive(False)  # type: ignore[assignment]

    def compose(self) -> ComposeResult:
        yield Static(id="output-preview-title")
        yield VerticalScroll(
            Static(id="output-preview-content"),
            id="output-preview-core-scroll",
        )
        yield Static("[b]fch preview:[/b]", id="output-preview-fch-title")
        yield VerticalScroll(
            Static(id="output-preview-fch"),
            id="output-preview-fch-scroll",
        )

    def watch_output_content(self, content: str) -> None:
        if not self.is_mounted:
            return
        output_widget = self.query_one("#output-preview-content", Static)
        output_widget.update(content)

    def watch_fch_content(self, content: str) -> None:
        if not self.is_mounted:
            return
        fch_widget = self.query_one("#output-preview-fch", Static)
        fch_widget.update(content)

    def watch_output_file(self, output_file: str) -> None:
        self._update_title(output_file, self.has_output)

    def watch_has_output(self, has_output: bool) -> None:
        self._update_title(self.output_file, has_output)

    def _update_title(self, output_file: str, has_output: bool) -> None:
        if not self.is_mounted:
            return
        title = "[b]Output Preview:[/b]"
        if output_file:
            title += f" [dim]({output_file})[/dim]"
        if has_output:
            title += " [green]●[/green]"
        title_widget = self.query_one("#output-preview-title", Static)
        title_widget.update(title)

    def set_output_file(self, filepath: str):
        """Set the output file path"""
        self.output_file = filepath
        if not self.output_content:
            self.output_content = "[dim]Loading output file...[/dim]"
        if not self.fch_content:
            self.fch_content = "[dim]No fch info available[/dim]"

    def set_output_content(self, content: str) -> None:
        """Set output preview content"""
        self.output_content = content

    def set_fch_content(self, content: str) -> None:
        """Set fch preview content"""
        self.fch_content = content

    def set_no_output(self):
        """Set to show no output available"""
        self.has_output = False
        self.output_file = ""
        self.output_content = "[dim]No output file found[/dim]"
        self.fch_content = "[dim]No fch info available[/dim]"


class MethodSelect(Select):
    """Method selection widget"""

    def __init__(self, generator=None):
        if generator is None:
            generator = GJFGenerator()
        options = generator.get_methods()

        # Initialize parent class
        super().__init__(options, prompt="Select method")
