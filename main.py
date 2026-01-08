from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Button, Static, Input, Label
from textual import on
from textual.events import Click
import subprocess, sys
from pathlib import Path

from parser import GJFParser
from gen import GJFGenerator
from widgets import InputPreview, TemplateInfo, MethodSelect
from screens import FileLoadScreen, OutputScreen


class MTUI(App):
    """TUI for Gaussian input generation"""

    CSS = """
    Screen {
        align: center middle;
    }
    
    #main-container {
        width: 95%;
        height: 95%;
        border: solid $primary;
        padding: 1;
    }
    
    #preview-box {
        height: 30%;
        border: solid $primary;
        margin: 1;
        padding: 1;
        background: $surface;
        overflow-y: auto;
    }
    
    #controls-container {  /* CHANGED: New container for collapsible */
        height: 40%;
        margin: 0;
        padding: 0;  /* Remove padding from container */
    }
    
    #controls-header {  /* NEW: Header for collapsible */
        height: 3;
        padding: 1;
        margin: 0;
    }
    
    #controls {  /* CHANGED: Now inside collapsible */
        padding: 1;
        height: 100%;
    }
    
    #buttons {
        dock: bottom;
        height: 10%;
        margin: 0;
        padding: 1;
        align: left bottom;
    }
    
    Button {
        margin: 0;
        color: $text;
        background: $surface;
        border: none;
    }
    .shortcut-hint {
        text-style: italic;
        color: $text-muted;
        margin-left: 1;
    }
    
    #method-select {
        width: 50;
        margin-right: 2;
    }
    
    Select, Input {
        margin-right: 2;
    }
    
    
    .label {
        width: 12;
    }
    
    #file-dialog, #output-dialog {
        width: 60%;
        height: 30%;
        border: thick $primary;
        background: $surface;
    }
    
    .dialog-title {
        text-align: center;
        padding: 1;
        text-style: bold;
    }
    .settings-title {
        margin-bottom: 0;
    }
    
    .option-group {
        margin: 0;
        padding: 0;
        border: none;
        height: auto;
    }
    
    .option-row {
        height: auto;
        margin: 0;
        align: left middle;
    }
    
    #keywords-input {
            width: 50;
        }

    .collapsible-title {
            padding-left: 1;
        }
    """

    def __init__(self):
        super().__init__()
        self.template_file = None
        self.input_file = "input.gjf"
        self.template_sections = {}
        self.template_path = None
        self.parser = GJFParser()
        self.generator = GJFGenerator()
        self.settings_visible = True

        self.options = {
            "method": "b3lyp",
            "basis_set": "6-31g(d)",
            "memory": "2GB",
            "processors": 4,
            "checkpoint": "input.chk",
            "charge": 0,
            "multiplicity": 1,
            "additional_keywords": "",
            "additional_mokit_options": "",
        }

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

        with Container(id="main-container"):
            yield TemplateInfo(id="template-info")
            yield InputPreview(id="preview-box")

            with Container(id="controls-container"):
                with Horizontal(id="controls-header"):
                    yield Static(
                        "🔧 [b]Calculation Settings[/b]", classes="collapsible-title",id="controls-title"
                    )
                    # yield Button("⬆️ Hide", id="toggle-settings-btn", variant="default")

                with Container(id="controls", classes="settings-content"):
                    with Container(classes="option-group"):
                        with Horizontal(classes="option-row"):
                            yield Label("Method: ", classes="label")
                            from widgets import MethodSelect
    
                            method_select = MethodSelect(self.generator)
                            method_select.id = "method-select"
                            yield method_select
    
                            yield Label("Basis Set: ", classes="label")
                            yield Input(
                                value="6-31g(d)",
                                placeholder="e.g., 6-31g(d), cc-pvdz",
                                id="basis-input",
                            )
    
                            # with Container(classes="option-group"):
                            #     with Horizontal(classes="option-row"):
                            # yield Label("Memory: ", classes="label")
                            # yield Input(
                            #     value="2GB",
                            #     placeholder="e.g., 2GB",
                            #     id="memory-input"
                            # )
    
                            yield Label("NProc: ", classes="label")
                            yield Input(value="4", placeholder="CPUs", id="proc-input")
    
                            # yield Label("Charge: ", classes="label")
                            # yield Input(
                            #     value="0",
                            #     placeholder="Charge",
                            #     id="charge-input"
                            # )
    
                            # yield Label("Mult: ", classes="label")
                            # yield Input(
                            #     value="1",
                            #     placeholder="Multiplicity",
                            #     id="mult-input"
                            # )
    
                    with Container(classes="option-group"):
                        with Horizontal(classes="option-row"):
                            yield Label("Extra Keywords: ", classes="label")
                            yield Input(value="", placeholder="", id="keywords-input")
                            # with Container(classes="option-group"):
                            #     with Horizontal(classes="option-row"):
                            yield Label("Mokit Options:", classes="label")
                            yield Input(
                                value="",
                                placeholder="e.g., npair=2",
                                id="mokit-options-input",
                            )

            with Horizontal(id="buttons"):
                # yield Button("📂 Load", variant="primary", id="load-btn")
                yield Button("▶️ Run", variant="default", id="run-btn")
                yield Button("💾 Save (s)", variant="default", id="save-btn")
                # yield Button("🧬 Geometry", variant="warning", id="geom-btn")
                yield Button("❌ Exit (q)", variant="error", id="exit-btn")

    def on_mount(self) -> None:
        """Initialize application"""
        self.load_template(self.template_file)

    def update_template_info(self, message: str) -> None:
        """Update template information display"""
        info_widget = self.query_one("#template-info", TemplateInfo)
        info_widget.info = message

    def load_template(self, filepath: str) -> None:
        """Load a template gjf file"""
        try:
            self.template_sections = self.parser.parse_gjf(filepath)
            self.template_path = filepath

            # Always set title to mokit{}
            self.template_sections["title"] = "mokit{}"

            # Update options from template
            self.options["charge"] = self.template_sections.get("charge", 0)
            self.options["multiplicity"] = self.template_sections.get("multiplicity", 1)

            # Update UI
            # self.query_one("#charge-input", Input).value = str(self.options['charge'])
            # self.query_one("#mult-input", Input).value = str(self.options['multiplicity'])

            # Extract atom info for display
            geometry = self.template_sections.get("geometry", "")
            atom_count, atom_types = self.parser.get_atom_info(geometry)

            # Update template info
            info = f"Loaded: {Path(filepath).name}"
            if atom_count > 0:
                info += f" | Atoms: {atom_count}"
                if atom_types:
                    info += f" ({', '.join(sorted(atom_types))})"

            self.update_template_info(info)
            self.update_preview()

            # self.notify(f"Template loaded. Title set to 'mokit{{}}'", severity="success")

        except Exception as e:
            self.notify(f"Error loading template: {str(e)}", severity="error")

    def generate_input(self) -> str:
        """Generate Gaussian input"""
        if not self.template_sections:
            return "# No template loaded\n\nPlease load a template .gjf file.\n\nmokit{}\n\n0 1"

        # Update template with current options
        self.template_sections["charge"] = int(self.options["charge"])
        self.template_sections["multiplicity"] = int(self.options["multiplicity"])

        mokit_options = self.template_sections.get("mokit_options", {}).copy()

        # Add additional options from UI
        if self.options.get("additional_mokit_options"):
            additional = self.generator.parse_mokit_option_string(
                self.options["additional_mokit_options"]
            )
            mokit_options.update(additional)

        # Update mokit options in template sections
        self.template_sections["mokit_options"] = mokit_options

        return self.generator.generate_gjf(self.template_sections, self.options)

    def update_preview(self) -> None:
        """Update preview box"""
        preview = self.query_one(InputPreview)
        preview.content = self.generate_input()

    def save_input_file(self) -> None:
        """Save to input.gjf"""
        content = self.generate_input()
        with open(self.input_file, "w") as f:
            f.write(content)

        file_size = Path(self.input_file).stat().st_size
        self.notify(
            f"Saved to {self.input_file} ({file_size} bytes)", severity="information"
        )

    def run_calculation(self) -> None:
        """Run backend program"""
        self.save_input_file()

        try:
            result = subprocess.run(
                ["xxx", self.input_file], capture_output=True, text=True, check=True
            )

            output = result.stdout if result.stdout else "No output"
            if result.stderr:
                output += f"\n\nSTDERR:\n{result.stderr}"

            self.app.push_screen(OutputScreen(output, title="Calculation Output"))

        except subprocess.CalledProcessError as e:
            self.app.push_screen(
                OutputScreen(
                    f"Error (code {e.returncode}):\n\n{e.stderr}", title="Error"
                )
            )
        except FileNotFoundError:
            self.notify("Backend 'xxx' not found!", severity="error")

    def show_geometry(self) -> None:
        """Show molecular geometry"""
        if self.template_sections.get("geometry"):
            geom = self.template_sections["geometry"]
            atom_count, atom_types = self.parser.get_atom_info(geom)

            info = f"Geometry contains {atom_count} atoms"
            if atom_types:
                info += f" ({', '.join(sorted(atom_types))})"

            self.app.push_screen(
                OutputScreen(f"{info}:\n\n{geom}", title="Molecular Geometry")
            )
        else:
            self.notify("No geometry loaded", severity="warning")

    @on(Button.Pressed, "#load-btn")
    async def on_load_button(self):
        result = await self.push_screen_wait(FileLoadScreen())
        if result:
            self.load_template(result)

    @on(Button.Pressed, "#run-btn")
    def on_run_button(self):
        self.run_calculation()

    @on(Button.Pressed, "#save-btn")
    def on_save_button(self):
        self.save_input_file()

    @on(Button.Pressed, "#geom-btn")
    def on_geom_button(self):
        self.show_geometry()

    @on(Button.Pressed, "#exit-btn")
    def on_exit_button(self):
        self.exit()

    @on(Click, "#controls-title")
    def on_settings_title_click(self):
        self.toggle_settings_visibility()
        
    def key_s(self) -> None:
        """s to save"""
        self.save_input_file()
    
    def key_escape(self) -> None:
        """esc to exit"""
        self.exit()
    def key_q(self) -> None:
        """esc to exit"""
        self.exit()

    @on(Input.Changed)
    def on_input_change(self, event):
        try:
            if event.input.id == "basis-input":
                self.options["basis_set"] = event.value
            elif event.input.id == "memory-input":
                self.options["memory"] = event.value
            elif event.input.id == "proc-input":
                self.options["processors"] = int(event.value)
            elif event.input.id == "charge-input":
                self.options["charge"] = int(event.value)
            elif event.input.id == "mult-input":
                self.options["multiplicity"] = int(event.value)
            elif event.input.id == "keywords-input":
                self.options["additional_keywords"] = event.value
            elif event.input.id == "mokit-options-input":  # NEW: Handle mokit options
                self.options["additional_mokit_options"] = event.value
        except ValueError:
            pass

        self.update_preview()

    @on(MethodSelect.Changed)
    def on_method_change(self, event):
        self.options["method"] = event.value
        self.update_preview()

    def toggle_settings_visibility(self) -> None:
        """Toggle visibility of settings panel"""
        self.settings_visible = not self.settings_visible
        controls = self.query_one("#controls", Container)
        # toggle_btn = self.query_one("#toggle-settings-btn", Button)

        if self.settings_visible:
            controls.display = True
            # toggle_btn.label = "⬆️ Hide"
            # Adjust container height
            controls_container = self.query_one("#controls-container", Container)
            controls_container.styles.height = "40%"
        else:
            controls.display = False
            # toggle_btn.label = "⬇️ Show"
            # Collapse container height
            controls_container = self.query_one("#controls-container", Container)
            controls_container.styles.height = "3"  # Just enough for header

        # Adjust preview box height based on settings visibility
        # preview_box = self.query_one("#preview-box", InputPreview)
        # if self.settings_visible:
        #     preview_box.styles.height = "40%"
        # else:
        #     preview_box.styles.height = "77%"  # Take up more space when settings hidden


def main():
    """Main entry point"""
    # Create sample template if needed
    sample_template = """%mem=2GB
%nprocshared=4
# B3LYP/6-31G(d) opt

Water molecule

0 1
O   0.000000   0.000000   0.119262
H   0.000000   0.763239  -0.477047
H   0.000000  -0.763239  -0.477047

"""

    template_file = sys.argv[1]
    # if not Path(template_file).exists():
    #     with open(template_file, "w") as f:
    #         f.write(sample_template)
    #     print(f"Created sample {template_file}")

    # print("\nMOKIT TUI")
    # print("Title will be automatically set to 'mokit{}'")
    # print("-" * 40)

    app = MTUI()
    app.template_file = template_file
    app.run()


if __name__ == "__main__":
    main()
