#!/bin/bash

# Automated Recruiter Email Processing System - Phase 1 Setup
# This script sets up the initial environment for the project, including
# installing dependencies and creating the initial Python script for
# Google OAuth 2.0 authentication.

# Exit immediately if a command exits with a non-zero status
set -e

# Print commands and their arguments as they are executed
set -x

echo "Starting Phase 1 setup for Automated Recruiter Email Processing System"

# Create project directory
PROJECT_DIR="recruiter_email_processor"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

echo "Created project directory: $PROJECT_DIR"

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

echo "Virtual environment created and activated"

# Upgrade pip
pip install --upgrade pip

echo "Pip upgraded to the latest version"

# Install required packages
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client openai markdown2

echo "Installed required Python packages"

# Create initial Python script for OAuth 2.0 setup
cat << EOF > oauth_setup.py
import os
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def setup_oauth():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = Flow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds

if __name__ == '__main__':
    print("Running OAuth 2.0 setup...")
    creds = setup_oauth()
    print("OAuth 2.0 setup complete. Token saved to token.json")
EOF

echo "Created initial Python script: oauth_setup.py"

# Create a README file with instructions
cat << EOF > README.md
# Automated Recruiter Email Processing System

## Phase 1: Google OAuth 2.0 Setup

### Prerequisites
- Python 3.x
- Google Cloud Console project with Gmail API enabled
- OAuth 2.0 Client ID and Client Secret

### Setup Instructions

1. Create a project in Google Cloud Console and enable the Gmail API.
2. Create OAuth 2.0 credentials (Client ID and Client Secret) for a Desktop application.
3. Download the credentials and save them as \`credentials.json\` in this directory.
4. Run the OAuth setup script:

   \`\`\`
   python oauth_setup.py
   \`\`\`

5. Follow the prompts to authorize the application.
6. Once complete, a \`token.json\` file will be created with your access token.

### Next Steps
- Implement email retrieval using the Gmail API
- Develop resume generation logic with OpenAI GPT
- Create email response formatting using Markdown

EOF

echo "Created README.md with setup instructions"

# Create a .gitignore file
cat << EOF > .gitignore
# Virtual environment
venv/

# Python cache files
__pycache__/
*.pyc

# OAuth 2.0 credentials and tokens
credentials.json
token.json

# Environment variables
.env

# IDE-specific files
.vscode/
.idea/

# macOS-specific files
.DS_Store
EOF

echo "Created .gitignore file"

echo "Phase 1 setup complete. Please follow the instructions in README.md to continue."

echo "Extending setup for email retrieval and resume generation"

# Ensure we're in the project directory

# Install additional required packages
pip install python-dotenv

echo "Installed additional required packages"

# Create a .env file for storing API keys
cat << EOF > .env
# Add your OpenAI API key here
OPENAI_API_KEY=your_openai_api_key_here
EOF

echo "Created .env file for API keys"

# Create Python script for email retrieval and resume generation
cat << EOF > process_emails.py
import os
import base64
import re
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import openai
from dotenv import load_dotenv
import markdown2

# Load environment variables
load_dotenv()

# Set up OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    return build('gmail', 'v1', credentials=creds)

def get_recruiter_emails(service, user_id='me', max_results=10):
    try:
        # Search for recruiter emails
        query = "subject:(job OR opportunity OR position) newer_than:7d"
        results = service.users().messages().list(userId=user_id, q=query, maxResults=max_results).execute()
        messages = results.get('messages', [])

        if not messages:
            print("No recruiter emails found.")
            return []

        recruiter_emails = []
        for message in messages:
            msg = service.users().messages().get(userId=user_id, id=message['id']).execute()
            email_data = parse_email(msg)
            if email_data:
                recruiter_emails.append(email_data)

        return recruiter_emails

    except HttpError as error:
        print(f"An error occurred: {error}")
        return []

def parse_email(msg):
    payload = msg['payload']
    headers = payload['headers']

    subject = next(header['value'] for header in headers if header['name'] == 'Subject')
    sender = next(header['value'] for header in headers if header['name'] == 'From')
    
    # Extract email body
    if 'parts' in payload:
        parts = payload['parts']
        data = parts[0]['body']['data']
    else:
        data = payload['body']['data']
    
    body = base64.urlsafe_b64decode(data).decode('utf-8')

    # Extract job description and company information
    job_description = extract_job_description(body)
    company_info = extract_company_info(body)

    return {
        'subject': subject,
        'sender': sender,
        'body': body,
        'job_description': job_description,
        'company_info': company_info
    }

def extract_job_description(body):
    # Implement logic to extract job description from email body
    # This is a simplified example; you may need more sophisticated parsing
    match = re.search(r'Job Description:(.*?)(?=\n\n|\Z)', body, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""

def extract_company_info(body):
    # Implement logic to extract company information from email body
    # This is a simplified example; you may need more sophisticated parsing
    match = re.search(r'Company:(.*?)(?=\n\n|\Z)', body, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""

def generate_tailored_resume(job_description, company_info):
    prompt = f"""
    Given the following job description and company information, create a tailored resume in Markdown format:

    Job Description:
    {job_description}

    Company Information:
    {company_info}

    Generate a professional resume that highlights relevant skills and experiences for this specific job opportunity.
    Use Markdown formatting for structure and readability.
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a professional resume writer."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000
    )

    return response.choices[0].message['content']

def main():
    service = get_gmail_service()
    recruiter_emails = get_recruiter_emails(service)

    for email in recruiter_emails:
        print(f"Processing email: {email['subject']}")
        tailored_resume = generate_tailored_resume(email['job_description'], email['company_info'])
        
        # Convert Markdown to HTML
        html_resume = markdown2.markdown(tailored_resume)

        # Here you would typically save or send the tailored resume
        # For demonstration, we'll just print it
        print("Tailored Resume (Markdown):")
        print(tailored_resume)
        print("\nTailored Resume (HTML):")
        print(html_resume)

if __name__ == '__main__':
    main()
EOF

echo "Created process_emails.py script"

# Update README with new instructions
cat << EOF >> README.md

## Email Retrieval and Resume Generation

After setting up OAuth 2.0:

1. Add your OpenAI API key to the \`.env\` file:
   
   \`\`\`
   OPENAI_API_KEY=your_openai_api_key_here
   \`\`\`

2. Run the email processing script:

   \`\`\`
   python process_emails.py
   \`\`\`

This script will retrieve recruiter emails from your Gmail account, extract job descriptions and company information, and generate tailored resumes using OpenAI GPT.

EOF

echo "Updated README.md with new instructions"

echo "Extended setup complete. Please follow the updated instructions in README.md to continue."

echo "Virtual environment deactivated. Extended setup script finished."