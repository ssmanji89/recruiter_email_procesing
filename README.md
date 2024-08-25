# Automated Recruiter Email Processing System (MVC Architecture)

## Setup Instructions

1. Ensure you have Python 3.x installed.
2. Create a project in Google Cloud Console and enable the Gmail API.
3. Create OAuth 2.0 credentials (Client ID and Client Secret) for a Desktop application.
4. Download the credentials and save them as `credentials.json` in the project root directory.
5. Add your OpenAI API key to the `.env` file:
   
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

6. Run the OAuth setup script (you need to create this separately based on the previous oauth_setup.py):

   ```
   python oauth_setup.py
   ```

7. Follow the prompts to authorize the application.
8. Run the Flask application:

   ```
   python -m flask run
   ```

9. Open a web browser and navigate to `http://localhost:5000` to see the processed emails and generated resumes.

## Project Structure

- `app/`: Main application directory
  - `models/`: Data models
  - `views/`: View logic
  - `controllers/`: Business logic
  - `services/`: External service integrations
  - `templates/`: HTML templates
  - `static/`: Static files (CSS, JS, etc.)
- `venv/`: Virtual environment
- `README.md`: Project documentation
- `.env`: Environment variables (API keys)
- `.gitignore`: Git ignore file

## Troubleshooting

Check the application logs for detailed error messages and debugging information.

