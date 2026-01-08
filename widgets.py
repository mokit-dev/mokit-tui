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
