import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json


class GJFParser:
    """Parse Gaussian .gjf files with mokit{} support"""

    @staticmethod
    def parse_gjf(filepath: str) -> Dict:
        """Parse a Gaussian gjf file into sections"""
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
            return {
                "warnings": [],
                "programs": [],
                "energies": [],
                "has_output": False
            }
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Parse warnings
            if self._is_warning_line(line):
                self.warnings.append({
                    "line": line,
                    "line_number": line_num
                })
            
            # Parse program usage
            elif self._is_program_line(line):
                self.programs.append({
                    "line": line,
                    "line_number": line_num
                })
            
            # Parse energies
            elif self._is_energy_line(line):
                self.energies.append({
                    "line": line,
                    "line_number": line_num
                })
        
        return {
            "warnings": self.warnings,
            "programs": self.programs,
            "energies": self.energies,
            "has_output": bool(self.warnings or self.programs or self.energies)
        }
    
    def _is_warning_line(self, line: str) -> bool:
        """Check if line contains a warning"""
        warning_patterns = [
            r"Warning:",
            r"WARNING:",
            r"UserWarning:",
            r"^.*[Ww]arning.*$",
        ]
        
        for pattern in warning_patterns:
            if re.search(pattern, line):
                return True
        return False
    
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
    
    def format_preview(self, parsed_data: Dict) -> str:
        """Format parsed data for display in preview widget"""
        if not parsed_data.get("has_output", False):
            return "[dim]No output file found or no key information detected[/dim]"
        
        sections = []
        
        # Format warnings
        if parsed_data["warnings"]:
            sections.append("[bold yellow]Warnings:[/bold yellow]")
            for warning in parsed_data["warnings"]:
                sections.append(f"[yellow]Line {warning['line_number']}: {warning['line']}[/yellow]")
            sections.append("")
        
        # Format programs
        if parsed_data["programs"]:
            sections.append("[bold blue]Programs Used:[/bold blue]")
            for program in parsed_data["programs"]:
                sections.append(f"[blue]Line {program['line_number']}: {program['line']}[/blue]")
            sections.append("")
        
        # Format energies
        if parsed_data["energies"]:
            sections.append("[bold green]Energies:[/bold green]")
            for energy in parsed_data["energies"]:
                sections.append(f"[green]Line {energy['line_number']}: {energy['line']}[/green]")
            sections.append("")
        
        return "\n".join(sections)
