from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static
from textual.widgets import (
    Header,
    Footer,
    Button,
    Input,
    Label,
    Select,
    TabbedContent,
    TabPane,
)
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
from mokit_tui.screens import OutputScreen, SaveScreen, SettingsScreen
from mokit_tui.css import CSS

from mokit_tui.workflow import (
    _build_next_step_content,
    populate_fch_files,
    prepare_next_step,
)


def parse_cli_args(args=None):
    """Parse command-line arguments for debugging options"""
    parser = argparse.ArgumentParser(description="MOKIT TUI")
    parser.add_argument("template_file", help="Template GJF file to load")
    parser.add_argument(
        "-s",
        "--auto-settings",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-n",
        "--auto-next-step",
        action="store_true",
        help=argparse.SUPPRESS,
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
        self.input_file = ""
        self.template_sections = {}
        self.template_path = None
        self.template_text = ""
        self.next_step_preview_content = "[dim]No next step prepared[/dim]"
        self.next_step_path = None
        self.next_step_content = ""
        self.parser = GJFParser()
        self.output_parser = OutputParser()
        self.generator = GJFGenerator()
        self.next_step_fch = "default.fch"
        self.auto_settings = cli_args.auto_settings if cli_args else False
        self.auto_next_step = cli_args.auto_next_step if cli_args else False
        self.preview_mode = "combined"
        self.preview_margin = 5

        self.options = {
            "method": "",
            "basis_set": "",
            "memory": "2GB",
            "processors": 4,
            "checkpoint": "input.chk",
            "charge": 0,
            "multiplicity": 1,
            "additional_keywords": "",
            "additional_mokit_options": "",
            "blocked_warnings": ["gvb_sort_pairs"],
        }
        self.next_step_method = ""

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

        with Container(id="main-container"):
            yield TemplateInfo(id="template-info")
            with Container(id="preview-container"):
                with Container(id="input-panel"):
                    with TabbedContent(id="input-preview-tabs"):
                        with TabPane("Input", id="input-preview-tab"):
                            yield InputPreview(id="preview-box")
                        with TabPane("Next Step", id="next-step-preview-tab"):
                            yield NextStepPreview(id="next-step-tab-preview")
                    with Container(id="next-step-container", classes="is-hidden"):
                        yield Static("[b]Next Step[/b]", id="next-step-title")
                        with Horizontal(id="next-step-name-row"):
                            yield Label("basename:", id="next-step-name-label")
                            yield Input(
                                placeholder="input_next",
                                id="next-step-basename-input",
                            )
                            yield Label("method:", id="next-step-method-label")
                            yield Select(
                                [],
                                id="next-step-method-select",
                                prompt="Select method",
                            )
                        with Horizontal(id="next-step-controls"):
                            yield Label("fch file:", id="next-step-fch-label")
                            yield Select([], id="next-step-fch-select")
                            yield Button(
                                "Prepare", variant="primary", id="next-step-prepare-btn"
                            )
                yield OutputPreview(id="output-preview")

            with Horizontal(id="buttons"):
                yield Button("Settings", variant="default", id="settings-btn")
                yield Button("UI Settings", variant="default", id="ui-settings-btn")
                yield Button("Next Step (n)", variant="default", id="next-step-btn")
                yield Button("Run (r)", variant="default", id="run-btn")
                yield Button("Save (s)", variant="default", id="save-btn")
                yield Button("Exit (q)", variant="error", id="exit-btn")

    def on_mount(self) -> None:
        """Initialize application"""
        if self.template_file:
            self.load_template(self.template_file)

        self.update_fch_select()

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
            self.input_file = filepath
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
            self.update_fch_select()
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
        tab_preview = self.query_one("#next-step-tab-preview", NextStepPreview)
        tab_preview.content = content  # type: ignore[attr-defined]

    def save_input_file(self) -> None:
        """Save to input.gjf"""
        if not self.input_file:
            self.notify_persistent("No input file loaded", severity="warning")
            return
        self.save_input_file_to(self.input_file)

    def save_input_file_to(self, filepath: str) -> None:
        """Save to specified gjf file"""
        content = self.generate_input()
        self.save_content_to(content, filepath)

    def save_content_to(self, content: str, filepath: str) -> None:
        """Save specified content to file"""
        with open(filepath, "w") as f:
            f.write(content)

        file_size = Path(filepath).stat().st_size
        self.notify_persistent(
            f"Saved to {filepath} ({file_size} bytes)", severity="information"
        )

    def _get_active_tab(self) -> str:
        tabbed = self.query_one("#input-preview-tabs", TabbedContent)
        return tabbed.active

    def _get_run_target(self) -> tuple[str, str] | None:
        active_tab = self._get_active_tab()
        if active_tab == "next-step-preview-tab":
            if self.next_step_path and Path(self.next_step_path).exists():
                return self.next_step_path, "next step"
            self.notify_persistent("No next step file prepared", severity="warning")
            return None

        if self.input_file and Path(self.input_file).exists():
            return self.input_file, "template"

        self.notify_persistent("No template loaded", severity="warning")
        return None

    def run_calculation(self) -> None:
        """Run backend program"""
        run_target = self._get_run_target()
        if not run_target:
            return

        input_path, _ = run_target
        output_path = f"{input_path}.out"

        try:
            with open(output_path, "w") as output_file:
                result = subprocess.run(
                    ["automr", input_path],
                    stdout=output_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                )

            output_text = "No output"
            output_file_path = Path(output_path)
            if output_file_path.exists():
                output_text = output_file_path.read_text() or "No output"

            if result.returncode == 0:
                self.app.push_screen(
                    OutputScreen(
                        output_text,
                        title=f"Calculation Output ({Path(input_path).name})",
                    )
                )
                self.load_output_if_exists(input_path)
            else:
                self.app.push_screen(
                    OutputScreen(
                        f"Error (code {result.returncode}):\n\n{output_text}",
                        title="Error",
                    )
                )
        except FileNotFoundError:
            self.notify_persistent("Backend 'automr' not found!", severity="error")
        except Exception as e:
            self.notify_persistent(f"Error running automr: {str(e)}", severity="error")

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
        """Programmatically prepare next step for debugging"""
        self.call_after_refresh(self._do_auto_open_next_step)

    def _do_auto_open_next_step(self) -> None:
        """Internal method to prepare next step with delay"""
        self.call_after_refresh(self.on_next_step_prepare_inline)
        self.notify_persistent("Auto-preparing next step...", severity="information")

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
    _build_next_step_content = _build_next_step_content

    def load_output_if_exists(self, gjf_path: str) -> None:
        """Load corresponding .out file if it exists"""
        try:
            # Try different possible output file names
            base_path = Path(gjf_path)
            possible_outputs = [
                str(base_path) + ".out",  # file.gjf.out
                base_path.with_suffix(".out"),  # file.out
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
        self.prepare_next_step_inline()

    @on(Button.Pressed, "#next-step-prepare-btn")
    def on_next_step_prepare_inline(self):
        self.prepare_next_step_inline()

    @on(Select.Changed, "#next-step-method-select")
    def on_next_step_method_changed(self, event: Select.Changed) -> None:
        selected_method = event.value
        if selected_method:
            self.next_step_method = selected_method
            self.options["method"] = selected_method

    def prepare_next_step_inline(self) -> None:
        self.show_next_step_container()
        name_input = self.query_one("#next-step-basename-input", Input)
        basename = name_input.value.strip()
        fch_select = self.query_one("#next-step-fch-select", Select)
        selected_fch = fch_select.value
        if selected_fch:
            self.next_step_fch = selected_fch
        method_select = self.query_one("#next-step-method-select", Select)
        selected_method = method_select.value
        if selected_method:
            self.next_step_method = selected_method
            self.options["method"] = selected_method
        self.prepare_next_step(selected_fch, basename)
        try:
            _, highlighted_content, _ = self._build_next_step_content(selected_fch)
            name_base = basename or "next_step_preview"
            if name_base.lower().endswith(".gjf"):
                name_base = name_base[:-4]
            preview_name = f"{name_base}.gjf"
            self.update_next_step_preview(
                f"[dim]{preview_name}[/dim]\n\n{highlighted_content}"
            )
        except Exception as e:
            self.notify(
                f"Error updating next step preview: {str(e)}",
                severity="error",
                timeout=0,
            )

    def show_next_step_container(self) -> None:
        container = self.query_one("#next-step-container", Container)
        container.remove_class("is-hidden")
        method_select = self.query_one("#next-step-method-select", Select)
        options = self._get_method_options()
        method_select.set_options(options)
        if self.next_step_method:
            method_select.value = self.next_step_method
        else:
            method_select.value = "CASSCF"

    def update_fch_select(self) -> None:
        fch_select = self.query_one("#next-step-fch-select", Select)
        options = self._get_fch_options()
        fch_select.set_options(options)
        if options:
            fch_select.value = options[0][1]

    def _get_method_options(self) -> list[tuple[str, str]]:
        return self.generator.get_methods()

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
        active_tab = self._get_active_tab()
        if active_tab == "next-step-preview-tab":
            current_file = self.next_step_path or ""
            tab_label = "Next Step"
        else:
            current_file = self.input_file
            tab_label = "Input"

        save_screen = SaveScreen(current_file, tab_label)

        async def handle_save_result(result):
            if not result:
                return
            action = result.get("action")
            filepath = result.get("path")
            if active_tab == "next-step-preview-tab":
                if action == "overwrite":
                    if not self.next_step_path:
                        self.notify_persistent(
                            "No next step file to overwrite", severity="warning"
                        )
                        return
                    if not self.next_step_content:
                        self.notify_persistent(
                            "No next step content to save", severity="warning"
                        )
                        return
                    self.save_content_to(self.next_step_content, self.next_step_path)
                elif action == "save_as" and filepath:
                    if not self.next_step_content:
                        self.notify_persistent(
                            "No next step content to save", severity="warning"
                        )
                        return
                    self.save_content_to(self.next_step_content, filepath)
                    self.next_step_path = filepath
            else:
                if action == "overwrite":
                    self.save_input_file()
                elif action == "save_as" and filepath:
                    self.save_input_file_to(filepath)
                    self.input_file = filepath

        self.push_screen(save_screen, handle_save_result)

    @on(Button.Pressed, "#geom-btn")
    def on_geom_button(self):
        self.show_geometry()

    @on(Button.Pressed, "#exit-btn")
    def on_exit_button(self):
        self.exit()

    def key_s(self) -> None:
        """s to save"""
        self.on_save_button()

    def key_escape(self) -> None:
        """esc to exit"""
        self.exit()

    def key_q(self) -> None:
        """esc to exit"""
        self.exit()

    def key_n(self) -> None:
        """n to prepare next step"""
        self.prepare_next_step_inline()

    def key_r(self) -> None:
        """r to run"""
        self.run_calculation()


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
