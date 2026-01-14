CSS = """
    Screen {
        align: center middle;
        background: $background;
    }
    
    #main-container {
        width: 90%;
        height: 75%;
        padding: 2;
        margin: 1;
    }
    
    #preview-box {
        height: 40%;
        padding: 1;
        margin: 1 0;
        overflow-y: auto;
        background: $surface;
    }
    
    #buttons {
        dock: bottom;
        height: 20%;
        padding: 1;
        margin: 0;
        align: center middle;
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
    
    #file-dialog, #output-dialog, #settings-dialog, #next-step-dialog {
        width: 50%;
        height: 30%;
        background: $surface;
        opacity: 0.95;
    }
    
    .dialog-title {
        text-align: center;
        padding: 1;
        text-style: bold;
        margin-bottom: 1;
    }
    """
