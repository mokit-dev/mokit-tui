# Input and IO Features

## Template Loading

- Loads a template `.gjf` file and stores the original text for preview.
- Extracts charge and multiplicity for UI options.
- Displays template info (filename, atom count, atom types).

## Input Generation

- Generates input using the template sections and current options.
- Adds optional keywords and mokit options from the UI.

## Save and Run

- Save writes the generated input to `input.gjf`.
- Run executes the backend command `xxx` on the saved input.

## Next Step Generation

- Adds `readno=<selected fch>` only when an fch is selected.
- Inherits `%mem` and `%nprocshared` / `%nproc` from the original template when present.
- Removes `%chk` from the next-step input.
- Writes a new file `input_next_<timestamp>.gjf` and updates the Next Step preview tab.
