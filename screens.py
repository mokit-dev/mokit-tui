from textual.screen import ModalScreen
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Static, Button, Input, TextArea, Label, Select
from textual import on
from pathlib import Path


class FileLoadScreen(ModalScreen):
    """Screen for loading template gjf file - simplified"""

    def compose(self):
        yield Container(
            Static("Load Template File"),
            Input(placeholder="template.gjf", id="file-input"),
            Horizontal(
                Button("Load", variant="primary", id="load-btn"),
                Button("Cancel", id="cancel-btn"),
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
    """Screen to display command output - simplified"""

    def __init__(self, output: str, title: str = "Output"):
        super().__init__()
        self.output = output
        self.title = title

    def compose(self):
        yield Container(
            Static(self.title),
            VerticalScroll(
                Static(self.output),
            ),
            Button("Close", variant="primary", id="close-btn"),
            id="output-dialog",
        )

    @on(Button.Pressed, "#close-btn")
    def on_close(self):
        self.dismiss()


class SettingsScreen(ModalScreen):
    """Screen for calculation settings - simplified overlay"""
    
    def __init__(self, current_options=None):
        super().__init__()
        self.current_options = current_options or {}
    
    def compose(self):
        method_options = [
            ("b3lyp", "b3lyp"),
            ("hf", "HF"),
            ("m062x", "M06-2X"),
            ("mp2", "MP2"),
            ("wb97xd", "ωB97X-D"),
        ]
        
        yield Container(
            Static("Calculation Settings"),
            Horizontal(
                Label("Method:"),
                Select(method_options, id="method-select", prompt="Select method"),
                Label("Basis:"),
                Input(value=self.current_options.get("basis_set", "6-31g(d)"), placeholder="6-31g(d)", id="basis-input"),
            ),
            Horizontal(
                Label("NProc:"),
                Input(value=str(self.current_options.get("processors", 4)), placeholder="4", id="proc-input"),
                Label("Keywords:"),
                Input(value=self.current_options.get("additional_keywords", ""), placeholder="", id="keywords-input"),
            ),
            Horizontal(
                Label("Mokit:"),
                Input(value=self.current_options.get("additional_mokit_options", ""), placeholder="npair=2", id="mokit-options-input"),
            ),
            Horizontal(
                Button("Apply", variant="primary", id="apply-btn"),
                Button("Cancel", id="cancel-btn"),
            ),
            id="settings-dialog",
        )
    
    @on(Button.Pressed, "#apply-btn")
    def on_apply(self):
        # Get all values and return them
        values = {
            "method": self.query_one("#method-select", Select).value,
            "basis_set": self.query_one("#basis-input", Input).value,
            "processors": self.query_one("#proc-input", Input).value,
            "additional_keywords": self.query_one("#keywords-input", Input).value,
            "additional_mokit_options": self.query_one("#mokit-options-input", Input).value,
        }
        self.dismiss(values)
    
    @on(Button.Pressed, "#cancel-btn")
    def on_cancel(self):
        self.dismiss(None)
    
    def on_mount(self):
        """Set initial method value"""
        method_select = self.query_one("#method-select", Select)
        method_select.value = self.current_options.get("method", "b3lyp")


class NextStepScreen(ModalScreen):
    """Screen for prepare next step - simplified overlay"""
    
    def compose(self):
        # Get FCH files
        fch_files = list(Path(".").glob("*.fch"))
        fch_options = [(f.name, f.name) for f in fch_files] if fch_files else [("No files", "")]
        
        yield Container(
            Static("Prepare Next Step"),
            Horizontal(
                Label("FCH File:"),
                Select(fch_options, id="fch-select", prompt="Select file"),
                Button("Prepare", variant="primary", id="prepare-btn"),
            ),
            Horizontal(
                Button("Apply", variant="primary", id="apply-btn"),
                Button("Cancel", id="cancel-btn"),
            ),
            id="next-step-dialog",
        )
        yield Container(
            Static("📝 [b]Prepare Next Step[/b]", classes="dialog-title"),
            Container(
                Horizontal(
                    Label("FCH File:", classes="label"),
                    Select([], id="fch-select", prompt="Select .fch file", classes="fch-select"),
                    Button("Prepare", variant="primary", id="prepare-btn"),
                    classes="option-row",
                ),
                classes="next-step-content",
            ),
            Horizontal(
                Button("Apply", variant="primary", id="apply-btn"),
                Button("Cancel", variant="error", id="cancel-btn"),
            ),
            id="next-step-dialog",
        )
    
    
    
    @on(Button.Pressed, "#prepare-btn")
    def on_prepare(self):
        # Get selected FCH file and prepare it
        fch_file = self.query_one("#fch-select", Select).value
        self.dismiss({"prepare": True, "fch_file": fch_file})
    
    @on(Button.Pressed, "#apply-btn")
    def on_apply(self):
        # Just apply and close
        fch_file = self.query_one("#fch-select", Select).value
        self.dismiss({"prepare": False, "fch_file": fch_file})
    
    @on(Button.Pressed, "#cancel-btn")
    def on_cancel(self):
        self.dismiss(None)
