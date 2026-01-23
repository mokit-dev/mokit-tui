import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, cast

from automr.anal_fch import dump_mo_composition_fch, get_noon_from_fch

__all__ = ["GJFParser", "OutputParser", "FchPreviewParser"]


class GJFParser:
    """Parse Gaussian .gjf files with mokit{} support"""

    @staticmethod
    def parse_gjf(filepath: str) -> Dict:
        """Parse a gjf file into sections"""
        with open(filepath, "r") as f:
            content = f.read()

        sections = {}

        # Find route section (starts with #)
        route_match = re.search(r"(#.*?)\n\n", content, re.DOTALL)
        if route_match:
            sections["route"] = route_match.group(1).strip()
        else:
            lines = content.split("\n")
            route_lines = []
            for line in lines:
                if line.strip().startswith("#"):
                    route_lines.append(line)
                elif route_lines and line.strip():
                    route_lines.append(line)
                elif route_lines:
                    break
            sections["route"] = "\n".join(route_lines)

        # Find title line (after route section)
        route_end = content.find(sections["route"]) + len(sections["route"])
        remaining = content[route_end:].lstrip("\n")

        title_lines = []
        for line in remaining.split("\n"):
            if re.match(r"^\s*-?\d+\s+-?\d+\s*$", line.strip()):
                break
            if line.strip():
                title_lines.append(line.strip())
            elif title_lines:
                break

        if title_lines:
            sections["title"] = "\n".join(title_lines)
            # Parse mokit options from title
            sections["mokit_options"] = GJFParser.parse_mokit_options(title_lines[0])
        else:
            sections["title"] = "mokit{}"
            sections["mokit_options"] = {}

        # Find charge and multiplicity
        charge_mult = re.search(r"\n\n\s*(-?\d+)\s+(-?\d+)\s*\n", content)
        if not charge_mult:
            charge_mult = re.search(r"\n\s*(-?\d+)\s+(-?\d+)\s*\n", content)

        if charge_mult:
            sections["charge"] = int(charge_mult.group(1))
            sections["multiplicity"] = int(charge_mult.group(2))
        else:
            sections["charge"] = 0
            sections["multiplicity"] = 1

        # Find molecular geometry
        geometry_start = 0
        if charge_mult:
            pattern = f"\n{charge_mult.group(1)}\\s+{charge_mult.group(2)}\n"
            geometry_start = content.find(pattern)
            if geometry_start != -1:
                geometry_start += len(pattern)

        if geometry_start:
            geometry_text = content[geometry_start:].strip()
            end_match = re.search(r"\n\n", geometry_text)
            sections["geometry"] = (
                geometry_text[: end_match.start()].strip()
                if end_match
                else geometry_text
            )
        else:
            sections["geometry"] = ""

        # Additional sections
        if sections.get("geometry"):
            geom_end = content.find(sections["geometry"]) + len(sections["geometry"])
            remaining = content[geom_end:].strip()
            if remaining:
                sections["additional"] = remaining

        return sections

    @staticmethod
    def parse_mokit_options(title_line: str) -> Dict:
        """Parse mokit options from title line like 'mokit{option1, option2=value}'"""
        options = {}

        # Look for mokit{...} pattern
        match = re.search(r"mokit\{([^}]*)\}", title_line)
        if not match:
            return options

        content = match.group(1).strip()
        if not content:
            return options

        # Parse comma-separated options
        # Handle both simple flags and key=value pairs
        for item in content.split(","):
            item = item.strip()
            if "=" in item:
                key, value = item.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Try to parse value types
                if value.lower() in ["true", "yes", "on"]:
                    options[key] = True
                elif value.lower() in ["false", "no", "off"]:
                    options[key] = False
                elif value.isdigit():
                    options[key] = int(value)
                elif re.match(r"^-?\d+\.\d+$", value):
                    options[key] = float(value)
                else:
                    options[key] = value
            else:
                # Simple flag
                if item:
                    options[item] = True

        return options

    @staticmethod
    def format_mokit_options(options: Dict) -> str:
        """Format mokit options back to string format"""
        if not options:
            return ""

        parts = []
        for key, value in sorted(options.items()):
            if isinstance(value, bool):
                if value:
                    parts.append(key)
                # Don't add false flags
            else:
                parts.append(f"{key}={value}")

        return ", ".join(parts)

    @staticmethod
    def get_atom_info(geometry: str) -> Tuple[int, List[str]]:
        """Extract atom count and types from geometry"""
        atoms = []
        for line in geometry.split("\n"):
            parts = line.strip().split()
            if len(parts) >= 1 and parts[0].isalpha():
                atoms.append(parts[0])
        return len(atoms), list(set(atoms))


