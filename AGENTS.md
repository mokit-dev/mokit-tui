# AGENTS.md - MOKIT TUI Development Guidelines

## Project Overview
This is a Python Textual TUI application for MOKIT input generation. The app provides a terminal-based interface for generating quantum chemistry calculation inputs.

## Build/Development Commands

### Running the Application
```bash
python main.py <template_file>.gjf
```

### Debug Mode Options
```bash
# Auto-open settings modal on startup
python main.py template.gjf -s

# Auto-open next step modal on startup  
python main.py template.gjf -n

# Both auto-settings and auto-next-step
python main.py template.gjf -s -n
```

### Linting and Type Checking
```bash
ruff check          # Lint with ruff
ruff format         # Format code with ruff
ruff check --fix    # Auto-fix fixable ruff issues
# Note: pyrightconfig.json exists but pyright is not installed in this environment
```

### Testing
No formal test framework is currently configured. Test case files are located in `testcase/vn/` directory but appear to be example input files rather than unit tests.

To run a specific test case file:
```bash
python main.py testcase/vn/filename.py
```

Default testcase for agent-run checks:
```bash
python main.py testcase/vn/vn.gjf
```

## Code Style Guidelines

### Import Organization
- Standard library imports first
- Third-party imports next (textual, pathlib, etc.)
- Local imports last (no relative imports within same package)
- Group related imports together
- Avoid wildcard imports (`import *`) - current codebase has some but should be avoided
- Remove unused imports - run `ruff check --fix` to clean up
- Example order:
```python
import re
import sys
import argparse
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button
from textual import on

from parser import GJFParser
from gen import GJFGenerator
```

### Type Hints
- Use type hints for all function signatures and class attributes
- Import typing constructs as needed: `Dict`, `List`, `Tuple`, `Optional`
- Keep type checking mode at "basic" per pyrightconfig.json
- Example:
```python
def parse_gjf(filepath: str) -> Dict:
def generate_gjf(self, sections: Dict, options: Dict) -> str:
```

### Naming Conventions
- **Classes**: PascalCase (`GJFParser`, `InputPreview`)
- **Functions/Methods**: snake_case (`parse_gjf`, `load_template`)
- **Variables**: snake_case (`template_sections`, `input_file`)
- **Constants**: UPPER_SNAKE_CASE (rare in this codebase)
- **Private methods**: underscore prefix (`_do_auto_open_settings`)

### Class Structure
- Inherit from appropriate Textual base classes
- Use `@staticmethod` for utility methods that don't need self
- Use `reactive` decorators for Textual widget properties
- Include docstrings for all classes and public methods

### Error Handling
- Use try-except blocks for file operations and external processes
- Provide user-friendly error messages via `self.notify()` or `self.notify_persistent()`
- Handle `FileNotFoundError` for missing files
- Handle `subprocess.CalledProcessError` for external command failures
- Example pattern:
```python
try:
    # operation
except Exception as e:
    self.notify_persistent(f"Error: {str(e)}", severity="error")
```

### Textual-Specific Patterns
- Use `@on(Button.Pressed, "#button-id")` for button event handlers
- Use `self.query_one("#widget-id", WidgetType)` to get widget references
- Use `self.call_after_refresh()` for deferred UI updates
- Use `async def` callbacks for modal screen results
- Use `self.push_screen()` to show modal screens

### File Organization
- `main.py`: Main application class and entry point
- `parser.py`: File parsing logic (GJFParser)
- `gen.py`: File generation logic (GJFGenerator)  
- `widgets.py`: Custom Textual widgets
- `screens.py`: Modal screen classes
- `css.py`: CSS styling constants
- `workflow.py`: Workflow and utility functions

### String Formatting
- Use f-strings for string formatting
- Use markdown syntax for Textual display: `[b]bold[/b]`, `[dim]dim[/dim]`, `[green]●[/green]`
- Include severity levels in notifications: `"information"`, `"warning"`, `"error"`

### Configuration
- Application options stored in `self.options` dictionary
- Template file data stored in `self.template_sections` dictionary
- Use Path objects for file operations
- Default input file: `input.gjf`
- Default checkpoint file pattern: `input.chk`

### Development Notes
- The application uses Textual framework for TUI
- Backend execution calls `xxx` command (placeholder for actual quantum chemistry program)
- Template files use `mokit{}` syntax for options
- fch files are used for calculation step sequencing
- Output files are automatically detected and loaded alongside templates

### Docs Index
- Summary and links: `doc/index.md`
- UI features: `doc/features_ui.md`
- Input/IO features: `doc/features_io.md`
- Output preview summary: `doc/features_output.md`
- fch preview details: `doc/preview_fch.md`

### Type Checking Notes
- pyright is configured for "basic" mode in pyrightconfig.json
- Focus on type hints for public APIs and critical paths
- Do not over-optimize typing; accept type checker warnings when it keeps changes simpler

### Code Patterns to Follow
- Use `Path(filepath).name` for filename extraction
- Use `Path(filepath).exists()` for file existence checks
- Use `subprocess.run()` with `check=True` for external commands
- Use `self.query_one("#widget-id", WidgetType)` for widget access
- Use `self.call_after_refresh()` for deferred UI operations
- Store configuration in dictionaries (self.options, self.template_sections)
- Use string splitting and iteration for file parsing
- Use regex for pattern matching in content parsing
