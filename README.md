# Automated Recruiter Email Processing System

## Phase 1: Google OAuth 2.0 Setup

### Prerequisites
- Python 3.x
- Google Cloud Console project with Gmail API enabled
- OAuth 2.0 Client ID and Client Secret

### Setup Instructions

1. Create a project in Google Cloud Console and enable the Gmail API.
2. Create OAuth 2.0 credentials (Client ID and Client Secret) for a Desktop application.
3. Download the credentials and save them as `credentials.json` in this directory.
4. Run the OAuth setup script:

   ```
   python oauth_setup.py
   ```

5. Follow the prompts to authorize the application.
6. Once complete, a `token.json` file will be created with your access token.

### Next Steps
- Implement email retrieval using the Gmail API
- Develop resume generation logic with OpenAI GPT
- Create email response formatting using Markdown


## Email Retrieval and Resume Generation

After setting up OAuth 2.0:

1. Add your OpenAI API key to the `.env` file:
   
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

2. Run the email processing script:

   ```
   python process_emails.py
   ```

This script will retrieve recruiter emails from your Gmail account, extract job descriptions and company information, and generate tailored resumes using OpenAI GPT.

