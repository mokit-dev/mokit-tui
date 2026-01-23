from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Button
from textual import on
import subprocess
import sys
import argparse
import re
from typing import cast
from pathlib import Path

from automr.anal_fch import dump_mo_composition_fch, get_noon_from_fch

if __package__ is None:
    from pathlib import Path as _Path
    import sys as _sys

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

from mokit_tui.parser import GJFParser, OutputParser
from mokit_tui.gen import GJFGenerator
from mokit_tui.widgets import InputPreview, TemplateInfo, OutputPreview
from mokit_tui.screens import OutputScreen, SettingsScreen, NextStepScreen
from mokit_tui.css import CSS

from mokit_tui.workflow import *


def parse_cli_args(args=None):
    """Parse command-line arguments for debugging options"""
    parser = argparse.ArgumentParser(
        description="MOKIT TUI"
    )
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
        self.parser = GJFParser()
        self.output_parser = OutputParser()
        self.generator = GJFGenerator()
        self.next_step_fch = "default.fch"
        self.auto_settings = cli_args.auto_settings if cli_args else False
        self.auto_next_step = cli_args.auto_next_step if cli_args else False

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
                yield InputPreview(id="preview-box")
                yield OutputPreview(id="output-preview")

            with Horizontal(id="buttons"):
                yield Button("Settings", variant="default", id="settings-btn")
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
        next_step_screen = NextStepScreen()

        async def handle_next_step_result(result):
            if result and result.get("prepare"):
                self.prepare_next_step_with_fch(result.get("fch_file"))
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
                fch_info = self.get_fch_preview_info(gjf_path, output_file)
                if fch_info:
                    formatted_output = f"{formatted_output}\n\n{fch_info}"

                output_preview = self.query_one("#output-preview", OutputPreview)
                output_preview.set_output_file(Path(output_file).name)
                output_preview.has_output = parsed_data.get("has_output", False)
                output_preview.content = formatted_output

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
            except:
                pass

    def get_fch_preview_info(self, gjf_path: str, output_file: str) -> str:
        """Extract fch information for the output preview"""
        base_path = Path(gjf_path)
        pattern = f"{base_path.stem}_*_CASSCF_NO.fch"
        candidates = sorted(base_path.parent.glob(pattern))
        if not candidates:
            return "[dim]fch info: No matching fch file found[/dim]"

        fch_file = max(candidates, key=lambda path: path.stat().st_mtime)
        try:
            noon_values = get_noon_from_fch(str(fch_file))
            composition = dump_mo_composition_fch(str(fch_file))
            active_space = self.parse_active_space(output_file)
            active_space = self.normalize_active_space(active_space, len(noon_values))
        except Exception as exc:
            return f"[dim]fch info: Failed to read {fch_file.name}: {exc}[/dim]"

        lines = ["[bold magenta]fch info:[/bold magenta]"]
        lines.append(f"[magenta]File: {fch_file.name}[/magenta]")

        if noon_values is not None:
            noon_list = list(noon_values)
            active_noons, total_count = self.filter_active_noons(
                noon_list, active_space
            )
            mismatch_line = self.format_orbital_count_check(active_space, total_count)
            display_count = min(len(active_noons), 20)
            formatted_noons = ", ".join(
                f"{value:.6f}" if isinstance(value, (int, float)) else str(value)
                for value in active_noons[:display_count]
            )
            if len(active_noons) > display_count:
                formatted_noons += f", ... ({len(active_noons)} total)"
            elif total_count is not None and len(active_noons) != total_count:
                formatted_noons += f" ({len(active_noons)} of {total_count})"
            lines.append(f"[magenta]NOONs: {formatted_noons}[/magenta]")
            if mismatch_line:
                lines.append(mismatch_line)
            active_space_lines = self.format_active_space(active_space)
            if active_space_lines:
                lines.extend(active_space_lines)

        composition_text = self.format_mo_composition(composition, active_space)
        lines.append(f"[magenta]MO composition:[/magenta]")
        lines.extend(composition_text)
        return "\n".join(lines)

    @staticmethod
    def parse_active_space(output_file: str) -> dict:
        """Parse active space data from output log"""
        active_space: dict = {}
        in_do_cas_section = False

        with open(output_file, "r") as handle:
            for line in handle:
                if "Enter subroutine do_cas" in line:
                    in_do_cas_section = True
                    continue

                if not in_do_cas_section:
                    continue

                casscf_match = re.search(r"CASSCF\((\d+)e,\s*(\d+)o\)", line)
                if casscf_match:
                    active_space["active_electrons"] = int(casscf_match.group(1))
                    active_space["active_orbitals"] = int(casscf_match.group(2))

                docc_match = re.search(r"doubly_occ\s*=\s*(\d+)", line)
                if docc_match:
                    active_space["doubly_occ"] = int(docc_match.group(1))

                vir_match = re.search(r"nvir\s*=\s*(\d+)", line)
                if vir_match:
                    active_space["nvir"] = int(vir_match.group(1))

        return active_space

    @staticmethod
    def normalize_active_space(active_space: dict, total_count: int) -> dict:
        """Normalize active space values to ensure consistent counts"""
        normalized = dict(active_space)
        active_orbitals = normalized.get("active_orbitals")
        nvir = normalized.get("nvir")

        if isinstance(active_orbitals, int) and isinstance(nvir, int):
            inferred_docc = total_count - active_orbitals - nvir
            if inferred_docc >= 0:
                normalized.setdefault("doubly_occ", inferred_docc)

        return normalized

    @staticmethod
    def format_active_space(active_space: dict) -> list[str]:
        """Format active space info for preview"""
        lines = ["[bold magenta]Active Space:[/bold magenta]"]
        for key in ("active_electrons", "active_orbitals", "doubly_occ", "nvir"):
            if key in active_space:
                value = active_space[key]
                lines.append(
                    f"[magenta]{key.replace('_', ' ').title()}: {value}[/magenta]"
                )
            else:
                lines.append(
                    f"[dim]{key.replace('_', ' ').title()}: n/a[/dim]"
                )
        return lines

    @staticmethod
    def filter_active_noons(noon_list: list, active_space: dict) -> tuple[list, int | None]:
        """Filter NOONs to active space range"""
        total_count = len(noon_list)

        start_index, end_index = MTUI.get_active_range(active_space, total_count)
        if start_index is not None and end_index is not None:
            return noon_list[start_index:end_index], total_count

        return noon_list, total_count

    @staticmethod
    def format_orbital_count_check(active_space: dict, total_count: int | None) -> str:
        """Check total orbital count against docc/active/vir values"""
        if total_count is None:
            return ""

        doubly_occ = active_space.get("doubly_occ")
        active_orbitals = active_space.get("active_orbitals")
        nvir = active_space.get("nvir")

        if not isinstance(doubly_occ, int):
            return ""
        if not isinstance(active_orbitals, int):
            return ""
        if not isinstance(nvir, int):
            return ""

        doubly_occ_value = cast(int, doubly_occ)
        active_orbitals_value = cast(int, active_orbitals)
        nvir_value = cast(int, nvir)
        expected = doubly_occ_value + active_orbitals_value + nvir_value
        if expected == total_count:
            return "[magenta]Orbitals: total matches docc+active+vir[/magenta]"
        return (
            "[yellow]Orbitals mismatch: "
            f"total {total_count} vs docc+active+vir {expected}[/yellow]"
        )

    @staticmethod
    def format_mo_composition(composition, active_space: dict) -> list[str]:
        """Format MO composition data into single-line entries"""
        if not composition:
            return ["[magenta]MO composition: (empty)[/magenta]"]

        if isinstance(composition, dict):
            items = [composition]
        else:
            try:
                items = list(composition)
            except TypeError:
                items = [composition]

        start_index, end_index = MTUI.get_active_range(active_space, len(items))

        if start_index is not None and end_index is not None:
            filtered_items = items[start_index:end_index]
            start_number = start_index + 1
        else:
            filtered_items = items
            start_number = 1

        lines = []
        for offset, mo in enumerate(filtered_items, start=0):
            index = start_number + offset
            if isinstance(mo, dict):
                parts = []
                for key, value in mo.items():
                    if isinstance(value, float):
                        value_text = f"{value:.3f}"
                    else:
                        value_text = str(value)
                    parts.append(f"{key} {value_text}")
                detail = ", ".join(parts) if parts else str(mo)
            else:
                detail = str(mo)
            lines.append(f"[magenta]MO #{index}: {detail}[/magenta]")

        max_lines = 50
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines.append("[magenta]... (truncated)[/magenta]")
        return lines

    @staticmethod
    def get_active_range(active_space: dict, total_count: int | None) -> tuple[int | None, int | None]:
        """Get active space indices based on orbital counts"""
        doubly_occ = active_space.get("doubly_occ")
        active_orbitals = active_space.get("active_orbitals")
        nvir = active_space.get("nvir")

        if isinstance(doubly_occ, int) and isinstance(active_orbitals, int):
            start_index = doubly_occ
            end_index = doubly_occ + active_orbitals
            return start_index, end_index

        if (
            isinstance(active_orbitals, int)
            and isinstance(nvir, int)
            and isinstance(total_count, int)
        ):
            inferred_docc = total_count - active_orbitals - nvir
            if inferred_docc >= 0:
                return inferred_docc, inferred_docc + active_orbitals

        return None, None

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

    @on(Button.Pressed, "#next-step-btn")
    def on_next_step_button(self):
        next_step_screen = NextStepScreen()

        async def handle_next_step_result(result):
            if result and result.get("prepare"):
                self.prepare_next_step_with_fch(result.get("fch_file"))

        self.push_screen(next_step_screen, handle_next_step_result)

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
