#!/bin/bash

# Get the current directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Check if the virtual environment exists
if [ -d "venv" ]; then
    # Activate the environment and run the app
    source venv/bin/activate
    python main.py
else
    # Show error if venv is not found
    if command -v zenity &> /dev/null
    then
        zenity --error --text="Virtual environment not found! Please open a terminal in the project folder and run 'bash install.sh' first." --title="AI Robot OS - Error"
    else
        echo "Virtual environment not found! Please open a terminal in the project folder and run 'bash install.sh' first."
        # Keep terminal open to see the error if started from terminal
        sleep 5
    fi
fi