class OutputParser:
    """Parse Gaussian/MOKIT output files to extract key information"""

    def __init__(self):
        self.warnings = []
        self.programs = []
        self.energies = []

    def parse_output_file(self, filepath: str) -> Dict:
        """Parse an output file and extract key information"""
        self.warnings = []
        self.programs = []
        self.energies = []

        try:
            with open(filepath, "r") as f:
                lines = f.readlines()
        except FileNotFoundError:
            return {"warnings": [], "programs": [], "energies": [], "has_output": False}

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            line_num = i + 1

            # Parse warnings (multi-line)
            if self._is_warning_line(line):
                # Start accumulating warning lines
                warning_lines = [line]
                start_line_num = line_num
                end_line_num = line_num
                
                # If the warning line itself is complete, don't accumulate more
                if not self._is_sentence_complete(line):
                    # Continue reading lines until sentence is complete
                    i += 1
                    while i < len(lines):
                        next_line = lines[i].strip()
                        warning_lines.append(next_line)
                        end_line_num = i + 1
                        
                        if self._is_sentence_complete(next_line):
                            break
                        i += 1
                
                # Store complete warning
                self.warnings.append({
                    "text": " ".join(warning_lines),
                    "start_line": start_line_num,
                    "end_line": end_line_num
                })
            
            # Parse program usage
            elif self._is_program_line(line):
                self.programs.append({"line": line, "line_number": line_num})
            
            # Parse energies
            elif self._is_energy_line(line):
                self.energies.append({"line": line, "line_number": line_num})

            i += 1

        return {
            "warnings": self.warnings,
            "programs": self.programs,
            "energies": self.energies,
            "has_output": bool(self.warnings or self.programs or self.energies),
        }

    def _is_warning_line(self, line: str) -> bool:
        """Check if line contains a warning"""
        warning_patterns = [
            r"^Warning:",
            r"^WARNING:",
            r"^UserWarning:",
        ]
        
        for pattern in warning_patterns:
            if re.search(pattern, line):
                return True
        return False
    
    def _is_sentence_complete(self, line: str) -> bool:
        """Check if a line forms a complete sentence"""
        stripped = line.strip()
        return stripped.endswith(('.', '!', '?', ':'))

    def _is_program_line(self, line: str) -> bool:
        """Check if line contains program usage information"""
        program_patterns = [
            r"using program\s+\w+",
            r"HF using program\s+\w+",
            r"CASSCF\([^)]+\)\s+using program\s+\w+",
            r"CASCI\([^)]+\)\s+using program\s+\w+",
            r"MC-PDFT\([^)]+\)\s+using program\s+\w+",
        ]

        for pattern in program_patterns:
            if re.search(pattern, line):
                return True
        return False

    def _is_energy_line(self, line: str) -> bool:
        """Check if line contains energy information"""
        energy_patterns = [
            r"E\([^)]+\)\s*=\s*[-+]?\d*\.\d+.*a\.u\.",
            r"E\(\w+\)\s*=\s*[-+]?\d*\.\d+",
            r"SCF Done:\s+E\([^)]+\)\s*=\s*[-+]?\d*\.\d+",
            r"CASCI E\s*=\s*[-+]?\d*\.\d+",
            r"E\(\w+\)\s*=\s*[-+]?\d*\.\d+\s*a\.u\.",
        ]

        for pattern in energy_patterns:
            if re.search(pattern, line):
                return True
        return False


    def format_preview(
        self, parsed_data: Dict, blocked_warnings: Optional[List[str]] = None
    ) -> str:
        """Format parsed data for display in preview widget"""
        if not parsed_data.get("has_output", False):
            return "[dim]No output file found or no key information detected[/dim]"

        if blocked_warnings is None:
            blocked_warnings = []

        sections = []

        # Format warnings (filtered)
        filtered_warnings = []
        for warning in parsed_data["warnings"]:
            is_blocked = False
            for blocked_pattern in blocked_warnings:
                if re.search(re.escape(blocked_pattern), warning["text"], re.IGNORECASE):
                    is_blocked = True
                    break
            if not is_blocked:
                filtered_warnings.append(warning)

        if filtered_warnings:
            sections.append("[bold yellow]Warnings:[/bold yellow]")
            for warning in filtered_warnings:
                if warning["start_line"] == warning["end_line"]:
                    line_info = f"Line {warning['start_line']}"
                else:
                    line_info = f"Lines {warning['start_line']}-{warning['end_line']}"
                sections.append(
                    f"[yellow]{line_info}: {warning['text']}[/yellow]"
                )
            sections.append("")

        # Format programs
        if parsed_data["programs"]:
            sections.append("[bold blue]Programs Used:[/bold blue]")
            for program in parsed_data["programs"]:
                sections.append(
                    f"[blue]Line {program['line_number']}: {program['line']}[/blue]"
                )
            sections.append("")

        # Format energies
        if parsed_data["energies"]:
            sections.append("[bold green]Energies:[/bold green]")
            for energy in parsed_data["energies"]:
                sections.append(
                    f"[green]Line {energy['line_number']}: {energy['line']}[/green]"
                )
            sections.append("")

        return "\n".join(sections)


