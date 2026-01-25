from pathlib import Path


# Update prepare_next_step() method to use selected fch file:
def prepare_next_step(self, selected_fch: str | None = None) -> None:
    """Prepare input for next calculation step"""
    try:
        if selected_fch is None:
            selected_fch = None

        original_mem = None
        original_nprocshared = None
        original_nproc = None
        for line in self.template_text.splitlines():
            stripped = line.strip()
            lower = stripped.lower()
            if lower.startswith("%mem=") and original_mem is None:
                original_mem = stripped
            elif lower.startswith("%nprocshared=") and original_nprocshared is None:
                original_nprocshared = stripped
            elif lower.startswith("%nproc=") and original_nproc is None:
                original_nproc = stripped

        # 1. Generate current input
        current_content = self.generate_input()

        # 2. Create modified content with readno option
        lines = current_content.split("\n")
        modified_lines = []

        for line in lines:
            if "mokit{" in line:
                # Add readno=selected_fch to mokit options
                if selected_fch is None:
                    modified_lines.append(line)
                    continue
                if "}" in line:
                    # Check if readno already exists
                    if "readno=" in line:
                        # Replace existing readno
                        import re

                        line = re.sub(r"readno=[^,}]+", f"readno={selected_fch}", line)
                    else:
                        # Add new readno before closing }
                        line = line.replace("}", f", readno={selected_fch}}}")
                else:
                    line = f"{line}, readno={selected_fch}"
            modified_lines.append(line)

        cleaned_lines = []
        for line in modified_lines:
            stripped = line.strip()
            lower = stripped.lower()
            if lower.startswith("%chk="):
                continue
            if original_mem and lower.startswith("%mem="):
                continue
            if (original_nprocshared or original_nproc) and (
                lower.startswith("%nprocshared=") or lower.startswith("%nproc=")
            ):
                continue
            cleaned_lines.append(line)

        insert_directives = []
        if original_mem:
            insert_directives.append(original_mem)
        if original_nprocshared:
            insert_directives.append(original_nprocshared)
        elif original_nproc:
            insert_directives.append(original_nproc)

        if insert_directives:
            insert_at = 0
            while insert_at < len(cleaned_lines) and cleaned_lines[
                insert_at
            ].lstrip().startswith("%"):
                insert_at += 1
            cleaned_lines = (
                cleaned_lines[:insert_at]
                + insert_directives
                + cleaned_lines[insert_at:]
            )
        new_content = "\n".join(cleaned_lines)

        # 3. Save to new file with timestamp
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"input_next_{timestamp}.gjf"

        with open(new_filename, "w") as f:
            f.write(new_content)

        # 4. Show in preview box with highlighting
        highlighted_lines = []
        for line in new_content.split("\n"):
            if "readno=" in line:
                highlighted_lines.append(f"[bold green]{line}[/bold green]")
            elif "mokit{" in line:
                highlighted_lines.append(f"[bold cyan]{line}[/bold cyan]")
            else:
                highlighted_lines.append(line)

        highlighted_content = "\n".join(highlighted_lines)
        self.update_next_step_preview(
            f"[dim]{new_filename}[/dim]\n\n{highlighted_content}"
        )

        fch_note = f"\nUsing fch: {selected_fch}" if selected_fch else ""
        self.notify(
            f"Next step prepared: {new_filename}{fch_note}",
            severity="success",
            timeout=0,
        )

    except Exception as e:
        self.notify(f"Error preparing next step: {str(e)}", severity="error", timeout=0)


def populate_fch_files(self) -> None:
    """Populate fch file dropdown"""
    fch_select = self.query_one("#fch-select", Select)
    fch_files = list(Path(".").glob("*.fch"))
    fch_files += list(Path(".").glob("*.FCH"))

    options = [("default.fch", "default.fch")]
    options += [(f.name, f.name) for f in sorted(fch_files)]

    fch_select.set_options(options)

    # Set current selection to first .fch file if available, otherwise default
    if fch_files:
        self.next_step_fch = fch_files[0].name
        fch_select.value = self.next_step_fch
    else:
        fch_select.value = "default.fch"
