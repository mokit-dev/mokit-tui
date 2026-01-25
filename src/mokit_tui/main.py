from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Button, TabbedContent, TabPane
from textual import on
import subprocess
import sys
import argparse
from pathlib import Path

if __package__ is None:
    from pathlib import Path as _Path
    import sys as _sys

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

from mokit_tui.parser import GJFParser, OutputParser
import mokit_tui.parser as parser
from mokit_tui.gen import GJFGenerator
from mokit_tui.widgets import (
    InputPreview,
    OutputPreview,
    TemplateInfo,
)
from mokit_tui.widgets import NextStepPreview  # type: ignore[attr-defined]
import mokit_tui.screens as screens  # type: ignore
from mokit_tui.screens import OutputScreen, SettingsScreen, NextStepScreen
from mokit_tui.css import CSS

from mokit_tui.workflow import populate_fch_files, prepare_next_step


def parse_cli_args(args=None):
    """Parse command-line arguments for debugging options"""
    parser = argparse.ArgumentParser(description="MOKIT TUI")
    parser.add_argument("template_file", help="Template GJF file to load")
    parser.add_argument(
        "-s",
        "--auto-settings",
        action="store_true",
        help="Auto-open settings modal on startup",
    )
    parser.add_argument(
        "-n",
        "--auto-next-step",
        action="store_true",
        help="Auto-open next step modal on startup",
    )
    if args is None:
        return parser.parse_args()
    else:
        return parser.parse_args(args)


