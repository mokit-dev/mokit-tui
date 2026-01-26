# UI Features

## Layout

- Left panel: input preview tabs, then the Next Step controls box.
- Right panel: output preview (unchanged).

## Input Preview

- The input preview displays the original template text, not regenerated content.
- Tabs include:
  - Input
  - Next Step (generated preview content)

## Next Step Controls

- Inline box under the input preview with selectors and buttons.
- Hidden by default and shown after pressing Next Step or Prepare.
- The generated Next Step input is shown in the Next Step tab, not in the box.
- Includes basename, method selector (default CASSCF), and fch file selection.

## Key Binds

- `n`: run Next Step (same as the Next Step button)
- `s`: save
- `r`: run
- `q` or `esc`: exit

## Save Button

- Save opens a modal to choose overwrite or save as a new file.
- The active tab controls which file is saved.
- Input tab overwrites the loaded template (or the last Save As target).
- Next Step tab overwrites the prepared next-step file.
- Save As writes to the user-entered filename and becomes the new file for that tab.

## Run Button

- Run executes `automr` on the active input tab.
- If the Input tab is active, it runs the original template file.
- If the Next Step tab is active, it runs the prepared next-step `.gjf` file.
- Output is written to `<input>.gjf.out` and shown in the output screen.

## UI Settings

- fch preview mode and margin are available via the UI Settings modal.
