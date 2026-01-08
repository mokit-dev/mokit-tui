CSS = """
    Screen {
        align: center middle;
    }
    
    #main-container {
        width: 95%;
        height: 95%;
        border: solid $primary;
        padding: 1;
    }
    
    #preview-box {
        height: 30%;
        border: solid $primary;
        margin: 1;
        padding: 1;
        background: $surface;
        overflow-y: auto;
    }
    
    #controls-container {  /* CHANGED: New container for collapsible */
        height: 40%;
        margin: 0;
        padding: 0;  /* Remove padding from container */
    }
    
    #controls-header {  /* NEW: Header for collapsible */
        height: 3;
        padding: 1;
        margin: 0;
    }
    
    #controls {  /* CHANGED: Now inside collapsible */
        padding: 1;
        height: 100%;
    }
    
    #buttons {
        dock: bottom;
        height: 10%;
        margin: 0;
        padding: 1;
        align: left bottom;
    }
    
    Button {
        margin: 0;
        color: $text;
        background: $surface;
        border: none;
    }
    .shortcut-hint {
        text-style: italic;
        color: $text-muted;
        margin-left: 1;
    }
    
    #method-select {
        width: 50;
        margin-right: 2;
    }
    
    Select, Input {
        margin-right: 2;
    }
    
    
    .label {
        width: 12;
    }
    
    #file-dialog, #output-dialog {
        width: 60%;
        height: 30%;
        border: thick $primary;
        background: $surface;
    }
    
    .dialog-title {
        text-align: center;
        padding: 1;
        text-style: bold;
    }
    .settings-title {
        margin-bottom: 0;
    }
    
    .option-group {
        margin: 0;
        padding: 0;
        border: none;
        height: auto;
    }
    
    .option-row {
        height: auto;
        margin: 0;
        align: left middle;
    }
    
    #keywords-input {
            width: 50;
        }

    .collapsible-title {
            padding-left: 1;
        }
    #next-step-container {
            height: auto;
            margin: 1;
            border: solid $primary;
            background: $surface;
        }
        
    #next-step-header {
            width: 100%;
            height: 3;
            padding: 0 1;
            background: $panel;  /* ADDED: background */
            border-bottom: solid $primary;  /* ADDED: border */
            align: center middle;
        }
        
    #next-step-title {
        text-align: left;
            content-align: left middle;
            width: 100%;
        }
        
    #next-step-content {
        padding: 1;
        height: auto;
        }
        
    #fch-select-container {
        height: auto;
            margin-top: 1;
        align: center middle;  /* ADDED: alignment */
        }
        
    .fch-select {
        width: 30;
        margin-right: 1;
    }
    """