class MTUI(App):
    """TUI for MOKIT input generation"""

    CSS = CSS

    def __init__(self, cli_args=None):
        super().__init__()
        self.cli_args = cli_args
        self.template_file = None
        self.input_file = "input.gjf"
        self.template_sections = {}
        self.template_path = None
        self.template_text = ""
        self.next_step_preview_content = "[dim]No next step prepared[/dim]"
        self.parser = GJFParser()
        self.output_parser = OutputParser()
        self.generator = GJFGenerator()
        self.next_step_fch = "default.fch"
        self.auto_settings = cli_args.auto_settings if cli_args else False
        self.auto_next_step = cli_args.auto_next_step if cli_args else False
        self.preview_mode = "combined"
        self.preview_margin = 5

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
            "blocked_warnings": ["gvb_sort_pairs"],
        }

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

        with Container(id="main-container"):
            yield TemplateInfo(id="template-info")
            with Container(id="preview-container"):
                with TabbedContent(id="input-preview-tabs"):
                    with TabPane("Input", id="input-preview-tab"):
                        yield InputPreview(id="preview-box")
                    with TabPane("Next Step", id="next-step-preview-tab"):
                        yield NextStepPreview(id="next-step-preview")
                yield OutputPreview(id="output-preview")

            with Horizontal(id="buttons"):
                yield Button("Settings", variant="default", id="settings-btn")
                yield Button("UI Settings", variant="default", id="ui-settings-btn")
                yield Button("Next Step", variant="default", id="next-step-btn")
                yield Button("Run", variant="default", id="run-btn")
                yield Button("Save (s)", variant="default", id="save-btn")
                yield Button("Exit (q)", variant="error", id="exit-btn")

    def on_mount(self) -> None:
        """Initialize application"""
        if self.template_file:
            self.load_template(self.template_file)

        # Set up automated debugging actions if CLI flags are set
        self.setup_auto_actions()

    def update_template_info(self, message: str) -> None:
        """Update template information display"""
        info_widget = self.query_one("#template-info", TemplateInfo)
        info_widget.info = message  # type: ignore[attr-defined]

    def load_template(self, filepath: str) -> None:
        """Load a template gjf file"""
        try:
            self.template_sections = self.parser.parse_gjf(filepath)
            self.template_path = filepath
            with open(filepath, "r") as f:
                self.template_text = f.read()

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
            self.load_output_if_exists(filepath)

            # self.notify(f"Template loaded. Title set to 'mokit{{}}'", severity="success")

        except Exception as e:
            self.notify_persistent(
                f"Error loading template: {str(e)}", severity="error"
            )

    def generate_input(self) -> str:
        """Generate MOKIT input"""
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
        preview = self.query_one("#preview-box", InputPreview)
        preview.content = self.template_text or ""  # type: ignore[attr-defined]

    def update_next_step_preview(self, content: str) -> None:
        """Update next step preview tab"""
        self.next_step_preview_content = content
        preview = self.query_one("#next-step-preview", NextStepPreview)
        preview.content = content  # type: ignore[attr-defined]

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

    def prepare_next_step_with_fch(self, fch_file):
        """Prepare next step with specific fch file"""
        if fch_file:
            self.next_step_fch = fch_file
            self.notify_persistent(
                f"Prepared next step with {fch_file}", severity="success"
            )
        else:
            self.notify_persistent("No fch file selected", severity="warning")

    def auto_open_settings(self) -> None:
        """Programmatically open settings modal for debugging"""
        self.call_after_refresh(self._do_auto_open_settings)

    def _do_auto_open_settings(self) -> None:
        """Internal method to open settings modal with delay"""
        settings_screen = SettingsScreen(self.options)

        async def handle_settings_result(result):
            if result:
                self.options.update(result)
                self.update_preview()
                self.notify_persistent("Auto-settings applied", severity="information")

                # If next step flag is also set, open it after settings
                if self.auto_next_step:
                    self.call_after_refresh(self.auto_open_next_step)

        self.push_screen(settings_screen, handle_settings_result)
        self.notify_persistent("Auto-opening settings modal...", severity="information")

    def auto_open_next_step(self) -> None:
        """Programmatically open next step modal for debugging"""
        self.call_after_refresh(self._do_auto_open_next_step)

    def _do_auto_open_next_step(self) -> None:
        """Internal method to open next step modal with delay"""
        fch_options = self._get_fch_options()
        next_step_screen = NextStepScreen(fch_options=fch_options)  # type: ignore[call-arg]

        async def handle_next_step_result(result):
            if result and result.get("prepare"):
                selected_fch = result.get("fch_file")
                if selected_fch:
                    self.next_step_fch = selected_fch
                self.prepare_next_step(selected_fch)
            self.notify_persistent("Auto-next-step completed", severity="information")

        self.push_screen(next_step_screen, handle_next_step_result)
        self.notify_persistent(
            "Auto-opening next step modal...", severity="information"
        )

    def setup_auto_actions(self) -> None:
        """Set up automated actions based on CLI flags"""
        if self.auto_settings and self.auto_next_step:
            # If both flags set, open settings first, then next step
            self.call_after_refresh(self.auto_open_settings)
        elif self.auto_settings:
            self.call_after_refresh(self.auto_open_settings)
        elif self.auto_next_step:
            self.call_after_refresh(self.auto_open_next_step)

    populate_fch_files = populate_fch_files
    prepare_next_step = prepare_next_step

    def load_output_if_exists(self, gjf_path: str) -> None:
        """Load corresponding .out file if it exists"""
        try:
            # Try different possible output file names
            base_path = Path(gjf_path)
            possible_outputs = [
                str(base_path) + ".out",  # file.gjf.out
                base_path.with_suffix(".out"),  # file.out
                str(base_path).replace(".gjf", ".out"),  # file.out
            ]

            output_file = None
            for candidate in possible_outputs:
                if Path(candidate).exists():
                    output_file = candidate
                    break

            if output_file:
                parsed_data = self.output_parser.parse_output_file(output_file)
                formatted_output = self.output_parser.format_preview(
                    parsed_data, self.options.get("blocked_warnings", [])
                )
                fch_info = parser.FchPreviewParser.get_fch_preview_info(  # type: ignore[attr-defined]
                    gjf_path,
                    output_file,
                    mode=self.preview_mode,
                    margin=self.preview_margin,
                )
                output_preview = self.query_one("#output-preview", OutputPreview)
                output_preview.set_output_file(Path(output_file).name)
                output_preview.has_output = parsed_data.get("has_output", False)
                output_preview.set_output_content(formatted_output)  # type: ignore[attr-defined]
                output_preview.set_fch_content(fch_info)  # type: ignore[attr-defined]

                # Show notification about successful loading
                if parsed_data.get("has_output", False):
                    self.notify_persistent(
                        f"Loaded output: {Path(output_file).name}", "information"
                    )
                else:
                    self.notify_persistent(
                        f"Output file found but no key information: {Path(output_file).name}",
                        "warning",
                    )
            else:
                # No output file found
                output_preview = self.query_one("#output-preview", OutputPreview)
                output_preview.set_no_output()

        except Exception as e:
            self.notify_persistent(f"Error loading output file: {str(e)}", "error")
            # Set no output state on error
            try:
                output_preview = self.query_one("#output-preview", OutputPreview)
                output_preview.set_no_output()
            except Exception:
                pass

    def update_output_preview(self) -> None:
        """Update output preview box"""
        if self.template_path:
            self.load_output_if_exists(self.template_path)

    def notify_persistent(self, message: str, severity: str = "information") -> None:
        """Show a notification that stays until dismissed"""
        self.notify(message, severity=severity, timeout=0)  # type: ignore

    @on(Button.Pressed, "#settings-btn")
    def on_settings_button(self):
        settings_screen = SettingsScreen(self.options)

        async def handle_settings_result(result):
            if result:
                self.options.update(result)
                self.update_preview()

        self.push_screen(settings_screen, handle_settings_result)

    @on(Button.Pressed, "#ui-settings-btn")
    def on_ui_settings_button(self):
        ui_settings_screen = screens.UISettingsScreen(  # type: ignore[attr-defined]
            self.preview_mode,
            self.preview_margin,
        )

        async def handle_ui_settings_result(result):
            if result:
                if result.get("preview_mode"):
                    self.preview_mode = result["preview_mode"]
                if result.get("preview_margin") is not None:
                    try:
                        self.preview_margin = int(result["preview_margin"])
                    except (TypeError, ValueError):
                        self.preview_margin = 5
                self.update_output_preview()

        self.push_screen(ui_settings_screen, handle_ui_settings_result)

    @on(Button.Pressed, "#next-step-btn")
    def on_next_step_button(self):
        fch_options = self._get_fch_options()
        next_step_screen = NextStepScreen(fch_options=fch_options)  # type: ignore[call-arg]

        async def handle_next_step_result(result):
            if result and result.get("prepare"):
                selected_fch = result.get("fch_file")
                if selected_fch:
                    self.next_step_fch = selected_fch
                self.prepare_next_step(selected_fch)

        self.push_screen(next_step_screen, handle_next_step_result)

    def _get_fch_options(self) -> list[tuple[str, str]]:
        search_dirs = {Path(".")}
        if self.template_path:
            search_dirs.add(Path(self.template_path).parent)
        fch_files = set()
        for directory in search_dirs:
            fch_files.update(directory.rglob("*.fch"))
            fch_files.update(directory.rglob("*.FCH"))
        options = []
        for fch_file in sorted({path.resolve() for path in fch_files}):
            try:
                label = str(fch_file.relative_to(Path(".").resolve()))
            except ValueError:
                label = fch_file.name
            options.append((label, label))
        return options

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

    def key_s(self) -> None:
        """s to save"""
        self.save_input_file()

    def key_escape(self) -> None:
        """esc to exit"""
        self.exit()

    def key_q(self) -> None:
        """esc to exit"""
        self.exit()


def main():
    """Main entry point"""

    # Parse CLI arguments
    cli_args = parse_cli_args()
    template_file = cli_args.template_file

    # Validate template file exists
    if not Path(template_file).exists():
        print(f"Error: Template file '{template_file}' not found!")
        sys.exit(1)

    # Print debug info if auto-flags are set
    if cli_args.auto_settings or cli_args.auto_next_step:
        print("MOKIT TUI - Debug Mode")
        print(f"  Auto-settings: {cli_args.auto_settings}")
        print(f"  Auto-next-step: {cli_args.auto_next_step}")
        print(f"  Template file: {template_file}")
        print("-" * 40)

    # Create and run app with CLI args
    app = MTUI(cli_args)
    app.template_file = template_file
    app.run()


if __name__ == "__main__":
    main()
