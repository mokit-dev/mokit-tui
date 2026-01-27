# Output and fch Features

## Output Preview

- Parses output logs for warnings, programs used, and energies.
- Displays results in the output preview panel.
- Output file search order: `xxx.gjf.out`, then `xxx.out`.
- Supports MRSF-CIS energy sections from GAMESS output.
- Supports SA-CAS energy sections from SA-CASSCF output.
- Detects section headers and parses multiple state lines.
- Backward compatible with existing single-line energy patterns.

For detailed energy parsing information, see `doc/energy_parsing.md`.

## fch Preview

- Attempts to locate a matching fch file for the loaded template.
- Displays NOONs, active space, and MO composition when available.
- UI Settings control the fch preview mode and margin.

For full details, see `doc/preview_fch.md`.