class FchPreviewParser:
    """Parse fch data for preview display"""

    @staticmethod
    def get_fch_preview_info(gjf_path: str, output_file: str) -> str:
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
            active_space = FchPreviewParser.parse_active_space(output_file)
            active_space = FchPreviewParser.normalize_active_space(
                active_space, len(noon_values)
            )
        except Exception as exc:
            return f"[dim]fch info: Failed to read {fch_file.name}: {exc}[/dim]"

        lines = ["[bold magenta]fch info:[/bold magenta]"]
        lines.append(f"[magenta]File: {fch_file.name}[/magenta]")

        if noon_values is not None:
            noon_list = list(noon_values)
            active_noons, total_count = FchPreviewParser.filter_active_noons(
                noon_list, active_space
            )
            mismatch_line = FchPreviewParser.format_orbital_count_check(
                active_space, total_count
            )
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
            active_space_lines = FchPreviewParser.format_active_space(active_space)
            if active_space_lines:
                lines.extend(active_space_lines)

        composition_text = FchPreviewParser.format_mo_composition(
            composition, active_space
        )
        lines.append("[magenta]MO composition:[/magenta]")
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
                    active_space["nacto"] = int(casscf_match.group(2))

                docc_match = re.search(r"doubly_occ\s*=\s*(\d+)", line)
                if docc_match:
                    active_space["ndb"] = int(docc_match.group(1))

                vir_match = re.search(r"nvir\s*=\s*(\d+)", line)
                if vir_match:
                    active_space["nvir"] = int(vir_match.group(1))

        return active_space

    @staticmethod
    def normalize_active_space(active_space: dict, total_count: int) -> dict:
        """Normalize active space values to ensure consistent counts"""
        normalized = dict(active_space)
        nacto = normalized.get("nacto")
        ndb = normalized.get("ndb")
        nvir = normalized.get("nvir")

        if not isinstance(nacto, int):
            raise ValueError("Missing nacto in output log")
        if not isinstance(ndb, int):
            raise ValueError("Missing ndb in output log")
        if not isinstance(nvir, int):
            raise ValueError("Missing nvir in output log")

        expected = ndb + nacto + nvir
        if expected != total_count:
            raise ValueError(
                "Active space counts do not match NOON total: "
                f"{expected} vs {total_count}"
            )

        return normalized

    @staticmethod
    def format_active_space(active_space: dict) -> list[str]:
        """Format active space info for preview"""
        label_map = {
            "active_electrons": "Active Electrons",
            "nacto": "NACTO",
            "ndb": "NDB",
            "nvir": "NVIR",
        }
        lines = ["[bold magenta]Active Space:[/bold magenta]"]
        for key in ("active_electrons", "nacto", "ndb", "nvir"):
            if key in active_space:
                value = active_space[key]
                lines.append(f"[magenta]{label_map[key]}: {value}[/magenta]")
            else:
                lines.append(f"[dim]{label_map[key]}: n/a[/dim]")
        return lines

    @staticmethod
    def filter_active_noons(noon_list: list, active_space: dict) -> tuple[list, int | None]:
        """Filter NOONs to active space range"""
        total_count = len(noon_list)

        start_index, end_index = FchPreviewParser.get_active_range(
            active_space, total_count
        )
        if start_index is not None and end_index is not None:
            return noon_list[start_index:end_index], total_count

        return noon_list, total_count

    @staticmethod
    def format_orbital_count_check(active_space: dict, total_count: int | None) -> str:
        """Check total orbital count against ndb/nacto/nvir values"""
        if total_count is None:
            return ""

        ndb = active_space.get("ndb")
        nacto = active_space.get("nacto")
        nvir = active_space.get("nvir")

        if not isinstance(ndb, int):
            return ""
        if not isinstance(nacto, int):
            return ""
        if not isinstance(nvir, int):
            return ""

        ndb_value = cast(int, ndb)
        nacto_value = cast(int, nacto)
        nvir_value = cast(int, nvir)
        expected = ndb_value + nacto_value + nvir_value
        if expected == total_count:
            return "[magenta]Orbitals: total matches ndb+nacto+nvir[/magenta]"
        return (
            "[yellow]Orbitals mismatch: "
            f"total {total_count} vs ndb+nacto+nvir {expected}[/yellow]"
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

        start_index, end_index = FchPreviewParser.get_active_range(
            active_space, len(items)
        )

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
        ndb = active_space.get("ndb")
        nacto = active_space.get("nacto")
        nvir = active_space.get("nvir")

        if isinstance(ndb, int) and isinstance(nacto, int):
            start_index = ndb
            end_index = ndb + nacto
            return start_index, end_index

        if (
            isinstance(nacto, int)
            and isinstance(nvir, int)
            and isinstance(total_count, int)
        ):
            inferred_ndb = total_count - nacto - nvir
            if inferred_ndb >= 0:
                return inferred_ndb, inferred_ndb + nacto

        return None, None
