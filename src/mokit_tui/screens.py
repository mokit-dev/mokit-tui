from textual.screen import ModalScreen
from pathlib import Path

from textual import on
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Button, Input, Label, Select, Static


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
        self.output = output or ""
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
        yield Container(
            Static("Calculation Settings"),
            Horizontal(
                Label("Basis:"),
                Input(
                    value=self.current_options.get("basis_set", ""),
                    placeholder="",
                    id="basis-input",
                ),
            ),
            Horizontal(
                Label("NProc:"),
                Input(
                    value=str(self.current_options.get("processors", 4)),
                    placeholder="4",
                    id="proc-input",
                ),
                Label("Keywords:"),
                Input(
                    value=self.current_options.get("additional_keywords", ""),
                    placeholder="",
                    id="keywords-input",
                ),
            ),
            Horizontal(
                Label("Mokit:"),
                Input(
                    value=self.current_options.get("additional_mokit_options", ""),
                    placeholder="npair=2",
                    id="mokit-options-input",
                ),
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
            "basis_set": self.query_one("#basis-input", Input).value,
            "processors": self.query_one("#proc-input", Input).value,
            "additional_keywords": self.query_one("#keywords-input", Input).value,
            "additional_mokit_options": self.query_one(
                "#mokit-options-input", Input
            ).value,
        }
        self.dismiss(values)

    @on(Button.Pressed, "#cancel-btn")
    def on_cancel(self):
        self.dismiss(None)

    def on_mount(self):
        """No-op mount hook for settings screen"""
        return


class UISettingsScreen(ModalScreen):
    """Screen for UI settings"""

    def __init__(self, preview_mode: str = "combined", preview_margin: int = 5):
        super().__init__()
        self.preview_mode = preview_mode
        self.preview_margin = preview_margin

    def compose(self):
        preview_options = [
            ("combined", "combined"),
            ("split", "split"),
        ]

        yield Container(
            Static("UI Settings"),
            Horizontal(
                Label("fch preview mode:"),
                Select(preview_options, id="preview-mode-select"),
            ),
            Horizontal(
                Label("fch preview margin:"),
                Input(
                    value=str(self.preview_margin),
                    placeholder="5",
                    id="preview-margin-input",
                ),
            ),
            Horizontal(
                Button("Apply", variant="primary", id="apply-btn"),
                Button("Cancel", id="cancel-btn"),
            ),
            id="ui-settings-dialog",
        )

    @on(Button.Pressed, "#apply-btn")
    def on_apply(self):
        preview_mode = self.query_one("#preview-mode-select", Select).value
        preview_margin = self.query_one("#preview-margin-input", Input).value
        self.dismiss(
            {
                "preview_mode": preview_mode,
                "preview_margin": preview_margin,
            }
        )

    @on(Button.Pressed, "#cancel-btn")
    def on_cancel(self):
        self.dismiss(None)

    def on_mount(self):
        """Set initial preview mode value"""
        preview_select = self.query_one("#preview-mode-select", Select)
        preview_select.value = self.preview_mode
        preview_input = self.query_one("#preview-margin-input", Input)
        preview_input.value = str(self.preview_margin)


class NextStepScreen(ModalScreen):
    """Screen for prepare next step - simplified overlay"""

    def __init__(self, fch_options=None):
        super().__init__()
        self.fch_options = fch_options or []
        self.selected_fch = None

    def compose(self):
        yield Container(
            Static("📝 [b]Prepare Next Step[/b]", classes="dialog-title"),
            Container(
                Horizontal(
                    Label("fch File:", classes="label"),
                    Select(
                        self.fch_options,
                        id="fch-select",
                        prompt="Select .fch file",
                        classes="fch-select",
                    ),
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

    def on_mount(self):
        fch_select = self.query_one("#fch-select", Select)
        fch_select.set_options(self.fch_options)

    @on(Select.Changed, "#fch-select")
    def on_fch_changed(self, event: Select.Changed) -> None:
        self.selected_fch = event.value

    @on(Button.Pressed, "#prepare-btn")
    def on_prepare(self):
        # Get selected fch file and prepare it
        fch_select = self.query_one("#fch-select", Select)
        fch_file = self.selected_fch or fch_select.value
        self.dismiss({"prepare": True, "fch_file": fch_file})

    @on(Button.Pressed, "#apply-btn")
    def on_apply(self):
        # Just apply and close
        fch_select = self.query_one("#fch-select", Select)
        fch_file = self.selected_fch or fch_select.value
        self.dismiss({"prepare": False, "fch_file": fch_file})

    @on(Button.Pressed, "#cancel-btn")
    def on_cancel(self):
        self.dismiss(None)
