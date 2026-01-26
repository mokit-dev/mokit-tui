CSS = """
    Screen {
        align: center middle;
        background: $background;
    }

    Screen.dialog-overlay {
        background: transparent;
    }
    
    #main-container {
        width: 90%;
        height: 90%;
        padding: 2;
        margin: 1;
    }
    
    #preview-container {
        height: 85%;
        layout: horizontal;
        margin: 1 0;
    }
    
    #input-panel, #output-preview {
        height: 100%;
        width: 1fr;
        padding: 1;
        background: $surface;
    }

    #input-panel {
        border-right: solid $primary;
        layout: vertical;
    }

    #input-preview-tabs {
        height: 1fr;
    }

    #preview-box {
        height: 1fr;
        min-height: 12;
        padding-bottom: 1;
        overflow-y: auto;
    }

    #next-step-container {
        height: auto;
        max-height: 12;
        padding: 1;
        margin-top: 1;
        border: solid $primary;
        background: $surface;
        overflow-y: auto;
    }

    .is-hidden {
        display: none;
    }

    #next-step-controls {
        margin-top: 0;
        padding: 1 0;
    }

    #next-step-name-row {
        margin-top: 0;
    }


    #next-step-basename-input,
    #next-step-method-select,
    #next-step-fch-select {
        width: 1fr;
    }

    #next-step-preview {
        margin-top: 1;
    }
    
    #output-preview {
        border-left: solid $primary;
    }

    #output-preview-core-scroll,
    #output-preview-fch-scroll {
        height: 1fr;
        overflow-y: auto;
        margin-top: 1;
    }

    #output-preview-fch-title {
        margin-top: 1;
    }
    
    #buttons {
        height: auto;
        padding: 1;
        margin: 1 0 0 0;
        align: center middle;
    }
    
    #buttons Button {
        margin: 0 1;
        min-width: 12;
        text-align: center;
    }
    
    /*Button {
        margin: 1;
        padding: 1 2;
        width: 12;
        height: 3;
        text-align: center;
    }*/

    /*Button:hover {
        background: $primary;
        color: $surface;
        text-style: underline;
    }

    Button:focus {
        background: $primary;
        color: $surface;
    }

    Button.-primary {
        background: $primary;
        color: $surface;
        text-style: bold;
    }*/
    
    Select, Input {
        margin: 0 1;
        padding: 0 1;
    }

    #save-dialog .save-row {
        margin-top: 0;
    }

    #save-dialog .save-row-overwrite {
        margin-top: 1;
    }

    #save-dialog #save-current-file {
        width: 1fr;
        overflow: hidden;
    }

    #save-dialog .save-row Label {
        width: 10;
        margin-right: 1;
    }

    #save-dialog .save-row Input {
        width: 1fr;
        margin: 0 1 0 0;
    }

    #save-dialog Button {
        min-width: 10;
        margin: 0 1 0 0;
    }


    
    Select:hover, Input:hover {
        background: $surface;
    }
    
    Select:focus, Input:focus {
        background: $primary;
    }
    
    .label {
        width: 10;
        margin-right: 1;
        text-align: right;
    }
    
    .option-row {
        margin: 1 0;
        padding: 0;
        align: left middle;
    }
    
    #file-dialog, #output-dialog, #settings-dialog, #ui-settings-dialog, #next-step-dialog, #save-dialog {
        width: 50%;
        height: auto;
        min-height: 12;
        max-height: 18;
        background: $surface;
        opacity: 0.95;
        border: solid #777777;
    }
    
    .dialog-title {
        text-align: center;
        padding: 1;
        text-style: bold;
        margin-bottom: 1;
    }
    """
