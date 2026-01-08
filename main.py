from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Button, Static, Input, Label, Select
from textual import on
from textual.events import Click
import subprocess, sys
from pathlib import Path

from parser import GJFParser
from gen import GJFGenerator
from widgets import InputPreview, TemplateInfo, MethodSelect
from screens import FileLoadScreen, OutputScreen
from css import CSS

from workflow import *


class MTUI(App):
    """TUI for Gaussian input generation"""

    CSS = CSS

    def __init__(self):
        super().__init__()
        self.template_file = None
        self.input_file = "input.gjf"
        self.template_sections = {}
        self.template_path = None
        self.parser = GJFParser()
        self.generator = GJFGenerator()
        self.settings_visible = True
        self.next_step_fch = "default.fch"
        self.next_step_visible = True  # NEW: Track next-step container visibility

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
                        "🔧 [b]Calculation Settings[/b]",
                        classes="collapsible-title",
                        id="controls-title",
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

            with Container(id="next-step-container"):
                with Horizontal(id="next-step-header"):
                    yield Button(
                        "📝 [b]Prepare Next Step[/b] ▼",
                        id="next-step-title",
                        variant="default",
                    )

                with Container(id="next-step-content"):
                    with Horizontal(id="fch-select-container"):
                        yield Label("FCH File:", classes="label")
                        yield Select(
                            [],  # Will be populated dynamically
                            id="fch-select",
                            prompt="Select .fch file",
                            classes="fch-select",
                        )
                        yield Button("Prepare", id="prepare-btn", variant="primary")

            with Horizontal(id="buttons"):
                # yield Button("📂 Load", variant="primary", id="load-btn")
                yield Button("▶️ Run", variant="default", id="run-btn")
                yield Button("💾 Save (s)", variant="default", id="save-btn")
                # yield Button("🧬 Geometry", variant="warning", id="geom-btn")
                yield Button("❌ Exit (q)", variant="error", id="exit-btn")

    def on_mount(self) -> None:
        """Initialize application"""
        self.load_template(self.template_file)

        # Populate FCH files dropdown
        self.populate_fch_files()

        # Ensure next-step container is visible
        # Don't call toggle_next_step() here as it toggles visibility
        # Just set initial state directly:
        content = self.query_one("#next-step-content", Container)
        content.display = True
        title_btn = self.query_one("#next-step-title", Button)
        title_btn.label = "📝 [b]Prepare Next Step[/b] ▼"

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
            self.notify_persistent(
                f"Error loading template: {str(e)}", severity="error"
            )

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
        self.notify_persistent(
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
            self.notify_persistent("Backend 'xxx' not found!", severity="error")

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
            self.notify_persistent("No geometry loaded", severity="warning")

    def toggle_next_step(self) -> None:
        """Toggle visibility of next-step container"""
        self.next_step_visible = not self.next_step_visible
        content = self.query_one("#next-step-content", Container)
        title_btn = self.query_one("#next-step-title", Button)

        if self.next_step_visible:
            content.display = True
            title_btn.label = "📝 [b]Prepare Next Step[/b] ▼"
            # Ensure container has proper height
            next_step_container = self.query_one("#next-step-container", Container)
            next_step_container.styles.height = "auto"
        else:
            content.display = False
            title_btn.label = "📝 [b]Prepare Next Step[/b] ▶"
            # Collapse container height
            next_step_container = self.query_one("#next-step-container", Container)
            next_step_container.styles.height = "3"

    prepare_next_step = prepare_next_step
    populate_fch_files = populate_fch_files

    def notify_persistent(self, message: str, severity: str = "information") -> None:
        """Show a notification that stays until dismissed"""
        self.notify(message, severity=severity, timeout=0)

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

    @on(Button.Pressed, "#next-step-title")
    def on_next_step_title_click(self):
        self.toggle_next_step()

    @on(Button.Pressed, "#prepare-btn")
    def on_prepare_button(self):
        self.prepare_next_step()

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
