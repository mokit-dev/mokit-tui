# Energy Parsing Features

This document describes the energy parsing capabilities of MOKIT TUI's OutputParser.

## Supported Energy Formats

### Single-Line Energy Patterns
The parser detects and extracts energy values from these formats:

- `E(RHF) = -38.88107823 a.u., <S**2>=  0.000`
- `E(UHF) = -38.89950060 a.u., <S**2>=  0.713`
- `E(GVB) = -38.93420838 a.u.`
- `E(CASCI)  = -38.90173912 a.u.`
- `E(CASSCF) = -38.90245513 a.u.`
- `SCF Done: E(RHF) = -38.88107823`
- `CASCI E  = -38.90173912 a.u.`

### Multi-Section Energy Formats

#### MRSF-CIS Sections
Supports GAMESS MRSF-CIS calculations with header and state lines:

```
MRSF-CIS energies from GAMESS:
Ground State    0: E=    -38.892459 a.u.                        <S**2>=   0.000
Excited State   1: E=    -38.822651 a.u. (  1.90 eV), f=0.0051, <S**2>=   0.000
Excited State   2: E=    -38.695945 a.u. (  5.35 eV), f=0.0089, <S**2>=   0.000
Excited State   3: E=    -38.657460 a.u. (  6.39 eV), f=0.0000, <S**2>=   0.000
```

#### SA-CAS Sections
Supports SA-CASSCF calculation energy states:

```
CASCI energies after SA-CASSCF(0 for ground state):   E_ex/eV   fosc
State   0, E =    -38.90257869 a.u. <S**2> = 2.000
State   1, E =    -38.89244580 a.u. <S**2> = 0.000    0.276   0.0000
State   2, E =    -38.82071323 a.u. <S**2> = 0.000    2.228   0.0000
State   3, E =    -38.71285121 a.u. <S**2> = 0.000    5.163   0.0000
```

## How It Works

### Single-Line Detection
The parser uses regex patterns to match common energy formats directly in output files.

### Section-Based Detection
For multi-section formats:

1. **Header Detection**: Identifies section headers like "MRSF-CIS energies from GAMESS:" or "CASCI energies after SA-CASSCF"
2. **State Parsing**: Extracts all following energy state lines until non-matching content is encountered
3. **Context Preservation**: Section headers are included in the preview to provide context for the following energy values

## Output Preview

All detected energies are displayed in the output preview panel with:
- Line numbers for reference
- Green text formatting
- Section headers shown before their corresponding state energies
- Backward compatibility with existing single-line energy formats

## Implementation Notes

- The parser stops parsing sections when encountering non-energy lines
- Multiple sections of the same type are supported in a single file
- Both MRSF-CIS and SA-CAS formats preserve header information in the preview
- Existing single-line energy patterns continue to work unchanged