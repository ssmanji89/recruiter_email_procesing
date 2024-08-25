#!/bin/bash

# Start the Recruiter Email Processing App

# Navigate to the project directory
cd "$(dirname "$0")"

# Activate the virtual environment
source venv/bin/activate

# Check if OAuth setup has been done
if [ ! -f "token.json" ]; then
    echo "OAuth setup not completed. Running oauth_setup.py..."
    python oauth_setup.py
fi

# Set Flask environment to development
export FLASK_ENV=development

# Start the Flask app
flask run