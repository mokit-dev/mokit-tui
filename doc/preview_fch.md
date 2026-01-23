# Output Preview fch Info

This document summarizes the output preview enhancements for fch-derived
active-space information and how the TUI uses output logs to scope the preview.

## Overview

When a template GJF is loaded, the output preview now attempts to extract
information from a matching formatted checkpoint file (fch). The preview
includes:

- NOONs (natural orbital occupation numbers)
- Active-space metadata (active electrons/orbitals, doubly occupied, virtual)
- MO composition lines, filtered to the active space while keeping MO numbering

If the fch file is missing or parsing fails, the preview shows a dim warning
instead of raising errors.

## fch File Naming

For a template `xxx.gjf`, the preview searches for:

```
xxx_*_CASSCF_NO.fch
```

The newest match by modification time is used.

## Active-Space Parsing Rules

Active-space values are parsed from the output log. The parser looks for these
lines after the marker `Enter subroutine do_cas`:

- `CASSCF(Ne,No)` -> active electrons and active orbitals
- `doubly_occ=...` -> number of doubly occupied orbitals
- `nvir=...` -> number of virtual orbitals

The values are displayed in the preview under an `Active Space` section.

If `doubly_occ` is missing but `active_orbitals` and `nvir` are present, the
preview infers:

```
doubly_occ = total_orbitals - active_orbitals - nvir
```

## NOON Preview Logic

NOONs are loaded using `automr.anal_fch.get_noon_from_fch`. The preview only
prints the active-space slice, ordered as:

```
doubly occupied -> active -> virtual
```

The slice range is computed as:

```
start = doubly_occ
end = doubly_occ + active_orbitals
```

If no active-space indices are available, the preview falls back to showing the
full NOON list.

The preview also reports whether the total number of NOONs matches
`doubly_occ + active_orbitals + nvir`.

## MO Composition Preview

MO composition is loaded using `automr.anal_fch.dump_mo_composition_fch`. Each
MO is printed on a single line as:

```
MO #n: key value, key value, ...
```

Only the active-space range is shown in the preview. The MO numbering remains
the original MO index, not renumbered to the slice.

Floating-point values are formatted to 3 digits after the decimal point.
