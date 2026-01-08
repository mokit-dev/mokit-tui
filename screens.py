from textual.screen import ModalScreen
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Static, Button, Input, TextArea
from textual import on
from pathlib import Path


class FileLoadScreen(ModalScreen):
    """Screen for loading template gjf file"""

    def compose(self):
        yield Container(
            Static("Load Template Gaussian Input File", classes="dialog-title"),
            Input(placeholder="Path to template.gjf", id="file-input"),
            Horizontal(
                Button("Load", variant="primary", id="load-btn"),
                Button("Cancel", variant="error", id="cancel-btn"),
            ),
            id="file-dialog",
        )

    @on(Button.Pressed, "#load-btn")
    def on_load(self):
        filepath = self.query_one("#file-input", Input).value
        if filepath and Path(filepath).exists():
            self.dismiss(filepath)
        else:
            self.notify("File not found!", severity="error")

    @on(Button.Pressed, "#cancel-btn")
    def on_cancel(self):
        self.dismiss(None)


class OutputScreen(ModalScreen):
    """Screen to display command output"""

    def __init__(self, output: str, title: str = "Output"):
        super().__init__()
        self.output = output
        self.title = title

    def compose(self):
        yield Container(
            Static(f"[b]{self.title}[/b]", classes="dialog-title"),
            VerticalScroll(
                TextArea(self.output, readonly=True, id="output-text"),
                classes="output-container",
            ),
            Button("Close", variant="primary", id="close-btn"),
            id="output-dialog",
        )

    @on(Button.Pressed, "#close-btn")
    def on_close(self):
        self.dismiss()
