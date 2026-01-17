from textual.widgets import Static, Select
from textual.reactive import reactive


class InputPreview(Static):
    """Widget to display the gjf file content"""

    content = reactive("")

    def watch_content(self, content: str) -> None:
        """Update display when content changes"""
        self.update(f"[b]Gaussian Input Preview:[/b]\n\n{content}")


class TemplateInfo(Static):
    """Display template information"""

    info = reactive("No template loaded")

    def watch_info(self, info: str) -> None:
        """Update display when info changes"""
        self.update(f"[b]Template Info:[/b] {info}")


class OutputPreview(Static):
    """Widget to display output file preview information"""

    content = reactive("")
    output_file = reactive("")
    has_output = reactive(False)

    def watch_content(self, content: str) -> None:
        """Update display when content changes"""
        title = "[b]Output Preview:[/b]"
        if self.output_file:
            title += f" [dim]({self.output_file})[/dim]"
        if self.has_output:
            title += " [green]●[/green]"

        self.update(f"{title}\n\n{content}")

    def set_output_file(self, filepath: str):
        """Set the output file path"""
        self.output_file = filepath
        if not self.content:
            self.content = "[dim]Loading output file...[/dim]"

    def set_no_output(self):
        """Set to show no output available"""
        self.has_output = False
        self.output_file = ""
        self.content = "[dim]No output file found[/dim]"


class MethodSelect(Select):
    """Method selection widget"""

    def __init__(self, generator=None):
        # Hardcode the options to avoid issues
        options = [
            ("b3lyp", "b3lyp"),
            ("hf", "HF"),
            ("m062x", "M06-2X"),
            ("mp2", "MP2"),
            ("wb97xd", "ωB97X-D"),
        ]

        # Initialize parent class
        super().__init__(options, prompt="Select method")
