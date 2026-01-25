import re
from typing import Dict
from .parser import GJFParser


class GJFGenerator:
    """Generate MOKIT input files with mokit{} support"""

    def __init__(self):
        self.methods = [
            ("GVB", "GVB"),
            ("CASCI", "CASCI"),
            ("CASSCF", "CASSCF"),
            ("DMRGCI", "DMRGCI"),
            ("DMRGSCF", "DMRGSCF"),
            ("NEVPT2", "NEVPT2"),
            ("CASPT2", "CASPT2"),
            ("CASPT2K", "CASPT2K"),
            ("CASPT3", "CASPT3"),
            ("SDSPT2", "SDSPT2"),
            ("MRMP2", "MRMP2"),
            ("OVBMP2", "OVBMP2"),
            ("MRCISD", "MRCISD"),
            ("MRCISDT", "MRCISDT"),
            ("MCPDFT", "MCPDFT"),
            ("DFTCI", "DFTCI"),
            ("FICMRCCSD", "FICMRCCSD"),
            ("BCCC2b", "BCCC2b"),
            ("BCCC3b", "BCCC3b"),
        ]

    def generate_gjf(self, sections: Dict, options: Dict) -> str:
        """Generate gjf content"""
        gjf_lines = []

        # Route section
        route = sections.get("route", "#")

        # Update method if specified
        if options.get("method"):
            route = self._update_route_method(route, options["method"])

        # Update basis set if specified
        if options.get("basis_set"):
            route = self._update_route_basis(route, options["basis_set"])

        # Add directives
        route_lines = route.split("\n")
        new_route = []

        # Add memory directive
        if not any("%mem" in line.lower() for line in route_lines):
            new_route.append(f"%mem={options.get('memory', '2GB')}")

        # Add nproc directive
        if not any("%nproc" in line.lower() for line in route_lines):
            new_route.append(f"%nprocshared={options.get('processors', 4)}")

        # Add checkpoint directive
        if not any("%chk" in line.lower() for line in route_lines):
            new_route.append(f"%chk={options.get('checkpoint', 'input.chk')}")

        # Add existing route lines
        new_route.extend(route_lines)

        # Add calculation keywords
        if options.get("additional_keywords"):
            calculation_line = new_route[-1] if new_route else "#"
            if options["additional_keywords"] not in calculation_line:
                new_route[-1] = f"{calculation_line} {options['additional_keywords']}"

        gjf_lines.append("\n".join(new_route))
        gjf_lines.append("")

        # Title with mokit{} options
        mokit_options = sections.get("mokit_options", {}).copy()

        # Add additional mokit options from UI
        if options.get("additional_mokit_options"):
            additional = self.parse_mokit_option_string(
                options["additional_mokit_options"]
            )
            mokit_options.update(additional)

        if mokit_options:
            mokit_str = GJFParser.format_mokit_options(mokit_options)
            gjf_lines.append(f"mokit{{{mokit_str}}}")
        else:
            gjf_lines.append("mokit{}")

        gjf_lines.append("")

        # Charge and multiplicity
        gjf_lines.append(
            f"  {sections.get('charge', 0)}  {sections.get('multiplicity', 1)}"
        )

        # Molecular geometry
        if sections.get("geometry"):
            gjf_lines.append(sections["geometry"])

        # Additional sections
        if sections.get("additional"):
            gjf_lines.append("")
            gjf_lines.append(sections["additional"])

        gjf_lines.append("")

        return "\n".join(gjf_lines)

    def parse_mokit_option_string(self, option_string: str) -> Dict:
        """Parse mokit options from UI input string"""
        options = {}
        if not option_string.strip():
            return options

        # Parse comma or space separated options
        for item in re.split(r"[,;\s]+", option_string):
            item = item.strip()
            if not item:
                continue

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
                options[item] = True

        return options

    @staticmethod
    def _update_route_method(route: str, method: str) -> str:
        if not method:
            return route

        def _replace_method(match: re.Match) -> str:
            prefix = match.group(1)
            suffix = match.group(3) or ""
            if "(" in method:
                return f"{prefix}{method}"
            return f"{prefix}{method}{suffix}"

        return re.sub(
            r"(?i)(#\s*p?\s+)([A-Za-z0-9-]+)(\([^)]*\))?",
            _replace_method,
            route,
            count=1,
        )

    @staticmethod
    def _update_route_basis(route: str, basis_set: str) -> str:
        if not basis_set:
            return route
        if "/" + basis_set in route:
            return route
        return re.sub(r"/(\S+)", f"/{basis_set}", route, count=1)

    def get_methods(self):
        """Get available methods"""
        return self.methods
